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
    logging.info(f"Starting formatting of {filtered_file_path}")

    base_path, _ = os.path.splitext(base_uploaded_file_path)
    part0_file = base_path + '_part0.xml'

    # Step 0: Clean the filtered XML first (remove XML declaration and <Root> tags)
    clean_filtered_xml(filtered_file_path)

    # Step 1: Read header from part0
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

    # Step 2: Find footer
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

    lines_to_append = []
    if other_parts:
        last_part_file = other_parts[-1]
        logging.info(f"Using last part file {last_part_file} for footer")
    else:
        last_part_file = part0_file
        logging.info(f"No other parts found. Using part0 file {part0_file} for footer")

    with open(last_part_file, 'r', encoding='utf-8') as file:
        recording = False
        for line in file:
            if recording:
                lines_to_append.append(line)
            if '</OnlineMessageList>' in line:
                recording = True
                lines_to_append.append(line)

    # Step 3: Prepend and append content
    prepend_content(filtered_file_path, lines_to_copy)
    append_content(filtered_file_path, lines_to_append)

    logging.info(f"Formatted {filtered_file_path} successfully.")

def clean_filtered_xml(file_path):
    """Remove <?xml ... ?>, <Root>, <OnlineMessageList>, and associated end tags from filtered XML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if '<?xml' in line:
            logging.info(f"Deleting line: {line.strip()}")
            continue
        if '<Root><OnlineMessageList>' in line:
            logging.info(f"Replacing line: {line.strip()}")
            line = line.replace('<Root><OnlineMessageList>', '    ')
        if '</OnlineMessageList></Root>' in line:
            logging.info(f"Deleting line: {line.strip()}")
            line = line.replace('</OnlineMessageList></Root>', '')
        new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def prepend_content(file, lines_to_prepend):
    logging.info("Prepending the following lines:")
    for line in lines_to_prepend:
        logging.info(line.strip())

    with open(file, 'r', encoding='utf-8') as original:
        original_content = original.read()
    with open(file, 'w', encoding='utf-8') as updated:
        updated.writelines(lines_to_prepend)
        updated.write(original_content)

def append_content(file, lines_to_append):
    logging.info("Appending the following lines:")
    for line in lines_to_append:
        logging.info(line.strip())

    with open(file, 'a', encoding='utf-8') as updated:
        updated.writelines(lines_to_append)

# Uncomment the next lines and call the function with your paths to test
# format_filtered_xml('path_to_filtered_file.xml', 'path_to_base_uploaded_file.xml')
