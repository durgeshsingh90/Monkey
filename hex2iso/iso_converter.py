import binascii

def hex_to_ascii(hex_str):
    return bytes.fromhex(hex_str).decode('utf-8', errors='ignore')

def ascii_to_hex(s):
    return binascii.hexlify(s.encode()).decode()

def parse_length(hex_str, digits=2):
    return int(hex_to_ascii(hex_str[:digits * 2])), digits * 2

def parse_variable(hex_str, var_type):
    if var_type == 'llvar':
        length, offset = parse_length(hex_str, 2)
    elif var_type == 'lllvar':
        length, offset = parse_length(hex_str, 3)
    else:
        raise Exception(f"Unknown variable type: {var_type}")
    data = hex_to_ascii(hex_str[offset:offset + length * 2])
    return data, offset + length * 2

def parse_bitmap(bitmap_hex):
    binary = bin(int(bitmap_hex, 16))[2:].zfill(64)
    return [i + 1 for i, b in enumerate(binary) if b == '1']

def parse_block(hex_str, block_def):
    pos = 0
    bitmap_len = block_def["bitmap"]["len"] * 2
    bitmap_hex = hex_str[pos:pos + bitmap_len]
    pos += bitmap_len

    present_fields = parse_bitmap(bitmap_hex)
    data = {}

    for field_num in present_fields:
        field_key = f"DE{str(field_num).zfill(3)}"
        field_def = block_def["fields"].get(field_key)
        if not field_def:
            continue

        if field_def.get("type") in ("text", "numeric"):
            field_len = field_def["len"]
            if isinstance(field_len, int):
                length = field_len * 2
                value = hex_to_ascii(hex_str[pos:pos + length])
                pos += length
            else:
                value, consumed = parse_variable(hex_str[pos:], field_len)
                pos += consumed

        elif field_def.get("type") == "tag_len_val":
            total_len, offset = parse_length(hex_str[pos:], 3)
            inner_pos = pos + offset
            end_pos = inner_pos + total_len * 2
            tags = {}
            while inner_pos < end_pos:
                tag = hex_to_ascii(hex_str[inner_pos:inner_pos + 4])
                inner_pos += 4
                tag_len, tag_off = parse_length(hex_str[inner_pos:], 2)
                inner_pos += tag_off
                tag_val = hex_to_ascii(hex_str[inner_pos:inner_pos + tag_len * 2])
                inner_pos += tag_len * 2
                tags[tag] = tag_val
            value = tags
            pos = end_pos

        elif field_def.get("type") == "len_tag_val":
            total_len, offset = parse_length(hex_str[pos:], 3)
            inner_pos = pos + offset
            end_pos = inner_pos + total_len * 2
            tags = {}
            while inner_pos < end_pos:
                tag = hex_to_ascii(hex_str[inner_pos:inner_pos + 4])
                inner_pos += 4
                tag_len, tag_off = parse_length(hex_str[inner_pos:], 3)
                inner_pos += tag_off
                tag_val = hex_to_ascii(hex_str[inner_pos:inner_pos + tag_len * 2])
                inner_pos += tag_len * 2
                tags[tag] = tag_val
            value = tags
            pos = end_pos

        else:
            continue

        data[field_key] = value

    return data, pos

def parse_iso8583_message(hex_str, schema):
    pos = 0
    mti_len = schema['fields']['mti']['len'] * 2
    mti = hex_to_ascii(hex_str[pos:pos + mti_len])
    pos += mti_len

    parsed = {'mti': mti, 'data_elements': {}}
    for block in schema['fields']['data_elements']['blocks']:
        block_data, consumed = parse_block(hex_str[pos:], block)
        parsed['data_elements'].update(block_data)
        pos += consumed
    return parsed

def encode_length(value, digits=2):
    return ascii_to_hex(str(len(value)).zfill(digits))

def get_field_hex(field_id, value, definition):
    if definition.get("type") in ("text", "numeric"):
        field_len = definition["len"]
        if isinstance(field_len, int):
            return ascii_to_hex(value)
        elif field_len.lower() == "llvar":
            return encode_length(value, 2) + ascii_to_hex(value)
        elif field_len.lower() == "lllvar":
            return encode_length(value, 3) + ascii_to_hex(value)

    elif definition.get("type") == "tag_len_val":
        encoded = ""
        for tag, val in value.items():
            encoded += ascii_to_hex(tag)
            encoded += encode_length(val, 2)
            encoded += ascii_to_hex(val)
        total_len = encode_length(encoded, 3)
        return total_len + encoded

    elif definition.get("type") == "len_tag_val":
        encoded = ""
        for tag, val in value.items():
            encoded += ascii_to_hex(tag)
            encoded += encode_length(val, 3)
            encoded += ascii_to_hex(val)
        total_len = encode_length(encoded, 3)
        return total_len + encoded

    return ""

def build_bitmap(field_ids):
    bitmap = [0] * 64
    for i in field_ids:
        if 1 <= i <= 64:
            bitmap[i - 1] = 1
    binary = ''.join(str(b) for b in bitmap)
    return hex(int(binary, 2))[2:].zfill(16).upper()

def build_iso8583_hex(json_data, schema):
    mti = ascii_to_hex(json_data["mti"])
    field_hex_parts = []
    field_ids = []

    first_block = schema["fields"]["data_elements"]["blocks"][0]["fields"]
    data_elements = json_data["data_elements"]

    for key, value in data_elements.items():
        if not key.startswith("DE"):
            continue
        field_num = int(key[2:])
        if key in first_block:
            field_def = first_block[key]
        else:
            continue  # (second bitmap support can be added later)

        encoded = get_field_hex(key, value, field_def)
        field_ids.append(field_num)
        field_hex_parts.append((field_num, encoded))

    bitmap_hex = build_bitmap(field_ids)
    result = mti + bitmap_hex

    for _, field_hex in sorted(field_hex_parts):
        result += field_hex

    return result
