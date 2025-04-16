import re
import time
import os
from collections import Counter

def parse_log_file(input_file, search_blocks):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    entries = []
    entry = []
    timestamp_pattern = re.compile(r'^\d{2}-\d{2}-\d{2}')
    
    for line in lines:
        if timestamp_pattern.match(line):
            if entry:
                entries.append("".join(entry))
            entry = [line]
        else:
            entry.append(line)
    
    if entry:
        entries.append("".join(entry))
    
    filtered_entries = []
    for entry in entries:
        for search_block in search_blocks:
            if all(term in entry for term in search_block):
                filtered_entries.append(entry)
                break
    
    return filtered_entries

def write_output_file(output_file, filtered_entries):
    with open(output_file, 'w') as file:
        for entry in filtered_entries:
            file.write(entry)

def count_unique_strings(output_file, patterns):
    with open(output_file, 'r') as file:
        lines = file.readlines()

    for pattern in patterns:
        matching_lines = [line for line in lines if re.search(pattern, line)]
        counter = Counter(matching_lines)
        
        print(f"Pattern: {pattern}")
        for line, count in counter.items():
            print(f"{line.strip()} - {count} times")
        print('-' * 40)

def main():
    start_time = time.time()

    input_file = r"C:\Users\f94gdos\Desktop\novate\transaction.log.2025-04-07"  
    search_blocks = [
       [
            "BCMC | 1.1        | \"1\"",
            "BCMC | 1.2        | \"2\"",
            "BCMC | 1.3        | \"3\"",
            "BCMC | 1.4        | \"0\""
        ],
                [
            "BCMC | 1.1        | \"1\"",
            "BCMC | 1.2        | \"1\"",
            "BCMC | 1.3        | \"3\"",
            "BCMC | 1.4        | \"0\""
        ],
                [
            "BCMC | 1.1        | \"1\"",
            "BCMC | 1.2        | \"1\"",
            "BCMC | 1.3        | \"1\"",
            "BCMC | 1.4        | \"0\""
        ],
        [
            "OMNIPAY | 39         | \"09\""
        ]
    ]

    filtered_entries = parse_log_file(input_file, search_blocks)
    output_file = f"{input_file}_output"

    write_output_file(output_file, filtered_entries)

    # Define the patterns to match
    patterns = [
        r'BCMC\s*\|\s*39\s*\|\s*".*?"',
        r'OMNIPAY\s*\|\s*39\s*\|\s*".*?"'
    ]
    count_unique_strings(output_file, patterns)

    # Delete the output file
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Deleted the output file: {output_file}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Total script execution time: {int(minutes)} minutes and {seconds:.2f} seconds")

if __name__ == "__main__":
    main()
