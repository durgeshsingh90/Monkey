import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

def split_file(file_path, max_file_size=20*1024*1024):
    """Split a file into smaller files with a maximum size."""
    base_name, ext = os.path.splitext(file_path)
    
    logging.info(f"Starting to split file: {file_path}")
    
    with open(file_path, 'rb') as source_file:
        file_part = 0
        while True:
            logging.debug(f"Reading chunk {file_part} from the file.")
            # Read chunks of max_file_size
            chunk = source_file.read(max_file_size)
            if not chunk:
                logging.info(f"Finished reading file. Total parts created: {file_part}.")
                break

            # Write chunks to new file parts
            file_part_name = f"{base_name}_part{file_part}{ext}"
            logging.debug(f"Writing chunk {file_part} to file: {file_part_name}")
            with open(file_part_name, 'wb') as dest_file:
                dest_file.write(chunk)
            file_part += 1
    
    logging.info(f"File split into {file_part} parts.")

# Example usage
split_file(r"C:\Users\f94gdos\Desktop\TP\L3_2025-03-19-1722.xml")
