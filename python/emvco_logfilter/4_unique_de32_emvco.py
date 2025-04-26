import xml.etree.ElementTree as ET
import os
import json
from concurrent.futures import ProcessPoolExecutor
import logging
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_file(part_file_path):
    file_value_counts = {}
    file_total_count = 0
    
    try:
        tree = ET.parse(part_file_path)
        root = tree.getroot()
        logger.debug(f"Successfully parsed {part_file_path}")
    except ET.ParseError as e:
        logger.error(f"Failed to parse {part_file_path}: {e}")
        return None

    fields = root.findall(".//Field")
    logger.debug(f"Found {len(fields)} Field elements in {part_file_path}")
    
    for field in fields:
        field_id = field.get('ID')
        if field_id and 'DE.032' in field_id:
            field_viewable = field.find('FieldViewable')
            if field_viewable is not None:
                value = field_viewable.text
                if value:
                    # Track counts for the individual file
                    if value in file_value_counts:
                        file_value_counts[value] += 1
                    else:
                        file_value_counts[value] = 1
                        
                    file_total_count += 1

    file_unique_count = len(file_value_counts)
    logger.info(f"Processed {part_file_path}: total_count = {file_total_count}, unique_count = {file_unique_count}")
    return {
        "file": part_file_path,
        "counts": file_value_counts,
        "total_count": file_total_count,
        "unique_count": file_unique_count
    }

def get_all_files(base_file_path):
    part_number = 0
    part_file_paths = []
    while True:
        part_file_path = f"{base_file_path}_part{part_number}.xml"
        if not os.path.exists(part_file_path):
            break
        part_file_paths.append(part_file_path)
        part_number += 1
    logger.debug(f"Found {len(part_file_paths)} files to process.")
    return part_file_paths

def get_de032_values(base_file_path, max_workers=10):
    total_value_counts = {}
    file_level_counts = []
    part_file_paths = get_all_files(base_file_path)
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, part_file_paths))
    
    for result in results:
        if result:
            file_level_counts.append(result)
            for value, count in result["counts"].items():
                if value in total_value_counts:
                    total_value_counts[value] += count
                else:
                    total_value_counts[value] = count
    
    total_de032_count = sum(total_value_counts.values())
    total_unique_count = len(total_value_counts)

    logger.info(f"Total DE.032 count = {total_de032_count}, Total unique count = {total_unique_count}")
    return file_level_counts, total_value_counts, total_de032_count, total_unique_count

if __name__ == "__main__":
    start_time = time.time()
    logger.info("Script execution started.")

    # Provide the base path to your XML file (without the _partX suffix)
    base_file_path = r"C:\Users\f94gdos\Desktop\New folder\L3_2025-03-19-1722"
    file_level_counts, total_value_counts, total_de032_count, total_unique_count = get_de032_values(base_file_path)

    output = {
        "file_level_counts": file_level_counts,
        "total_counts": total_value_counts,
        "total_de032_count": total_de032_count,
        "total_unique_count": total_unique_count
    }

    # Determine the output file path
    base_dir = os.path.dirname(base_file_path)
    output_file_path = os.path.join(base_dir, "unique_bm32_emvco.json")

    # Write the output to the JSON file
    with open(output_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)
    
    logger.info(f"Output written to {output_file_path}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Script execution completed.")
    logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
