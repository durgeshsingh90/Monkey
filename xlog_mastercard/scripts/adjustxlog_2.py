import os
import logging
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def adjust_file(file_path):
    """
    Validates and slightly adjusts split .xlog files if necessary.
    Since each file after splitting already contains one <logEntry>, we only ensure proper formatting.
    """
    base_filepath, ext = os.path.splitext(file_path)
    split_folder = f"{base_filepath}_split"

    if not os.path.exists(split_folder):
        logging.error(f"Split folder {split_folder} does not exist!")
        return

    part_files = sorted([f for f in os.listdir(split_folder) if f.endswith('.xlog')])

    for filename in part_files:
        part_path = os.path.join(split_folder, filename)
        logging.debug(f"Validating {part_path}")

        try:
            # Try parsing to ensure it is valid XML
            tree = ET.parse(part_path)
            root = tree.getroot()

            if root.tag != 'log':
                logging.warning(f"Root tag is not <log> in {filename}")

            # Save again to clean formatting
            tree.write(part_path, encoding='utf-8', xml_declaration=True)
            logging.info(f"Validated and formatted {filename}")

        except ET.ParseError as e:
            logging.error(f"Parse error in {filename}: {e}")
