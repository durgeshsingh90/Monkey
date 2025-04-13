import os
import json
import logging
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse

# Set up logging
logger = logging.getLogger(__name__)

# Store files temporarily in media/validate_testcase
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'validate_testcase')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def index(request):
    return render(request, 'validate_testcase/index.html')

def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        filename = fs.save(excel_file.name, excel_file)
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            # Read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
            full_data = {}

            for sheet_name, df in excel_data.items():
                df = df.fillna("")
                original_len = len(df)

                skipped_rows = []
                kept_rows = []

                for i, row in df.iterrows():
                    non_empty_cols = [df.columns[j] for j in range(len(df.columns)) if row[j] != ""]
                    if len(non_empty_cols) <= 3:
                        skipped_rows.append((i + 2, dict(row), non_empty_cols))  # i+2 because Excel rows start from 1 and header is row 1
                    else:
                        kept_rows.append(row)

                # Log skipped rows
                for row_num, data, filled_cols in skipped_rows:
                    logger.debug(f"🚫 Skipped Row {row_num} in Sheet '{sheet_name}' — Filled Columns: {filled_cols} | Data: {data}")

                # Convert valid rows
                clean_df = pd.DataFrame(kept_rows)
                sheet_records = clean_df.to_dict(orient='records')
                full_data[sheet_name] = sheet_records

                logger.info(f"✅ Processed Sheet: {sheet_name} | Kept: {len(sheet_records)} | Skipped: {len(skipped_rows)}")

                for idx, row in enumerate(sheet_records):
                    logger.debug(f"[{sheet_name}] Row {idx + 1}: {row}")

            # Save JSON output
            json_file_path = os.path.join(UPLOAD_DIR, 'excel_data.json')
            with open(json_file_path, 'w') as f:
                json.dump(full_data, f, indent=2)

            logger.info(f"✅ Excel file '{filename}' successfully parsed and saved as JSON")

            return redirect('index')

        except Exception as e:
            logger.error(f"❌ Error parsing Excel file '{filename}': {e}", exc_info=True)
            return JsonResponse({'error': 'Failed to parse Excel'}, status=500)

    return JsonResponse({'error': 'Invalid Excel upload'}, status=400)

def upload_logs(request):
    if request.method == 'POST' and request.FILES.get('log_file'):
        log_file = request.FILES['log_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        filename = fs.save(log_file.name, log_file)
        file_path = os.path.join(UPLOAD_DIR, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            log_json = [{'line': line.strip()} for line in lines]

            with open(os.path.join(UPLOAD_DIR, 'log_data.json'), 'w') as f:
                json.dump(log_json, f, indent=2)

            logger.info(f"✅ Uploaded log file: {filename}")
            logger.debug(f"📜 First 5 lines:\n" + "\n".join([l['line'] for l in log_json[:5]]))

            return redirect('index')
        except Exception as e:
            logger.error(f"❌ Error processing log file: {e}", exc_info=True)
            return JsonResponse({'error': 'Failed to parse log file'}, status=500)

    return JsonResponse({'error': 'Invalid log upload'}, status=400)
