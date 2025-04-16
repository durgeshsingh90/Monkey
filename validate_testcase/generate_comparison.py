import json
import re
import os

def normalize_value(val):
    if val is None:
        return ""
    return str(val).strip()

def is_client_defined(value):
    return value == "" or re.search(r"(?i)client[-\s]?defined", value)

def is_de_key(key):
    return re.match(r"^(DE|BM)\d{3}(\.\d{2})?$", key)

def wildcard_match(value, log_value):
    if value.endswith('x'):
        return log_value.startswith(value[:-1])
    return value == log_value

def match_de060_63(value, log_value):
    if '+' in value:
        prefix = value.split('+')[0]
        return log_value.startswith(prefix)
    return value == log_value

def find_best_log_match(testcase, log_data):
    rrn = testcase.get("DE037")
    mti = testcase.get("MTI") or testcase.get("0200")
    de003 = testcase.get("DE003")
    de004 = testcase.get("DE004")

    candidates = [log for log in log_data if log.get("data_elements", {}).get("DE037") == rrn]

    if len(candidates) > 1 and mti:
        candidates = [log for log in candidates if str(log.get("mti")) == str(mti)]
    if len(candidates) > 1 and de003:
        candidates = [log for log in candidates if log.get("data_elements", {}).get("DE003") == de003]
    if len(candidates) > 1 and de004:
        candidates = [log for log in candidates if log.get("data_elements", {}).get("DE004") == de004]

    return candidates[0] if candidates else None

def build_comparison(sheet_name, testcases, log_data):
    result = []
    for tc in testcases:
        extracted_tc = {}
        for k, v in tc.items():
            if is_de_key(k):
                extracted_tc[k] = normalize_value(v)

        for key in extracted_tc:
            if key.endswith("037"):
                extracted_tc["DE037"] = extracted_tc[key]
            elif key == "0200":
                extracted_tc["MTI"] = extracted_tc["0200"]
            elif key.endswith("003"):
                extracted_tc["DE003"] = extracted_tc[key]
            elif key.endswith("004"):
                extracted_tc["DE004"] = extracted_tc[key]

        matched_log = find_best_log_match(extracted_tc, log_data)
        if not matched_log:
            result.append({
                "test_case_id": tc.get("TC001", "Unknown"),
                "matched_log_rrn": None,
                "comparison": "No matching log found"
            })
            continue

        log_de = matched_log.get("data_elements", {})
        comparison = {}

        for key, expected_value in extracted_tc.items():
            if not is_de_key(key):
                continue

            actual_value = log_de
            if '.' in key:
                parts = key.split('.')
                actual_value = actual_value.get(parts[0], {})
                actual_value = actual_value.get(parts[1], "") if isinstance(actual_value, dict) else ""
            else:
                actual_value = actual_value.get(key)

            expected_value = normalize_value(expected_value)
            actual_value = normalize_value(actual_value)

            if is_client_defined(expected_value):
                status = "accepted (client-defined)"
            elif key in ["DE060.63", "BM060.63"]:
                status = "match" if match_de060_63(expected_value, actual_value) else "mismatch"
            elif expected_value.endswith("x"):
                status = "match" if actual_value.startswith(expected_value[:-1]) else "mismatch"
            else:
                status = "match" if expected_value == actual_value else "mismatch"

            comparison[key] = {
                "expected": expected_value,
                "actual": actual_value,
                "status": status
            }

        result.append({
            "test_case_id": tc.get("TC001", "Unknown"),
            "matched_log_rrn": extracted_tc.get("DE037"),
            "comparison": comparison
        })

    return {sheet_name: result}


# ✅ Callable function for views.py
def run_comparison(excel_json_path, log_json_path, output_path):
    with open(excel_json_path, 'r', encoding='utf-8') as f:
        excel_data = json.load(f)

    with open(log_json_path, 'r', encoding='utf-8') as f:
        log_data = json.load(f)

    final_result = {}

    for sheet_name, testcases in excel_data.items():
        sheet_result = build_comparison(sheet_name, testcases, log_data)
        final_result.update(sheet_result)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2)

    print("✅ Comparison file generated at", output_path)


# ✅ Optional CLI test runner
if __name__ == "__main__":
    default_base = os.path.join("Monkey", "media", "validate_testcase")
    run_comparison(
        os.path.join(default_base, "excel_data.json"),
        os.path.join(default_base, "log_data.json"),
        os.path.join(default_base, "comparison_result.json")
    )
