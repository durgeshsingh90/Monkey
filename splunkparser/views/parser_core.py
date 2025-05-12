from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re
import logging

from .utils import extract_timestamp, extract_route, extract_message_id, get_field_definitions
from .utils import settings_file_path, output_file_path, field_definitions_path
from .parser_helper import parse_emv_field_55, update_de55, parse_de090_fields
from splunkparser.views.validate_output import validate_transaction, load_json

logger = logging.getLogger('splunkparser')


@csrf_exempt
def parse_logs(request):
    if request.method == 'POST':
        try:
            content_type = request.content_type
            if content_type == 'application/json':
                data = json.loads(request.body)
                log_data = data.get('log_data', '')
            elif content_type.startswith('multipart/form-data'):
                file = request.FILES.get('file')
                if file:
                    log_data = file.read().decode('utf-8')
                else:
                    return JsonResponse({'status': 'error', 'message': 'File not provided'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': 'Unsupported content type'}, status=415)

            logger.info("Received request for log parsing.")
            logger.debug(f"Raw log data received: {log_data}")

            parsed_output = parse_iso8583(log_data)

            # Load schema and validate
            schema = load_json(field_definitions_path)
            validation_result = validate_transaction(schema, parsed_output)

            logger.info("Log data parsed and validated successfully.")
            logger.debug(f"Parsed output: {parsed_output}")
            logger.debug(f"Validation result: {validation_result}")

            return JsonResponse({
                'status': 'success',
                'timestamp': extract_timestamp(log_data),
                'route': extract_route(log_data),
                'message_id': extract_message_id(log_data),
                'result': parsed_output,
                'validation': validation_result
            })

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            logger.critical(f"Unexpected error during log parsing: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


def parse_iso8583(log_data):
    message = {}
    de007_parts = []
    bm43_parts = []
    de053_parts = []
    de055_parts = []
    de090_parts = []
    mti = ""

    lines = log_data.split("\n")
    logger.debug(f"Number of lines received for parsing: {len(lines)}")

    has_in = any("in[" in line for line in lines)
    has_out = any("out[" in line for line in lines)

    if has_in and has_out:
        logger.error("❌ Mixed input: both 'in[' and 'out[' detected.")
        raise ValueError("Log input cannot contain both 'in[' and 'out[' lines. Use only one direction.")

    prefix = "in[" if has_in else "out[" if has_out else None
    if not prefix:
        logger.error("❌ No valid 'in[' or 'out[' prefix detected.")
        raise ValueError("Log input must contain either 'in[' or 'out[' lines.")

    escaped_prefix = prefix.replace('[', r'\[').replace(']', r'\]')

    data_elements = {}
    integer_fields = ['004', '049']
    pad_zero_fields = {
        '003': 6,
        '012': 6,
        '018': 4,
        '013': 4,
        '019': 3,
        '022': 3,
        '023': 3,
        '025': 2
    }
    first_bm53_skipped = False

    for line in lines:
        line = line.strip()
        if not mti:
            mti_match = re.match(r"msgno\[\s*0\]<(.+)>", line)
            if mti_match:
                mti = mti_match.group(1)
                logger.info(f"MTI extracted: {mti}")
                continue

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if re.search(r'\[\s*129\s*:\s*\]|DE0129', line):
            logger.info(f"Omitting DE129: {line}")
            continue

        match = re.match(rf"{escaped_prefix}\s*(\d+):?\s*\]<(.+)>", line)
        if match:
            field_number = match.group(1).zfill(3)
            value = match.group(2)
            logger.debug(f"Field {field_number} detected with value: {value}")

            if field_number == '004':
                value = 0 if value.strip('0') == '' else int(value.lstrip('0'))
                logger.debug(f"Converted DE004 to integer: {value}")

            if field_number in ['060', '061', '062', '065', '066']:
                value = parse_bm6x(value)
                logger.info(f"Parsed DE {field_number} (BM6x format): {value}")

            if field_number == '055':
                de055_parts.append(value)
                logger.debug(f"Accumulating DE055 parts: {de055_parts}")
                continue
            if field_number == '007':
                de007_parts.append(value)
                continue
            if field_number == '090':
                de090_parts.append(value)
                continue
            if field_number == '043':
                bm43_parts.append(value)
                continue
            if field_number == '053':
                if not first_bm53_skipped:
                    first_bm53_skipped = True
                else:
                    de053_parts.append(value.strip())
                continue

            if field_number in integer_fields and field_number != '004':
                if value.strip():
                    value = int(value.lstrip('0'))
            if field_number in pad_zero_fields:
                value = str(value).zfill(pad_zero_fields[field_number])

            data_elements[f"DE{field_number}"] = value

    if de007_parts:
        combined_de007 = ''.join(de007_parts)
        data_elements["DE007"] = combined_de007.zfill(10)
        logger.info(f"Combined DE007: {data_elements['DE007']}")

    if de090_parts:
        combined_de090 = ''.join(de090_parts)
        parsed_de090 = parse_de090_fields(combined_de090)
        data_elements["DE090"] = parsed_de090
        logger.info(f"Parsed DE090: {data_elements['DE090']}")

    if bm43_parts:
        data_elements["DE043"] = ''.join(bm43_parts)
        logger.info(f"Combined DE043: {data_elements['DE043']}")

    if de053_parts:
        data_elements["DE053"] = ''.join(de053_parts)
        logger.info(f"Combined DE053: {data_elements['DE053']}")

    if de055_parts:
        combined_de055 = ''.join(de055_parts)
        FIELD_DEFINITIONS = get_field_definitions()
        if not FIELD_DEFINITIONS.get("055"):
            logger.warning("[WARN] FIELD_DEFINITIONS missing for DE055. Will still parse raw.")
        parsed_de055 = parse_emv_field_55(combined_de055, FIELD_DEFINITIONS)
        update_de55(parsed_de055)
        data_elements["DE055"] = parsed_de055
        logger.info(f"Parsed DE055: {data_elements['DE055']}")

    sorted_data_elements = dict(sorted(data_elements.items()))
    logger.info("Final data elements constructed successfully.")

    try:
        mti = int(mti)
    except ValueError:
        logger.debug(f"MTI is not numeric: {mti}")

    if mti:
        message["mti"] = mti
    message["data_elements"] = sorted_data_elements

    logger.info("Final ISO8583 message ready.")
    return message


def parse_bm6x(value):
    subfields = []
    values = []
    errors = []
    i = 0

    while i < len(value):
        try:
            if i + 5 > len(value):
                raise ValueError(f"Incomplete header at offset {i}: '{value[i:]}'")

            subfield_length_str = value[i:i + 3]
            if not subfield_length_str.isdigit():
                raise ValueError(f"Non-numeric subfield length '{subfield_length_str}' at offset {i}")

            subfield_length = int(subfield_length_str)
            subfield = value[i + 3:i + 5]
            data_start = i + 5
            data_end = data_start + subfield_length - 2

            if subfield_length < 2:
                raise ValueError(f"Invalid subfield length {subfield_length} for subfield {subfield}")

            if data_end > len(value):
                raise ValueError(f"Incomplete data for subfield {subfield} at offset {i}")

            value_str = value[data_start:data_end]
            subfields.append(subfield)
            values.append(value_str)
            i += 5 + subfield_length - 2
        except Exception as e:
            error_msg = f"Subfield at offset {i} failed: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)
            break

    parsed_fields = {subfields[idx]: values[idx] for idx in range(len(subfields))}
    if errors:
        parsed_fields['__errors__'] = errors

    logger.debug(f"DE6x parsed fields: {parsed_fields}")
    return parsed_fields
