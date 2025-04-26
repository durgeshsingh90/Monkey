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
    """Moved to top-level."""
    file_value_counts = {}
    file_total_count = 0
    try:
        tree = ET.parse(part_file_path)
        root = tree.getroot()
        logger.debug(f"Parsed {part_file_path}")
    except ET.ParseError as e:
        logger.error(f"Parse error in {part_file_path}: {e}")
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
                    file_value_counts[value] = file_value_counts.get(value, 0) + 1
                    file_total_count += 1

    file_unique_count = len(file_value_counts)
    logger.info(f"Processed {part_file_path}: total_count={file_total_count}, unique_count={file_unique_count}")
    return {
        "file": part_file_path,
        "counts": file_value_counts,
        "total_count": file_total_count,
        "unique_count": file_unique_count
    }

def extract_de032(base_file_path, max_workers=10):
    """
    Extracts DE.032 field values from XML part files and saves a summary JSON.
    """
    def get_all_files(base_path):
        part_number = 0
        part_file_paths = []
        while True:
            part_file_path = f"{base_path}_part{part_number}.xml"
            if not os.path.exists(part_file_path):
                break
            part_file_paths.append(part_file_path)
            part_number += 1
        logger.debug(f"Found {len(part_file_paths)} files to process.")
        return part_file_paths

def extract_de032(base_file_path, max_workers=10):
    """
    Extracts DE.032 field values from XML part files and saves a summary JSON.
    """
    base_path, _ = os.path.splitext(base_file_path)

    start_time = time.time()
    logger.info("Starting DE032 extraction")

    base_path, _ = os.path.splitext(base_file_path)
    part_file_paths = get_all_files(base_path)
    total_value_counts = {}
    file_level_counts = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, part_file_paths))

    for result in results:
        if result:
            file_level_counts.append(result)
            for value, count in result["counts"].items():
                total_value_counts[value] = total_value_counts.get(value, 0) + count

    output = {
        "file_level_counts": file_level_counts,
        "total_counts": total_value_counts,
        "total_de032_count": sum(total_value_counts.values()),
        "total_unique_count": len(total_value_counts)
    }

    output_file_path = os.path.join(os.path.dirname(base_file_path), "unique_bm32_emvco.json")
    with open(output_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)

    end_time = time.time()
    logger.info(f"Extraction complete. Output written to {output_file_path}")
    logger.info(f"Total time: {end_time - start_time:.2f} seconds")
