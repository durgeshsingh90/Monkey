import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_filtered_xml(filtered_file_path, base_uploaded_file_path):
    """
    Clean the filtered .xlog XML file.
    Removes unnecessary <Root> tags (if any) but keeps <log> structure.
    """
    logging.info(f"Starting formatting of {filtered_file_path}")

    # Step 1: Clean the filtered XML
    clean_filtered_xml(filtered_file_path)

    # No need to prepend or append anything for xlog
    logging.info(f"Formatted {filtered_file_path} successfully.")

def clean_filtered_xml(file_path):
    """Remove <?xml ... ?> and <Root> tags from filtered XML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        if '<?xml' in line:
            continue
        if '<Root>' in line:
            continue
        if '</Root>' in line:
            continue
        new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
