import json
import re
import logging
import os

# -------------------- SETUP LOGGING --------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
log_file_path = os.path.join(current_dir, "validation.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# --------------------------------------------------------

def load_schema(schema_path):
    logger.info(f"Loading schema from {schema_path}")
    with open(schema_path, 'r') as f:
        return json.load(f)

def load_log(log_path):
    logger.info(f"Loading transaction log from {log_path}")
    with open(log_path, 'r') as f:
        return json.load(f)

# Format validators
def is_valid_format(value, fmt, formats_info):
    value_str = str(value)
    fmt = fmt.upper()

    if fmt == "N":
        return value_str.isdigit()
    elif fmt == "A":
        return bool(re.fullmatch(r"[A-Z]+", value_str))
    elif fmt == "AN":
        return bool(re.fullmatch(r"[A-Za-z0-9]+", value_str))
    elif fmt == "ANS":
        return bool(re.fullmatch(r"[A-Za-z0-9\s\-\.,'!@#\$%\^&\*\(\)_\+=\[\]{};:\"\\|<>\/\?~]+", value_str))
    elif fmt == "S":
        return bool(re.fullmatch(r"[^\w\s]", value_str))  # Special chars
    elif fmt == "B":
        return bool(re.fullmatch(r"[0-9A-Fa-f]*", value_str))
    elif fmt == "Z":
        return bool(re.fullmatch(r"[0-9=^]*", value_str))
    elif fmt == "H":
        return bool(re.fullmatch(r"[0-9A-Fa-f]*", value_str))
    elif fmt in ["LLVAR", "LLLVAR"]:
        return True  # LLVAR/LLLVAR length is checked separately
    else:
        logger.warning(f"Unknown format '{fmt}', skipping format validation.")
        return True

# Validate LLVAR and LLLVAR fields
def validate_var_length_field(value, fmt):
    value_str = str(value)
    if fmt == "LLVAR":
        if len(value_str) < 2:
            return False, "Too short to contain LLVAR length"
        try:
            expected_len = int(value_str[:2])
            actual_data = value_str[2:]
            if len(actual_data) != expected_len:
                return False, f"LLVAR mismatch: header says {expected_len}, data has {len(actual_data)}"
        except ValueError:
            return False, "Invalid LLVAR length field"
    elif fmt == "LLLVAR":
        if len(value_str) < 3:
            return False, "Too short to contain LLLVAR length"
        try:
            expected_len = int(value_str[:3])
            actual_data = value_str[3:]
            if len(actual_data) != expected_len:
                return False, f"LLLVAR mismatch: header says {expected_len}, data has {len(actual_data)}"
        except ValueError:
            return False, "Invalid LLLVAR length field"
    return True, ""

# Field validator
def validate_field(field_name, field_value, field_schema, formats_info):
    errors = []

    if isinstance(field_value, dict) and "subfields" in field_schema:
        subfields_schema = field_schema.get("subfields", {})
        for subfield, subvalue in field_value.items():
            if subfield == "__errors__":
                continue
            sub_schema = subfields_schema.get(subfield)
            if sub_schema:
                errors.extend(validate_field(f"{field_name}.{subfield}", subvalue, sub_schema, formats_info))
            else:
                errors.append(f"{field_name}.{subfield}: Unknown subfield")
        return errors

    value_str = str(field_value).replace(" ", "")
    fmt = field_schema.get("format")

    # Length validations
    if "length" in field_schema and field_schema["length"] is not None:
        expected_len = field_schema["length"]
        if len(value_str) != expected_len:
            errors.append(f"{field_name}: Invalid length {len(value_str)} (expected {expected_len})")
    if "max_length" in field_schema:
        if len(value_str) > field_schema["max_length"]:
            errors.append(f"{field_name}: Length {len(value_str)} exceeds max_length {field_schema['max_length']}")

    # Variable length validations
    if fmt in ("LLVAR", "LLLVAR"):
        valid, message = validate_var_length_field(value_str, fmt)
        if not valid:
            errors.append(f"{field_name}: {message}")

    # Format validations
    if fmt and fmt not in ("LLVAR", "LLLVAR"):
        if not is_valid_format(field_value, fmt, formats_info):
            errors.append(f"{field_name}: Invalid format for expected {fmt}")

    return errors

# Transaction validator
def validate_transaction(schema, transaction):
    errors = []
    fields_schema = schema.get("fields", {})
    formats_info = schema.get("attributes", {}).get("formats", {})

    data_elements = transaction.get("data_elements", {})
    for field, value in data_elements.items():
        field_schema = fields_schema.get(field)
        if field_schema:
            logger.info(f"Validating {field}")
            field_errors = validate_field(field, value, field_schema, formats_info)
            if field_errors:
                for e in field_errors:
                    logger.error(e)
            errors.extend(field_errors)
        else:
            logger.warning(f"No schema found for {field}, skipping validation.")

    return errors

# Generate summary JSON
def generate_validation_summary(errors_list):
    result = {}
    for error in errors_list:
        try:
            field_name = error.split(":")[0]
            result[field_name] = error.split(":")[1].strip()
        except Exception:
            result["Unknown"] = error
    return result

# Save summary JSON
def save_json_summary(summary_dict, output_filename="validation_result.json"):
    output_path = os.path.join(current_dir, output_filename)
    with open(output_path, "w") as f:
        json.dump(summary_dict, f, indent=2)
    logger.info(f"Validation summary saved to {output_filename}")

# Main block
if __name__ == "__main__":
    schema_path = os.path.join(current_dir, "..\media\schemas\omnipay.json")
    log_path = os.path.join(current_dir, "..\media\splunkparser\output.json")  # <-- Replace this with actual path!

    try:
        schema = load_schema(schema_path)
        transaction = load_log(log_path)

        validation_errors = validate_transaction(schema, transaction)

        if validation_errors:
            logger.error("Validation Errors Found:")
            for error in validation_errors:
                logger.error(error)

            validation_summary = generate_validation_summary(validation_errors)
            save_json_summary(validation_summary)
        else:
            logger.info("All fields are valid!")

            fields_present = transaction.get("data_elements", {}).keys()
            validation_summary = {field: "OK" for field in fields_present}
            save_json_summary(validation_summary)

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
