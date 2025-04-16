import time
import json
import logging
from bs4 import BeautifulSoup
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
import re
import os

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Create file handler
    fh = logging.FileHandler("processing.log")
    fh.setLevel(logging.INFO)
    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # Add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

# Function to process a single chunk
def process_chunk(chunk):
    values = []
    de032_values = []

    # Parse the HTML content of the chunk using BeautifulSoup with lxml parser
    soup = BeautifulSoup(chunk, 'lxml')

    # Extract the text content of all cells with the class 'cell7'
    cells = soup.find_all('td', class_='cell7')
    values.extend([cell.get_text(strip=True) for cell in cells])

    # Extract DE032 values only
    for row in soup.find_all('tr'):
        cell1 = row.find('td', class_='cell1norm')
        if cell1 and 'DE032' in cell1.get_text(strip=True):
            cell7 = row.find('td', class_='cell7')
            if cell7:
                de032_values.append(cell7.get_text(strip=True))

    return values, de032_values

# Function to split the HTML file into chunks at `<br>` tags
def split_html_file(filepath, delimiter='<br>'):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    except FileNotFoundError as e:
        logging.error(f"File not found: {filepath}")
        return []

    parts = content.split(delimiter)
    parts = [part + delimiter for part in parts[:-1]] + [parts[-1]]

    return parts

# Function to process a single file sequentially
def sequential_process_file(html_file_path):
    logging.info(f"Processing file: {html_file_path}")
    # Split the HTML file into parts
    parts = split_html_file(html_file_path)
    if not parts:  # File was not found or could not be split
        return html_file_path, Counter(), Counter()

    values = []
    de032_values = []

    # Process each chunk sequentially
    for chunk in parts:
        result_values, result_de032 = process_chunk(chunk)
        values.extend(result_values)
        de032_values.extend(result_de032)

    # Get the count of unique values using Counter
    value_counts = Counter(values)

    # Get the count of DE032 unique values
    de032_value_counts = Counter(de032_values)

    logging.info(f"Finished processing file: {html_file_path}")

    return html_file_path, value_counts, de032_value_counts

def generate_filenames(html_file_path):
    # Use pathlib to get the base file name and generate part file patterns
    base_path = Path(html_file_path).parent
    base_name = Path(html_file_path).stem
    file_pattern = re.compile(re.escape(base_name) + r'_part(\d+)\.html')

    # Gather all part files, sort them by part number
    part_files = sorted(
        base_path.glob(f"{base_name}_part*.html"),
        key=lambda x: int(file_pattern.search(x.name).group(1))
    )

    return [str(path) for path in part_files]

def main(html_file_path, max_processes):
    # Start the timer
    start_time = time.time()

    # Generate file names
    file_names = generate_filenames(html_file_path)

    # Filter out files that do not exist and check if any files exist
    existing_files = [file for file in file_names if Path(file).exists()]

    if not existing_files:
        logging.warning("No valid _part files to process.")
        return

    logging.info(f"Found {len(existing_files)} files to process.")

    # Process each file in parallel at the top level
    with Pool(processes=max_processes) as pool:
        results = pool.map(sequential_process_file, existing_files)

    total_de032_value_counts = Counter()

    # Create result data structure
    result_data = {
        "total_DE032_count": 0,
        "files": []
    }

    # Combine the results from all files and gather data
    for file_path, value_counts, de032_value_counts in results:
        total_de032_value_counts.update(de032_value_counts)

        # Add file-specific data to result
        result_data["files"].append({
            "file_name": file_path,
            "unique_value_count": len(value_counts),
            "de032_value_counts": dict(de032_value_counts)
        })

    # Calculate totals
    result_data["total_DE032_count"] = sum(total_de032_value_counts.values())
    result_data["consolidated_de032_value_counts"] = dict(total_de032_value_counts)

    # End the timer
    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate hour, minute, and second components
    hours = int(execution_time // 3600)
    minutes = int((execution_time % 3600) // 60)
    seconds = execution_time % 60

    # Add execution time data to result
    result_data["execution_time"] = {
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds
    }

    # Print total execution time and JSON file output status
    logging.info(f"\nTotal execution time: {hours} hours, {minutes} minutes, {seconds:.2f} seconds")

    # Output the result data as JSON in the same directory as the input file
    output_filename = Path(html_file_path).parent / "unique_bm32.json"
    with open(output_filename, "w", encoding='utf-8') as json_file:
        json.dump(result_data, json_file, indent=4)

    logging.info(f"\nResults have been saved to {output_filename}")

if __name__ == "__main__":
    # Path to your main HTML file (e.g., r"C:\path\to\your\file.html")
    html_file_path = os.path.join(r"C:\Users\f94gdos\Desktop\2025-03-31", "ID-7121-Visa_BASE_I_(Standard)_Message_viewer_.html")
    
    # Set the maximum number of parallel processes
    max_processes = 10  # Adjust based on testing and system capabilities

    main(html_file_path, max_processes)
