import os
import json
import xml.etree.ElementTree as ET
import time
import logging
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(PROJECT_ROOT, 'media', 'xlog_mastercard', 'unique_bm32_xlog.json')

# from xlog_mastercard.scripts.format_xlog_filter_6 import format_filtered_xml


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


def load_json_mapping(json_file_path):
    logging.debug(f"Loading JSON mapping from: {json_file_path}")
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
    logging.debug(f"Loaded {len(file_mappings)} conditions from JSON mapping.")
    return file_mappings

def filter_online_messages(part_xml_file, condition):
    logging.debug(f"Filtering file: {part_xml_file} for condition: {condition}")
    try:
        tree = ET.parse(part_xml_file)
    except ET.ParseError as e:
        logging.error(f"Error parsing {part_xml_file}: {e}")
        return []

    root = tree.getroot()
    filtered_entries = []

    all_log_entries = root.findall('.//LogEntry')

    previous_entry = None
    for log_entry in all_log_entries:
        found_match = False
        for field in log_entry.findall('.//Field'):
            name_attr = field.attrib.get('Name')
            if name_attr and name_attr.lstrip('0') == '32':
                value_elem = field.find('Value')
                if value_elem is not None and value_elem.text and value_elem.text.strip() == condition:
                    found_match = True
                    break

        if found_match:
            if previous_entry is not None:
                filtered_entries.append(previous_entry)  # add previous LogEntry first
            filtered_entries.append(log_entry)  # add the matching LogEntry
            logging.debug(f"Match found and added previous + current LogEntry from file: {part_xml_file}")

        previous_entry = log_entry  # Move previous pointer forward

    logging.debug(f"Total {len(filtered_entries)} LogEntries collected for condition {condition}")
    return filtered_entries



def indent(elem, level=0):
    """Helper to pretty format XML with 4 spaces indentation."""
    i = "\n" + level*"    "  # 4 spaces
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        for child in elem:
            indent(child, level+1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i
    return elem

def write_filtered_file(base_path, condition, part_xml_file, filtered_messages):
    base_name, ext = os.path.splitext(os.path.basename(part_xml_file))
    base_name = '_'.join(base_name.split('_')[:-1])
    output_file = os.path.join(base_path, f"{base_name}_filtered_{condition}{ext}")

    # Read the first line from the original part0 (or any part) file
    with open(part_xml_file, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()

    logging.debug(f"First line copied from {part_xml_file}: {first_line}")

    # Create XML structure under <Log>
    log_elem = ET.Element("Log")

    for message in filtered_messages:
        log_elem.append(message)

    # Indent the XML tree nicely
    indent(log_elem)

    # Write manually: first <xmltag> line, then pretty printed <Log> and <LogEntry>
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(first_line + "\n")  # <xmltag> line
        f.write(ET.tostring(log_elem, encoding='unicode', method='xml'))  # pretty printed <Log>

    logging.info(f"Filtered file written: {output_file}")
    return output_file



def filter_by_conditions(conditions, uploaded_file_path):
    start_time = time.time()

    logging.info(f"Starting filtering for {len(conditions)} conditions.")
    output_base_path = os.path.dirname(JSON_FILE_PATH)
    condition_file_map = load_json_mapping(JSON_FILE_PATH)

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
                part_file = futures[future]
                try:
                    part_filtered_messages = future.result()
                    if part_filtered_messages:
                        logging.debug(f"{len(part_filtered_messages)} entries found in {part_file}")
                    else:
                        logging.debug(f"No entries found in {part_file} for condition {condition}")
                    filtered_messages.extend(part_filtered_messages)
                except Exception as exc:
                    logging.error(f"Error in part file '{part_file}': {exc}")

        if filtered_messages:
            output_file = write_filtered_file(output_base_path, condition, part_files[0], filtered_messages)
            # format_filtered_xml(output_file, uploaded_file_path)
            generated_files.append(output_file)
        else:
            logging.warning(f"No messages matched for condition {condition}, skipping file creation.")

    if not generated_files:
        logging.warning("No filtered files were generated. ZIP will be empty!")

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
            logging.debug(f"Deleted temporary file: {file}")

    end_time = time.time()
    logging.info(f"Filtering completed in {end_time - start_time:.2f} seconds")
    logging.info(f"Filtered ZIP created: {zip_filename}")

    return zip_filename
