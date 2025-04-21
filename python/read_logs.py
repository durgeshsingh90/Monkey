import re
import json
import logging
import requests
import os
from collections import defaultdict

# ========== CONFIGURATION ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s — %(levelname)s — %(message)s')

# ✅ Route to API mapping
ROUTE_TO_API_MAP = {
    "fromiso": "http://localhost:8000/splunkparser/parse/",
    "toiso": "http://localhost:8000/splunkparser/parse/",
    "default": "http://localhost:8000/genericparser/parse_fallback/",
}

# ========== PATTERNS ==========
TIMESTAMP_PATTERN = re.compile(r'^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}')
ROUTE_PATTERN = re.compile(r'\[\s*([A-Za-z]+:\d+)\s*\]')
MSGID_PATTERN = re.compile(r'message id\[(.*?)\]', re.IGNORECASE)

# ========== UTILS ==========
def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def hex_to_ascii(value):
    try:
        return bytes.fromhex(value).decode('ascii')
    except:
        return value

def ascii_to_hex(s):
    return ''.join(format(ord(c), '02x') for c in s)

def normalize_rrn(rrn, existing_rrns):
    if not isinstance(rrn, str):
        return rrn
    if rrn in existing_rrns:
        return rrn
    if is_hex(rrn):
        try:
            decoded = bytes.fromhex(rrn).decode('ascii')
            if decoded.isprintable() and decoded.isdigit():
                return decoded
        except:
            pass
    for existing in existing_rrns:
        if ascii_to_hex(existing) == rrn:
            return existing
    return rrn

# ========== CORE LOGIC ==========
def extract_route_and_message_id(block):
    route = None
    message_id = None
    logging.debug("Extracting route and message ID...")

    for line in block.split('\n'):
        line = line.strip()
        logging.debug("Analyzing line: '%s'", line)

        if not route:
            match = ROUTE_PATTERN.search(line)
            if match:
                route = match.group(1).strip()
                logging.debug("Found route: %s", route)

        if not message_id:
            match = MSGID_PATTERN.search(line)
            if match:
                message_id = match.group(1).strip()
                logging.debug("Found message ID: %s", message_id)

        if route and message_id:
            break

    return route, message_id

def split_log_blocks(log_file_path):
    with open(log_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = []
    current_block = []

    for line in lines:
        if TIMESTAMP_PATTERN.match(line) and current_block:
            blocks.append("".join(current_block))
            current_block = []
        current_block.append(line)

    if current_block:
        blocks.append("".join(current_block))

    logging.info("Split into %d blocks", len(blocks))
    return [{"block": b} for b in blocks]

def send_to_api(log_block, block_index, route=None, message_id=None, url=None, session=None, all_responses=None):
    session = session or requests
    try:
        logging.info("\n📨 Sending Block %d", block_index)
        logging.info("📌 Route: %s", route)
        logging.info("📌 Message ID: %s", message_id)

        response = session.post(url, json={'log_data': log_block})
        response.raise_for_status()

        response_json = response.json()
        response_json.update({
            'block_index': block_index,
            'route': route,
            'message_id': message_id
        })

        if all_responses is not None:
            all_responses.append(response_json)

        logging.info("📩 Received Response for Block %d", block_index)
    except Exception as e:
        logging.error("❌ Error sending Block %d: %s", block_index, e)

def process_log_file(log_file_path):
    all_responses = []
    logging.info("\n📄 Reading Log File and Sending Blocks:")
    blocks = split_log_blocks(log_file_path)
    session = requests.Session()

    for idx, block in enumerate(blocks, start=1):
        content = block['block']
        route, message_id = extract_route_and_message_id(content)

        if route:
            route_key = route.lower().split(":")[0]
            api_url = ROUTE_TO_API_MAP.get(route_key, ROUTE_TO_API_MAP["default"])
            logging.info("🚀 Sending block %d to API at %s", idx, api_url)
            send_to_api(content, idx, route, message_id, url=api_url, session=session, all_responses=all_responses)
        else:
            logging.warning("⏭️ Skipping block %d — No route found", idx)

    session.close()
    return all_responses

def group_responses_by_rrn(responses):
    grouped = defaultdict(list)
    rrn_to_stan = {}
    existing_rrns = set()

    for res in responses:
        data = res.get('result', {}).get('data_elements', {})
        rrn = data.get('DE037')
        stan = data.get('DE011')

        if rrn:
            norm_rrn = normalize_rrn(rrn, existing_rrns)
            key = f"RRN_{norm_rrn}"
            grouped[key].append(res)
            existing_rrns.add(norm_rrn)
            if stan:
                rrn_to_stan[stan] = key
        elif stan:
            key = rrn_to_stan.get(stan, f"STAN_{stan}")
            grouped[key].append(res)
        else:
            grouped["UNKNOWN"].append(res)

    logging.info("\n📊 Grouping Summary:")
    for k, v in grouped.items():
        logging.info("• %s → %d block(s)", k, len(v))

    return dict(grouped)

# ========== MAIN ==========
if __name__ == "__main__":
    # 🔒 Hardcoded input file path (change it as needed)
    log_file = r"D:\Projects\VSCode\MangoData\splunk_log.txt"

    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        exit(1)

    # Process and group
    responses = process_log_file(log_file)
    grouped = group_responses_by_rrn(responses)

    # Save grouped responses
    base_name = os.path.splitext(os.path.basename(log_file))[0]
    dir_name = os.path.dirname(log_file)
    output_file = os.path.join(dir_name, f"{base_name}_logs.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(grouped, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Done. Grouped responses saved to:\n{output_file}")
