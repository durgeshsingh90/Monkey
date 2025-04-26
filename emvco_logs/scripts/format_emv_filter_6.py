import glob
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_filtered_xml(filtered_file_path, base_uploaded_file_path):
    """
    Prepend starting tags and append ending tags to the filtered XML file.
    
    :param filtered_file_path: Path to the filtered XML file generated after conditions
    :param base_uploaded_file_path: Original uploaded XML path (to fetch part0 and last part)
    """
    base_path, _ = os.path.splitext(base_uploaded_file_path)
    part0_file = base_path + '_part0.xml'

    # Read header from _part0
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

    # Find last part file
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

    # Prepend and append to the filtered file
    prepend_content(filtered_file_path, lines_to_copy)
    append_content(filtered_file_path, lines_to_append)

    logging.info(f"Formatted {filtered_file_path} successfully.")

def prepend_content(file, lines_to_prepend):
    with open(file, 'r', encoding='utf-8') as original:
        original_content = original.read()
    with open(file, 'w', encoding='utf-8') as updated:
        updated.writelines(lines_to_prepend)
        updated.write(original_content)

def append_content(file, lines_to_append):
    with open(file, 'a', encoding='utf-8') as updated:
        updated.writelines(lines_to_append)
