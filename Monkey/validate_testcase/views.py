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
from .compare import compare_excel_to_logs  # your comparison logic

import logging
logger = logging.getLogger(__name__)

# File paths
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, 'validate_testcase')
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXCEL_JSON = os.path.join(UPLOAD_DIR, 'excel_data.json')
LOG_JSON = os.path.join(UPLOAD_DIR, 'log_data.json')
COMPARE_JSON = os.path.join(UPLOAD_DIR, 'comparison_result.json')

def index(request):
    # Clear previous uploads (except processed jsons)
    try:
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path) and not filename.endswith('_data.json') and not filename.startswith('comparison'):
                os.remove(file_path)
        logger.info("✅ Cleared raw uploaded files, kept jsons.")
    except Exception as e:
        logger.error(f"❌ Error cleaning folder: {e}", exc_info=True)
    return render(request, 'validate_testcase/index.html')

# === Threaded Processing Helpers ===

def process_excel_file(file_path):
    try:
        logger.info("🚀 [Thread] Processing Excel")
        excel_data = pd.read_excel(file_path, sheet_name=None)
        full_data = {sheet: df.fillna("").to_dict(orient='records') for sheet, df in excel_data.items()}

        with open(EXCEL_JSON, 'w') as f:
            json.dump(full_data, f, indent=2)

        logger.info("✅ Excel JSON saved")
        try_run_comparison()
    except Exception as e:
        logger.exception("❌ Failed to process Excel file")

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
        try_run_comparison()
    except Exception as e:
        logger.exception("❌ Failed to process Log file")

def try_run_comparison():
    if os.path.exists(EXCEL_JSON) and os.path.exists(LOG_JSON):
        try:
            logger.info("⚙ Starting comparison of Excel and Log data")
            result = compare_excel_to_logs(EXCEL_JSON, LOG_JSON)
            with open(COMPARE_JSON, 'w') as f:
                json.dump(result, f, indent=2)
            logger.info("🎯 Comparison complete and saved")
        except Exception as e:
            logger.exception("❌ Comparison failed")

# === Upload Views ===

@csrf_exempt
def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        file_path = os.path.join(UPLOAD_DIR, fs.save(file.name, file))
        threading.Thread(target=process_excel_file, args=(file_path,)).start()
        return redirect('index')
    return JsonResponse({'error': 'Invalid Excel upload'}, status=400)

@csrf_exempt
def upload_logs(request):
    if request.method == 'POST' and request.FILES.get('log_file'):
        file = request.FILES['log_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        file_path = os.path.join(UPLOAD_DIR, fs.save(file.name, file))
        threading.Thread(target=process_log_file, args=(file_path,)).start()
        return redirect('index')
    return JsonResponse({'error': 'Invalid log upload'}, status=400)

def view_comparison_result(request):
    excel_path = os.path.join(UPLOAD_DIR, 'excel_data.json')
    compare_path = os.path.join(UPLOAD_DIR, 'comparison_result.json')

    if not os.path.exists(excel_path) or not os.path.exists(compare_path):
        return JsonResponse({'error': 'Excel or comparison result not found'}, status=404)

    with open(excel_path, 'r') as f1:
        excel_data = json.load(f1)
    with open(compare_path, 'r') as f2:
        compare_data = json.load(f2)

    # Build a lookup of mismatches
    mismatch_map = {}
    for result in compare_data:
        key = f"{result['sheet']}::{result['testcase_id']}"
        mismatch_map[key] = result

    return render(request, 'validate_testcase/comparison_result.html', {
        'excel_data': excel_data,
        'mismatch_map': mismatch_map
    })
from django.views.decorators.http import require_GET

@require_GET
def check_status(request):
    comparison_path = os.path.join(UPLOAD_DIR, 'comparison_result.json')
    if os.path.exists(comparison_path):
        return JsonResponse({'status': 'ready'})
    return JsonResponse({'status': 'processing'})