# splunkparser/views/parser_core.py
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import re
import logging

from .utils import extract_timestamp, extract_route, extract_message_id, FIELD_DEFINITIONS  # ✅ Import FIELD_DEFINITIONS directly
from .parser_helper import parse_emv_field_55, update_de55, parse_de090_fields

# Logger
logger = logging.getLogger('splunkparser')

# ✅ No need to call load_field_definitions()

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

            logger.info("Log data parsed successfully.")
            logger.debug(f"Parsed output: {parsed_output}")

            return JsonResponse({
                'status': 'success',
                'timestamp': extract_timestamp(log_data),
                'route': extract_route(log_data),
                'message_id': extract_message_id(log_data),
                'result': parsed_output
            })

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
        except Exception as e:
            logger.critical(f"Unexpected error during log parsing: {e}")
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

    # Detect if log uses only one of "in[" or "out["
    has_in = any("in[" in line for line in lines)
    has_out = any("out[" in line for line in lines)

    if has_in and has_out:
        logger.error("❌ Mixed input: both 'in[' and 'out[' detected.")
        raise ValueError("Log input cannot contain both 'in[' and 'out[' lines. Use only one direction.")

    prefix = "in[" if has_in else "out[" if has_out else None

    if not prefix:
        logger.error("❌ No valid 'in[' or 'out[' prefix detected in input.")
        raise ValueError("Log input must contain either 'in[' or 'out[' lines.")

    escaped_prefix = prefix.replace('[', r'\[').replace(']', r'\]')  # Escape for regex

    data_elements = {}  # Dictionary to store Data Elements

    # Define which DE fields should be converted to integers
    integer_fields = ['004', '049']  # Add more fields if needed
    # Define which DE fields need to be zero-padded and their respective lengths
    pad_zero_fields = {
        '013': 4,
        '019': 3,
        '022': 3,
        '023': 3,
        '025': 2
    }

    # Define the flags for DE053
    first_bm53_skipped = False

    # Search for MTI anywhere in the input
    for line in lines:
        logger.debug(f"Processing line: '{line.strip()}'")
        if not mti:
            mti_match = re.match(r"msgno\[\s*0\]<(.+)>", line.strip())
            if mti_match:
                mti = mti_match.group(1)
                logger.info(f"MTI extracted: {mti}")
                continue

    # Extract Data Elements
    for line in lines:
        line = line.strip()
        if not line:
            logger.debug("Skipping empty line.")
            continue

        # ✅ Skip DE129 explicitly regardless of direction or format
        if re.search(r'\[\s*129\s*:\s*\]|DE0129', line):
            logger.info(f"Omitting DE129: {line.strip()}")
            continue

        match = re.match(rf"{escaped_prefix}\s*(\d+):?\s*\]<(.+)>", line)
        if match:
            field_number = match.group(1).zfill(3)
            value = match.group(2)

            logger.debug(f"Field {field_number} detected with value: {value}")

            # Retrieve field definition
            field_def = FIELD_DEFINITIONS.get(field_number)
            if field_def:
                field_length = field_def.get('length')

                # Adjust the length if needed
                if field_number == '003':
                    # DE003 must always be 6-digit string
                    if value.strip() == '':
                        value = "000000"
                    else:
                        value = value.zfill(6)
                    logger.debug(f"Adjusted DE003 to 6 digits: {value}")

                # Enable below line for DE004 to get output like     "DE004": "000000001000"
                # elif field_number == '004':
                #     if value.strip() and value.strip('0'):  # Ensure non-empty and not just zeros
                #         value = int(value.lstrip('0'))
                
                # Enable below line for DE004 to get output like     "DE004": 1000,
                elif field_number == '004':
                    # DE004 must always be integer
                    if value.strip('0') == '':
                        value = 0
                    else:
                        value = int(value.lstrip('0'))
                    logger.debug(f"Converted DE004 to integer: {value}")

            # Special handling for DE060, 061, and 062
            if field_number in ['060', '061', '062','065', '066']:
                value = parse_bm6x(value)
                logger.info(f"Parsed DE {field_number}: {value}")

            # Handling for DE 55 across multiple lines
            if field_number == '055':
                de055_parts.append(value)
                logger.debug(f"Accumulating DE 55 parts: {de055_parts}")
                continue

            # Handling for DE007
            if field_number == '007':
                de007_parts.append(value)
                logger.debug(f"Accumulating DE 007 parts: {de007_parts}")
                continue

            # Handling for DE090
            if field_number == '090':
                de090_parts.append(value)
                logger.debug(f"Accumulating DE 090 parts: {de090_parts}")
                continue

            # Handling for DE 43
            if field_number == '043':
                bm43_parts.append(value)  # Append value without stripping spaces
                logger.debug(f"Accumulating DE 43 parts: {bm43_parts}")
                continue

            # Handling for DE 53: Ignore the first line and combine the rest
            if field_number == '053':
                if not first_bm53_skipped:
                    first_bm53_skipped = True
                    logger.debug(f"Skipping first DE 53 part: {value}")
                else:
                    de053_parts.append(value.strip())  # You can decide whether to strip or not
                    logger.debug(f"Accumulating DE 53 parts: {de053_parts}")
                continue

            # Convert to integer if the field is in the integer_fields list, and it's not empty
            if field_number in integer_fields and field_number != '004':  # Skip DE004 here, as it's handled above
                if value.strip():  # Ensure value is not empty
                    value = int(value.lstrip('0'))
                    logger.debug(f"Converted field {field_number} to integer: {value}")

            # Pad with zeros if the field is in the pad_zero_fields list
            if field_number in pad_zero_fields:
                value = value.zfill(pad_zero_fields[field_number])
                logger.debug(f"Padded field {field_number} with zeros: {value}")

            data_elements[f"DE{field_number}"] = value

    # Combine and pad DE007
    if de007_parts:
        combined_de007 = ''.join(de007_parts)
        data_elements["DE007"] = combined_de007.zfill(10)
        logger.info(f"Combined DE007: {data_elements['DE007']}")

    # Combine and pad DE090
    if de090_parts:
        combined_de090 = ''.join(de090_parts)
        logger.debug(f"Combined DE090: {combined_de090}")
        parsed_de090 = parse_de090_fields(combined_de090)  # Call parse function for DE090
        data_elements["DE090"] = parsed_de090
        logger.info(f"Parsed DE090: {data_elements['DE090']}")

    # Combine parts of DE043 without stripping spaces
    if bm43_parts:
        data_elements["DE043"] = ''.join(bm43_parts)  # Combine without stripping spaces
        logger.info(f"Combined DE043: {data_elements['DE043']}")

    # Combine parts of DE053
    if de053_parts:
        data_elements["DE053"] = ''.join(de053_parts)  # Retain spaces if needed
        logger.info(f"Combined DE053: {data_elements['DE053']}")

    # Combine parts of DE055 and parse as TLV
    if de055_parts:
        combined_de055 = ''.join(de055_parts)
        logger.debug(f"Combined DE055: {combined_de055}")
        parsed_de055 = parse_emv_field_55(combined_de055)  # Parse the combined DE55
        # Update the DE55 data if necessary
        update_de55(parsed_de055)
        data_elements["DE055"] = parsed_de055
        logger.info(f"Parsed DE055: {data_elements['DE055']}")

    # Sort data_elements by keys in ascending order
    sorted_data_elements = dict(sorted(data_elements.items()))

    logger.info("Final data elements constructed successfully.")
    logger.debug(f"Final sorted data elements: {sorted_data_elements}")

    # Convert MTI to integer if it is numeric
    try:
        mti = int(mti)
    except ValueError:
        logger.debug(f"MTI is not numeric: {mti}")

    # Construct the final message
    if mti:
        message["mti"] = mti

    message["data_elements"] = sorted_data_elements

    logger.info("Final message constructed successfully with data elements.")
    logger.debug(f"Final message: {message}")

    return message

def parse_bm6x(value):
    subfields = []
    values = []
    errors = []
    i = 0
    offset = 0  # for better error logging

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
                raise ValueError(f"Invalid subfield length {subfield_length} for subfield {subfield} at offset {i}")

            if data_end > len(value):
                raise ValueError(f"Incomplete data for subfield {subfield} at offset {i}. Needed till {data_end}, only {len(value)} available.")

            value_str = value[data_start:data_end]
            logger.debug(f"Parsed subfield {subfield} ({subfield_length}): {value_str}")

            subfields.append(subfield)
            values.append(value_str)

            i += 5 + subfield_length - 2
        except Exception as e:
            error_msg = f"Subfield at offset {i} failed: {e}"
            logger.warning(error_msg)
            errors.append(error_msg)
            break  # Or optionally: i += 1 and continue to keep parsing

    parsed_fields = {subfields[idx]: values[idx] for idx in range(len(subfields))}
    if errors:
        parsed_fields['__errors__'] = errors

    logger.debug(f"DE6x parsed fields: {parsed_fields}")
    return parsed_fields
