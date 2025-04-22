# runquery/scripts/db_connection.py

import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import time

from django.conf import settings

# Logging setup
logging.basicConfig(level=logging.INFO)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super().default(obj)

def get_db_config(db_key):
    try:
        config = settings.DATABASES[db_key]
        return {
            "user": config["USER"],
            "password": config["PASSWORD"],
            "dsn": config["NAME"],
            "client_path": config.get("client_path")
        }
    except KeyError:
        raise ValueError(f"Invalid database key: {db_key}")

def initialize_connection(db_key):
    try:
        config = get_db_config(db_key)
        if config["client_path"]:
            oracledb.init_oracle_client(lib_dir=config["client_path"])
            logging.info(f"Oracle client initialized from {config['client_path']}")
        connection = oracledb.connect(user=config["user"], password=config["password"], dsn=config["dsn"])
        logging.info(f"Successfully connected to database [{db_key}]")
        return connection
    except oracledb.DatabaseError as e:
        logging.error(f"Database connection error: {e}")
        return None

def execute_query(query, db_key="uat_ist"):
    query_result = {"query": query, "db_key": db_key, "result": None, "error": None}
    connection = initialize_connection(db_key)
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        return query_result
    
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query.rstrip(';'))
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
            query_result["result"] = result
        finally:
            cursor.close()
            connection.close()
    except oracledb.DatabaseError as e:
        error = e.args[0]
        logging.error(f"DB error {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        query_result["error"] = str(e)

    return query_result

def save_query_result_to_file(result, query, script_name="manual_script"):
    table_name = query.split()[3].split('.')[-1]
    output_dir = os.path.join('Monkey', 'media', 'oracledb', script_name)
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"{table_name}_output.json")
    with open(output_filename, 'w') as f:
        json.dump(result, f, cls=CustomJSONEncoder, indent=4)

def execute_queries_with_new_connection(queries, db_key="uat_ist", script_name="manual_script"):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {
            executor.submit(execute_query, q, db_key): q for q in queries
        }
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result()
                results.append(result)
                save_query_result_to_file(result, query, script_name)
            except Exception as e:
                logging.error(f"Query failed: {query}, Exception: {e}")
                results.append({"query": query, "result": None, "error": str(e)})
    return results

def execute_multiple_query_sets(query_sets_dict, script_name="manual_script"):
    # query_sets_dict format: {"uat_ist": [query1, query2], "prod_ist": [query3]}
    all_results = []
    with ThreadPoolExecutor(max_workers=len(query_sets_dict)) as executor:
        future_to_dbkey = {
            executor.submit(execute_queries_with_new_connection, qset, db_key, script_name): db_key
            for db_key, qset in query_sets_dict.items()
        }
        for future in as_completed(future_to_dbkey):
            db_key = future_to_dbkey[future]
            try:
                result = future.result()
                all_results.extend(result)
            except Exception as e:
                logging.error(f"[{db_key}] Query set failed: {e}")
                all_results.append({"db_key": db_key, "error": str(e)})
    return all_results
