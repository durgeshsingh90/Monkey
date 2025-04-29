import os
import json
import re
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Setup logger
logger = logging.getLogger('splunkparser')

# Paths
SCHEMA_PATH = os.path.join(settings.BASE_DIR, 'media', 'schemas', 'omnipay.json')
OUTPUT_PATH = os.path.join(settings.BASE_DIR, 'media', 'splunkparser', 'output.json')
VALIDATION_RESULT_PATH = os.path.join(settings.BASE_DIR, 'media', 'splunkparser', 'validation_result.json')

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_valid_format(value, fmt):
    value = str(value).replace(' ', '')
    if fmt == 'N':
        return value.isdigit()
    elif fmt == 'A':
        return bool(re.fullmatch(r'[A-Z]+', value))
    elif fmt == 'AN':
        return bool(re.fullmatch(r'[A-Za-z0-9]+', value))
    elif fmt == 'ANS':
        return bool(re.fullmatch(r'[A-Za-z0-9\s\-\.,!@#\$%\^&\*\(\)_\+=\[\]{};:\"\\|<>\/?~]+', value))
    elif fmt == 'S':
        return bool(re.fullmatch(r'[^\w\s]', value))
    elif fmt == 'B':
        return bool(re.fullmatch(r'[0-9A-Fa-f]*', value))
    elif fmt == 'Z':
        return bool(re.fullmatch(r'[0-9=^]*', value))
    elif fmt == 'H':
        return bool(re.fullmatch(r'[0-9A-Fa-f]*', value))
    else:
        return True

def validate_field(field_name, field_value, field_schema):
    success = []
    wrong_length = []
    wrong_format = []

    # Subfields (like DE055, DE060, etc)
    if isinstance(field_value, dict) and 'subfields' in field_schema:
        subfields_schema = field_schema.get('subfields', {})
        for subfield, subvalue in field_value.items():
            if subfield == "__errors__":
                continue
            sub_schema = subfields_schema.get(subfield)
            if sub_schema:
                s, wl, wf = validate_field(f"{field_name}.{subfield}", subvalue, sub_schema)
                success.extend(s)
                wrong_length.extend(wl)
                wrong_format.extend(wf)
            else:
                wrong_format.append(f"{field_name}.{subfield}: Unknown subfield")
        return success, wrong_length, wrong_format

    fmt = field_schema.get('format')
    value_str = str(field_value)
    
    # Only strip spaces for numeric, binary, hex fields
    if fmt in ['N', 'B', 'H']:
        value_str = value_str.replace(' ', '')
    

    # ✅ Ignore masked values (e.g., ****)
    if value_str and set(value_str) == {'*'}:
        success.append(field_name)
        return success, wrong_length, wrong_format

    fmt = field_schema.get('format')
    variable = field_schema.get('variable', False)

    if variable:
        max_length = field_schema.get('max_length')
        if max_length and len(value_str) > max_length:
            wrong_length.append(f"{field_name}: Length {len(value_str)} exceeds max_length {max_length}")
        else:
            logger.info(f"{field_name} length is valid (variable)")
    else:
        fixed_length = field_schema.get('length')
        if fixed_length and len(value_str) != fixed_length:
            wrong_length.append(f"{field_name}: Length {len(value_str)} (expected {fixed_length})")
        else:
            logger.info(f"{field_name} length is valid (fixed)")

    # Validate format
    if fmt and not is_valid_format(value_str, fmt):
        wrong_format.append(f"{field_name}: Format mismatch (expected {fmt})")
    else:
        success.append(field_name)

    return success, wrong_length, wrong_format

def validate_transaction(schema, transaction):
    success = []
    wrong_length = []
    wrong_format = []

    fields_schema = schema.get('fields', {})
    data_elements = transaction.get('data_elements', {})

    for field, value in data_elements.items():
        field_schema = fields_schema.get(field)
        if field_schema:
            logger.info(f"Validating {field}")
            s, wl, wf = validate_field(field, value, field_schema)
            success.extend(s)
            wrong_length.extend(wl)
            wrong_format.extend(wf)
        else:
            logger.warning(f"No schema found for {field}")

    return {
        "successful": success,
        "wrong_length": wrong_length,
        "wrong_format": wrong_format
    }

def save_validation_result(validation_result):
    os.makedirs(os.path.dirname(VALIDATION_RESULT_PATH), exist_ok=True)
    with open(VALIDATION_RESULT_PATH, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, indent=2)
    logger.info(f"Validation result written to {VALIDATION_RESULT_PATH}")

@csrf_exempt
def validate_output(request):
    try:
        schema = load_json(SCHEMA_PATH)
        transaction = load_json(OUTPUT_PATH)

        result = validate_transaction(schema, transaction)
        save_validation_result(result)

        return JsonResponse({"status": "success", "validation": result})
    except Exception as e:
        logger.error("Validation failed.", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
