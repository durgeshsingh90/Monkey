import os
import json
import threading
import pandas as pd
import re
import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .generate_comparison import run_comparison


import logging
logger = logging.getLogger(__name__)

# File paths
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'validate_testcase')
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXCEL_JSON = os.path.join(UPLOAD_DIR, 'excel_data.json')
LOG_JSON = os.path.join(UPLOAD_DIR, 'log_data.json')
COMPARE_JSON = os.path.join(UPLOAD_DIR, 'comparison_result.json')

def index(request):
    try:
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        logger.info("🧹 Cleared all files from validate_testcase media folder on page refresh.")
    except Exception as e:
        logger.error(f"❌ Error cleaning folder on refresh: {e}", exc_info=True)
    return render(request, 'validate_testcase/index.html')


def trigger_comparison_if_ready():
    if os.path.exists(EXCEL_JSON) and os.path.exists(LOG_JSON):
        try:
            logger.info("🧠 Both excel_data.json and log_data.json found. Running comparison...")
            run_comparison(EXCEL_JSON, LOG_JSON, COMPARE_JSON)
            logger.info("✅ comparison_result.json generated successfully at %s", COMPARE_JSON)
        except Exception as e:
            logger.error("❌ Error during comparison generation", exc_info=True)

# === Threaded Processing Helpers ===

def process_excel_file(file_path):
    try:
        logger.info("🚀 [Thread] Processing Excel")
        excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
        full_data = {}

        for sheet, df in excel_data.items():
            if "info" in sheet.lower():
                logger.info(f"⚠️ Skipping sheet '{sheet}' because it contains 'info'")
                continue
            df = df.fillna("")

            # Drop fully empty rows first
            df = df[~df.apply(lambda row: row.astype(str).str.strip().eq("").all(), axis=1)]
            df = df.reset_index(drop=True)

            def is_de_header_row(row_values):
                match_count = 0
                for val in row_values:
                    val = str(val).strip().upper().replace(" ", "")
                    if re.match(r'^(?:BM|DE)?\d{1,3}(\.\d+)?$', val):
                        match_count += 1
                return match_count >= 2

            header_row_index = None
            for idx in [1, 2, 3]:
                if len(df) > idx and is_de_header_row(df.iloc[idx].tolist()):
                    header_row_index = idx
                    break
            if header_row_index is not None:
                logger.info(f"🔍 Using row {header_row_index+1} as header for sheet: {sheet}")
                df.columns = df.iloc[header_row_index]
                df = df.drop(index=list(range(header_row_index + 1)))
            else:
                logger.info(f"📄 Defaulting to row 1 as header for sheet: {sheet}")
                df.columns = df.iloc[0]
                df = df.drop(index=[0])

            # Normalize column names like DE 02 -> DE002
            df.columns = [normalize_column(c) for c in df.columns]
            df = df.reset_index(drop=True)
            df = df.fillna("")

            def is_comment_row(row):
                non_empty_cells = row.astype(str).ne("").sum()
                if non_empty_cells <= 3:
                    return row.iloc[3:].eq("").all()
                return False

            df_filtered = df[~df.apply(is_comment_row, axis=1)]

            full_data[sheet] = df_filtered.to_dict(orient='records')

        with open(EXCEL_JSON, 'w') as f:
            json.dump(full_data, f, indent=2)

        logger.info("✅ Excel JSON saved")

    except Exception as e:
        logger.exception("❌ Failed to process Excel file")


import re
# Normalize and filter out non-DE/BM columns
def is_valid_de_column(col):
    return re.match(r'^DE\d{3}(\.\d+)?$', col)

def normalize_column(col):
    col = str(col).strip().upper().replace(" ", "")
    match = re.match(r'^(?:BM|DE)?(\d{1,3})(\.\d+)?$', col)
    if match:
        main_num = match.group(1).zfill(3)
        subfield = match.group(2) if match.group(2) else ''
        return f'DE{main_num}{subfield}'
    return col

def process_log_file(file_path):
    try:
        logger.info("🚀 [Thread] Processing Log")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = r'(?=\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3})'
        blocks = re.split(pattern, content)
        blocks = [b.strip() for b in blocks if b.strip()]
        parsed = []

        for i, b in enumerate(blocks):
            res = requests.post(
                'http://localhost:8000/splunkparser/parse/',
                json={'log_data': b},
                headers={'Content-Type': 'application/json'}
            )
            if res.status_code == 200 and res.json().get('status') == 'success':
                parsed.append(res.json()['result'])
                logger.info(f"✔ Parsed block {i+1}")
            else:
                logger.warning(f"❌ Failed to parse block {i+1}: {res.text}")

        with open(LOG_JSON, 'w') as f:
            json.dump(parsed, f, indent=2)

        logger.info("✅ Log JSON saved")
  
    except Exception as e:
        logger.exception("❌ Failed to process Log file")



