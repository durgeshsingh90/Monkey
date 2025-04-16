import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

def read_file_with_fallback(file_path):
    encodings = ['utf-8', 'ISO-8859-1', 'windows-1252']
    for enc in encodings:
        try:
            logging.debug(f"Trying to read file: {file_path} with encoding: {enc}")
            with open(file_path, 'r', encoding=enc) as file:
                return file.readlines()
        except UnicodeDecodeError:
            logging.debug(f"Failed to read file: {file_path} with encoding: {enc}")
            continue
    raise ValueError(f"Could not read the file: {file_path} with the tried encodings.")

def get_total_parts(file_path):
    part_number = 0
    while True:
        part_file_name = f"{os.path.splitext(file_path)[0]}_part{part_number}.html"
        if not os.path.exists(part_file_name):
            break  # No more part files available
        part_number += 1
    logging.debug(f"Total parts found: {part_number}")
    return part_number

def process_html_file(file_path, total_parts):
    for part_number in range(total_parts):
        part_file_name = f"{os.path.splitext(file_path)[0]}_part{part_number}.html"
        next_part_file_name = f"{os.path.splitext(file_path)[0]}_part{part_number + 1}.html"
        
        logging.debug(f"Reading part file: {part_file_name}")
        lines = read_file_with_fallback(part_file_name)

        # Check if the lines are empty (meaning there's nothing to process)
        if not lines:
            logging.debug(f"No content in {part_file_name}, stopping processing.")
            break

        parts_to_append = []
        found_br_tag = False

        for line in reversed(lines):
            if line.strip() == "<BR></BR>":
                found_br_tag = True
                break  # Stop if we find <BR></BR>
            parts_to_append.append(line.strip())  # Collect lines before <BR></BR>
        
        if found_br_tag:
            logging.debug(f"Found <BR></BR> in {part_file_name}. Snatched lines: {len(parts_to_append)}")
            parts_to_append.reverse()  # Reverse to keep original order for appending
            
            # Read existing contents of the next part file
            next_part_lines = []
            if os.path.exists(next_part_file_name):
                next_part_lines = read_file_with_fallback(next_part_file_name)

            # Write <BR></BR> and appended parts to the start of the next part file
            with open(next_part_file_name, 'w', encoding='utf-8') as next_part_file:
                logging.debug(f"Writing to next part file: {next_part_file_name}")
                # Write <BR></BR> first
                next_part_file.write("<BR></BR>\n")
                
                # Write the collected lines next
                for line in parts_to_append:
                    next_part_file.write(line + '\n')
                
                # Then write the existing lines from the next part file
                for line in next_part_lines:
                    next_part_file.write(line)
            
            # Remove collected lines from the original part file
            remaining_lines = lines[:-len(parts_to_append) - 1]  # Exclude copied lines and <BR></BR>
            with open(part_file_name, 'w', encoding='utf-8') as original_file:
                logging.debug(f"Rewriting original part file: {part_file_name}")
                original_file.writelines(remaining_lines)  # Rewrite the original part file without the copied lines
        else:
            logging.debug(f"No <BR></BR> found in {part_file_name}.")
            break  # Stop if no <BR></BR> is found

def main():
    main_file_path = r"C:\Users\f94gdos\Desktop\2025-03-31\ID-7121-Visa_BASE_I_(Standard)_Message_viewer_.html"
    
    try:
        logging.info(f"Processing main file: {main_file_path}")
        total_parts = get_total_parts(main_file_path)
        process_html_file(main_file_path, total_parts)
        logging.info(f"Processing completed for file: {main_file_path}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
