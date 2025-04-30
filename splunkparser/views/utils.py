import os
import json
import logging
import re
from django.conf import settings

# Configure logger
logger = logging.getLogger('splunkparser')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File paths
settings_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'settings.json')
output_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'output.json')
field_definitions_path = os.path.join(settings.MEDIA_ROOT, 'schemas', 'omnipay.json')

# Lazy-loaded FIELD_DEFINITIONS
FIELD_DEFINITIONS = None

def get_field_definitions():
    """
    Loads and returns the field definitions from omnipay.json.
    Caches the result in FIELD_DEFINITIONS after the first call.
    """
    global FIELD_DEFINITIONS
    if FIELD_DEFINITIONS is None:
        try:
            logger.info(f"Loading FIELD_DEFINITIONS from {field_definitions_path}")
            with open(field_definitions_path, 'r', encoding='utf-8') as f:
                raw_definitions = json.load(f)
            FIELD_DEFINITIONS = raw_definitions.get("fields", raw_definitions)

            if "DE055" in FIELD_DEFINITIONS and "055" not in FIELD_DEFINITIONS:
                FIELD_DEFINITIONS["055"] = FIELD_DEFINITIONS["DE055"]

            logger.info("FIELD_DEFINITIONS loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load field definitions: {e}", exc_info=True)
            FIELD_DEFINITIONS = {}

    return FIELD_DEFINITIONS

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {filepath}: {e}", exc_info=True)
        return None

def extract_timestamp(log_data):
    match = re.search(r'\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', log_data)
    return match.group(0) if match else None

def extract_route(log_data):
    match = re.search(r'\[\s*([A-Za-z]+:\d+)\s*\]', log_data)
    return match.group(1).strip() if match else None

def extract_message_id(log_data):
    match = re.search(r'MESSAGE ID\[(.*?)\]', log_data)
<<<<<<< HEAD
    return match.group(1).strip() if match else None
=======
    return match.group(1).strip() if match else None


import os
import json
import logging
from django.conf import settings

logger = logging.getLogger('splunkparser')

# Initialize FIELD_DEFINITIONS as None
FIELD_DEFINITIONS = None

def get_field_definitions():
    global FIELD_DEFINITIONS
    if FIELD_DEFINITIONS is None:
        try:
            field_def_path = os.path.join(settings.MEDIA_ROOT, 'schemas', 'omnipay.json')
            logger.info(f"Loading FIELD_DEFINITIONS from {field_def_path}")
            with open(field_def_path, 'r') as f:
                raw_definitions = json.load(f)
            raw_fields = raw_definitions.get("fields", raw_definitions)

            # Normalize field keys (strip "DE" if present)
            FIELD_DEFINITIONS = {}
            for key, value in raw_fields.items():
                normalized_key = key.replace("DE", "") if key.startswith("DE") else key
                FIELD_DEFINITIONS[normalized_key] = value

            # Optional: alias DE055 if needed
            if "055" not in FIELD_DEFINITIONS and "DE055" in raw_fields:
                FIELD_DEFINITIONS["055"] = raw_fields["DE055"]

            logger.info("FIELD_DEFINITIONS loaded and normalized successfully.")

        except Exception as e:
            logger.error(f"Failed to load field definitions: {e}")
            FIELD_DEFINITIONS = {}

    return FIELD_DEFINITIONS
>>>>>>> fix-splunk-parser
