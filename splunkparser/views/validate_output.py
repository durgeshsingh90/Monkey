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

    # Handle subfields recursively
    if isinstance(field_value, dict) and 'subfields' in field_schema:
        subfields_schema = field_schema.get('subfields', {})
        for subfield_key, subfield_value in field_value.items():
            if subfield_key == "__errors__":
                continue
            sub_schema = subfields_schema.get(subfield_key)
            full_subfield_name = f"{field_name}.{subfield_key}"
            if sub_schema:
                s, wl, wf = validate_field(full_subfield_name, subfield_value, sub_schema)
                success.extend(s)
                wrong_length.extend(wl)
                wrong_format.extend(wf)
            else:
                wrong_format.append(f"{full_subfield_name}: Unknown subfield")
        return success, wrong_length, wrong_format

    # For standard fields
    raw_value_str = str(field_value)
    value_str_nospaces = raw_value_str.replace(' ', '')
    fmt = field_schema.get('format')
    variable = field_schema.get('variable_length', False)

    # ✅ Skip DE004 length validation since it's intentionally converted to int
    if field_name == "DE004":
        if fmt and not is_valid_format(value_str_nospaces, fmt):
            wrong_format.append(f"{field_name}: Format mismatch (expected {fmt})")
        else:
            success.append(field_name)
        return success, wrong_length, wrong_format
    
    # Ignore masked values
    if value_str_nospaces and re.fullmatch(r'[0-9]*\*+[0-9]*', value_str_nospaces):
        logger.info(f"{field_name} appears masked and will be excluded from validation.")
        success.append(field_name)
        return success, wrong_length, wrong_format


    # Length validation (spaces included)
    # Length validation (spaces included)
    if variable:
        max_length = field_schema.get('max_length')
        if max_length and len(raw_value_str) > max_length:
            wrong_length.append(f"{field_name}: Length {len(raw_value_str)} exceeds max_length {max_length}")
        else:
            success.append(field_name)  

    else:
        fixed_length = field_schema.get('length')
        if fixed_length and len(raw_value_str) != fixed_length:
            wrong_length.append(f"{field_name}: Length {len(raw_value_str)} (expected {fixed_length})")
        else:
            success.append(field_name)

    # Format validation (spaces excluded)
    if fmt and not is_valid_format(value_str_nospaces, fmt):
        wrong_format.append(f"{field_name}: Format mismatch (expected {fmt})")

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

        total_wrong_length = len(result.get('wrong_length', []))
        total_wrong_format = len(result.get('wrong_format', []))
        total_errors = total_wrong_length + total_wrong_format

        if total_wrong_length == 0 and total_wrong_format == 0:
            message = "✅ All fields and subfields passed validation!"
        else:
            message = (
                f"⚠️ Validation completed with {total_wrong_length + total_wrong_format} issues "
                f"(Wrong Length: {total_wrong_length}, Wrong Format: {total_wrong_format})"
            )


        return JsonResponse({
            "status": "success",
            "message": message,
            "validation": result
        })

    except Exception as e:
        logger.error("Validation failed.", exc_info=True)
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)
