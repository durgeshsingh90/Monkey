import os
import logging

logger = logging.getLogger('astrex_html_filter')

def split_file(file_path, max_file_size=20*1024*1024):
    """Split a file into smaller files with a maximum size."""
    base_name, ext = os.path.splitext(file_path)
    
    logger.info(f"Starting to split file: {file_path}")
    
    with open(file_path, 'rb') as source_file:
        file_part = 0
        while True:
            logger.debug(f"Reading chunk {file_part} from the file.")
            # Read chunks of max_file_size
            chunk = source_file.read(max_file_size)
            if not chunk:
                logger.info(f"Finished reading file. Total parts created: {file_part}.")
                break

            # Write chunks to new file parts
            file_part_name = f"{base_name}_part{file_part}{ext}"
            logger.debug(f"Writing chunk {file_part} to file: {file_part_name}")
            with open(file_part_name, 'wb') as dest_file:
                dest_file.write(chunk)
            file_part += 1
    
    logger.info(f"File split into {file_part} parts.")

# # Example usage
# split_file(r"C:\Users\f94gdos\Desktop\2025-03-31\ID-7121-Visa_BASE_I_(Standard)_Message_viewer_.html")

# At bottom of file
def run_breakhtml(filepath, max_file_size=20*1024*1024):
    split_file(filepath, max_file_size)
