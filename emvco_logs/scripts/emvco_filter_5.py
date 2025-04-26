import os
import json
import xml.etree.ElementTree as ET
import time
import logging
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def element_to_string(element):
    """Convert element text and all subelement text to a single string."""
    content = []
    for elem in element.iter():
        if elem.text:
            content.append(elem.text.strip())
    return " ".join(content)

def evaluate_conditions(content, conditions):
    """Evaluate complex conditions within the given content."""
    def parse_condition(condition):
        if ' AND ' in condition:
            sub_conditions = condition.split(' AND ')
            return all(parse_condition(sub) for sub in sub_conditions)
        elif ' OR ' in condition:
            sub_conditions = condition.split(' OR ')
            return any(parse_condition(sub) for sub in sub_conditions)
        elif ' NOT ' in condition:
            sub_conditions = condition.split(' NOT ')
            return not parse_condition(sub_conditions[1])
        else:
            return condition in content

    return parse_condition(conditions)

def filter_online_messages(part_xml_file, condition):
    try:
        tree = ET.parse(part_xml_file)
    except ET.ParseError as e:
        logging.error(f"Error parsing {part_xml_file}: {e}")
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

def load_json_mapping(json_file_path):
    with open(json_file_path, 'r') as f:
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
    return output_file

def filter_by_conditions(json_file_path, conditions):
    """
    Main callable function to filter XML messages based on DE032 conditions.
    :param json_file_path: Path to unique_bm32_emvco.json
    :param conditions: List of DE032 values or conditions to filter
    """
    start_time = time.time()

    output_base_path = os.path.dirname(json_file_path)
    condition_file_map = load_json_mapping(json_file_path)

    generated_files = []

    for idx, condition in enumerate(conditions, start=1):
        logging.info(f"Processing condition {idx}/{len(conditions)}: {condition}")
        filtered_messages = []

        part_files = condition_file_map.get(condition, [])
        if not part_files:
            logging.warning(f"No part files found for condition '{condition}'")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(filter_online_messages, part_file, condition): part_file for part_file in part_files}
            for future in as_completed(futures):
                try:
                    part_filtered_messages = future.result()
                    filtered_messages.extend(part_filtered_messages)
                except Exception as exc:
                    logging.error(f"Error in part file '{futures[future]}': {exc}")

        if filtered_messages:
            output_file = write_filtered_file(output_base_path, condition, part_files[0], filtered_messages)
            generated_files.append(output_file)

    # Zip all filtered files
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    zip_filename = os.path.join(output_base_path, f"filtered_files_psp_{timestamp}.zip")

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in generated_files:
            zipf.write(file, os.path.basename(file))
            logging.info(f"Added '{file}' to ZIP.")
    
    # Clean up individual XMLs after zipping
    for file in generated_files:
        if os.path.exists(file):
            os.remove(file)

    end_time = time.time()
    logging.info(f"Filtering completed. Total time: {end_time - start_time:.2f} seconds")
    logging.info(f"Filtered ZIP created: {zip_filename}")

    return zip_filename
