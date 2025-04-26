import os
import json
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Import processing scripts
from .scripts.breakemvco_1 import process_file as split_file
from .scripts.adjustemvco_2 import adjust_file as fix_unclosed_online_messages
from .scripts.adjustelements_3 import adjust_elements
from .scripts.unique_de32_emvco_4 import extract_de032
from .scripts.emvco_filter_5 import filter_by_conditions  # <-- Your corrected filter

def clear_previous_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'emvco_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename in ["bm32_config.json"]:
                continue  # Skip config file
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

def index(request):
    clear_previous_files()
    return render(request, 'emvco_logs/index.html')

def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            clear_previous_files()

            uploaded_file = request.FILES['file']
            save_path = os.path.join(settings.MEDIA_ROOT, 'emvco_logs', uploaded_file.name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save uploaded file
            with open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Step 1: Split XML
            split_file(save_path)

            # Step 2: Fix unclosed OnlineMessage elements
            fix_unclosed_online_messages(save_path)

            # Step 3: Add headers/footers
            adjust_elements(save_path)

            # Step 4: Extract DE032 mappings
            extract_de032(save_path)

            return JsonResponse({'status': 'success', 'filename': uploaded_file.name})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)

@csrf_exempt
def download_filtered_by_de032(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conditions = data.get('conditions', [])

            if not conditions:
                return JsonResponse({'status': 'error', 'error': 'No conditions provided'}, status=400)

            json_path = os.path.join(settings.MEDIA_ROOT, 'emvco_logs', 'unique_bm32_emvco.json')

            # Dynamically generate filtered XMLs and ZIP
            zip_file_path = filter_by_conditions(json_path, conditions)

            # Return ZIP for download
            zip_filename = os.path.basename(zip_file_path)
            return FileResponse(open(zip_file_path, 'rb'), as_attachment=True, filename=zip_filename)

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)
