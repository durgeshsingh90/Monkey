import glob
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def adjust_elements(base_file_path):
    """
    Prepends initial tags and appends final tags to all XML part files
    after splitting and adjusting unclosed OnlineMessage elements.
    """
    base_path, _ = os.path.splitext(base_file_path)
    part0_file = base_path + '_part0.xml'

    logging.info(f"Processing adjust_elements for {base_file_path}")

    # Read up to <OnlineMessageList> from _part0
    lines_to_copy = []
    if os.path.exists(part0_file):
        with open(part0_file, 'r', encoding='utf-8') as file:
            for line in file:
                lines_to_copy.append(line)
                if '<OnlineMessageList>' in line:
                    break
    else:
        logging.error(f"Part 0 file {part0_file} not found.")
        return

    # Find other parts
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

    # Read from </OnlineMessageList> in last part
    lines_to_append = []
    if other_parts:
        last_part_file = other_parts[-1]
        with open(last_part_file, 'r', encoding='utf-8') as file:
            recording = False
            for line in file:
                if recording:
                    lines_to_append.append(line)
                if '</OnlineMessageList>' in line:
                    recording = True
                    lines_to_append.append(line)

    def prepend_content(file, lines_to_prepend):
        with open(file, 'r', encoding='utf-8') as original:
            original_content = original.read()
        with open(file, 'w', encoding='utf-8') as updated:
            updated.writelines(lines_to_prepend)
            updated.write(original_content)

    def append_content(file, lines_to_append):
        with open(file, 'a', encoding='utf-8') as updated:
            updated.writelines(lines_to_append)

    # Prepend lines to other parts
    for part_file in other_parts:
        prepend_content(part_file, lines_to_copy)

    # Append lines to all except last part
    for part_file in [part0_file] + other_parts[:-1]:
        append_content(part_file, lines_to_append)

    logging.info("Adjust elements completed.")
