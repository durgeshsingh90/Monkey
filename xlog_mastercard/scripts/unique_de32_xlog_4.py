import xml.etree.ElementTree as ET
import os
import json
from concurrent.futures import ProcessPoolExecutor
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_file(part_file_path):
    file_value_counts = {}
    file_total_count = 0
    first_timestamp, last_timestamp = None, None
    try:
        tree = ET.parse(part_file_path)
        root = tree.getroot()
        logger.debug(f"Parsed {part_file_path}")
    except ET.ParseError as e:
        logger.error(f"Parse error in {part_file_path}: {e}")
        return None

    # Find all Field elements
    fields = root.findall(".//Field")
    logger.debug(f"Found {len(fields)} Field elements in {part_file_path}")

    for field in fields:
        field_name = field.get('Name')
        if field_name == "032":  # Only looking for DE032
            value_element = field.find('Value')
            if value_element is not None and value_element.text:
                value = value_element.text.strip()
                file_value_counts[value] = file_value_counts.get(value, 0) + 1
                file_total_count += 1

    # Find timestamps
    log_entries = root.findall(".//LogEntry")
    if log_entries:
        first_timestamp = log_entries[0].get('timestamp')
        last_timestamp = log_entries[-1].get('timestamp')

    logger.info(f"Processed {part_file_path}: total_count={file_total_count}, unique_count={len(file_value_counts)}")
    return {
        "file": part_file_path,
        "counts": file_value_counts,
        "total_count": file_total_count,
        "unique_count": len(file_value_counts),
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp
    }

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

def format_time_difference(delta):
    days = delta.days if not delta.days < 0 else abs(delta.days + 1)
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days} day(s), {hours} hour(s), {minutes} minute(s), {seconds} second(s)"

def extract_de032(base_file_path, max_workers=10):
    """
    Extracts DE032 field values from XLOG part files and saves a summary JSON.
    """
    base_path, _ = os.path.splitext(base_file_path)

    start_time = time.time()
    logger.info("Starting DE032 extraction")

    part_file_paths = get_all_files(base_path)
    total_value_counts = {}
    file_level_counts = []
    overall_first_timestamp, overall_last_timestamp = None, None

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, part_file_paths))

    for result in results:
        if result:
            file_level_counts.append(result)
            for value, count in result["counts"].items():
                total_value_counts[value] = total_value_counts.get(value, 0) + count
            
            if result["first_timestamp"] and (not overall_first_timestamp or result["first_timestamp"] < overall_first_timestamp):
                overall_first_timestamp = result["first_timestamp"]
            if result["last_timestamp"] and (not overall_last_timestamp or result["last_timestamp"] > overall_last_timestamp):
                overall_last_timestamp = result["last_timestamp"]

    output = {
        "file_level_counts": file_level_counts,
        "total_counts": total_value_counts,
        "total_de032_count": sum(total_value_counts.values()),
        "total_unique_count": len(total_value_counts),
        "start_time": overall_first_timestamp,
        "end_time": overall_last_timestamp
    }

    if overall_first_timestamp and overall_last_timestamp:
        start_dt = datetime.fromisoformat(overall_first_timestamp.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(overall_last_timestamp.replace("Z", "+00:00"))
        time_difference = end_dt - start_dt
        output["time_difference"] = format_time_difference(time_difference)

    # Save to a JSON file
    output_file_path = os.path.join(os.path.dirname(base_path), "unique_bm32_xlog.json")
    with open(output_file_path, 'w') as json_file:
        json.dump(output, json_file, indent=4)

    end_time = time.time()
    logger.info(f"Extraction complete. Output written to {output_file_path}")
    logger.info(f"Total time: {end_time - start_time:.2f} seconds")
