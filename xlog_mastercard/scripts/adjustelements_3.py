import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def adjust_elements(base_file_path):
    """
    Ensures each split part of the .xlog has a proper XML structure:
    - part0: ensure ends with </log>
    - middle parts: add XML header + <log> + </log>
    - last part: add XML header + <log> + </log>
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

    if len(part_files) == 1:
        logger.info("Only one part exists. No adjustment needed.")
        return

    part0 = part_files[0]
    last_part = part_files[-1]
    middle_parts = part_files[1:-1]

    logger.info(f"Total parts: {len(part_files)} (Middle parts to fix: {len(middle_parts)})")

    # --- Fix Part0 ---
    logger.debug(f"Checking footer for {part0}")
    with open(part0, 'r', encoding='utf-8') as file:
        content = file.read()

    if not content.strip().endswith('</log>'):
        logger.info(f"Adding missing </log> to {part0}")
        content = content.rstrip() + '\n</log>\n'
        with open(part0, 'w', encoding='utf-8') as file:
            file.write(content)

    # --- Fix Middle Parts ---
    for part_file in middle_parts:
        logger.debug(f"Fixing {part_file}")

        with open(part_file, 'r', encoding='utf-8') as file:
            content = file.read()

        new_content = content

        # Add header at the top
        if not new_content.lstrip().startswith('<?xml'):
            logger.info(f"Adding XML declaration to {part_file}")
            new_content = '<?xml version="1.0" encoding="utf-8"?>\n<log>\n' + new_content

        # Add footer at the end
        if not new_content.strip().endswith('</log>'):
            logger.info(f"Adding closing </log> to {part_file}")
            new_content = new_content.rstrip() + '\n</log>\n'

        with open(part_file, 'w', encoding='utf-8') as file:
            file.write(new_content)

        logger.debug(f"Adjusted {part_file} successfully.")

    # --- Fix Last Part ---
    logger.debug(f"Fixing last part: {last_part}")

    with open(last_part, 'r', encoding='utf-8') as file:
        content = file.read()

    new_content = content

    # Add header at the top if missing
    if not new_content.lstrip().startswith('<?xml'):
        logger.info(f"Adding XML declaration to {last_part}")
        new_content = '<?xml version="1.0" encoding="utf-8"?>\n<log>\n' + new_content

    # Add footer at the end if missing
    if not new_content.strip().endswith('</log>'):
        logger.info(f"Adding closing </log> to {last_part}")
        new_content = new_content.rstrip() + '\n</log>\n'

    with open(last_part, 'w', encoding='utf-8') as file:
        file.write(new_content)

    logger.info("adjust_elements completed successfully for all parts.")
