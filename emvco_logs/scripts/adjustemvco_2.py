# emvco_logs/scripts/2_adjustemvco.py

import os
import logging

# Use Django logging style
logger = logging.getLogger(__name__)

def adjust_emvco_file(file_path):
    """
    Adjusts EMVCo XML files by moving unclosed <OnlineMessage> to next part file.
    """
    base_filepath, ext = os.path.splitext(file_path)
    part_number = 0

    while True:
        current_part_filename = f"{base_filepath}_part{part_number}{ext}"
        next_part_filename = f"{base_filepath}_part{part_number + 1}{ext}"

        logger.debug(f"Processing {current_part_filename}")

        if not os.path.exists(current_part_filename):
            logger.info(f"{current_part_filename} does not exist. Stopping.")
            break

        with open(current_part_filename, 'r') as file:
            current_part_content = file.read()

        last_open_online_message = current_part_content.rfind('<OnlineMessage')
        last_close_online_message = current_part_content.rfind('</OnlineMessage>')

        if last_open_online_message != -1 and (last_close_online_message == -1 or last_open_online_message > last_close_online_message):
            unclosed_message = current_part_content[last_open_online_message:]
            current_part_content = current_part_content[:last_open_online_message].rstrip()

            logger.info(f"Found unclosed <OnlineMessage> in {current_part_filename}. Moving it to {next_part_filename}.")

            with open(current_part_filename, 'w') as file:
                file.write(current_part_content + '\n')

            if os.path.exists(next_part_filename):
                with open(next_part_filename, 'r') as file:
                    next_part_content = file.read()

                if not next_part_content.lstrip().startswith('<'):
                    next_part_content = unclosed_message + next_part_content
                    logger.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} without newline.")
                else:
                    next_part_content = unclosed_message + '\n' + next_part_content
                    logger.info(f"Prepended unclosed <OnlineMessage> to {next_part_filename} with newline.")

                with open(next_part_filename, 'w') as file:
                    file.write(next_part_content)
            else:
                with open(next_part_filename, 'w') as file:
                    file.write(unclosed_message + '\n')

                logger.info(f"Created {next_part_filename} with unclosed <OnlineMessage>.")

        else:
            logger.debug(f"All <OnlineMessage> tags are properly closed in {current_part_filename}.")

        part_number += 1
