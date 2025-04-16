import os
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def process_xml_parts(file_path):
    # Extract the base file path without the suffixing part
    base_filepath, ext = os.path.splitext(file_path)
    
    part_number = 0

    while True:
        current_part_filename = f"{base_filepath}_part{part_number}{ext}"
        next_part_filename = f"{base_filepath}_part{part_number + 1}{ext}"
        
        logging.debug(f"Processing {current_part_filename}")
        
        if not os.path.exists(current_part_filename):
            logging.info(f"{current_part_filename} does not exist. Stopping.")
            break
        
        with open(current_part_filename, 'r') as file:
            current_part_content = file.read()
        
        # Check for the last unclosed <OnlineMessage> at the end of the file
        last_open_online_message = current_part_content.rfind('<OnlineMessage')
        last_close_online_message = current_part_content.rfind('</OnlineMessage>')
        
        # Determine if the last <OnlineMessage> is not closed
        if last_open_online_message != -1 and (last_close_online_message == -1 or last_open_online_message > last_close_online_message):
            unclosed_message = current_part_content[last_open_online_message:]
            current_part_content = current_part_content[:last_open_online_message].rstrip()
            
            logging.info(f"Found unclosed <OnlineMessage> in {current_part_filename}. Moving it to {next_part_filename}.")
            
            # Remove unclosed message from current part file
            with open(current_part_filename, 'w') as file:
                file.write(current_part_content + '\n')
            
            # Prepare to write the unclosed message to the next part
            if os.path.exists(next_part_filename):
                with open(next_part_filename, 'r') as file:
                    next_part_content = file.read()
                
                # Check if next part starts with a proper element
                if not next_part_content.lstrip().startswith('<'):
                    next_part_content = unclosed_message + next_part_content
                    logging.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} without newline.")
                else:
                    next_part_content = unclosed_message + '\n' + next_part_content
                    logging.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} with newline.")
                
                # Update the next part file with the unclosed message at the start
                with open(next_part_filename, 'w') as file:
                    file.write(next_part_content)
            else:
                # If next part does not exist, create it with the unclosed message
                with open(next_part_filename, 'w') as file:
                    file.write(unclosed_message + '\n')
                
                logging.info(f"Created {next_part_filename} with unclosed <OnlineMessage>.")
        else:
            logging.debug(f"All <OnlineMessage> tags are properly closed in {current_part_filename}.")
        
        part_number += 1

# Example usage:
process_xml_parts(r"C:\Users\f94gdos\Desktop\TP\L3_2025-03-19-1722.xml")
