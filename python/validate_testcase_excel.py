# excel_and_log_parser.py

import pandas as pd
import re
import requests

# Configure pandas to print everything
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# === ISO8583 HEADER DETECTION ===

# Regex pattern to match DE or BM fields in various formats
DE_PATTERN = re.compile(r'\b(?:DE|BM)\s*0*\d+(?:\.\d+)?(?:\s*\([^)]+\))?')

def is_valid_header(row):
    count = 0
    for cell in row:
        if pd.isna(cell):
            continue
        matches = DE_PATTERN.findall(str(cell))
        count += len(matches)
    return count > 5

def read_and_print_excel(file_path):
    # print("\n📘 Reading Excel File:")
    all_sheets = pd.read_excel(file_path, sheet_name=None, header=None)

    for sheet_name, df in all_sheets.items():
        # print(f"\n=== Sheet: {sheet_name} ===")
        header_row_index = None

        for i, row in df.iterrows():
            if is_valid_header(row):
                header_row_index = i
                break

        if header_row_index is not None:
            df.columns = df.iloc[header_row_index]
            df = df[(header_row_index + 1):].reset_index(drop=True)
            # print(df)
        else:
            print("⚠️ No valid header with >5 ISO8583 DEs found.")

# === LOG PARSER + API SENDER ===

TIMESTAMP_PATTERN = re.compile(r'^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')

import re

def split_log_blocks(log_file_path):
    with open(log_file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    blocks = []
    current_block = []
    current_route = None
    current_message_id = None

    for line in lines:
        if 'INBOUND MESSAGE ID' in line:
            # Save previous block
            if current_block:
                blocks.append({
                    'block': "".join(current_block),
                    'route': current_route,
                    'message_id': current_message_id
                })
                current_block = []

            # Extract route
            route_match = re.search(r'\[\s*([A-Za-z]+:\d+)\s*\]', line)
            if route_match:
                current_route = route_match.group(1).strip()


            # Extract message_id
            msgid_match = re.search(r'MESSAGE ID\[(.*?)\]', line)
            if msgid_match:
                current_message_id = msgid_match.group(1).strip()

        current_block.append(line)

    # Append final block
    if current_block:
        blocks.append({
            'block': "".join(current_block),
            'route': current_route,
            'message_id': current_message_id
        })

    return blocks




all_responses = []

def send_to_api(log_block, block_index, route=None, message_id=None):
    url = 'http://localhost:8000/splunkparser/parse/'

    try:
        response = requests.post(url, json={'log_data': log_block})
        response_json = response.json()

        # Add metadata
        response_json['block_index'] = block_index
        response_json['route'] = route
        response_json['message_id'] = message_id

        all_responses.append(response_json)

        print(f"\n================== 📩 Response for Block {block_index} ==================")
        print(json.dumps(response_json, indent=2))

    except Exception as e:
        print(f"❌ Error sending Block {block_index}: {e}")

def process_log_file(log_file_path):
    print("\n📄 Reading Log File and Sending Blocks:")
    blocks = split_log_blocks(log_file_path)
    print(f"📦 Found {len(blocks)} message blocks.\n")

    for i, block_data in enumerate(blocks, start=1):
        print(f"🚀 Sending block {i}...")
        send_to_api(block_data['block'], i, block_data['route'], block_data['message_id'])


# === Grouping ===
import binascii
from collections import defaultdict

def hex_to_ascii(value):
    try:
        # If it's already ASCII, this will fail and fall back
        return bytes.fromhex(value).decode('ascii')
    except:
        return value  # already ASCII

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

# === MAIN ===
import json
if __name__ == "__main__":
    excel_file_path = r"D:\Projects\VSCode\MangoData\ISO8583_eCommerce_TestCases (1).xlsx"
    log_file_path = r"D:\Projects\VSCode\MangoData\splunk_log.txt"

    read_and_print_excel(excel_file_path)

    # 🧺 Init list to collect all responses globally
    all_responses = []

    # 📨 Send and collect parsed blocks
    process_log_file(log_file_path)

    # 📊 Group by RRN/STAN and save
    grouped_data = group_responses_by_rrn(all_responses)

    with open("grouped_by_rrn.json", "w") as f:
        json.dump(grouped_data, f, indent=2)

    print("✅ Grouped data saved to grouped_by_rrn.json")
