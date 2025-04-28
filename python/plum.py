import json
import binascii
import logging
import os

# === Setup logging ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# === Load schema ===
def load_schema(schema_path):
    logger.info(f"Loading schema from {schema_path}")
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    return schema

# === Helper functions ===
def parse_fixed(data, length):
    return data[:length], data[length:]

def parse_llvar(data):
    ll = int(data[:2])
    value = data[2:2+ll]
    return value, data[2+ll:]

def parse_lllvar(data):
    lll = int(data[:3])
    value = data[3:3+lll]
    return value, data[3+lll:]

def parse_bitmap(bitmap_hex):
    bitmap_bin = bin(int(bitmap_hex, 16))[2:].zfill(64)
    fields = []
    for i, bit in enumerate(bitmap_bin):
        if bit == '1':
            fields.append(i + 1)
    return fields

# === Main parse function ===
def parse_iso8583(hex_data, schema):
    logger.info("Starting to parse ISO8583 message")
    ascii_data = binascii.unhexlify(hex_data).decode('utf-8', errors='ignore')
    output = {}

    # Parse MTI
    mti, ascii_data = parse_fixed(ascii_data, schema['mti']['length'])
    output['MTI'] = mti
    logger.info(f"Parsed MTI: {mti}")

    # Parse Bitmap
    bitmap_hex, ascii_data = parse_fixed(ascii_data, schema['bitmap']['length'])
    fields_present = parse_bitmap(bitmap_hex)
    logger.info(f"Fields present according to bitmap: {fields_present}")

    # Parse each field
    for field_number in fields_present:
        field_key = f'DE{str(field_number).zfill(3)}'
        field_info = schema['fields'].get(field_key)

        if not field_info:
            logger.warning(f"Field {field_key} not found in schema. Skipping.")
            continue

        logger.info(f"Parsing field {field_key} ({field_info.get('name', 'Unknown')})")

        if field_info.get('variable_length'):
            format_type = field_info['format']
            if format_type == 'LLVAR':
                value, ascii_data = parse_llvar(ascii_data)
            elif format_type == 'LLLVAR':
                value, ascii_data = parse_lllvar(ascii_data)
            else:
                logger.error(f"Unsupported variable length format {format_type} for {field_key}")
                break
        else:
            value, ascii_data = parse_fixed(ascii_data, field_info['length'])

        output[field_key] = value

    logger.info("Finished parsing message")
    return output

# === Save output to JSON file ===
def save_output_to_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Parsed output saved to {filename}")

# === Convert JSON to HEX dump ===
def json_to_hex(json_data):
    combined_data = ''
    combined_data += json_data.get('MTI', '')
    # Bitmap and fields are not being reassembled here, you would need additional logic to rebuild it correctly.
    for key in sorted(json_data.keys()):
        if key.startswith('DE'):
            combined_data += json_data[key]
    return binascii.hexlify(combined_data.encode('utf-8')).decode('utf-8')

# === Main execution ===
if __name__ == "__main__":
    # Load schema
    schema_path = os.path.join('media', 'schemas', 'omnipay.json')
    schema = load_schema(schema_path)

    logger.info("Awaiting user input (hex string or JSON)...")
    print("Paste your input (type END on a new line to finish):")
    user_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        user_lines.append(line)

    user_input = ''.join(user_lines)
    user_input = user_input.strip().replace('\n', '').replace(' ', '')

    try:
        # Try parsing as JSON
        json_data = json.loads(user_input)
        logger.info("Detected JSON input.")
        hex_output = json_to_hex(json_data)
        output_filename = 'hex_output.txt'
        with open(output_filename, 'w') as f:
            f.write(hex_output)
        logger.info(f"Hex output saved to {output_filename}")
        print(hex_output)
    except json.JSONDecodeError:
        # Otherwise treat it as hex
        logger.info("Detected HEX input.")
        parsed_data = parse_iso8583(user_input, schema)
        output_filename = 'parsed_output.json'
        save_output_to_file(parsed_data, output_filename)
        print(json.dumps(parsed_data, indent=2))