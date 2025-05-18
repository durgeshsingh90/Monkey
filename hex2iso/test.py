import json
import logging
import sys

# Setup logging
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [stream_handler]

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

# === Entry point ===
if __name__ == "__main__":
    with open("sample.json", "r") as f:
        data = json.load(f)

    de055 = data.get("data_elements", {}).get("DE055")

    if not de055:
        logging.error("❌ DE055 not found in input JSON")
    else:
        plain_text = get_de055_plain_text(de055)
        hex_output = convert_plain_text_to_hex(plain_text)
        print("\n✅ Final DE055 HEX:\n" + hex_output)