# === Upload Views ===

@csrf_exempt
def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        # Delete existing Excel files and related JSON before upload
        try:
            for filename in os.listdir(UPLOAD_DIR):
                if filename.endswith('.xls') or filename.endswith('.xlsx') or filename == 'excel_data.json':
                    os.remove(os.path.join(UPLOAD_DIR, filename))
            logger.info("🧹 Cleared old Excel files and excel_data.json")
        except Exception as e:
            logger.error(f"❌ Error deleting old Excel files: {e}", exc_info=True)

        # Save new file
        file = request.FILES['excel_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        file_path = os.path.join(UPLOAD_DIR, fs.save(file.name, file))

        try:
            process_excel_file(file_path)  # Wait for JSON generation
            trigger_comparison_if_ready()
            return JsonResponse({'status': 'success', 'filename': file.name})
        except Exception as e:
            logger.error("❌ Excel processing failed", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'error': 'Invalid Excel upload'}, status=400)

@csrf_exempt
def upload_logs(request):
    if request.method == 'POST' and request.FILES.get('log_file'):
        try:
            log_extensions = ('.log', '.txt', '.html', '.xml', '.json', '.debug')
            for filename in os.listdir(UPLOAD_DIR):
                lower_filename = filename.lower()
                if lower_filename.endswith(log_extensions) and lower_filename not in ['excel_data.json', 'comparison_result.json']:
                    os.remove(os.path.join(UPLOAD_DIR, filename))
            logger.info("🧹 Cleared old log files and log_data.json")
        except Exception as e:
            logger.error(f"❌ Error deleting old log files: {e}", exc_info=True)

        # Save new log file
        file = request.FILES['log_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        file_path = os.path.join(UPLOAD_DIR, fs.save(file.name, file))

        try:
            process_log_file(file_path)  # 🔁 Synchronous execution
            trigger_comparison_if_ready()

            return JsonResponse({'status': 'success', 'filename': file.name})
        except Exception as e:
            logger.error("❌ Log processing failed", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'error': 'Invalid log upload'}, status=400)


import glob
import pandas as pd
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.http import JsonResponse
import os
import json
import logging

logger = logging.getLogger(__name__)

def highlight_comparison_results(request):
    try:
        # Get original uploaded Excel file path
        excel_files = glob.glob(os.path.join(UPLOAD_DIR, '*.xls*'))
        if not excel_files:
            raise FileNotFoundError("Excel file not found.")
        original_excel_path = excel_files[0]

        # Read original Excel sheets (preserving headers and layout)
        original_excel = pd.read_excel(original_excel_path, sheet_name=None)
        
        # Load comparison result
        with open(COMPARE_JSON, 'r') as f:
            comparison_data = json.load(f)

        highlighted_sheets = {}

        for sheet_name, testcases in comparison_data.items():
            df = original_excel.get(sheet_name)
            if df is None or df.empty:
                continue

            df = df.fillna("")

            for result in testcases:
                comparison = result.get("comparison", {})
                if not isinstance(comparison, dict):
                    continue  # Skip "No matching log found"

                tc_id = result.get("test_case_id")
                rrn = result.get("matched_log_rrn")
                mti = None
                de003 = None

                for k, comp in comparison.items():
                    if "MTI" in k:
                        mti = comp.get("expected")
                    elif k.endswith("003"):
                        de003 = comp.get("expected")

                # Match row in Excel using RRN + TC001 first
                match = df[
                    (df.get("DE037", "") == rrn) &
                    (df.get("TC001", "") == tc_id)
                ]

                if len(match) != 1:
                    # Fallback using MTI + DE003
                    match = df[
                        (df.get("MTI", "") == mti) &
                        (df.get("DE003", "") == de003)
                    ]

                if not match.empty:
                    idx = match.index[0]
                    for de, comp in comparison.items():
                        expected = escape(comp.get("expected", ""))
                        actual = escape(comp.get("actual", ""))
                        status = comp.get("status", "")

                        color = {
                            "match": "background-color: white;",
                            "mismatch": "background-color: #f99;",
                            "accepted (client-defined)": "background-color: #ff9;"
                        }.get(status, "background-color: #ccc;")

                        display = f"{expected} | {actual}" if expected != actual else expected

                        if de in df.columns:
                            df.at[idx, de] = f'<div style="{color}">{display}</div>'

            # Convert final DataFrame to HTML with color-coded cells
            highlighted_sheets[sheet_name] = mark_safe(df.to_html(escape=False, index=False))

        return render(request, 'validate_testcase/comparison_result.html', {
            "highlighted_sheets": highlighted_sheets
        })

    except Exception as e:
        logger.exception("❌ Error rendering comparison result")
        return JsonResponse({"error": str(e)}, status=500)
