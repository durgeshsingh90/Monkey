def string_to_hex(s):
    return s.encode('utf-8').hex()

def hex_to_string(hex_str):
    return bytes.fromhex(hex_str).decode('utf-8')

def convert_input(user_input):
    if len(user_input) == 12:
        # Assume it's a string and convert to hexadecimal
        hex_output = string_to_hex(user_input)
        return f"{user_input} OR {hex_output}"
    elif len(user_input) == 24:
        # Assume it's a hexadecimal string and convert to the original string
        original_string = hex_to_string(user_input)
        return f"{user_input} OR {original_string}"
    else:
        return f"Invalid input length for '{user_input}'"

# Input from user
print("Enter strings or hexadecimals (one in each line). Type 'END' to finish input:")

inputs = []
while True:
    user_input = input()
    if user_input.upper() == 'END':
        break
    inputs.append(user_input)

# Process each input and combine results
results = []
for user_input in inputs:
    results.append(convert_input(user_input))

combined_result = " OR ".join(results)

# Print the combined result
print(f"index = application_omnipay {combined_result} | reverse")
