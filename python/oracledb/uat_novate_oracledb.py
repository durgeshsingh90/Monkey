import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Oracle connection details
username = 'novate'
password = 'nov1234'
dsn_alias = 'ISTU2'  # Alias defined in TNSNAMES.ORA


# Provide the path to the Oracle Instant Client libraries
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"

# Custom JSON encoder for handling specific data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def initialize_connection():
    try:
        oracledb.init_oracle_client(lib_dir=oracle_client_path)
        logging.info(f"Oracle client initialized from {oracle_client_path}")
        connection = oracledb.connect(user=username, password=password, dsn=dsn_alias)
        logging.info("Successfully connected to the database")
        return connection
    except oracledb.DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        return None

def execute_query(query):
    query_result = {"query": query, "result": None, "error": None}
    connection = initialize_connection()
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
            for row in rows:
                row_dict = {}
                for idx, value in enumerate(row):
                    col_name = columns[idx]
                    row_dict[col_name] = value
                result.append(row_dict)

            query_result["result"] = result

        finally:
            cursor.close()
            connection.close()

    except oracledb.DatabaseError as e:
        error = e.args[0]
        logging.error(f"An error occurred: {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        query_result["error"] = str(e)

    return query_result

def save_query_result_to_file(result, query):
    # Extract table name from query
    table_name = query.split()[3].split('.')[1]

    # Create the output directory path based on script filename and table name
    script_filename = os.path.splitext(os.path.basename(__file__))[0]
    output_dir = os.path.join('Monkey', 'media','oracledb', script_filename)
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"{table_name}_output.json")

    # Write each query result to a separate JSON file
    with open(output_filename, 'w') as output_file:
        json.dump(result, output_file, cls=CustomJSONEncoder, indent=4)

def execute_queries_with_new_connection(queries):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {executor.submit(execute_query, query): query for query in queries}
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            start_time = time.time()
            try:
                result = future.result()
                results.append(result)
                logging.info(f"Query completed: {query}")

                # Save query result to file
                save_query_result_to_file(result, query)

            except Exception as exc:
                logging.error(f"Query {query} generated an exception: {exc}")
                results.append({"query": query, "result": None, "error": str(exc)})

            end_time = time.time()
            elapsed_time = end_time - start_time
            hours, rem = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(rem, 60)

    return results

def execute_multiple_query_sets(query_sets):
    all_results = []
    with ThreadPoolExecutor(max_workers=len(query_sets)) as executor:
        future_to_query_set = {executor.submit(execute_queries_with_new_connection, queries): queries for queries in query_sets}
        for future in as_completed(future_to_query_set):
            query_set = future_to_query_set[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as exc:
                logging.error(f"Query set {query_set} generated an exception: {exc}")
                all_results.append({"query_set": query_set, "result": None, "error": str(exc)})
    return all_results

query_set_1 = [""" select * from oasis77.card_scheme """]
query_set_2 = [""" select * from oasis77.institution """]
query_set_3 = [""" select * from oasis77.acq_profile """]
query_set_4 = [""" select * from oasis77.iss_profile """]
query_set_5 = [""" select * from oasis77.inst_profile """]
query_set_6 = [""" select * from oasis77.shcbin """]
query_set_7 = [""" select * from oasis77.shckeys """]
query_set_8 = [""" select * from oasis77.shcextbindb """]
query_set_9 = [""" select * from oasis77.istreplaytab """]

query_sets = [
    query_set_1,
    query_set_2,
    query_set_3,
    query_set_4,
    # query_set_5,
    # query_set_6,
    # query_set_7,
    # query_set_8,
    # query_set_9
]

start_time = time.time()

results = execute_multiple_query_sets(query_sets)

end_time = time.time()

total_elapsed_time = end_time - start_time
total_hours, total_rem = divmod(total_elapsed_time, 3600)
total_minutes, total_seconds = divmod(total_rem, 60)

# print(json.dumps(results, cls=CustomJSONEncoder, indent=4))

print(f"Total time taken for all queries: {int(total_hours)} hours {int(total_minutes)} minutes {total_seconds:.2f} seconds")
