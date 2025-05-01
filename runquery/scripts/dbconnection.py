import oracledb
import logging
import json
from datetime import datetime
import base64

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Oracle connection details
username = 'oasis77'
password = 'ist0py'
dsn_alias = 'ISTU2_EQU'  # Alias defined in TNSNAMES.ORA

# Provide the path to the Oracle Instant Client libraries
oracle_client_path = r"C:\Oracle\Ora12c_64\BIN"  # Your Oracle Instant Client path

# Custom JSON encoder for handling specific data types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        return super(CustomJSONEncoder, self).default(obj)

def execute_query(query):
    try:
        # Initialize the Oracle client with the provided library path
        oracledb.init_oracle_client(lib_dir=oracle_client_path)
        logging.info(f"Oracle client initialized from {oracle_client_path}")

        # Attempt to create a connection using the TNS alias
        connection = oracledb.connect(user=username, password=password, dsn=dsn_alias)
        logging.info("Successfully connected to the database")

        # Create a cursor
        cursor = connection.cursor()

        # Execute the query
        cursor.execute(query.rstrip(';'))  # Remove the semicolon if present
        logging.info(f"Executed query: {query}")

        # Fetch all rows and column names with their data types
        rows = cursor.fetchall()
        metadata = cursor.description
        columns = [(col[0], col[1]) for col in metadata]

        # Convert rows to list of dictionaries for JSON output
        result = []
        for row in rows:
            row_dict = {}
            for idx, value in enumerate(row):
                col_name, col_type = columns[idx]
                # Handle datatype conversions based on col_type
                if col_type in (oracledb.DB_TYPE_TIMESTAMP, oracledb.DB_TYPE_DATE):
                    if value is not None:
                        value = value.isoformat()
                elif col_type == oracledb.DB_TYPE_RAW:
                    if value is not None:
                        value = base64.b64encode(value).decode('utf-8')
                row_dict[col_name] = value
            result.append(row_dict)

        # Convert result to JSON string with CustomJSONEncoder for datetime and bytes
        json_result = json.dumps(result, indent=2, cls=CustomJSONEncoder)
        print(json_result)

        # Close the cursor and the connection
        cursor.close()
        connection.close()
        logging.info("Connection closed")

    except oracledb.DatabaseError as e:
        # Handle connection errors
        error, = e.args
        logging.error(f"An error occurred: {error.code}: {error.message}")

        if error.isrecoverable:
            logging.error("The error is recoverable. You might want to retry the connection.")
        else:
            logging.error("The error is not recoverable. Check your configuration and network.")

        # Provide user guide link for further help
        logging.error(f"For troubleshooting help, visit: {error.context}")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Function to read multi-line SQL input from the user
def read_multiline_input(prompt):
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)
    return "\n.join(lines)"

# Main logic
if __name__ == "__main__":
    # Prompt the user to input a multi-line SQL query
    sql_query = read_multiline_input("Please enter your SQL query (end with a blank line):")
    execute_query(sql_query)
