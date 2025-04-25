# emvco_logs/scripts/filter_de032_emvco.py

import os
import json
import xml.etree.ElementTree as ET
import time
import logging
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

def element_to_string(element):
    content = []
    for elem in element.iter():
        if elem.text:
            content.append(elem.text.strip())
    return " ".join(content)

def evaluate_conditions(content, conditions):
    def parse_condition(condition):
        if ' AND ' in condition:
            return all(parse_condition(sub) for sub in condition.split(' AND '))
        elif ' OR ' in condition:
            return any(parse_condition(sub) for sub in condition.split(' OR '))
        elif ' NOT ' in condition:
            return not parse_condition(condition.split(' NOT ')[1])
        else:
            return condition in content

    return parse_condition(conditions)

def filter_online_messages(part_xml_file, condition):
    try:
        tree = ET.parse(part_xml_file)
    except ET.ParseError as e:
        logger.error(f"Error parsing {part_xml_file}: {e}")
        return []

    root = tree.getroot()
    online_message_list = root.find('OnlineMessageList')
    filtered_messages = []

    if online_message_list is not None:
        keep_message = False
        for online_message in online_message_list.findall('OnlineMessage'):
            content = element_to_string(online_message)
            if evaluate_conditions(content, condition):
                keep_message = True
                filtered_messages.append(online_message)
            elif keep_message:
                filtered_messages.append(online_message)
                keep_message = False

    return filtered_messages

def load_json_mapping(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    file_mappings = {}
    for file_info in data['file_level_counts']:
        file_path = file_info['file']
        counts = file_info['counts']
        for condition, count in counts.items():
            if condition not in file_mappings:
                file_mappings[condition] = []
            file_mappings[condition].append(file_path)
    return file_mappings

def write_filtered_file(base_path, condition, part_xml_file, filtered_messages):
    base_name, ext = os.path.splitext(os.path.basename(part_xml_file))
    base_name = '_'.join(base_name.split('_')[:-1])
    output_file = os.path.join(base_path, f"{base_name}_filtered_{condition}{ext}")

    new_tree = ET.ElementTree(ET.Element("Root"))
    new_root = new_tree.getroot()
    online_message_list = ET.SubElement(new_root, "OnlineMessageList")

    for message in filtered_messages:
        online_message_list.append(message)

    new_tree.write(output_file, encoding='utf-8', xml_declaration=True)
    logger.info(f"Filtered file saved: {output_file}")
    return output_file

def filter_conditions_and_zip(json_file, conditions, output_base_path):
    start_time = time.time()

    if not os.path.exists(json_file):
        raise FileNotFoundError(f"JSON file {json_file} not found.")

    condition_file_map = load_json_mapping(json_file)
    first_condition_files = condition_file_map.get(conditions[0], [])
    
    if first_condition_files:
        first_file = first_condition_files[0]
        base_name = os.path.splitext(os.path.basename(first_file))[0]
        base_name = '_'.join(base_name.split('_')[:-1])
    else:
        base_name = "filtered_files"

    generated_files = []

    for idx, condition in enumerate(conditions, start=1):
        logger.info(f"Processing condition {idx}/{len(conditions)}: {condition}")
        filtered_messages = []

        part_files = condition_file_map.get(condition, [])
        if not part_files:
            logger.warning(f"No part files for condition '{condition}'")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(filter_online_messages, part_file, condition): part_file for part_file in part_files}
            for future in as_completed(futures):
                try:
                    part_filtered = future.result()
                    filtered_messages.extend(part_filtered)
                except Exception as e:
                    logger.error(f"Error processing {futures[future]}: {e}")

        if filtered_messages:
            output_file = write_filtered_file(output_base_path, condition, part_files[0], filtered_messages)
            generated_files.append(output_file)

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    zip_filename = f"{base_name}_pspfiltered_{timestamp}.zip"
    zip_path = os.path.join(output_base_path, zip_filename)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in generated_files:
            zipf.write(file, os.path.basename(file))
            logger.info(f"Added {file} to zip.")

    for file in generated_files:
        os.remove(file)
        logger.info(f"Deleted {file}")

    elapsed_time = time.time() - start_time
    logger.info(f"Completed all filtering in {elapsed_time:.2f} seconds. Zip file: {zip_path}")
    return zip_path
