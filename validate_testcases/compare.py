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
    match = re.search(r'(?:DE|BM)[\s\-]?(\d{1,3})(?:\.(\d{1,3}))?', str(name), re.IGNORECASE)
    if match:
        main = match.group(1).zfill(3)
        sub = match.group(2)
        return f"DE{main}.{sub}" if sub else f"DE{main}"
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

        def clean_rrn(value):
            try:
                val_str = str(value).strip()
                if '.' in val_str:
                    val_str = val_str.split('.')[0]
                return val_str if re.fullmatch(r"\d{12}", val_str) else ""
            except:
                return ""

        for sheet_name, raw_df in sheets.items():
            header_row_index = find_custom_header_row(raw_df)
            if header_row_index is None:
                continue

            # Load header
            df = pd.read_excel(excel_path, sheet_name=sheet_name, header=header_row_index, dtype=str).fillna("")

            # Find the RRN column name (BM 37, DE037, etc.)
            rrn_col = None
            for col in df.columns:
                col_upper = str(col).strip().upper()
                if col_upper in ["BM 37", "BM37", "DE037"]:
                    rrn_col = col
                    break

            if not rrn_col:
                continue  # Skip if no DE037/BM37 found

            # Apply cleaning to RRN column only
            df[rrn_col] = df[rrn_col].apply(clean_rrn)

            for idx, row in df.iterrows():
                rrn = str(row.get(rrn_col, "")).strip()
                if not re.fullmatch(r"\d{12}", rrn):
                    continue

                row_dict = row.to_dict()
                row_dict["DE037"] = rrn  # Ensure it's included explicitly

                log_key = f"RRN_{rrn}"
                if log_key not in logs_json:
                    all_logs.append(f"\n=== Row {idx} | RRN: {rrn} ===\n❌ RRN not found in log.")
                    continue

                result = compare_excel_to_log(row_dict, logs_json[log_key], idx)
                all_logs.append(result)

        with open(log_output_path, 'w', encoding='utf-8') as log_file:
            log_file.write("\n".join(all_logs))

        print(f"✅ Comparison complete. Log saved to:\n{log_output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")

def compare_and_style(df, logs_json, validation_json, result_log, sheet_name):
    result_log.append(f"\n📄 Sheet: {sheet_name}")
    styled_rows = []

    def clean_rrn(val):
        val_str = str(val).strip()
        if '.' in val_str:
            val_str = val_str.split('.')[0]
        return val_str if re.fullmatch(r"\d{12}", val_str) else val_str

    for col in df.columns:
        if str(col).strip().upper() in ["BM 37", "BM37", "DE037"]:
            df[col] = df[col].apply(clean_rrn)

    for idx, row in df.iterrows():
        rrn = clean_rrn(row.get("BM 37", ""))
        log_key = f"RRN_{rrn}"
        matched_log = None
        row_result = []

        if log_key not in logs_json:
            result_log.append(f"\n❌ Row {idx}: RRN {rrn} not found in logs.")
            row_result = [{'match': None, 'value': row[col]} for col in df.columns]
            styled_rows.append(row_result)
            continue

        log_blocks = logs_json[log_key]
        fromiso = [b for b in log_blocks if b.get("route", "").lower().startswith("fromiso")]
        matched_log = fromiso[0].get("result", {}).get("data_elements", {}) if fromiso else {}
        result_log.append(f"\n✅Row {idx}: RRN {rrn} matched. Comparing DEs:========================")

        validation_block = validation_json.get(f"Block_{idx+1}", {})
        invalid_fields = set(validation_block.get("wrong_length", []) + validation_block.get("wrong_format", []))

        for col in df.columns:
            val = row[col]
            val_str = str(val).strip()
            de_key = normalize_column_name(col)

            cell_match = True
            if not de_key or pd.isna(val) or val_str == "":
                row_result.append({'match': True, 'value': val})
                continue

            failed_messages = [msg for msg in invalid_fields if msg.startswith(de_key)]
            if failed_messages:
                row_result.append({'match': False, 'value': val})
                result_log.append(f"  ❌ {de_key} failed schema validation.")
                for msg in failed_messages:
                    result_log.append(f"  ❌ {msg}")
                continue

            if val_str.lower() in ["client defined", "valid value"]:
                row_result.append({'match': True, 'value': val})
                result_log.append(f"  ✅ {de_key}: Skipped ({val_str})")
                continue

            log_val = matched_log.get(de_key, "")
            log_val_str = str(log_val).strip()
            
            if val_str.endswith("x") and len(val_str) == 3 and val_str[:2].isdigit():
                prefix = val_str[:2]
                match = log_val_str.startswith(prefix) and len(log_val_str) == 3 and log_val_str.isdigit()
                emoji = "✅" if match else "❌"
                result_log.append(f"  {emoji} {de_key}: prefix match '{prefix}x' | found '{log_val_str}'")
            elif log_val_str == val_str:
                match = True
                result_log.append(f"  ✅ {de_key}: expected '{val_str}' | found '{log_val_str}'")
            else:
                match = False
                result_log.append(f"  ❌ {de_key}: expected '{val_str}' | found '{log_val_str}'")
            
            row_result.append({'match': match, 'value': val})
            

        styled_rows.append(row_result)

    return pd.DataFrame(styled_rows, columns=df.columns)

def run_comparison_from_web(excel_path, json_log_path, output_log_path):
    with open(json_log_path, 'r', encoding='utf-8') as f:
        logs_json = json.load(f)

    validation_path = json_log_path.replace("grouped_rrn_logs.json", "validation_summary.json")
    if os.path.exists(validation_path):
        with open(validation_path, 'r', encoding='utf-8') as vf:
            validation_json = json.load(vf)
    else:
        validation_json = {}

    all_results = {}
    comparison_logs = []
    xls = pd.read_excel(excel_path, sheet_name=None, header=None)

    for sheet, raw_df in xls.items():
        header_row = next((i for i, r in raw_df.iterrows() if any("DE" in str(c) or "BM" in str(c) for c in r)), 0)
        df = pd.read_excel(excel_path, sheet_name=sheet, header=header_row).fillna('')
        styled_df = compare_and_style(df, logs_json, validation_json, comparison_logs, sheet)
        all_results[sheet] = styled_df

    with open(output_log_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(comparison_logs))

    return all_results, "\n".join(comparison_logs)
