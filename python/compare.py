import pandas as pd
import json
import re
import os

# ------------------ Utility: Pattern Matching ------------------ #
def contains_de_or_bm(cell):
    if not isinstance(cell, str):
        return False
    pattern = r'\b(?:DE|BM)[\s\-]?0?\d{1,3}(?:\.\d{1,3})?\b'
    return re.search(pattern, cell, re.IGNORECASE) is not None

def find_custom_header_row(df):
    for idx, row in df.iterrows():
        if any(contains_de_or_bm(str(cell)) for cell in row):
            return idx
    return None

def normalize_column_name(name):
    # Match DE or BM patterns
    match = re.search(r'(?:DE|BM)[\s\-]?(\d{1,3})(?:\.(\d{1,3}))?', str(name), re.IGNORECASE)
    if match:
        main_part = match.group(1).zfill(3)  # Pad with leading zeros, e.g., 3 → 003
        subfield = match.group(2)
        if subfield:
            return f"DE{main_part}.{subfield}"
        return f"DE{main_part}"
    return None


def matches_pattern(expected, actual):
    if expected in ["Client Defined", "valid value"]:
        return actual is not None
    if isinstance(expected, str) and expected.endswith("x"):
        return str(actual).startswith(expected[:-1])
    return str(expected) == str(actual)

# ------------------ Core Comparison ------------------ #
def compare_excel_to_log(excel_row, log_blocks, row_index):
    mti = str(excel_row.get("Message Type", "")).strip()
    de003 = str(excel_row.get("DE003", "")).strip()
    matched_log = None

    log_output = [f"\n=== Row {row_index} | RRN: {excel_row['DE037']} ==="]

    # Step 1: Filter FromIso blocks
    fromiso_blocks = [
        block for block in log_blocks
        if block.get("route", "").startswith("FromIso")
    ]

    if not fromiso_blocks:
        log_output.append("❌ No FromIso blocks found for this RRN.")
        return "\n".join(log_output)

    # Step 2: If only one FromIso block, use it directly
    if len(fromiso_blocks) == 1:
        matched_log = fromiso_blocks[0].get("result", {}).get("data_elements", {})
        log_output.append("✅ Single FromIso block found — using it directly.")
    else:
        # Step 3: Match FromIso using MTI + DE003
        for block in fromiso_blocks:
            result = block.get("result", {})
            mti_log = str(result.get("mti", "")).strip()
            de003_log = str(result.get("data_elements", {}).get("DE003", "")).strip()

            log_output.append(f"🔍 Checking FromIso: MTI={mti_log}, DE003={de003_log}")

            if mti_log == mti and de003_log == de003:
                matched_log = result.get("data_elements", {})
                log_output.append("✅ Found matching FromIso block using MTI + DE003.")
                break

        if not matched_log:
            log_output.append("❌ No matching FromIso block found with MTI + DE003.")
            return "\n".join(log_output)

    # Step 4: Compare DEs from Excel row to matched log
    for col, value in excel_row.items():
        de_key = normalize_column_name(col)
        if not de_key or pd.isna(value):
            continue

        value_str = str(value).strip()
        log_val = matched_log.get(de_key)

        # Special case: DE043 subfields
        if de_key.startswith("DE043.") and "DE043" in matched_log:
            full_43 = str(matched_log.get("DE043", ""))
            if value_str.lower() in full_43.lower():
                log_output.append(f"✅ {de_key}: found '{value_str}' in DE043")
            else:
                log_output.append(f"❌ {de_key}: '{value_str}' not found in DE043 → '{full_43}'")

        # Nested DEs in 60x range: DE060.xx, DE061.xx, etc.
        elif '.' in de_key:
            parent, subfield = de_key.split('.')
            if parent.startswith("DE06") or parent.startswith("DE6"):
                nested = matched_log.get(parent)
                if isinstance(nested, dict):
                    nested_val = nested.get(subfield)
                    if value_str in ["Client Defined", "valid value"]:
                        if subfield in nested:
                            log_output.append(f"✅ {de_key} is present (Client Defined)")
                        else:
                            log_output.append(f"❌ {de_key} is missing (Client Defined)")
                    elif value_str.endswith("x") and len(value_str) >= 2:
                        if nested_val and str(nested_val).startswith(value_str[:-1]):
                            log_output.append(f"✅ {de_key}: starts with '{value_str[:-1]}'")
                        else:
                            log_output.append(f"❌ {de_key}: expected prefix '{value_str[:-1]}', got '{nested_val}'")
                    elif str(nested_val) == value_str:
                        log_output.append(f"✅ {de_key}: {value_str}")
                    else:
                        log_output.append(f"❌ {de_key}: expected '{value_str}', got '{nested_val}'")
                else:
                    log_output.append(f"❌ {de_key}: parent field '{parent}' not found or not a nested dict")

        # Generic rules
        elif value_str in ["Client Defined", "valid value"]:
            if de_key in matched_log:
                log_output.append(f"✅ {de_key} is present (Client Defined)")
            else:
                log_output.append(f"❌ {de_key} is missing (Client Defined)")

        elif value_str.endswith("x") and len(value_str) >= 2:
            if log_val and str(log_val).startswith(value_str[:-1]):
                log_output.append(f"✅ {de_key}: starts with '{value_str[:-1]}'")
            else:
                log_output.append(f"❌ {de_key}: expected prefix '{value_str[:-1]}', got '{log_val}'")

        elif str(log_val) == value_str:
            log_output.append(f"✅ {de_key}: {value_str}")

        else:
            log_output.append(f"❌ {de_key}: expected '{value_str}', got '{log_val}'")

    return "\n".join(log_output)

# ------------------ Main Runner ------------------ #
def process_excel_and_log(excel_path, json_log_path, log_output_path):
    try:
        sheets = pd.read_excel(excel_path, sheet_name=None, header=None)
        with open(json_log_path, 'r', encoding='utf-8') as f:
            logs_json = json.load(f)

        all_logs = []

        for sheet_name, raw_df in sheets.items():
            header_row_index = find_custom_header_row(raw_df)
            if header_row_index is None:
                continue

            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row_index)

            for idx, row in df.iterrows():
                if "BM 37" not in df.columns:
                    continue
                rrn = str(row["BM 37"]).strip()
                if not re.fullmatch(r"\d{12}", rrn):
                    continue

                row_dict = row.to_dict()
                row_dict["DE037"] = rrn  # ensure it's part of the mapping

                log_key = f"RRN_{rrn}"
                if log_key not in logs_json:
                    all_logs.append(f"\n=== Row {idx} | RRN: {rrn} ===\n❌ RRN not found in log.")
                    continue

                result = compare_excel_to_log(row_dict, logs_json[log_key], idx)
                all_logs.append(result)

        # Write result log
        with open(log_output_path, 'w', encoding='utf-8') as log_file:
            log_file.write("\n".join(all_logs))

        print(f"✅ Comparison complete. Log saved to:\n{log_output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")

# ------------------ Usage ------------------ #
if __name__ == "__main__":
    excel_file = r"D:\Projects\VSCode\MangoData\VisaAFTTestcase.xlsx"
    log_json_file = r"D:\Projects\VSCode\MangoData\splunk_log_logs.json"
    log_output_file = r"D:\Projects\VSCode\MangoData\comparison_result.log"

    process_excel_and_log(excel_file, log_json_file, log_output_file)
