# runquery/scripts/db_connection.py

import oracledb
import logging
import json
from datetime import datetime
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from django.conf import settings
from pathlib import Path
import time

# Logging setup
logging.basicConfig(level=logging.INFO)

# Global session storage
db_sessions = {}
session_expiry = {}

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, bytes):
                return base64.b64encode(obj).decode("utf-8")
            elif isinstance(obj, oracledb.LOB):
                return obj.read() if obj.type == oracledb.DB_TYPE_CLOB else base64.b64encode(obj.read()).decode("utf-8")
        except Exception as e:
            return f"[Unserializable object: {type(obj).__name__}]"
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

def get_session_connection(db_key):
    now = time.time()
    expiry = session_expiry.get(db_key, 0)

    if db_key in db_sessions and now < expiry:
        return db_sessions[db_key]

    connection = initialize_connection(db_key)
    if connection:
        db_sessions[db_key] = connection
        session_expiry[db_key] = now + 600  # 10 minutes
    return connection

def execute_query(query, db_key="uat_ist", use_session=False):
    query_result = {"query": query, "db_key": db_key, "result": None, "error": None}
    connection = get_session_connection(db_key) if use_session else initialize_connection(db_key)
    if connection is None:
        query_result["error"] = "Unable to establish database connection"
        log_query_execution(db_key, query, query_result, 0)
        return query_result

    start_time = time.time()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(query)
            if query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in rows]
                query_result["result"] = result
            else:
                connection.commit()
                query_result["result"] = {
                    "message": f"✅ {cursor.rowcount} row(s) affected.",
                    "status": "success"
                }
        finally:
            cursor.close()
            if not use_session:
                connection.close()
    except oracledb.DatabaseError as e:
        error = e.args[0]
        logging.error(f"DB error {error.code}: {error.message}")
        query_result["error"] = f"Database error {error.code}: {error.message}"
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        query_result["error"] = str(e)

    duration = time.time() - start_time
    log_query_execution(db_key, query, query_result, duration)
    return query_result



def execute_queries_with_new_connection(queries, db_key="uat_ist", script_name="manual_script", use_session=False):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_query = {
            executor.submit(execute_query, q, db_key, use_session): q for q in queries
        }
        for future in as_completed(future_to_query):
            query = future_to_query[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logging.error(f"Query failed: {query}, Exception: {e}")
                results.append({"query": query, "result": None, "error": str(e)})
    return results

def execute_multiple_query_sets(query_sets_dict, script_name="manual_script", use_session=False):
    all_results = []
    with ThreadPoolExecutor(max_workers=len(query_sets_dict)) as executor:
        future_to_dbkey = {
            executor.submit(execute_queries_with_new_connection, qset, db_key, script_name, use_session): db_key
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

def get_or_load_table_metadata(db_key="uat_ist", refresh=False):
    metadata_dir = Path(settings.MEDIA_ROOT) / "runquery" / "metadata"
    metadata_file = metadata_dir / f"{db_key}.json"

    if not refresh and metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"error": f"Failed to read cached metadata: {str(e)}"}

    connection = initialize_connection(db_key)
    if not connection:
        return {"error": f"Unable to connect to DB '{db_key}'"}

    metadata = {}
    try:
        cursor = connection.cursor()
        db_settings = settings.DATABASES.get(db_key, {})
        owner = db_settings.get("owner", db_settings.get("USER")).upper()

        cursor.execute("""
            SELECT table_name 
            FROM all_tables 
            WHERE owner = :1 
            AND table_name NOT LIKE 'BIN$%' 
            ORDER BY table_name ASC
        """, [owner])
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            cursor.execute("""
                SELECT column_name 
                FROM all_tab_columns 
                WHERE table_name = :1 AND owner = :2 
                ORDER BY column_name ASC
            """, [table, owner])
            columns = [row[0] for row in cursor.fetchall()]
            qualified_key = f"{owner}.{table}"
            metadata[qualified_key] = columns


    except Exception as e:
        return {"error": str(e)}
    finally:
        cursor.close()
        connection.close()

    metadata_dir.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, 'w') as f:
        json.dump({"tables": metadata}, f, indent=2)

    return {"tables": metadata}

from datetime import datetime
import json
from pathlib import Path
from django.conf import settings

def log_query_execution(db_key, query, result, duration):
    """
    Writes only the most recent query result to query_logs.json,
    safely overwriting previous logs and ensuring valid JSON.
    """
    log_dir = Path(settings.MEDIA_ROOT) / "runquery"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "query_logs.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "db": db_key,
        "query": query.strip(),
        "duration_sec": round(duration, 3),
        "result": result.get("result") if result.get("error") is None else None,
        "error": result.get("error"),
    }

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=2, cls=CustomJSONEncoder)
    except Exception as e:
        print(f"❌ Failed to write query log: {e}")
