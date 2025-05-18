import json
import logging
import sys

# UTF-8-safe logging
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [stream_handler]

DE6X_FIELDS = ['DE060', 'DE061', 'DE062', 'DE065', 'DE066']

def ascii_to_hex(ascii_str):
    return ascii_str.encode().hex().lower()

def build_fixed_length(value, length):
    return ascii_to_hex(str(value).ljust(length, '0'))

def build_variable_length(value, length_digits):
    prefix = str(len(value)).zfill(length_digits)
    safe_value = ''.join(c if ord(c) < 128 else '?' for c in value)
    logging.info(f"building {length_digits}-digit length prefix: {prefix} for value: {safe_value}")
    return ascii_to_hex(prefix + value)

def build_de6x_subfields(de_dict):
    result = ""
    for sub_id, val in de_dict.items():
        total_len = str(len(val) + 2).zfill(3)
        logging.info(f"{sub_id}: total_length={total_len}, value={val}")
        result += total_len + sub_id + val
    return result

def encode_tlv(tag, value):
    tag_bytes = bytes.fromhex(tag.lower())
    value_bytes = bytes.fromhex(value)
    length = len(value_bytes)
    if length <= 127:
        length_bytes = bytes([length])
    else:
        len_len = (length.bit_length() + 7) // 8
        length_bytes = bytes([0x80 | len_len]) + length.to_bytes(len_len, 'big')
    return tag_bytes + length_bytes + value_bytes

def build_tlv(tlv_dict):
    result = b''
    for tag, value in tlv_dict.items():
        entry = encode_tlv(tag, value)
        result += entry
        logging.info(f"tlv tag {tag}: len={len(value)//2} -> hex={entry.hex().upper()}")
    return result.hex().upper()  # 🔁 Uppercase the full TLV hex string


def build_bitmap(fields_present):
    bits = ['0'] * 128
    for field in fields_present:
        if field.startswith("DE"):
            index = int(field[2:]) - 1
            if 0 <= index < 128:
                bits[index] = '1'

    primary = bits[:64]
    secondary = bits[64:]

    if '1' in secondary:
        primary[0] = '1'
        full_bitmap = ''.join(primary + secondary)
        bitmap_hex = hex(int(full_bitmap, 2))[2:].zfill(32).upper()
    else:
        full_bitmap = ''.join(primary)
        bitmap_hex = hex(int(full_bitmap, 2))[2:].zfill(16).upper()

    return bitmap_hex.encode().hex()

def json_to_hex(data, schema_path=r"D:\Projects\VSCode\docker\monkey\media\schemas\omnipay.json"):
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    logging.info(f"\n\n📥 input JSON:\n{json.dumps(data, indent=2)}")

    mti = data.get("mti", "")
    hex_str = ascii_to_hex(mti)
    logging.info(f"mti: {mti} -> {hex_str}")

    fields = data.get("data_elements", {})
    sorted_fields = sorted(fields.keys(), key=lambda x: int(x[2:]))

    bitmap_hex = build_bitmap(sorted_fields)
    logging.info(f"bitmap ascii: {bitmap_hex}")
    hex_str += bitmap_hex.upper()

    for de in sorted_fields:
        field_schema = schema['fields'].get(de)
        if not isinstance(field_schema, dict):
            logging.warning(f"Schema for {de} is not a valid object: {field_schema} (type: {type(field_schema)}), skipping.")
            continue
        

        logging.info(f"encoding {de.lower()}: {field_schema.get('name', '')}")
        value = fields[de]
        field_type = field_schema.get("field_type", "").lower()

        if de == "DE055":
            plain_text = get_de055_plain_text(value)
            de055_hex = convert_plain_text_to_hex(plain_text)
            hex_str += de055_hex



        

        elif de in DE6X_FIELDS:
            nested = build_de6x_subfields(value)
            hex_str += build_variable_length(nested, 3)
        elif 'length' in field_schema:
            hex_str += build_fixed_length(value, field_schema['length'])
        elif 'max_length' in field_schema:
            if field_type == 'llvar':
                hex_str += build_variable_length(value, 2)
            elif field_type == 'lllvar':
                hex_str += build_variable_length(value, 3)
            else:
                logging.warning(f"{de} has max_length but no valid field_type")
        else:
            logging.warning(f"{de} has no length/max_length")

    logging.info(f"\n✅ final hex:\n{hex_str}")
    return hex_str

def get_de055_plain_text(de055_dict):
    plain_str = ""

    for tag, value_hex in de055_dict.items():
        value_bytes = bytes.fromhex(value_hex)
        value_len = len(value_bytes)
        value_len_str = str(value_len).zfill(2)
        entry = tag + value_len_str + value_hex.upper()
        plain_str += entry

        logging.info(f"DE055 tag {tag}: len={value_len} -> {entry}")

    total_len = len(plain_str)
    total_len_prefix = str(total_len).zfill(3)
    full_plain = total_len_prefix + plain_str

    logging.info(f"\n🧾 Final DE055 plain text:\n{full_plain}")
    return full_plain

def convert_plain_text_to_hex(plain_text):
    hex_result = plain_text.encode('ascii').hex().upper()
    logging.info(f"\n🔁 Final DE055 HEX (from ASCII):\n{hex_result}")
    return hex_result


# if __name__ == '__main__':
#     with open("sample.json", "r") as f:
#         sample_json = json.load(f)
#     result = json_to_hex(sample_json)
#     print("\nfinal hex output:\n" + result)
