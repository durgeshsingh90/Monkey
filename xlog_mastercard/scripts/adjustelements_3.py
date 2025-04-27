import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def adjust_elements(base_file_path):
    """
    Ensures each split part of the .xlog has a proper XML structure:
    - XML declaration at the top
    - <log> opening tag after declaration
    - </log> closing tag at the end
    This replaces adjustelements_3.py for xlog_mastercard project.
    """
    base_path, _ = os.path.splitext(base_file_path)
    part_number = 0
    part_files = []

    logger.info(f"Starting adjust_elements for {base_file_path}")

    # Gather all part files
    while True:
        part_file_path = f"{base_path}_part{part_number}.xlog"
        if not os.path.exists(part_file_path):
            break
        part_files.append(part_file_path)
        part_number += 1

    if not part_files:
        logger.error(f"No part files found for {base_file_path}. Exiting adjust_elements.")
        return

    # Fix each part
    for part_file in part_files:
        logger.debug(f"Adjusting {part_file}")

        with open(part_file, 'r', encoding='utf-8') as file:
            content = file.read()

        modified = False
        new_content = content

        # Ensure XML declaration
        if not new_content.lstrip().startswith('<?xml'):
            logger.info(f"Missing XML declaration in {part_file}. Adding it.")
            new_content = '<?xml version="1.0" encoding="utf-8"?>\n' + new_content
            modified = True

        # Ensure <log> tag at top
        lines = new_content.splitlines()
        if len(lines) < 2 or '<log>' not in lines[1]:
            logger.info(f"Missing <log> tag in {part_file}. Adding it.")
            new_content = lines[0] + '\n<log>\n' + '\n'.join(lines[1:])
            modified = True

        # Ensure </log> tag at bottom
        if not new_content.strip().endswith('</log>'):
            logger.info(f"Missing </log> tag in {part_file}. Adding it.")
            new_content = new_content.rstrip() + '\n</log>\n'
            modified = True

        if modified:
            with open(part_file, 'w', encoding='utf-8') as file:
                file.write(new_content)
            logger.debug(f"Adjusted {part_file} successfully.")

    logger.info("adjust_elements completed successfully for all parts.")

