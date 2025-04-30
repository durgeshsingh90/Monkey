import json
import re
import logging

logger = logging.getLogger('splunkparser')

def parse_emv_field_55(emv_data, field_definitions):
    parsed_tlvs = {}
    index = 3  # Skip the first 3 digits representing total DE55 length
    total_bm55_value_length = 0

    exact_length_tags = ["9F1E", "9F13"]
    special_tags = ["9F1A", "5F2A", "9C"]
    de055_subfields = field_definitions.get("055", {}).get("subfields", {})

    logger.debug(f"Parsing DE 55 with available subfields: {de055_subfields.keys()}")

    while index < len(emv_data):
        try:
            tag = emv_data[index:index + 2]
            index += 2

            if tag.startswith(("9F", "5F", "DF")):
                tag += emv_data[index:index + 2]
                index += 2

            logger.debug(f"Extracted tag: {tag}")

            if tag not in de055_subfields:
                logger.warning(f"Tag {tag} not defined in DE 55 subfields.")
                continue

            length = int(emv_data[index:index + 2], 16)
            index += 2

            if tag in ["9F1A", "5F2A"]:
                value = emv_data[index:index + 3]
                index += 3
                peek = emv_data[index:index + 2]
                if peek in de055_subfields or peek.startswith(("9F", "5F", "DF")):
                    value = '0' + value
                    logger.debug(f"Prefixed {tag} value: {value}")

            elif tag == "9C":
                value = emv_data[index:index + 1]
                index += 1
                peek = emv_data[index:index + 2]
                if peek in de055_subfields or peek.startswith(("9F", "5F", "DF")):
                    value = '0' + value
                    logger.debug(f"Prefixed 9C value: {value}")

            elif tag in exact_length_tags:
                value = emv_data[index:index + length]
                index += length
                logger.debug(f"Exact-length value for tag {tag}: {value}")
            else:
                value = emv_data[index:index + length * 2]
                index += length * 2
                logger.debug(f"Hex-doubled value for tag {tag}: {value}")

            parsed_tlvs[tag] = value
            total_bm55_value_length += len(value)
            logger.debug(f"Extracted value for tag {tag}: {value}")

        except Exception as e:
            logger.error(f"Failed to parse tag at index {index}: {e}")
            break

    logger.info(f"Total length of DE55 values: {total_bm55_value_length} characters")
    return parsed_tlvs


def parse_de090_fields(value):
    fields = {
        "orig_mti": value[0:3].zfill(4),
        "orig_stan": value[3:9].zfill(6),
        "orig_xmsn_datetime": value[9:18].zfill(10),
        "orig_acq_id": value[18:29].zfill(11),
        "orig_frwd_id": value[29:40].zfill(11)
    }
    return fields


def update_de55(de55_data):
    if '9F1E' in de55_data:
        try:
            original_value = de55_data['9F1E']
            hex_value = ''.join(format(ord(c), '02x') for c in original_value)
            de55_data['9F1E'] = hex_value
            logger.info(f"Converted 9F1E to hex: {hex_value}")
        except Exception as e:
            logger.warning(f"Failed to convert 9F1E to hex: {e}")
    else:
        logger.debug("Tag 9F1E not present in DE55.")
