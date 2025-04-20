import pandas as pd
import re
import requests
from collections import defaultdict
import json
import logging

# Configure pandas to print everything
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

ROUTE_TO_API_MAP = {
    "fromiso": "http://localhost:8000/splunkparser/parse/",
    "toiso": "http://localhost:8000/splunkparser/parse/",
    "default": "http://localhost:8000/genericparser/parse_fallback/",  # <-- handles the rest
}

# Custom logging handler to handle Unicode characters
class UnicodeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if not hasattr(stream, 'encoding') or stream.encoding == 'ANSI_X3.4-1968':
                stream.write(msg.encode('utf-8', 'ignore').decode('utf-8') + self.terminator)
            else:
                stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("debug.log", mode='w', encoding='utf-8'),
                              UnicodeStreamHandler()])

# ISO8583 HEADER DETECTION

# Regex pattern to match DE or BM fields in various formats
DE_PATTERN = re.compile(r'\b(?:DE|BM)\s*0*\d+(?:\.\d+)?(?:\s*\([^)]+\))?')

# Function to validate header based on DE pattern
def is_valid_header(row):
    count = 0
    for cell in row:
        if pd.isna(cell):
            continue
        matches = DE_PATTERN.findall(str(cell))
        count += len(matches)
    return count > 5

# Function to read and print Excel data, identifying headers using DE pattern
def read_and_print_excel(file_path):
    all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    for sheet_name, df in all_sheets.items():
        header_row_index = None
        for i, row in df.iterrows():
            if is_valid_header(row):
                header_row_index = i
                break

        if header_row_index is not None:
            df.columns = df.iloc[header_row_index]
            df = df[(header_row_index + 1):].reset_index(drop=True)
        else:
            logging.warning("No valid header with >5 ISO8583 DEs found in sheet '%s'.", sheet_name)

# === LOG PARSER + API SENDER ===

TIMESTAMP_PATTERN = re.compile(r'^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')
ROUTE_PATTERN = re.compile(r'\[\s*([A-Za-z]+:\d+)\s*\]')
MSGID_PATTERN = re.compile(r'message id\[(.*?)\]', re.IGNORECASE)

# Function to extract route and message ID from a block of text
def extract_route_and_message_id(block):
    route = None
    message_id = None

    logging.debug("Extracting route and message ID...")
    for line in block.split('\n'):
        line = line.strip()
        logging.debug("Analyzing line: '%s'", line)  # Debug log to see the current line being analyzed
        
        # Extract route if not yet found
        if not route:
            route_match = ROUTE_PATTERN.search(line)
            if route_match:
                route = route_match.group(1).strip()
                logging.debug("Found route: %s", route)  # Debug log for route detection

        # Extract message_id if not yet found
        if not message_id:
            msgid_match = MSGID_PATTERN.search(line)
            if msgid_match:
                message_id = msgid_match.group(1).strip()
                logging.debug("Found message ID: %s", message_id)  # Debug log for message ID detection

        # If both route and message ID are found, no need to continue searching
        if route and message_id:
            break

    logging.debug("Finished route extraction: %s, message ID extraction: %s", route, message_id)
    return route, message_id

# Function to split the log file into blocks based on timestamps
def split_log_blocks(log_file_path):
    with open(log_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    blocks = []
    current_block = []
    for line in lines:
        timestamp_match = TIMESTAMP_PATTERN.match(line)

        if timestamp_match and current_block:
            blocks.append("".join(current_block))
            current_block = []

        current_block.append(line)

    if current_block:
        blocks.append("".join(current_block))

    logging.info("Split into %d blocks", len(blocks))
    return [{"block": block} for block in blocks]

all_responses = []

# Function to send a log block to the API
def send_to_api(log_block, block_index, route=None, message_id=None):
    url = 'http://localhost:8000/splunkparser/parse/'
    try:
        logging.info("\n================== 📨 Sending Block %d ==================", block_index)
        logging.info("📌 Route: %s", route)
        logging.info("📌 Message ID: %s", message_id)
        logging.info("📜 Block Content:\n%s", log_block)
        logging.info("====================================================")

        response = requests.post(url, json={'log_data': log_block})
        response_json = response.json()

        # Add metadata
        response_json['block_index'] = block_index
        response_json['route'] = route
        response_json['message_id'] = message_id

        all_responses.append(response_json)

        logging.info("\n================== 📩 Response for Block %d ==================", block_index)
        logging.info(json.dumps(response_json, indent=2))
        logging.info("====================================================\n")

    except Exception as e:
        logging.error("Error sending Block %d: %s", block_index, e)

# Function to process the log file, split into blocks, and send to the API
def process_log_file(log_file_path):
    logging.info("\n📄 Reading Log File and Sending Blocks:")
    blocks = split_log_blocks(log_file_path)
    logging.info("📦 Found %d message blocks.\n", len(blocks))

    for i, block_data in enumerate(blocks, start=1):
        block_content = block_data['block']
        route, message_id = extract_route_and_message_id(block_content)

        if route:
            route_key = route.lower().split(":")[0]  # e.g., 'FromIso:1234' → 'fromiso'
            api_url = ROUTE_TO_API_MAP.get(route_key, ROUTE_TO_API_MAP["default"])  # fallback if not found

            logging.info("🚀 Sending block %d [Route: %s] to %s", i, route, api_url)
            send_to_api(block_content, i, route, message_id, url=api_url)
        else:
            logging.info("⏭️ Skipping block %d — No route detected.", i)

# Function to convert HEX to ASCII, if possible
def hex_to_ascii(value):
    try:
        return bytes.fromhex(value).decode('ascii')
    except:
        return value  # already ASCII

# Function to group responses by RRN or STAN
def group_responses_by_rrn(responses):
    grouped = defaultdict(list)
    for response in responses:
        data_elements = response.get('result', {}).get('data_elements', {})
        rrn = data_elements.get('DE037')
        stan = data_elements.get('DE011')

        if rrn:
            normalized_rrn = hex_to_ascii(rrn)
            grouped[normalized_rrn].append(response)
        elif stan:
            grouped[f'STAN_{stan}'].append(response)
        else:
            grouped['UNKNOWN'].append(response)

    return dict(grouped)

if __name__ == "__main__":
    excel_file_path = r"C:\Users\f94gdos\Desktop\New folder (6)\CNP Integrated Test cases spreadsheet v6.1.xlsx"
    log_file_path = r"C:\Users\f94gdos\Desktop\New folder (6)\RAW.txt"

    read_and_print_excel(excel_file_path)

    # 🧺 Init list to collect all responses globally
    all_responses = []

    # 📨 Send and collect parsed blocks
    process_log_file(log_file_path)

    # 📊 Group by RRN/STAN and save
    grouped_data = group_responses_by_rrn(all_responses)

    with open("grouped_by_rrn.json", "w") as f:
        json.dump(grouped_data, f, indent=2)

    logging.info("✅ Grouped data saved to grouped_by_rrn.json")
