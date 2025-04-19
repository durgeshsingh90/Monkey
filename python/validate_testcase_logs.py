# send_iso_logs.py

import re
import requests

# Regex to detect a new timestamp line (start of a new message block)
TIMESTAMP_PATTERN = re.compile(r'^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')

def split_log_blocks(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    blocks = []
    current_block = []

    for line in lines:
        if TIMESTAMP_PATTERN.match(line):
            if current_block:
                blocks.append("".join(current_block))
                current_block = []
        current_block.append(line)

    # Add the last block if any
    if current_block:
        blocks.append("".join(current_block))

    return blocks

def send_to_api(log_block):
    url = 'http://localhost:8000/splunkparser/parse/'
    try:
        response = requests.post(url, data={'log': log_block})
        print("✅ Sent block. Response:")
        print(response.text)
    except requests.RequestException as e:
        print(f"❌ Error sending block: {e}")

if __name__ == "__main__":
    log_file_path = r"D:\Projects\VSCode\MangoData\splunk_log.txt"  # Change to your file path
    blocks = split_log_blocks(log_file_path)

    print(f"📦 Found {len(blocks)} message blocks.\n")

    for i, block in enumerate(blocks, start=1):
        print(f"🚀 Sending block {i}...")
        send_to_api(block)
