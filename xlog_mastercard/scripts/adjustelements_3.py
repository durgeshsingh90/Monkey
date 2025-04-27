import glob
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_elements(base_file_path):
    """
    Prepends XML declaration and <log> start tag,
    and appends </log> end tag to all XML part files.
    """
    base_path, _ = os.path.splitext(base_file_path)
    part0_file = base_path + '_part0.xml'

    logging.info(f"Processing adjust_elements for {base_file_path}")

    # Step 1: Read first 2 lines from part0.xml (header)
    lines_to_prepend = []
    if os.path.exists(part0_file):
        with open(part0_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) >= 2:
                lines_to_prepend = lines[:2]
            else:
                logging.error("Part0 file does not have enough lines to extract header.")
                return
    else:
        logging.error(f"Part 0 file {part0_file} not found.")
        return

    # Step 2: Read last line from last part (footer)
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

    if other_parts:
        last_part_file = other_parts[-1]
    else:
        last_part_file = part0_file  # only part0 exists

    lines_to_append = []
    if os.path.exists(last_part_file):
        with open(last_part_file, 'r', encoding='utf-8') as file:
            temp_lines = file.readlines()
            if temp_lines:
                last_line = temp_lines[-1]
                if '</log>' in last_line:
                    lines_to_append = [last_line]
                else:
                    logging.warning("Footer </log> tag not found in last part file.")
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

    all_parts = [part0_file] + other_parts

    # Step 3: Apply to all parts
    for part_file in all_parts:
        logging.info(f"Adjusting {part_file}")
        prepend_content(part_file, lines_to_prepend)
        append_content(part_file, lines_to_append)

    logging.info("Adjust elements completed successfully.")
