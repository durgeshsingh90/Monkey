import os
import string
import logging
import threading
import subprocess
import json
import time
import re
import unicodedata
from django.shortcuts import render
from django.conf import settings

# Get the logger for the binblock app
logger = logging.getLogger('binblock')

# Define the output directory
OUTPUT_DIR = os.path.join(settings.BASE_DIR, 'binblock', 'output')

def run_sqlplus_command(command, query, output_file, server_name):
    """Run SQL*Plus command and capture the output."""
    logger.debug(f"Running SQL*Plus command on {server_name} with query: {query}")
    
    start_time = time.time()  # Start timing
    
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate(input=query.encode())
    
    end_time = time.time()  # End timing
    
    # Calculate time taken
    elapsed_time = end_time - start_time
    logger.info(f"SQL*Plus command on {server_name} completed in {elapsed_time:.2f} seconds.")

    if process.returncode != 0:
        logger.error(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")
        raise Exception(f"SQL*Plus command failed on {server_name}: {stderr.decode()}")

    output_lines = [line for line in stdout.decode().splitlines() if line.strip()]
    with open(output_file, "w") as file:
        file.write("\n".join(output_lines) + "\n")
    
    logger.debug(f"SQL*Plus command completed on {server_name}. Output written to {output_file}")

def clean_file(file_path):
    """Clean the output file by removing unnecessary lines."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find indexes for relevant content
    start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
    end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

    # Clean lines between indexes
    cleaned_lines = [
        ''.join(char for char in line if char in string.printable).strip()
        for line in lines[start_index:end_index]
        if 'rows selected' not in line.lower() and not line.strip().startswith('-') and line.strip() != 'JSON_DATA'
    ]

    with open(file_path, 'w') as file:
        file.write("\n".join(cleaned_lines) + "\n")

def clean_distinct_file(file_path):
    """Clean the distinct output file and return as a list of cleaned items."""
    logger.debug(f"Cleaning output file for distinct query: {file_path}")
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Find the start and end indices for relevant content
        start_index = next((i for i, line in enumerate(lines) if 'SQL>' in line), 0) + 1
        end_index = next((i for i in range(len(lines) - 1, -1, -1) if 'SQL>' in lines[i]), len(lines))

        # Clean lines between the determined indices
        cleaned_list = []
        for line in lines[start_index:end_index]:
            line = ''.join(char for char in line if char in string.printable).strip()

            if not line or 'rows selected' in line.lower():
                continue

            if line.startswith('-') or line == 'DESCRIPTION':
                continue

            cleaned_list.append(line)

        logger.info(f"Successfully cleaned distinct output file: {file_path} with {len(cleaned_list)} entries")
        return cleaned_list

    except Exception as e:
        logger.error(f"Error cleaning distinct output file {file_path}: {e}")
        return []

def remove_control_characters(text):
    """Remove all control characters and normalize the text."""
    normalized_text = unicodedata.normalize('NFKD', text)
    cleaned_text = ''.join(c for c in normalized_text if c.isprintable())
    cleaned_text = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_text)
    return cleaned_text

def remove_null_values(d):
    """Recursively remove null values from dictionaries and lists."""
    if isinstance(d, dict):
        cleaned_data = {k: remove_null_values(v) for k, v in d.items() if v is not None}
    elif isinstance(d, list):
        cleaned_data = [remove_null_values(v) for v in d if v is not None]
    else:
        cleaned_data = d
    return cleaned_data

def apply_length_checks(json_obj):
    """Apply length checks to JSON fields based on configuration."""
    length_config = {
        "LOWBIN": {"type": "CHAR", "length": 15},
        "HIGHBIN": {"type": "CHAR", "length": 15},
        "O_LEVEL": {"type": "NUMBER", "length": 1},
        "STATUS": {"type": "CHAR", "length": 1},
        "DESCRIPTION": {"type": "CHAR", "length": 50},
        "DESTINATION": {"type": "CHAR", "length": 3},
        "ENTITY_ID": {"type": "CHAR", "length": 1},
        "CARDPRODUCT": {"type": "CHAR", "length": 20},
        "NETWORK_DATA": {"type": "CHAR", "length": 10},
        "FILE_NAME": {"type": "CHAR", "length": 10},
        "FILE_VERSION": {"type": "CHAR", "length": 5},
        "FILE_DATE": {"type": "DATE", "length": None},
        "COUNTRY_CODE": {"type": "CHAR", "length": 3},
        "NETWORK_CONFIG": {"type": "CHAR", "length": 10},
        "BIN_LENGTH": {"type": "NUMBER", "length": 2}
    }

    for key, value in json_obj.items():
        if key in length_config:
            config = length_config[key]
            if config["type"] == "CHAR" and config["length"] is not None:
                json_obj[key] = str(value).ljust(config["length"])[:config["length"]]
            elif config["type"] == "NUMBER" and config["length"] is not None:
                json_obj[key] = str(value).zfill(config["length"])[:config["length"]]
    return json_obj

def generate_sql_insert_statements(json_list, table_name):
    """Generate SQL INSERT statements from a list of JSON objects."""
    logger.debug("Starting generate_sql_insert_statements")
    statements = []
    
    for json_obj in json_list:
        keys = json_obj.keys()
        values = []
        for key in keys:
            value = json_obj[key]
            if isinstance(value, str):
                value = value.replace("'", "''")  # Escape single quotes
                value = f"'{value}'"
            elif value is None:
                value = 'NULL'
            values.append(value)
        
        sql_statement = f"INSERT INTO {table_name} ({', '.join(keys)}) VALUES ({', '.join(values)});"
        statements.append(sql_statement)
    
    logger.debug("Completed generate_sql_insert_statements")
    return statements

def save_sql_statements_to_file(statements, file_path):
    """Save SQL INSERT statements to a file."""
    logger.debug(f"Starting save_sql_statements_to_file for {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(statements))
        logger.info(f"SQL statements saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving SQL statements to file {file_path}: {e}")
    logger.debug(f"Completed save_sql_statements_to_file for {file_path}")

def preprocess_json_file(file_path, table_name, output_sql_file):
    """Preprocess the JSON file to remove unwanted control characters, format it properly, remove null values, apply length checks, and save as SQL insert statements."""
    logger.debug(f"Starting preprocess_json_file for file: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        cleaned_lines = [remove_control_characters(line.strip()) for line in lines if line.strip()]
        json_data = ''.join(cleaned_lines)
        json_data = re.sub(r'\}\s*\{', '},{', json_data)
        json_data = f"[{json_data}]"

        try:
            json_object = json.loads(json_data)
        except json.JSONDecodeError as e:
            logger.error(f"Error loading JSON data: {e}")
            raise

        cleaned_json_object = [remove_null_values(obj) for obj in json_object]
        checked_json_object = [apply_length_checks(obj) for obj in cleaned_json_object]

        formatted_json = json.dumps(checked_json_object, indent=4)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(formatted_json)

        sql_statements = generate_sql_insert_statements(checked_json_object, table_name)
        save_sql_statements_to_file(sql_statements, output_sql_file)

        logger.debug(f"Completed preprocess_json_file for file: {file_path}")

    except Exception as e:
        logger.error(f"Error preprocessing JSON file {file_path}: {e}")

def run_background_queries():
    """Run prod and uat queries in the background, clean the output files, and perform further processing."""
    logger.debug("Starting background queries for prod and uat")

    def run_query_and_process(command, query, output_file, server_name):
        try:
            logger.debug(f"Running query for {server_name}")
            run_sqlplus_command(command, query, output_file, server_name)
            
            cleaned_data = clean_file(output_file)
            logger.info(f"Cleaned data from {server_name}: {cleaned_data}")

            preprocess_json_file(output_file, 'your_table_name', os.path.join(OUTPUT_DIR, f"{server_name.lower()}_insert_statements.sql"))

        except Exception as e:
            logger.error(f"Error running SQL query or processing data on {server_name}: {e}")

    prod_command = "sqlplus oasis77/ist0py@istu2"
    uat_command = "sqlplus oasis77/ist0py@istu2"
    query = "SELECT JSON_OBJECT(*) AS JSON_DATA FROM (SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN) WHERE ROWNUM <= 4;"
    prod_output_file = os.path.join(OUTPUT_DIR, 'prod_output.json')
    uat_output_file = os.path.join(OUTPUT_DIR, 'uat_output.json')

    threading.Thread(target=run_query_and_process, args=(prod_command, query, prod_output_file, "Prod")).start()
    threading.Thread(target=run_query_and_process, args=(uat_command, query, uat_output_file, "UAT")).start()

def remove_duplicates_and_subsets(bin_list):
    """Remove duplicate and subset bins."""
    bin_set = sorted(set(bin_list), key=lambda x: (len(x), x))
    return [
        bin for bin in bin_set
        if not any(bin.startswith(existing_bin) for existing_bin in bin_set if existing_bin != bin)
    ]

def combine_consecutives(bins):
    """Combine consecutive bins into ranges."""
    bins = sorted(bins, key=lambda x: int(x.split('-')[0]))
    combined = []
    i = 0
    while i < len(bins):
        start_bin = end_bin = bins[i]
        while i + 1 < len(bins) and int(bins[i + 1].split('-')[0]) == int(bins[i].split('-')[0]) + 1:
            end_bin = bins[i + 1]
            i += 1
        combined.append(f"{start_bin}-{end_bin}" if start_bin != end_bin else start_bin)
        i += 1
    return combined, i

def process_bins(bins):
    """Process BIN numbers to remove duplicates, handle subsets, and combine consecutive ranges."""
    logger.debug("Starting to process BIN numbers")

    # Remove duplicates and subsets
    cleaned_bins = remove_duplicates_and_subsets(bins)
    logger.debug(f"Cleaned BINs after removing duplicates and subsets: {cleaned_bins}")

    # Combine consecutive bins into ranges
    combined_bins, _ = combine_consecutives(cleaned_bins)
    logger.info(f"Processed BINs: {combined_bins}")

    return combined_bins

def calculate_bins_with_neighbors(processed_bins):
    """
    Calculate the start and end bins for each processed bin range along with neighboring bins.
    """
    result = []

    for bin_range in processed_bins:
        bin_range = bin_range.strip()  # Clean up any extra spaces

        # Check if the bin_range is a range
        if '-' in bin_range:
            start_bin, end_bin = bin_range.split('-')
            start_bin = start_bin.strip().ljust(15, '0')  # Pad the start_bin with '0' to make it 15 characters
            end_bin = end_bin.strip().ljust(15, '9')    # Pad the end_bin with '9' to make it 15 characters

            # Calculate neighbors for the start and end bins
            start_bin_int = int(start_bin.strip())
            end_bin_int = int(end_bin.strip())
            neighbor_minus_1 = str(start_bin_int - 1).ljust(15, '9')  # Decrement start_bin and pad with '9'
            neighbor_plus_1 = str(end_bin_int + 1).ljust(15, '0')   # Increment end_bin and pad with '0'
        else:
            start_bin = end_bin = bin_range.strip()
            start_bin = start_bin.ljust(15, '0')  # Pad the bin with '0' to make it 15 characters
            end_bin = end_bin.ljust(15, '9')     # Pad the bin with '9' to make it 15 characters

            # Calculate neighbors for a single bin
            bin_int = int(bin_range.strip())
            neighbor_minus_1 = str(bin_int - 1).ljust(15, '9')  # Decrement bin and pad with '9'
            neighbor_plus_1 = str(bin_int + 1).ljust(15, '0')   # Increment bin and pad with '0'

        result.append((start_bin, end_bin, neighbor_minus_1, neighbor_plus_1))

    return result

def parse_sql_statements(statements):
    """Parse SQL statements without filtering by search items."""
    filtered_statements = []

    for statement in statements:
        try:
            values_part = statement.split("VALUES (")[1]
            values = values_part.split(",")

            lowbin = values[0].strip(" '")
            highbin = values[1].strip(" '")
            description = ' '.join(values[4].strip(" '").lower().split())  # Normalize description

            # Include all statements without filtering by search_items
            filtered_statements.append((lowbin, highbin, description, statement))

        except IndexError:
            logger.error(f"Error parsing statement: {statement}")

    return filtered_statements

def duplicate_and_modify_sql(sql_statements, bins_with_neighbors, blocked_item):
    """
    Duplicate and modify SQL statements based on processed bins and the blocked item, applying length checks and removing empty lines.
    
    Args:
    sql_statements (list): List of SQL statements to process.
    bins_with_neighbors (list): Processed bins with start and end ranges, along with their neighboring bins.
    blocked_item (str): The item to be blocked.

    Returns:
    tuple: A tuple containing the modified SQL statements and the remaining original SQL statements.
    """
    # Logging the inputs for debugging purposes
    logger.debug(f"SQL Statements to be processed: {sql_statements}")
    logger.debug(f"Bins with Neighbors: {bins_with_neighbors}")
    logger.debug(f"Blocked Item: {blocked_item}")

    modified_statements = []
    remaining_statements = []

    # Define the field names based on the order in the SQL statements
    field_names = ["LOWBIN", "HIGHBIN", "O_LEVEL", "STATUS", "DESCRIPTION", "DESTINATION", "ENTITY_ID", 
                   "CARDPRODUCT", "FILE_NAME", "FILE_VERSION", "FILE_DATE"]

    # Iterate over each SQL statement
    for statement in sql_statements:
        # Extract the fields from the SQL statement
        try:
            # Preserve the original format of the statement
            insert_part, values_part = statement.split("VALUES (", 1)
            values_part = values_part.rstrip("); \n").strip()

            # Split the values part and strip each value of leading/trailing whitespace and quotes
            values = [value.strip(" '") for value in values_part.split(",")]

            # Ensure there are enough values to process
            if len(values) != len(field_names):  # Match the number of fields
                logger.error(f"Unexpected number of fields in statement: {statement}. Found {len(values)} fields.")
                remaining_statements.append(statement)
                continue

            # Convert LOWBIN and HIGHBIN to integers for comparison
            lowbin_int = int(values[0])
            highbin_int = int(values[1])
        except (IndexError, ValueError) as e:
            logger.error(f"Error parsing fields from statement: {statement}. Error: {e}")
            remaining_statements.append(statement)
            continue

        # Check if any of the bins need to be modified based on the blocked item
        statement_modified = False

        for (start_bin, end_bin, neighbor_minus_1, neighbor_plus_1) in bins_with_neighbors:
            # Convert start_bin and end_bin to integers for comparison
            try:
                start_bin_int = int(start_bin.strip())
                end_bin_int = int(end_bin.strip())
            except ValueError:
                logger.error(f"Invalid start_bin or end_bin format: {start_bin}, {end_bin}")
                continue

            # Check if start_bin falls within the range of LOWBIN and HIGHBIN
            if lowbin_int <= start_bin_int <= highbin_int:
                # Log the modification details
                logger.debug(f"Modifying SQL statement: {statement} for BIN range {start_bin} - {end_bin}")

                # Create three new SQL statements based on the split
                # Part 1: Before the blocked range (if applicable)
                if lowbin_int < start_bin_int:
                    part1_values = values.copy()
                    part1_values[0] = str(lowbin_int)  # Original LOWBIN
                    part1_values[1] = neighbor_minus_1  # HIGHBIN before blocked range
                    part1_values_dict = {key: value for key, value in zip(field_names, part1_values)}
                    part1_values_dict = apply_length_checks(part1_values_dict)
                    part1_statement = "{}VALUES ({});".format(
                        insert_part, ', '.join(f"'{part1_values_dict[key]}'" for key in field_names if part1_values_dict[key].strip())
                    )
                    modified_statements.append(part1_statement)

                # Part 2: The blocked range
                blocked_values = values.copy()
                blocked_values[0] = start_bin  # LOWBIN for blocked range
                blocked_values[1] = end_bin  # HIGHBIN for blocked range
                blocked_values[4] = blocked_item  # DESCRIPTION changed to blocked_item
                blocked_values[7] = blocked_item  # CARDPRODUCT changed to blocked_item
                blocked_values_dict = {key: value for key, value in zip(field_names, blocked_values)}
                blocked_values_dict = apply_length_checks(blocked_values_dict)
                blocked_statement = "{}VALUES ({});".format(
                    insert_part, ', '.join(f"'{blocked_values_dict[key]}'" for key in field_names if blocked_values_dict[key].strip())
                )
                modified_statements.append(blocked_statement)

                # Part 3: After the blocked range (if applicable)
                if highbin_int > end_bin_int:
                    part3_values = values.copy()
                    part3_values[0] = neighbor_plus_1  # LOWBIN after blocked range
                    part3_values[1] = str(highbin_int)  # Original HIGHBIN
                    part3_values_dict = {key: value for key, value in zip(field_names, part3_values)}
                    part3_values_dict = apply_length_checks(part3_values_dict)
                    part3_statement = "{}VALUES ({});".format(
                        insert_part, ', '.join(f"'{part3_values_dict[key]}'" for key in field_names if part3_values_dict[key].strip())
                    )
                    modified_statements.append(part3_statement)

                statement_modified = True
                break

        if not statement_modified:
            remaining_statements.append(statement)

    # Remove any empty or blank lines
    modified_statements = [stmt for stmt in modified_statements if stmt.strip()]

    # Log the results of the modification process
    logger.debug(f"Modified SQL Statements: {modified_statements}")
    logger.debug(f"Remaining SQL Statements: {remaining_statements}")

    return modified_statements, remaining_statements
def merge_and_sort_sql(modified_statements, remaining_statements):
    """Merge unaffected and modified SQL statements and sort by LOWBIN."""
    combined_statements_sorted = sorted(
        remaining_statements + modified_statements,
        key=lambda stmt: int(stmt.split("VALUES ('")[1].split("', '")[0])
    )

    return combined_statements_sorted

def bin_blocking_editor(request):
    logger.info("Bin blocking editor view accessed")
    result = None
    log_with_delays = None
    prod_distinct_list = []
    categorized_list = []

    try:
        distinct_command = "sqlplus oasis77/ist0py@istu2"
        distinct_query = "SELECT DISTINCT description FROM oasis77.SHCEXTBINDB ORDER BY DESCRIPTION;"
        distinct_output_file = os.path.join(OUTPUT_DIR, 'prod_distinct_output.txt')
        run_sqlplus_command(distinct_command, distinct_query, distinct_output_file, "Distinct")
        processed_bins_output = os.path.join(OUTPUT_DIR, 'processed_bins.txt')

        prod_distinct_list = clean_distinct_file(distinct_output_file)

        logger.info(f"prod_distinct_list: {prod_distinct_list}")  # Debug log to check the list

        run_background_queries()

    except Exception as e:
        logger.error(f"Error running distinct query: {e}")
        categorized_list = []

    if request.method == 'POST':
        # Get user inputs
        bin_input = request.POST.get('bins', '').splitlines()
        blocked_item = request.POST.get('blocked_item')

        # Log the blocked_item to see if it's captured correctly
        logger.info(f"Blocked Item selected: {blocked_item}")

        # Process BIN numbers
        processed_bins = process_bins(bin_input)

        with open(processed_bins_output, 'w', encoding='utf-8') as file:
            for item in processed_bins:
                file.write(f"{item}\n")

        logger.info(f"Processed BINs: {processed_bins}")

        # Calculate neighbors for processed bins
        bins_with_neighbors = calculate_bins_with_neighbors(processed_bins)
        logger.info(f"Bins with neighbors: {bins_with_neighbors}")

        # Load the generated Prod SQL statements (assume they are stored in a list or file)
        prod_sql_statements = generate_sql_insert_statements_for_prod()

        # Process Prod SQL statements
        prod_modified_sql, prod_remaining_sql = duplicate_and_modify_sql(
            prod_sql_statements, bins_with_neighbors, blocked_item
        )
        prod_merged_sorted_sql = merge_and_sort_sql(prod_modified_sql, prod_remaining_sql)

        # Save the new merged insert statements
        save_sql_statements_to_file(prod_merged_sorted_sql, os.path.join(OUTPUT_DIR, 'final_prod_insert_statements.sql'))

        # Log final merged SQL statements for Prod
        logger.info(f"Final merged Prod SQL statements: {prod_merged_sorted_sql}")

        context = {
            'result': processed_bins,
            'bins_with_neighbors': bins_with_neighbors,
            'prod_sql_statements': prod_merged_sorted_sql,
            'log_with_delays': log_with_delays,
            'prod_distinct_list': prod_distinct_list  # Correctly pass the prod_distinct_list
        }
        logger.info("Rendering binblocker.html with context data after processing")
        return render(request, 'binblock/binblocker.html', context)

    context = {
        'result': result,
        'log_with_delays': log_with_delays,
        'prod_distinct_list': prod_distinct_list  # Correctly pass the prod_distinct_list
    }
    logger.info("Rendering binblocker.html with initial context data")
    return render(request, 'binblock/binblocker.html', context)

def generate_sql_insert_statements_for_prod():
    """Generate or retrieve the previously created SQL insert statements for Prod."""
    sql_file_path = os.path.join(OUTPUT_DIR, 'prod_insert_statements.sql')
    with open(sql_file_path, 'r') as file:
        return file.readlines()

def save_sql_statements_to_file(statements, file_path):
    """Save SQL INSERT statements to a file."""
    logger.debug(f"Saving SQL statements to {file_path}")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write("\n".join(statements))
        logger.info(f"SQL statements saved to {file_path}")
    except Exception as e:
        logger.error(f"Error saving SQL statements to file {file_path}: {e}")
    logger.debug(f"Completed saving SQL statements to {file_path}")