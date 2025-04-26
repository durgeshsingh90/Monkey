import os
import logging
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

def process_file(file_path):
    """
    Splits the uploaded .xlog XML file into individual logEntry XML files.
    Each <logEntry> is saved separately, wrapped inside a <log> root.
    """
    base_name, ext = os.path.splitext(file_path)
    output_folder = f"{base_name}_split"
    os.makedirs(output_folder, exist_ok=True)

    logging.info(f"Starting to split XLOG (XML format) file: {file_path}")

    tree = ET.parse(file_path)
    root = tree.getroot()

    block_index = 0
    for log_entry in root.findall('logEntry'):
        block_filename = os.path.join(output_folder, f"block_{block_index:04}.xlog")
        logging.debug(f"Saving logEntry {block_index} to file: {block_filename}")

        # Wrap it inside <log> root
        new_log_root = ET.Element('log')
        new_log_root.append(log_entry)

        new_tree = ET.ElementTree(new_log_root)
        new_tree.write(block_filename, encoding='utf-8', xml_declaration=True)

        block_index += 1

    logging.info(f"Splitting complete. Total logEntry blocks created: {block_index}")
