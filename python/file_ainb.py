import os
def count_strings_in_file(file_path, strings_to_search):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    count_dict = {}
    for string in strings_to_search:
        count_dict[string] = content.count(string)
    
    found_count = sum(1 for count in count_dict.values() if count > 0)
    not_found_count = len(strings_to_search) - found_count
    
    return count_dict, found_count, not_found_count

def search_strings_in_files(file_paths, strings_to_search):
    result = {}
    
    for file_path in file_paths:
        if os.path.isfile(file_path):
            counts, found, not_found = count_strings_in_file(file_path, strings_to_search)
            result[os.path.basename(file_path)] = {
                'counts': counts,
                'found': found,
                'not_found': not_found
            }
    
    return result

# Example usage
file_paths = [
    r"C:\Users\f94gdos\Desktop\TP\ID-7106-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html",
    r"C:\Users\f94gdos\Desktop\TP\ID-7106-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__pspfiltered.html",
    r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer_.html",
    r"C:\Users\f94gdos\Desktop\TP\ID-7107-DCI_Relay_Xpress_(DinersDiscover)_Message_viewer__pspfiltered.html"
]
strings_to_search = [
    '507813753762'

]

search_results = search_strings_in_files(file_paths, strings_to_search)

for file, data in search_results.items():
    print(f"File: {file}")
    print("Count of each string:")
    for string, count in data['counts'].items():
        print(f"  {string}: {count}")
    print(f"Strings found: {data['found']}")
    print(f"Strings not found: {data['not_found']}")
    print("---------------------------------")
