# emvco_logs/scripts/fix_filtered_file.py

import os
import glob
import logging

logger = logging.getLogger(__name__)

def fix_filtered_file(base_filename, specific_file):
    """
    Prepend content from part0 and append content from the last part to a specific filtered file.
    """

    if not base_filename.endswith('.xml'):
        raise ValueError('Base filename must be a .xml file')

    if not os.path.exists(specific_file):
        raise FileNotFoundError(f"Specific file '{specific_file}' not found")

    base_path = base_filename[:-4]  # Remove .xml

    part0_file = base_path + '_part0.xml'
    if not os.path.exists(part0_file):
        raise FileNotFoundError(f"Part0 file '{part0_file}' not found")

    # Read up to <OnlineMessageList> from part0
    lines_to_copy = []
    with open(part0_file, 'r', encoding='utf-8') as file:
        for line in file:
            lines_to_copy.append(line)
            if '<OnlineMessageList>' in line:
                break

    # Find the last part file
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

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
    else:
        raise FileNotFoundError("No other part files found to get footer content.")

    # Prepend content
    with open(specific_file, 'r', encoding='utf-8') as original:
        original_content = original.read()

    with open(specific_file, 'w', encoding='utf-8') as updated:
        updated.writelines(lines_to_copy)
        updated.write(original_content)

    # Append content
    with open(specific_file, 'a', encoding='utf-8') as updated:
        updated.writelines(lines_to_append)

    logger.info(f"Successfully prepended and appended content to {specific_file}")
    return specific_file
