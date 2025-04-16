import re
import time

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

def main():
    input_file = r"C:\Users\f94gdos\Desktop\novate\transaction.log.2025-04-07"  # Adjust the path to your log file
    search_blocks = [
        # [
        #     "OMNIPAY | 1.1        | \"0\"",
        #     "OMNIPAY | 1.2        | \"2\"",
        #     "OMNIPAY | 1.3        | \"1\"",
        #     "OMNIPAY | 1.4        | \"0\""
        # ],
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

        # Add more search blocks as needed
    ]

    start_time = time.time()

    filtered_entries = parse_log_file(input_file, search_blocks)
    output_file = f"{input_file}_output"
    
    write_output_file(output_file, filtered_entries)

    end_time = time.time()
    elapsed_time = end_time - start_time

    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Time taken: {int(minutes)} minutes and {seconds:.2f} seconds")

if __name__ == "__main__":
    main()
