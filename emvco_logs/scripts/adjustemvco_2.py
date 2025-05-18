import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def adjust_file(file_path):
    """
    Adjusts XML parts to fix unclosed <OnlineMessage> tags.
    Called automatically after splitting the XML.
    """
    base_filepath, ext = os.path.splitext(file_path)
    part_number = 0

    while True:
        current_part_filename = f"{base_filepath}_part{part_number}{ext}"
        next_part_filename = f"{base_filepath}_part{part_number + 1}{ext}"

        logging.debug(f"Processing {current_part_filename}")

        if not os.path.exists(current_part_filename):
            logging.info(f"{current_part_filename} does not exist. Stopping.")
            break

        try:
            with open(current_part_filename, 'rb') as file:
                current_part_content = file.read().decode('latin-1')  # decoding as 'latin-1'

            last_open_online_message = current_part_content.rfind('<OnlineMessage')
            last_close_online_message = current_part_content.rfind('</OnlineMessage>')

            if last_open_online_message != -1 and (last_close_online_message == -1 or last_open_online_message > last_close_online_message):
                unclosed_message = current_part_content[last_open_online_message:]
                current_part_content = current_part_content[:last_open_online_message].rstrip()

                logging.info(f"Found unclosed <OnlineMessage> in {current_part_filename}. Moving it to {next_part_filename}.")

                # Save current file after removing unclosed message
                with open(current_part_filename, 'wb') as file:
                    file.write((current_part_content + '\n').encode('latin-1'))

                # Append unclosed message to next part
                if os.path.exists(next_part_filename):
                    with open(next_part_filename, 'rb') as file:
                        next_part_content = file.read().decode('latin-1')

                    if not next_part_content.lstrip().startswith('<'):
                        next_part_content = unclosed_message + next_part_content
                        logging.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} without newline.")
                    else:
                        next_part_content = unclosed_message + '\n' + next_part_content
                        logging.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} with newline.")

                    with open(next_part_filename, 'wb') as file:
                        file.write(next_part_content.encode('latin-1'))
                else:
                    with open(next_part_filename, 'wb') as file:
                        file.write((unclosed_message + '\n').encode('latin-1'))

                    logging.info(f"Created {next_part_filename} with unclosed <OnlineMessage>.")
            else:
                logging.debug(f"All <OnlineMessage> tags are properly closed in {current_part_filename}.")

        except (UnicodeDecodeError, UnicodeEncodeError) as e:
            logging.error(f"Error processing file {current_part_filename}: {e}")
            break
        
        part_number += 1

# Example call to adjust_file
# adjust_file('C:\\Durgesh\\Office\\Automation\\monkey\\media\\emvco_logs\\L3_2025-05-13-1224.xml')
