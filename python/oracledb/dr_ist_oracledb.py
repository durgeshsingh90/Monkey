import oracledb
import logging
import json
import yaml
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Oracle connection details
username = 'F94GDOS'
password = 'Ireland2025!'
dsn_alias = 'A4PCDO8001.ESH.PAR_IST'  # Alias defined in TNSNAMES.ORA


# Provide the path to the Oracle Instant Client libraries
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"

# Connection pool parameters
pool_min = 1
pool_max = 2
pool_increment = 1

# Initialize Oracle client
oracledb.init_oracle_client(lib_dir=oracle_client_path)
logging.info(f"Oracle client initialized from {oracle_client_path}")

# Custom JSON encoder for handling specific data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def initialize_connection_pool():
    try:
        pool = oracledb.create_pool(user=username, password=password, dsn=dsn_alias, min=pool_min, max=pool_max, increment=pool_increment)
        logging.info("Successfully created connection pool")
        return pool
    except oracledb.DatabaseError as e:
        logging.error(f"Database connection pool creation error: {e}")
        return None

def generate_insert_statement(table_name, columns, row):
    columns_str = ', '.join(columns)
    values_str = ', '.join(f"'{value}'" if value is not None else 'NULL' for value in row)
    insert_statement = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});"
    return insert_statement

def execute_query(connection, query):
    query_result = {"query": query, "result": None, "error": None}
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        return query_result
    
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query.rstrip(';'))
            logging.info(f"Executed query: {query}")

            rows = cursor.fetchall()
            metadata = cursor.description
            columns = [col[0] for col in metadata]

            result = []
            insert_statements = []

            for row in rows:
                row_dict = {}
                for idx, value in enumerate(row):
                    col_name = columns[idx]
                    row_dict[col_name] = value
                result.append(row_dict)
                
                # Generate the insert statement for the row
                table_name = query.split()[3].split('.')[1]
                insert_statements.append(generate_insert_statement(table_name, columns, row))

            query_result["result"] = {
                "data": result,
                "insert_statements": insert_statements
            }

        finally:
            cursor.close()  # cursor is closed here

    except oracledb.DatabaseError as e:
        error = e.args[0]
        logging.error(f"An error occurred: {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        query_result["error"] = str(e)

    return query_result

def save_query_result_to_file(result, query, output_types):
    table_name = query.split()[3].split('.')[1]
    script_filename = os.path.splitext(os.path.basename(__file__))[0]
    output_dir = os.path.join('Monkey', 'media','oracledb', script_filename)
    os.makedirs(output_dir, exist_ok=True)

    if 'json' in output_types:
        # Write data output to JSON file
        output_filename_json = os.path.join(output_dir, f"{table_name}.json")
        with open(output_filename_json, 'w', encoding='utf-8') as output_file:
            json.dump(result["result"]["data"], output_file, cls=CustomJSONEncoder, indent=4)

    if 'sql' in output_types:
        # Write insert statements to SQL file
        output_filename_sql = os.path.join(output_dir, f"{table_name}.sql")
        with open(output_filename_sql, 'w', encoding='utf-8') as sql_file:
            for statement in result["result"]["insert_statements"]:
                sql_file.write(statement + '\n')

def execute_queries_with_pool(pool, queries, output_types):
    results = []
    connection = pool.acquire()
    try:
        for query in queries:
            result = execute_query(connection, query)
            results.append(result)
            save_query_result_to_file(result, query, output_types)
    finally:
        pool.release(connection)  # Return the connection to the pool
    
    return results

def execute_multiple_query_sets(pool, query_sets, output_types):
    all_results = []
    with ThreadPoolExecutor(max_workers=2) as executor:  # Adjust the number of workers as needed
        future_to_query_set = {executor.submit(execute_queries_with_pool, pool, queries, output_types): queries for queries in query_sets}
        for future in as_completed(future_to_query_set):
            query_set = future_to_query_set[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logging.error(f"Query set {query_set} generated an exception: {exc}")
                all_results.append({"query_set": query_set, "result": None, "error": str(exc)})
    return all_results

def load_queries_from_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        queries_yaml = yaml.safe_load(file)
    query_sets = [queries_yaml[key] for key in queries_yaml]
    return query_sets

# Load queries from a YAML file
yaml_file_path = r"Monkey\python\oracledb\queries.yaml"
query_sets = load_queries_from_yaml(yaml_file_path)

output_types = ['sql']  # Options: 'json', 'sql', or both

# Initialize connection pool
pool = initialize_connection_pool()
if pool is None:
    logging.error("Failed to create connection pool. Exiting...")
    exit(1)

start_time = time.time()

results = execute_multiple_query_sets(pool, query_sets, output_types)

end_time = time.time()

total_elapsed_time = end_time - start_time
total_hours, total_rem = divmod(total_elapsed_time, 3600)
total_minutes, total_seconds = divmod(total_rem, 60)

print(f"Total time taken for all queries: {int(total_hours)} hours {int(total_minutes)} minutes {total_seconds:.2f} seconds")
