from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re
import logging
import os
from .utils import FIELD_DEFINITIONS

logger = logging.getLogger('splunkparser')

def parse_emv_field_55(emv_data):
    parsed_tlvs = {}
    index = 3  # Skip the first 3 digits which represent the total length of DE 55
    total_bm55_value_length = 0  # Variable to accumulate the total length of DE55 values

    # Tags that have their value length as exact, not doubled
    exact_length_tags = ["9F1E", "9F13"]  # Add more tags if needed
    # Tags that follow the special logic
    special_tags = ["9F1A", "5F2A", "9C"]  # Add 9C to the list
    de055_subfields = FIELD_DEFINITIONS.get("DE055", {}).get("subfields", {})
    logger.debug(f"Parsing DE 55 data with available subfields: {de055_subfields.keys()}")

    while index < len(emv_data):
        # Determine if the tag is 2 or 4 characters long
        tag = emv_data[index:index + 2]
        index += 2

        # If the first part of the tag is "9F", "5F", or "DF", the tag is 4 characters long
        if tag.startswith(("9F", "5F", "DF")):
            tag += emv_data[index:index + 2]
            index += 2

        # Log the tag extraction
        logger.debug(f"Extracted tag: {tag}")

        # Check if the tag is defined in the subfields
        if tag not in de055_subfields:
            logger.warning(f"Tag {tag} not defined in DE 55 subfields.")
            continue

        # The next two characters represent the length of the value in bytes
        length = int(emv_data[index:index + 2], 16)
        index += 2

        # Log the length
        logger.debug(f"Length of value for tag {tag}: {length}")

        # Special handling for 9F1A, 5F2A, and 9C
        if tag == "9F1A" or tag == "5F2A":
            value = emv_data[index:index + 3]  # Pick only 3 characters for these tags
            index += 3

            # Peek at the next two characters to check if it's a valid tag
            next_two_chars = emv_data[index:index + 2]
            logger.debug(f"Next two characters after {tag}: {next_two_chars}")

            # Check if the next two characters form a valid tag
            if next_two_chars in de055_subfields or next_two_chars.startswith(("9F", "5F", "DF")):
                # If valid, prefix the value with '0'
                value = '0' + value
                logger.debug(f"Prefixed {tag} value: {value}")
        
        elif tag == "9C":
            value = emv_data[index:index + 1]  # Pick only 1 character for 9C
            index += 1

            # Peek at the next two characters to check if it's a valid tag
            next_two_chars = emv_data[index:index + 2]
            logger.debug(f"Next two characters after 9C: {next_two_chars}")

            # Check if the next two characters form a valid tag
            if next_two_chars in de055_subfields or next_two_chars.startswith(("9F", "5F", "DF")):
                # If valid, prefix the value with '0'
                value = '0' + value
                logger.debug(f"Prefixed 9C value: {value}")

        elif tag in exact_length_tags:
            # For exact-length tags, pick exactly the specified number of hex characters
            value = emv_data[index:index + length]
            index += length
            logger.debug(f"Exact-length value for tag {tag}: {value}")
        else:
            # For other tags, pick twice the length (since the value is in hex)
            value = emv_data[index:index + length * 2]
            index += length * 2
            logger.debug(f"Hex-doubled value for tag {tag}: {value}")

        # Store the tag and value in the parsed TLVs dictionary
        parsed_tlvs[tag] = value

        # Accumulate the length of DE55 values
        total_bm55_value_length += len(value)

        logger.debug(f"Extracted value for tag {tag}: {value}")

    # Log the total length of DE55 values
    logger.info(f"Total length of DE55 values: {total_bm55_value_length} characters")

    logger.info("Completed parsing DE 55.")
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
        original_value = de55_data['9F1E']
        hex_value = ''.join(format(ord(c), '02x') for c in original_value)
        de55_data['9F1E'] = hex_value
        logger.info(f"Converted 9F1E value to hexadecimal: {hex_value}")
    else:
        logger.debug("Tag 9F1E not present in DE55 data.")
