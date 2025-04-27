import glob
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_elements(base_file_path):
    """
    Prepend header and append footer correctly for XLOG part files.
    """
    base_path, _ = os.path.splitext(base_file_path)
    part0_file = base_path + '_part0.xlog'

    logging.info(f"Processing adjust_elements for {base_file_path}")

    # Step 1: Read header lines from part0
    header_lines = []
    if os.path.exists(part0_file):
        with open(part0_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                header_lines = lines[:2]
            else:
                logging.error("Part0 file does not have enough lines for header.")
                return
    else:
        logging.error(f"Part 0 file {part0_file} not found.")
        return

    # Step 2: Read footer line (</log>) from last part
    part_files_pattern = base_path + '_part*.xlog'
    part_files = sorted(glob.glob(part_files_pattern))

    if not part_files:
        logging.error("No part files found.")
        return

    last_part_file = part_files[-1]

    footer_lines = []
    if os.path.exists(last_part_file):
        with open(last_part_file, 'r', encoding='utf-8') as file:
            temp_lines = file.readlines()
            if temp_lines:
                last_line = temp_lines[-1]
                if '</log>' in last_line:
                    footer_lines = [last_line]
                else:
                    logging.warning("Footer </log> tag not found in last part.")
            else:
                logging.error("Last part file is empty.")
                return
    else:
        logging.error(f"Last part file {last_part_file} not found.")
        return

    def prepend_content(file, lines_to_prepend):
        with open(file, 'r', encoding='utf-8') as original:
            original_content = original.read()
        with open(file, 'w', encoding='utf-8') as updated:
            updated.writelines(lines_to_prepend)
            updated.write(original_content)

    def append_content(file, lines_to_append):
        with open(file, 'a', encoding='utf-8') as updated:
            updated.writelines(lines_to_append)

    # Step 3: Process all parts
    for idx, part_file in enumerate(part_files):
        logging.info(f"Adjusting {part_file}")

        is_part0 = (part_file == part0_file)
        is_last_part = (part_file == last_part_file)

        if is_part0:
            # _part0: Only append footer
            append_content(part_file, footer_lines)
        elif is_last_part:
            # Last part: Only prepend header
            prepend_content(part_file, header_lines)
        else:
            # Middle parts: Prepend header and append footer
            prepend_content(part_file, header_lines)
            append_content(part_file, footer_lines)

    logging.info("Adjust elements completed successfully.")
