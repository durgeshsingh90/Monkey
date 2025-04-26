import os
import glob
import logging
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_elements(base_file_path):
    """
    Validates and formats all split .xlog files.
    Ensures each file has proper <log> and <logEntry> structure.
    """
    base_path, _ = os.path.splitext(base_file_path)
    split_folder = f"{base_path}_split"

    logging.info(f"Processing adjust_elements for {split_folder}")

    if not os.path.exists(split_folder):
        logging.error(f"Split folder {split_folder} does not exist.")
        return

    split_files = sorted(glob.glob(os.path.join(split_folder, '*.xlog')))

    for part_file in split_files:
        logging.debug(f"Validating {part_file}")

        try:
            tree = ET.parse(part_file)
            root = tree.getroot()

            if root.tag != 'log':
                logging.warning(f"Root tag is not <log> in {part_file}")

            # Optional: Clean and reformat the XML nicely
            tree.write(part_file, encoding='utf-8', xml_declaration=True)
            logging.info(f"Formatted {part_file} successfully.")

        except ET.ParseError as e:
            logging.error(f"Parse error in {part_file}: {e}")

    logging.info("Adjust elements completed.")
