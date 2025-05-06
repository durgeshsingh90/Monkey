import os
import re
import glob
import multiprocessing
import logging
from datetime import datetime

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcoded folder path
folder_path = r"C:\Users\f94gdos\Downloads\New folder (6)\logs\logs"

# Output file path
output_file = os.path.join(folder_path, "merged_debug.log")

# Number of multiprocessing processes (can be configured)
num_processes = 10

# Function to read and process each file
def process_file(file_path):
    log_entries = []
    current_timestamp = None
    unknown_logs = ""
    file_name = os.path.basename(file_path)

    logging.info(f'Processing file: {file_name}')

    with open(file_path, 'r') as file:
        for line in file:
            timestamp_match = re.match(r'^([0-9]{2}\.[0-9]{2}\.[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})', line)
            if timestamp_match:
                # Update current timestamp
                current_timestamp = datetime.strptime(timestamp_match.group(1), '%d.%m.%y %H:%M:%S.%f').timestamp()
                # Append previous unknown_logs to log_entries
                if unknown_logs:
                    log_entries.append((current_timestamp, unknown_logs))
                    unknown_logs = ""
                # Prefix the timestamp line with the filename
                log_entries.append((current_timestamp, f"{file_name}: {line}"))
            else:
                if current_timestamp:
                    log_entries.append((current_timestamp, line))
                else:
                    unknown_logs += line + '\n'
    
    if unknown_logs and current_timestamp is not None:
        log_entries.append((current_timestamp, unknown_logs))
    
    return log_entries

def merge_logs(file_list, output_file):
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = pool.map(process_file, file_list)
    
    # Flatten results list of lists
    all_entries = [entry for sublist in results for entry in sublist]

    # Sort the collected log entries by timestamp
    all_entries.sort(key=lambda x: x[0])

    # Write sorted log entries to the output file
    with open(output_file, 'w') as merged_file:
        for _, entry in all_entries:
            merged_file.write(entry)

if __name__ == "__main__":
    # Validate the folder path
    if not os.path.isdir(folder_path):
        logging.error(f'The provided path "{folder_path}" is not a valid directory.')
        exit(1)

    # Identify all the .debug files in the specified folder
    log_files = glob.glob(os.path.join(folder_path, '*.debug'))

    if not log_files:
        logging.info('No .debug files found in the specified folder.')
    else:
        logging.info(f'Found {len(log_files)} .debug files to process.')
        
        # Process the log files and merge the contents
        merge_logs(log_files, output_file)

        # Notify the user that the merged file has been created
        logging.info(f'Merged log file created as {output_file}')
        logging.info(f'Total number of files processed: {len(log_files)}')
