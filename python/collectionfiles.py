import os
import shutil
import re

def find_and_copy_files(source_dir, dest_dir, search_pattern):
    # Create the destination directory if it doesn't exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Walk through the source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # Check if the file matches the search pattern
            if search_pattern.search(file):
                # Construct the full file path
                file_path = os.path.join(root, file)
                # Copy the file to the destination directory
                shutil.copy(file_path, dest_dir)
                print(f"Copied: {file_path}")

source_directory = r"C:\Durgesh\New folder\Omnipay Compliance Impact"       # Replace with the source directory you want to search
destination_directory = r"C:\Durgesh\New folder\Omnipay Compliance Impact"  # Replace with the destination directory
search_pattern = re.compile(r".*BCMC.*\.pdf", re.IGNORECASE)  # Regular expression to match filenames containing "FEXCO" and ending with .pdf

find_and_copy_files(source_directory, destination_directory, search_pattern)
