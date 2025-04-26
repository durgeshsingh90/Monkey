from django.http import JsonResponse
import os
import zipfile
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json

from .scripts.astrex_html_logfilter.breakhtml_1 import run_breakhtml
from .scripts.astrex_html_logfilter.adjusthtml_2 import run_adjusthtml
from .scripts.astrex_html_logfilter.unique_de32_html_3 import run_unique_de32_html
from .scripts.astrex_html_logfilter.astrex_html_filter_4 import run_astrex_html_filter
from .scripts.astrex_html_logfilter.html2emvco_5 import run_html2emvco

def index(request):
    clear_previous_files()
    return render(request, 'astrex_html_logs/index.html')

def clear_previous_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename in ["bm32_config.json"]:
                continue  # Skip config file
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

@csrf_exempt
def upload_log(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()

            upload_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, uploaded_file.name)

            # Delete all files before uploading the new one
            clear_previous_files()

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            if filename.endswith('.html'):
                run_breakhtml(file_path)
                run_adjusthtml(file_path)
                de032_result = run_unique_de32_html(file_path, max_processes=10)

                total_DE032_count = de032_result["total_DE032_count"]
                total_txn = de032_result.get("total_transactions", "")
                start_log_time = de032_result.get("start_log_time", "")
                end_log_time = de032_result.get("end_log_time", "")
                execution_time = de032_result["execution_time"]

                return JsonResponse({
                    'status': 'success',
                    'message': f'File {uploaded_file.name} uploaded and processed successfully.',
                    'filename': uploaded_file.name,
                    'de032_counts': de032_result.get("consolidated_de032_value_counts", {}),
                    'total_DE032_count': total_DE032_count,
                    'total_txn': total_txn,
                    'start_log_time': start_log_time,
                    'end_log_time': end_log_time,
                    'execution_time': execution_time,
                })

            return JsonResponse({'status': 'error', 'message': 'Only .html files are supported.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@csrf_exempt
def download_filtered_by_de032(request):
    if request.method == 'POST':
        try:
            de032_value = request.POST.get('de032')
            filename = request.POST.get('filename')  # original .html filename

            if not de032_value or not filename:
                return JsonResponse({'status': 'error', 'message': 'Missing DE032 or filename'})

            json_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', 'unique_bm32.json')
            conditions = de032_value.split(',')

            # Run filter and get the path of the generated zip
            zip_file_path = run_astrex_html_filter(json_path, conditions)
            
            if zip_file_path and os.path.exists(zip_file_path):
                return JsonResponse({
                    'status': 'success',
                    'filtered_file': f"astrex_html_logs/{os.path.basename(zip_file_path)}"
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Filtered ZIP not created.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

from pathlib import Path

# This will point to: Monkey/astrex_html_logs/scripts/astrex_html_logfilter/emvco_template.xml
template_path = os.path.join(
    Path(__file__).resolve().parent,
    'scripts',
    'astrex_html_logfilter',
    'emvco_template.xml'
)
@csrf_exempt
def zip_filtered_files(request):
    if request.method == 'POST':
        try:
            filename = request.POST.get('filename')
            if not filename:
                return JsonResponse({'status': 'error', 'message': 'Filename not provided'})

            json_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', 'unique_bm32.json')

            if not os.path.exists(json_path):
                return JsonResponse({'status': 'error', 'message': 'unique_bm32.json not found'})

            with open(json_path, 'r') as f:
                json_data = json.load(f)

            # Extract all unique BM32s
            consolidated_counts = json_data.get("consolidated_de032_value_counts", {})
            all_conditions = list(consolidated_counts.keys())

            # Call the script with all conditions
            zip_file_path = run_astrex_html_filter(json_path, all_conditions)

            if zip_file_path and os.path.exists(zip_file_path):
                return JsonResponse({
                    'status': 'success',
                    'zip_file': f"astrex_html_logs/{os.path.basename(zip_file_path)}"
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Filtered ZIP not created.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': f'Server error: {str(e)}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

from django.views.decorators.csrf import csrf_exempt

def admin_config(request):
    return render(request, 'astrex_html_logs/admin.html')

@csrf_exempt
def save_config(request):
    if request.method == 'POST':
        try:
            config_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', 'bm32_config.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                f.write(request.body.decode('utf-8'))
            return JsonResponse({'status': 'success', 'message': 'Config saved successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def load_config(request):
    config_path = os.path.join(settings.MEDIA_ROOT, 'astrex_html_logs', 'bm32_config.json')

    # 🚀 If missing, recreate with full default nested structure
    if not os.path.exists(config_path):
        default_config = {
            "Diners Club": {
                "360001": "Diners Club Test Gateway",
                "360002": "Diners Club Production Node"
            },
            "Visa": {
                "411111": "Visa PSP India",
                "450001": "Visa Europe Node",
                "450002": "Visa USA Node"
            },
            "MasterCard": {
                "512345": "MasterCard PSP Dubai",
                "520082": "MasterCard Sandbox Singapore",
                "530125": "MasterCard PSP India"
            },
            "JCB": {
                "352800": "JCB Japan PSP",
                "353011": "JCB Asia Production"
            },
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)

    # 🚀 Now safely load the config
    with open(config_path, 'r') as f:
        data = json.load(f)

    return JsonResponse(data, safe=False)

import re

def extract_datetime_from_cell8norm(cell_text):
    # Find [inside brackets]
    match = re.search(r'\[(.*?)\]', cell_text)
    if match:
        return match.group(1)
    return None
