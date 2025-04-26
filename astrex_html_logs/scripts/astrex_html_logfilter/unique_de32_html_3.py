import time
import json
import logging
from bs4 import BeautifulSoup
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
import re
import os

logger = logging.getLogger('astrex_html_filter')

def extract_datetime_from_cell8norm(cell_text):
    import re
    match = re.search(r'\[(.*?)\]', cell_text)
    if match:
        return match.group(1)
    return None

# Function to process a single chunk
def process_chunk(chunk):
    values = []
    de032_values = []
    de007_timestamps = []  # 🚀 New: To capture DE007 timestamps

    soup = BeautifulSoup(chunk, 'lxml')

    cells = soup.find_all('td', class_='cell7')
    values.extend([cell.get_text(strip=True) for cell in cells])

    for row in soup.find_all('tr'):
        cell1 = row.find('td', class_='cell1norm')
        if cell1:
            text = cell1.get_text(strip=True)
            if 'DE032' in text:
                cell7 = row.find('td', class_='cell7')
                if cell7:
                    de032_values.append(cell7.get_text(strip=True))
            elif 'DE007' in text:  # 🚀 New: Check for DE007
                cell8 = row.find('td', class_='cell8norm')
                if cell8:
                    extracted_time = extract_datetime_from_cell8norm(cell8.get_text(strip=True))
                    if extracted_time:
                        de007_timestamps.append(extracted_time)

    return values, de032_values, de007_timestamps  # 🚀 Now returns de007_timestamps also

def split_html_file(filepath, delimiter='<br>'):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    except FileNotFoundError as e:
        logger.error(f"File not found: {filepath}")
        return []

    parts = content.split(delimiter)
    parts = [part + delimiter for part in parts[:-1]] + [parts[-1]]

    return parts

def sequential_process_file(html_file_path):
    logger.info(f"Processing file: {html_file_path}")
    parts = split_html_file(html_file_path)
    if not parts:
        return html_file_path, Counter(), Counter(), [], []

    values = []
    de032_values = []
    all_de007_times_per_part = []

    for chunk in parts:
        result_values, result_de032, result_de007 = process_chunk(chunk)
        values.extend(result_values)
        de032_values.extend(result_de032)
        all_de007_times_per_part.append(result_de007)  # 🚀 Collect timestamps part-wise

    value_counts = Counter(values)
    de032_value_counts = Counter(de032_values)

    logger.info(f"Finished processing file: {html_file_path}")

    return html_file_path, value_counts, de032_value_counts, all_de007_times_per_part, parts

def generate_filenames(html_file_path):
    base_path = Path(html_file_path).parent
    base_name = Path(html_file_path).stem
    file_pattern = re.compile(re.escape(base_name) + r'_part(\d+)\.html')

    part_files = sorted(
        base_path.glob(f"{base_name}_part*.html"),
        key=lambda x: int(file_pattern.search(x.name).group(1))
    )

    return [str(path) for path in part_files]

def main(html_file_path, max_processes):
    start_time = time.time()

    file_names = generate_filenames(html_file_path)
    existing_files = [file for file in file_names if Path(file).exists()]

    if not existing_files:
        logger.warning("No valid _part files to process.")
        return

    logger.info(f"Found {len(existing_files)} files to process.")

    with Pool(processes=max_processes) as pool:
        results = pool.map(sequential_process_file, existing_files)

    total_de032_value_counts = Counter()

    result_data = {
        "total_DE032_count": 0,
        "files": []
    }

    all_start_times = []
    all_end_times = []

    for file_path, value_counts, de032_value_counts, all_de007_times_per_part, parts in results:
        total_de032_value_counts.update(de032_value_counts)

        # 🚀 Extract start and end from DE007
        if all_de007_times_per_part:
            # Part0 start time
            first_part_times = all_de007_times_per_part[0]
            if first_part_times:
                all_start_times.append(first_part_times[0])  # First DE007 in first part

            # Last part end time
            last_part_times = all_de007_times_per_part[-1]
            if last_part_times:
                all_end_times.append(last_part_times[-1])  # Last DE007 in last part

        result_data["files"].append({
            "file_name": file_path,
            "unique_value_count": len(value_counts),
            "de032_value_counts": dict(de032_value_counts)
        })

    result_data["total_DE032_count"] = sum(total_de032_value_counts.values())
    result_data["consolidated_de032_value_counts"] = dict(total_de032_value_counts)

    end_time = time.time()
    execution_time = end_time - start_time

    hours = int(execution_time // 3600)
    minutes = int((execution_time % 3600) // 60)
    seconds = execution_time % 60

    result_data["execution_time"] = {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds
    }

    # 🚀 Final set of start and end time
    result_data["start_log_time"] = all_start_times[0] if all_start_times else ""
    result_data["end_log_time"] = all_end_times[0] if all_end_times else ""

    logger.info(f"\nTotal execution time: {hours} hours, {minutes} minutes, {seconds:.2f} seconds")

    output_filename = Path(html_file_path).parent / "unique_bm32.json"
    with open(output_filename, "w", encoding='utf-8') as json_file:
        json.dump(result_data, json_file, indent=4)

    logger.info(f"\nResults have been saved to {output_filename}")
    return result_data

def run_unique_de32_html(file_path, max_processes=10):
    return main(file_path, max_processes)
