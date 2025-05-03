import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Data elements that use LLL + subfield format (e.g., DE060, DE061, DE062, DE065)
DE6X_FIELDS = ['DE060', 'DE061', 'DE062', 'DE065','DE066']


# ========== Helper Functions ==========

def hex_to_ascii(hex_str):
    if len(hex_str) % 2 != 0:
        raise ValueError(f"Invalid hex length: {len(hex_str)} for input {hex_str}")
    return bytearray.fromhex(hex_str).decode()

def hex_to_bin(hex_str):
    return bin(int(hex_str, 16))[2:].zfill(len(hex_str) * 4)

def get_active_des(bitmap_binary):
    return ['DE' + str(i + 1).zfill(3) for i, bit in enumerate(bitmap_binary) if bit == '1']

def read_variable_length(data, length_digits, max_allowed_length=None):
    len_prefix_hex = data[:length_digits * 2]
    len_ascii = hex_to_ascii(len_prefix_hex)

    try:
        length = int(len_ascii)
    except ValueError:
        raise ValueError(f"Invalid ASCII length prefix: {len_ascii} in hex {len_prefix_hex}")

    if max_allowed_length and length > max_allowed_length:
        raise ValueError(f"Declared length {length} exceeds max allowed {max_allowed_length}")

    offset = length_digits * 2
    value_hex = data[offset:offset + length * 2]
    value_ascii = hex_to_ascii(value_hex)

    logging.info(f"Length prefix (HEX): {len_prefix_hex} → {len_ascii}")
    logging.info(f"Value HEX: {value_hex}")
    logging.info(f"Value ASCII: {value_ascii}")

    return value_ascii, offset + length * 2

def read_fixed_length(data, length):
    value_hex = data[:length * 2]
    value_ascii = hex_to_ascii(value_hex)
    logging.info(f"Value HEX: {value_hex}")
    logging.info(f"Value ASCII: {value_ascii}")
    return value_ascii, length * 2

def parse_field(field_key, field_schema, hex_data):
    field_name = field_schema.get("name", field_key)
    field_type = field_schema.get("field_type", "").lower()

    logging.info(f"Parsing {field_key} - {field_name}")

    if 'length' in field_schema:
        length = field_schema['length']
        value, consumed = read_fixed_length(hex_data, length)

    elif 'max_length' in field_schema:
        max_length = field_schema['max_length']

        if field_type == 'llvar':
            length_digits = 2
        elif field_type == 'lllvar':
            length_digits = 3
        else:
            raise ValueError(f"{field_key} has 'max_length' but invalid or missing 'field_type'.")

        value, consumed = read_variable_length(hex_data, length_digits, max_allowed_length=max_length)

    else:
        raise ValueError(f"{field_key} is missing both 'length' and 'max_length'.")

    # Special case for DE055 - parse TLV using subfield schema
    if field_key == 'DE055':
        subfield_schema = field_schema.get('subfields', {})
        value_dict = parse_tlv(value, subfield_schema)
        logging.info(f"{field_key} - Parsed TLV Subfields: {json.dumps(value_dict, indent=2)}")
        return value_dict, consumed

    if field_key in DE6X_FIELDS:
        subfield_schema = field_schema.get('subfields', {})
        value_dict = parse_de6x_subfields(value, subfield_schema, field_key)
        logging.info(f"{field_key} - Parsed Subfields: {json.dumps(value_dict, indent=2)}")
        return value_dict, consumed


    logging.info(f"{field_key} - Final HEX used: {hex_data[:consumed]}")
    logging.info(f"{field_key} - Final VALUE: {value}")
    return value, consumed


# ========== Main Parser ==========

