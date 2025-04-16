import json

# Function to recursively collect all values from a nested dictionary
def collect_values(data):
    values = []
    for key, value in data.items():
        if isinstance(value, dict):
            if key == "DE060":
                # Handle DE060 specifically by adding total length before subfield processing
                subfield_values = []
                total_de060_length = 0
                for subfield_key, subfield_value in value.items():
                    subfield_value_str = str(subfield_value)
                    subfield_length = len(subfield_key) + len(subfield_value_str)
                    subfield_full_value = str(subfield_length).zfill(3) + subfield_key + subfield_value_str
                    subfield_values.append(subfield_full_value)
                    total_de060_length += len(subfield_full_value)
                total_de060_length_str = str(total_de060_length).zfill(3)
                # Append total length before the actual subfield values
                values.append(total_de060_length_str)
                values.extend(subfield_values)
            elif key == "DE055":
                # Handle DE055 by processing each tag and value
                de055_values = []
                total_de055_length = 0
                for tag, tag_value in value.items():
                    tag_value_str = str(tag_value)
                    tag_length = len(tag_value_str) // 2  # Halve the length
                    tag_full_value = tag + str(tag_length).zfill(2) + tag_value_str
                    de055_values.append(tag_full_value)
                    total_de055_length += len(tag_full_value)
                total_de055_length_str = str(total_de055_length).zfill(3)
                # Append total length before the actual DE055 values
                values.append(total_de055_length_str)
                values.extend(de055_values)
            else:
                values.extend(collect_values(value))
        else:
            if key in ["DE002", "DE032", "DE035", "DE053"]:
                # Add the 2-digit length before the value for DE002, DE032, DE035, and DE053
                length_str = str(len(str(value))).zfill(2)
                values.append(length_str + str(value))
            elif key == "DE004":
                # Ensure DE004 value is 12 digits long by prefixing it with 0s if necessary
                de004_value = str(value).zfill(12)
                values.append(de004_value)
            else:
                values.append(str(value))
    return values

# Ensure DE keys (except DE032, DE035, DE004, DE055, and DE060) are prefixed with 0s to make them a 5-digit DE number
def ensure_de_keys(data_elements):
    new_data_elements = {}
    for key, value in data_elements.items():
        if key.startswith("DE") and key not in ["DE002", "DE032", "DE035", "DE053", "DE004", "DE055"]:
            new_key = key[:2] + ''.join(['0'] * (5 - len(key))) + key[2:]  # Make the key a 5-digit DE number
            new_data_elements[new_key] = value
        else:
            new_data_elements[key] = value
    return new_data_elements

# Calculate and generate the bitmap
def generate_bitmap(data_elements):
    bitmap = [0] * 128
    for key in data_elements.keys():
        if key.startswith("DE"):
            de_number = int(key[2:])
            if 1 <= de_number <= 128:
                bitmap[de_number - 1] = 1

    primary_bitmap = bitmap[:64]
    secondary_bitmap = bitmap[64:]

    # If any bit in the secondary bitmap is set, mark the first bit of the primary bitmap
    if any(secondary_bitmap):
        primary_bitmap[0] = 1

    primary_bitmap_hex = "{:016X}".format(int("".join(map(str, primary_bitmap)), 2))
    secondary_bitmap_hex = ""
    if any(secondary_bitmap):
        secondary_bitmap_hex = "{:016X}".format(int("".join(map(str, secondary_bitmap)), 2))

    return primary_bitmap_hex + secondary_bitmap_hex

# Convert a string to its hexadecimal representation (in lowercase)
def str_to_hex(s):
    return s.encode('utf-8').hex()

# Load JSON data from input
def load_json_from_input():
    print("Please enter your JSON data (end input with an empty line):")
    json_string = ""
    while True:
        line = input()
        if line == "":
            break
        json_string += line + "\n"
    return json.loads(json_string)

# Load and process the JSON data
json_data = load_json_from_input()

# Ensure DE keys are properly formatted
if "data_elements" in json_data:
    json_data["data_elements"] = ensure_de_keys(json_data["data_elements"])

# Generate the bitmap
bitmap = ""
if "data_elements" in json_data:
    bitmap = generate_bitmap(json_data["data_elements"])

# Collect values
flattened_values = collect_values(json_data["data_elements"])

# Join the MTI, bitmap, and all values in a single line without spaces
mti = str(json_data.get("mti", "")).zfill(4)
flattened_line = mti + bitmap + "".join(flattened_values)
print(flattened_line)

# Convert the final output to hexadecimal and print it
hex_output = str_to_hex(flattened_line)
print(hex_output)
