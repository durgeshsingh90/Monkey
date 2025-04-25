# emvco_logs/views.py

import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Import your 6 scripts (your uploaded ones)
from .scripts.breakemvco_1 import run_breakhtml
from .scripts.adjustemvco_2 import adjust_emvco_file
from .scripts.adjustelements_3 import adjust_elements
from .scripts.unique_de32_emvco_4 import extract_de032
from .scripts.emvco_filter_5 import filter_conditions_and_zip
from .scripts.format_emv_filter_6 import fix_filtered_file

def clear_previous_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'emvco_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def index(request):
    clear_previous_files()
    return render(request, 'emvco_logs/index.html')

@csrf_exempt
def upload_log(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()

            upload_path = os.path.join(settings.MEDIA_ROOT, 'emvco_logs')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, uploaded_file.name)

            clear_previous_files()

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            if filename.endswith('.xml'):
                base_file_path = file_path[:-4]

                # Sequentially run your uploaded scripts
                run_breakhtml(file_path)
                adjust_emvco_file(file_path)
                adjust_elements(file_path)
                json_file = extract_de032(base_file_path)

                with open(json_file, 'r') as f:
                    data = json.load(f)

                de032_counts = data.get('total_counts', {})
                total_de032_count = data.get('total_de032_count', 0)

                return JsonResponse({
                    'status': 'success',
                    'message': f'File {uploaded_file.name} uploaded and processed successfully.',
                    'filename': uploaded_file.name,
                    'de032_counts': de032_counts,
                    'total_de032_count': total_de032_count,
                })

            return JsonResponse({'status': 'error', 'message': 'Only XML files are supported.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@csrf_exempt
def download_filtered_by_de032(request):
    if request.method == 'POST':
        try:
            de032_value = request.POST.get('de032')
            filename = request.POST.get('filename')

            if not de032_value or not filename:
                return JsonResponse({'status': 'error', 'message': 'Missing DE032 or filename'})

            base_file_path = os.path.join(settings.MEDIA_ROOT, 'emvco_logs', filename)
            json_file = os.path.join(settings.MEDIA_ROOT, 'emvco_logs', 'unique_bm32_emvco.json')

            if not os.path.exists(json_file):
                return JsonResponse({'status': 'error', 'message': 'unique_bm32_emvco.json not found'})

            conditions = [de032_value]
            zip_file_path = filter_conditions_and_zip(json_file, conditions, os.path.dirname(base_file_path))

            if zip_file_path and os.path.exists(zip_file_path):
                return JsonResponse({
                    'status': 'success',
                    'filtered_file': f"emvco_logs/{os.path.basename(zip_file_path)}"
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Filtered ZIP not created.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
