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

    # Step 1: Read header (everything BEFORE first <LogEntry>)
    lines_to_prepend = []
    if os.path.exists(part0_file):
        with open(part0_file, 'r', encoding='utf-8') as file:
            for line in file:
                lines_to_prepend.append(line)
                if '<LogEntry' in line:  # very important: '<LogEntry' not exactly '<LogEntry>'
                    lines_to_prepend.pop()  # Remove the <LogEntry> line itself
                    break
    else:
        logging.error(f"Part 0 file {part0_file} not found.")
        return

    # Step 2: Find footer (everything AFTER last </LogEntry>)
    part_files_pattern = base_path + '_part[1-9]*.xml'
    other_parts = sorted(glob.glob(part_files_pattern))

    lines_to_append = []
    if other_parts:
        last_part_file = other_parts[-1]
    else:
        last_part_file = part0_file  # If only part0 exists

    found_last_logentry = False
    if os.path.exists(last_part_file):
        with open(last_part_file, 'r', encoding='utf-8') as file:
            temp_lines = file.readlines()
            for idx in reversed(range(len(temp_lines))):
                if '</LogEntry>' in temp_lines[idx] and not found_last_logentry:
                    found_last_logentry = True
                    continue  # skip the </LogEntry> line itself
                if found_last_logentry:
                    lines_to_append.insert(0, temp_lines[idx])  # Prepend lines after </LogEntry>
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

    # Step 3: Apply prepend and append to all parts
    for part_file in all_parts:
        logging.info(f"Adjusting {part_file}")
        prepend_content(part_file, lines_to_prepend)
        append_content(part_file, lines_to_append)

    logging.info("Adjust elements completed successfully.")
