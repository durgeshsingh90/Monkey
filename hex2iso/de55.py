import json

def ascii_to_hex(s):
    """Convert ASCII string to hex (e.g., '146' -> '313436')"""
    return ''.join(f'{ord(c):02X}' for c in s)

def encode_tlv(tag, value):
    """
    Encode a single TLV field:
    - tag: hex string (e.g., '9F1A')
    - value: hex string (e.g., '0276')
    """
    tag_bytes = bytes.fromhex(tag)
    value_bytes = bytes.fromhex(value)
    length = len(value_bytes)

    # EMV-style length encoding
    if length <= 127:
        length_bytes = bytes([length])
    else:
        len_len = (length.bit_length() + 7) // 8
        length_bytes = bytes([0x80 | len_len]) + length.to_bytes(len_len, 'big')

    return tag_bytes + length_bytes + value_bytes

def build_de055_tlv_block(tlv_dict):
    """
    Build full DE055 block:
    - TLV-encode all subfields
    - Add 3-digit ASCII length prefix
    - Return as uppercase hex string
    """
    result = b''
    for tag in sorted(tlv_dict.keys()):  # sorted for consistency
        tlv = encode_tlv(tag, tlv_dict[tag])
        result += tlv

    length_prefix = ascii_to_hex(str(len(result)).zfill(3))  # e.g., 146 → '146' → '313436'
    return length_prefix + result.hex().upper()

# === Example usage ===

if __name__ == '__main__':
    de055_input = {
        "5F2A": "0978",
        "82": "2000",
        "84": "A0000000031010",
        "95": "0000000000",
        "9A": "241204",
        "9C": "00",
        "9F02": "000000000124",
        "9F03": "000000000000",
        "9F09": "0001",
        "9F10": "1F220100A000000000564953414C335445535443415345000000000000000000",
        "9F1A": "0276",
        "9F26": "A102FB07319A4437",
        "9F27": "80",
        "9F33": "20F8C8",
        "9F34": "020000",
        "9F35": "21",
        "9F36": "0002",
        "9F37": "AC9E2702",
        "9F6E": "20700000"
    }

    de055_hex = build_de055_tlv_block(de055_input)
    print("✅ Final DE055 Hex (LLLVAR + TLV):")
    print(de055_hex)
