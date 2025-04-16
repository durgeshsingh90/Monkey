import re
import time

def parse_log_file(input_file, search_terms_list):
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
        for search_terms in search_terms_list:
            if all(term in entry for term in search_terms):
                filtered_entries.append(entry)
                break
    
    return filtered_entries

def write_output_file(output_file, filtered_entries):
    with open(output_file, 'w') as file:
        for entry in filtered_entries:
            file.write(entry)

def main():
    input_file = r"C:\Users\f94gdos\Desktop\novate\transaction.log.2025-04-07"  # Adjust the path to your log file
    search_strings = [
        # "'INFO  BCMC-BSAD' AND 'Response IN'",  # Example search string 1
        # "'INFO  OMNIPAY' AND 'Request IN'",     # Example search string 2
        "'Response OUT'"
        # Add more search strings as needed
    ]

    search_terms_list = []
    for search_string in search_strings:
        search_terms = [term.strip().strip("'") for term in re.split(r'\sAND\s|\sOR\s|\sNOT\s', search_string)]
        search_terms_list.append(search_terms)

    start_time = time.time()

    filtered_entries = parse_log_file(input_file, search_terms_list)
    output_file = f"{input_file}_output"
    
    write_output_file(output_file, filtered_entries)

    end_time = time.time()
    elapsed_time = end_time - start_time

    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Time taken: {int(minutes)} minutes and {seconds:.2f} seconds")

if __name__ == "__main__":
    main()
