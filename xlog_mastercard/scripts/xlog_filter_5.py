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

# Global path for JSON
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_FILE_PATH = os.path.join(PROJECT_ROOT, 'media', 'xlog_mastercard', 'unique_bm32_xlog.json')

# from xlog_mastercard.scripts.format_xlog_filter import format_filtered_xml_xlog

def find_de32_value(log_entry):
    """Find DE032 value inside a <LogEntry>."""
    for field in log_entry.findall('.//Field[@Name="32"]'):
        value_elem = field.find('Value')
        if value_elem is not None and value_elem.text:
            return value_elem.text.strip()
    return None

def filter_log_entries(part_xml_file, condition):
    try:
        tree = ET.parse(part_xml_file)
    except ET.ParseError as e:
        logging.error(f"Error parsing {part_xml_file}: {e}")
        return []

    root = tree.getroot()
    log = root.find('Log')
    filtered_entries = []

    if log is not None:
        for log_entry in log.findall('LogEntry'):
            de32_value = find_de32_value(log_entry)
            if de32_value == condition:
                filtered_entries.append(log_entry)

    return filtered_entries

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

def write_filtered_file(base_path, condition, part_xml_file, filtered_entries):
    base_name, ext = os.path.splitext(os.path.basename(part_xml_file))
    base_name = '_'.join(base_name.split('_')[:-1])
    output_file = os.path.join(base_path, f"{base_name}_filtered_{condition}{ext}")

    new_tree = ET.ElementTree(ET.Element("xmltag"))
    new_root = new_tree.getroot()
    log_elem = ET.SubElement(new_root, "Log")

    for entry in filtered_entries:
        log_elem.append(entry)

    new_tree.write(output_file, encoding='utf-8', xml_declaration=True)
    return output_file

def filter_by_conditions(conditions, uploaded_file_path):
    start_time = time.time()

    output_base_path = os.path.dirname(JSON_FILE_PATH)
    condition_file_map = load_json_mapping(JSON_FILE_PATH)

    generated_files = []

    for idx, condition in enumerate(conditions, start=1):
        logging.info(f"Processing condition {idx}/{len(conditions)}: {condition}")
        filtered_entries = []

        part_files = condition_file_map.get(condition, [])
        if not part_files:
            logging.warning(f"No part files found for condition '{condition}'")
            continue

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(filter_log_entries, part_file, condition): part_file for part_file in part_files}
            for future in as_completed(futures):
                try:
                    part_filtered_entries = future.result()
                    filtered_entries.extend(part_filtered_entries)
                except Exception as exc:
                    logging.error(f"Error in part file '{futures[future]}': {exc}")

        if filtered_entries:
            output_file = write_filtered_file(output_base_path, condition, part_files[0], filtered_entries)
            # Format the filtered XML before zipping
            # format_filtered_xml_xlog(output_file, uploaded_file_path)
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