def parse_iso8583(hex_str, schema_path='omnipay.json'):
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    logging.info("🔍 Starting ISO 8583 parsing...")

    # Step 1: Parse MTI
    mti_len = schema['mti']['length']
    mti_hex = hex_str[:mti_len * 2]
    mti = hex_to_ascii(mti_hex)
    logging.info(f"MTI HEX: {mti_hex}")
    logging.info(f"MTI VALUE: {mti}")

    # Step 2: Parse Bitmap
    bitmap_ascii_hex = hex_str[mti_len * 2:mti_len * 2 + 32]
    bitmap_ascii = hex_to_ascii(bitmap_ascii_hex)
    bitmap_bin = hex_to_bin(bitmap_ascii)
    active_des = get_active_des(bitmap_bin)

    logging.info(f"Bitmap HEX: {bitmap_ascii_hex}")
    logging.info(f"Bitmap ASCII: {bitmap_ascii}")
    logging.info(f"Bitmap BIN: {bitmap_bin}")
    logging.info(f"Active DEs: {active_des}")

    # Step 3: Parse DEs
    pointer = mti_len * 2 + 32
    data_elements = {}
    for de in active_des:
        field_schema = schema['fields'].get(de)
        if not field_schema:
            logging.warning(f"Schema for {de} not found. Skipping.")
            continue

        logging.debug(f"Pointer before {de}: {pointer}")
        logging.debug(f"Next hex preview: {hex_str[pointer:pointer + 40]}")

        try:
            value, consumed = parse_field(de, field_schema, hex_str[pointer:])
            data_elements[de] = value  # keep everything as string to preserve leading zeros
            pointer += consumed
        except Exception as e:
            logging.error(f"❌ Failed to parse {de}: {str(e)}")
            break

    return {
        "mti": mti,
        "data_elements": data_elements
    }
def parse_tlv(data_hex, subfield_schema):
    pointer = 0
    result = {}

    while pointer < len(data_hex):
        # --- Read Tag ---
        tag = data_hex[pointer:pointer + 2]
        pointer += 2

        if int(tag, 16) & 0x1F == 0x1F:  # 2-byte tag
            tag += data_hex[pointer:pointer + 2]
            pointer += 2

        # --- Read Length ---
        length_byte = int(data_hex[pointer:pointer + 2], 16)
        pointer += 2

        if length_byte <= 127:
            length = length_byte
        else:
            # Extended length format (e.g., 81xx)
            num_bytes = length_byte & 0x7F
            length = int(data_hex[pointer:pointer + (num_bytes * 2)], 16)
            pointer += num_bytes * 2

        # --- Read Value ---
        value_hex = data_hex[pointer:pointer + (length * 2)]
        pointer += length * 2

        # Store result using tag name if available
        tag_str = tag.upper()
        tag_name = subfield_schema.get(tag_str, {}).get("name", tag_str)
        result[tag_str] = value_hex

    return result

def parse_de6x_subfields(data_ascii, subfield_schema, field_key="DExx"):
    pointer = 0
    result = {}

    while pointer + 3 <= len(data_ascii):
        length_str = data_ascii[pointer:pointer + 3]
        try:
            total_len = int(length_str)
        except ValueError:
            raise ValueError(f"{field_key}: Invalid LLL length: {length_str}")

        pointer += 3

        if total_len < 2 or pointer + total_len > len(data_ascii):
            logging.warning(f"{field_key}: Invalid or out-of-bounds subfield length {total_len}.")
            break

        subfield_id = data_ascii[pointer:pointer + 2]
        value = data_ascii[pointer + 2:pointer + total_len]

        pointer += total_len

        name = subfield_schema.get(subfield_id, {}).get("name", subfield_id)
        result[subfield_id] = value
        logging.info(f"{field_key} Subfield {subfield_id} ({name}): {value}")

    return result

# ========== Example Usage ==========

if __name__ == '__main__':
    hex_input = "303130303732334336363831323845303941313831363431373636363232323030313030333430303030303030303030303030303031323431323034313331313038313033303537313431313038313230343331313235343939383236303731303033303930363030303032303332343137363636323232303031303033343d3331313232303131313532333335383433333931333130333035374d434c3441455a4c30303031303230303732373233393153756d557020202a66697365727631202020202020202020204265726c696e2020202020202044453937383934414535444443343445394530443237363330333033313330333033323030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303032393235463241303230393738383230323230303038343037413030303030303030333130313039353035303030303030303030303941303332343132303439433031303039463032303630303030303030303031323439463033303630303030303030303030303039463039303230303031394631303230314632323031303041303030303030303030353634393533343134433333353434353533353434333431353334353030303030303030303030303030303030303946314130323032373639463236303841313032464230373331394134343337394632373031383039463333303332304638433839463334303330323030303039463335303132313946333630323030303239463337303441433945323730323946364530343230373030303030303138303037333531303234333030353533303033313335303137313930303031303230303732373233393130343834304950472020202020202037643937376166372d643238622d343065652d613565632d353063626437656436656532303132343154433953505246525a4430313334323835303234373936313333303130363131303037323531313031373633202020202020204d434c3441455a4c"  # replace with full ISO hex string
    parsed = parse_iso8583(hex_input, 'D:/Projects/VSCode/docker/monkey/media/schemas/omnipay.json')
    print("\n--- Parsed JSON Output ---")
    print(json.dumps(parsed, indent=2))
