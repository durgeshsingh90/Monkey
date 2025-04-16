import os
import multiprocessing
import time
import queue
import json
import logging
from lxml import etree
import zipfile
from datetime import datetime

logger = logging.getLogger('astrex_html_filter')


def condition_to_expression(conditions_list):
    conditions_str = " ".join(conditions_list)
    conditions_str = conditions_str.replace("'", "")
    conditions_str = conditions_str.replace('AND', 'and')
    conditions_str = conditions_str.replace('OR', 'or')
    conditions_str = conditions_str.replace('NOT', 'not')
    return conditions_str

def match_conditions(value, conditions_list):
    expr = condition_to_expression(conditions_list)
    expr = expr.replace("and", " and ").replace("or", " or ").replace("not", " not ")
    variables = set(expr.split())
    
    for var in variables:
        if var not in {"and", "or", "not"}:
            expr = expr.replace(var, str(var in value))
    
    return eval(expr)

def sanitize_filename(filename):
    return filename.replace("'", "").replace(' ', '_').replace(",", "")

def extract_style(html):
    parser = etree.HTMLParser()
    tree = etree.HTML(html, parser)
    styles = tree.xpath('//style')
    if styles:
        return etree.tostring(styles[0], pretty_print=True, encoding='unicode')
    return ""

def extract_matching_tables(html, conditions_list):
    parser = etree.HTMLParser()
    tree = etree.HTML(html, parser)
    
    tables = tree.xpath('//table')
    matching_tables = []

    for table in tables:
        rows = table.xpath('.//tr')
        for row in rows:
            cells = row.xpath('.//td')
            if len(cells) > 6:
                cell_text = cells[6].text.strip() if cells[6].text is not None else ""
                if match_conditions(cell_text, [conditions_list]): # Wrap the condition in a list
                    matching_tables.append(etree.tostring(table, pretty_print=True, encoding='unicode'))
                    break

    output_html = ""
    for table in matching_tables:
        output_html += table
    return output_html

def process_file(file_path, condition, output_filepath): # update function parameter
    conditions_list = [condition] # Wrap the condition in a list
    logger.info(f"Processing file: {file_path} with conditions: {conditions_list}")
    with open(file_path, 'r', encoding='utf-8') as file:
        input_html = file.read()
    
    output_html = extract_matching_tables(input_html, condition)
    
    if not output_html.strip():
        logger.info(f"No tables matched the given conditions in file: {file_path}")
        return False

    with open(output_filepath, 'a', encoding='utf-8') as file:
        file.write(output_html)
    
    logger.info(f"Filtered HTML appended to {output_filepath}")
    return True

def worker(task_queue, output_filepath, match_queue):
    match_found = False
    while True:
        try:
            file_path, condition = task_queue.get_nowait() # update variables names
            if process_file(file_path, condition, output_filepath):
                match_found = True
        except queue.Empty:
            break
    match_queue.put(match_found)

def process_files_condition_by_condition(json_path, conditions, num_processes=10): # update variables names
    start_time = time.time()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    style_html = ""
    file_paths_dict = {}
    for condition in conditions:
        file_paths_dict[condition] = []

    part0_file_path = None
    
    for file in data["files"]:
        file_name = file["file_name"]
        de032_value_counts = file["de032_value_counts"]
        if part0_file_path is None and "part0" in file_name:
            part0_file_path = file_name

        for condition in conditions:
            if condition in de032_value_counts:
                file_paths_dict[condition].append(file_name)
    
    if part0_file_path:
        with open(part0_file_path, 'r', encoding='utf-8') as file:
            style_html = extract_style(file.read())

    output_dir = os.path.dirname(json_path)
    filtered_files = []
    base_name = os.path.basename(part0_file_path).split('__part')[0] if part0_file_path else "output"

    total_conditions = len(conditions)
    for idx, condition in enumerate(conditions, start=1):
        conditions_progress = f"{str(idx).zfill(2)}/{str(total_conditions).zfill(2)}"
        logger.info(f"Processing with condition [{conditions_progress}]: {condition}")

        conditions_str = sanitize_filename(condition)
        output_filename = f"{base_name}_filtered_{conditions_str}.html"

        # Use the directory of the JSON file for output
        output_filepath = os.path.join(output_dir, output_filename)

        filtered_files.append(output_filepath)
        
        # Ensure we write the style at the beginning
        with open(output_filepath, 'w', encoding='utf-8') as file:
            file.write(style_html)
        
        task_queue = multiprocessing.Queue()
        match_queue = multiprocessing.Queue()

        for file_path in file_paths_dict[condition]:
            task_queue.put((file_path, condition))

        processes = []
        for _ in range(num_processes):
            p = multiprocessing.Process(target=worker, args=(task_queue, output_filepath, match_queue))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        
        match_found = any(match_queue.get() for _ in processes)

        if not match_found:
            if os.path.exists(output_filepath):
                os.remove(output_filepath)
                logger.info(f"Deleted {output_filepath} as no tables matched the conditions")
            filtered_files.remove(output_filepath)
            continue

    # Create a zip file and add all filtered HTML files to it
    datetime_stamp = datetime.now().strftime('%Y%m%d%H%M%S')
    zip_filename = os.path.join(output_dir, f"{base_name}_pspfiltered_{datetime_stamp}.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in filtered_files:
            zipf.write(file, os.path.basename(file))
            os.remove(file)  # Delete the filtered HTML file after adding it to the zip

    logger.info(f"All filtered files have been zipped into {zip_filename}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, rem = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(rem, 60)
    logger.info(f"Processing completed in {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")
    return zip_filename

# if __name__ == '__main__':
#     # Path to the JSON file
#     json_path = r"C:\Users\f94gdos\Desktop\2025-03-31\unique_bm32.json"

#     # Define your search conditions as a list of strings
#     conditions = [
# "456896",
# "411975",

#     ]

#     # Process the files condition by condition in parallel
#     process_files_condition_by_condition(json_path, conditions)

# Replace if __name__ == '__main__': block with:
def run_astrex_html_filter(json_path, conditions, num_processes=10):
    return process_files_condition_by_condition(json_path, conditions, num_processes)
