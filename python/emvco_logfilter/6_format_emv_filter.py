import glob
import os

# Define the full filename with .xml extension
base_filename = r"C:\Users\f94gdos\Desktop\New folder\L3_2025-03-19-1722.xml"

# Remove the .xml extension to get the base path
base_path = base_filename[:-4]

# Define the suffix for the part0 file
part0_suffix = '_part0.xml'

# Get the full filename of the _part0 file
part0_file = base_path + part0_suffix

# Read the content up to <OnlineMessageList> from the _part0 file
lines_to_copy = []
with open(part0_file, 'r', encoding='utf-8') as file:
    for line in file:
        lines_to_copy.append(line)
        if '<OnlineMessageList>' in line:
            break

# Get a list of all part files except _part0 and sort them to find the last part file
part_files_pattern = base_path + '_part[1-9]*.xml'
other_parts = sorted(glob.glob(part_files_pattern))

# Read the content from </OnlineMessageList> to the end from the last part file
lines_to_append = []
if other_parts:
    last_part_file = other_parts[-1]
    with open(last_part_file, 'r', encoding='utf-8') as file:
        recording = False
        for line in file:
            if recording:
                lines_to_append.append(line)
            if '</OnlineMessageList>' in line:
                recording = True
                lines_to_append.append(line)

# Function to prepend content to a file
def prepend_content(file, lines_to_prepend):
    with open(file, 'r', encoding='utf-8') as original:
        original_content = original.read()
    
    with open(file, 'w', encoding='utf-8') as updated:
        # Prepend content
        updated.writelines(lines_to_prepend)
        # Write original content
        updated.write(original_content)

# Function to append content to a file
def append_content(file, lines_to_append):
    with open(file, 'a', encoding='utf-8') as updated:
        # Append content
        updated.writelines(lines_to_append)

# Specify the specific file you want to modify
specific_file = r"C:\Users\f94gdos\Desktop\TP\L3_2025-03-19-1722_filtered_00000367631.xml"

# Prepend and append content to the specific file
prepend_content(specific_file, lines_to_copy)
append_content(specific_file, lines_to_append)

print("Content prepended from part0 and appended from the last part successfully to the specific file.")
