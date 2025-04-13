import json
import logging
from binascii import unhexlify

logger = logging.getLogger(__name__)

def hex_to_ascii(hex_str):
    try:
        return unhexlify(hex_str).decode('utf-8')
    except Exception:
        return hex_str

def clean_de_key(label):
    if not label.startswith(("DE", "BM")):
        return None
    return "DE" + label.split()[0][2:]  # normalize "BM003" → "DE003"

def is_meaningful(value):
    if value is None: return False
    val = str(value).strip().lower()
    return val != "" and not val.startswith("client-defined")

def compare_excel_to_logs(excel_path, log_path):
    with open(excel_path, 'r') as f1:
        excel_data = json.load(f1)

    with open(log_path, 'r') as f2:
        log_data = json.load(f2)

    # 🧠 Step 1: Group logs by decoded RRN
    log_map = {}
    for log in log_data:
        mti = str(log.get("mti", ""))
        de = log.get("data_elements", {})
        rrn = de.get("DE037")
        if not rrn:
            continue

        key = rrn if mti == "100" else hex_to_ascii(rrn)
        if key not in log_map:
            log_map[key] = {}
        log_map[key][mti] = de

    # 🧠 Step 2: Compare test cases
    results = []

    for sheet_name, rows in excel_data.items():
        for row in rows:
            tc_id = row.get("Test Case ID", "").strip() or "Unnamed"
            rrn = row.get("DE037 (RRN)", "").strip()
            auth = row.get("DE038 (Auth Code)", "").strip()

            if not rrn or rrn.lower() == "client-defined":
                results.append({
                    "testcase_id": tc_id,
                    "sheet": sheet_name,
                    "status": "⚠ Skipped - Missing RRN",
                    "details": {}
                })
                continue

            logs = log_map.get(rrn)
            if not logs:
                results.append({
                    "testcase_id": tc_id,
                    "sheet": sheet_name,
                    "status": "❌ RRN not found in logs",
                    "details": {"expected_rrn": rrn}
                })
                continue

            mismatches = {}
            fallback_used = False

            for col, expected_val in row.items():
                field = clean_de_key(col)
                if not field or not is_meaningful(expected_val):
                    continue

                val_100 = logs.get("100", {}).get(field)
                val_110 = logs.get("110", {}).get(field)

                actual_val = val_100 or val_110
                if not val_100 and val_110:
                    fallback_used = True

                if str(expected_val).strip() != str(actual_val).strip():
                    mismatches[field] = {
                        "expected": expected_val,
                        "actual": actual_val or "Missing"
                    }

            status = "✔ Match"
            if mismatches:
                status = "❌ Mismatch"
            if fallback_used:
                status += " (used 110 fallback)"

            results.append({
                "testcase_id": tc_id,
                "sheet": sheet_name,
                "status": status,
                "details": mismatches
            })

    logger.info(f"✅ Comparison done. Total: {len(results)} test cases.")
    return results
