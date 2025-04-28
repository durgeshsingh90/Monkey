# splunkparser/views/utils.py

import logging
import json
import os
import re
import random

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
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

# Load FIELD_DEFINITIONS only ONCE globally
try:
    with open(field_definitions_path, 'r') as f:
        raw_definitions = json.load(f)
    FIELD_DEFINITIONS = raw_definitions.get("fields", raw_definitions)
    if "DE055" in FIELD_DEFINITIONS and "055" not in FIELD_DEFINITIONS:
        FIELD_DEFINITIONS["055"] = FIELD_DEFINITIONS["DE055"]
    logger.info(f"Loaded and normalized field definitions from: {field_definitions_path}")
except Exception as e:
    FIELD_DEFINITIONS = {}
    logger.error(f"Failed to load field definitions: {e}")

def extract_timestamp(log_data):
    match = re.search(r'\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', log_data)
    return match.group(0) if match else None

def extract_route(log_data):
    match = re.search(r'\[\s*([A-Za-z]+:\d+)\s*\]', log_data)
    return match.group(1).strip() if match else None

def extract_message_id(log_data):
    match = re.search(r'MESSAGE ID\[(.*?)\]', log_data)
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
            FIELD_DEFINITIONS = raw_definitions.get("fields", raw_definitions)

            # Normalize DE055 if needed
            if "DE055" in FIELD_DEFINITIONS and "055" not in FIELD_DEFINITIONS:
                FIELD_DEFINITIONS["055"] = FIELD_DEFINITIONS["DE055"]

            logger.info("FIELD_DEFINITIONS loaded successfully.")

        except Exception as e:
            logger.error(f"Failed to load field definitions: {e}")
            FIELD_DEFINITIONS = {}

    return FIELD_DEFINITIONS
