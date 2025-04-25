# emvco_logs/scripts/adjustelements_3.py

import glob
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

def adjust_elements(file_path):
    """
    Prepend <OnlineMessageList> header and append footer to EMVCo part files.
    """
    if not file_path.endswith('.xml'):
        raise ValueError('Provided file must have a .xml extension.')

    # Remove the .xml extension to get the base path
    base_path = file_path[:-4]

    part0_suffix = '_part0.xml'
    part0_file = base_path + part0_suffix

    # Read up to <OnlineMessageList> from part0
    lines_to_copy = []
    with open(part0_file, 'r', encoding='utf-8') as file:
        for line in file:
            lines_to_copy.append(line)
            if '<OnlineMessageList>' in line:
                break

    # Find all part files except _part0
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

    # Read footer from the last part
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

    # Helper to prepend content
    def prepend_content(file, lines_to_prepend):
        with open(file, 'r', encoding='utf-8') as original:
            original_content = original.read()

        with open(file, 'w', encoding='utf-8') as updated:
            updated.writelines(lines_to_prepend)
            updated.write(original_content)

    # Helper to append content
    def append_content(file, lines_to_append):
        with open(file, 'a', encoding='utf-8') as updated:
            updated.writelines(lines_to_append)

    # Prepend header to all parts except part0
    for part_file in other_parts:
        prepend_content(part_file, lines_to_copy)

    # Append footer to all parts except last part
    for part_file in [part0_file] + other_parts[:-1]:
        append_content(part_file, lines_to_append)

    logger.info("Header and footer successfully adjusted in all EMVCo part files.")
