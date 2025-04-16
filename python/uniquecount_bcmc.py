import re
from collections import defaultdict

# File path
file_path = r"C:\Users\f94gdos\Downloads\transaction.log.2025-04-07"

# Regular expressions to match timestamp, id, and DE39
timestamp_pattern = re.compile(r'\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+')
id_pattern = re.compile(r'\[id: (\d+)\]')
de39_pattern = re.compile(r'OMNIPAY \| 39\s+\| "(\d{2})"')

# Dictionary to keep track of counts of DE39 codes with unique IDs
unique_counts = defaultdict(set)

# Read and process the log file
current_id = None
with open(file_path, 'r') as file:
    for line in file:
        timestamp_match = timestamp_pattern.search(line)
        id_match = id_pattern.search(line)
        de39_match = de39_pattern.search(line)
        
        # Check for new timestamp
        if timestamp_match:
            current_id = None  # Reset current_id with each new timestamp
        
        # Check for an id match
        if id_match:
            current_id = id_match.group(1)
        
        # Check for DE39 match
        if de39_match and current_id:
            de39_value = de39_match.group(1)
            unique_counts[de39_value].add(current_id)

# Count unique DE39 values
unique_de39_counts = {de39: len(ids) for de39, ids in unique_counts.items()}

# Sort and print the results
for de39, count in sorted(unique_de39_counts.items()):
    print(f'{de39}: {count}')
