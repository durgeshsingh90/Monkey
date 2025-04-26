import os
import json
import logging
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Import your processing scripts
from .scripts.breakemvco_1 import process_file as split_file
from .scripts.adjustemvco_2 import adjust_file as fix_unclosed_online_messages
from .scripts.adjustelements_3 import adjust_elements
from .scripts.unique_de32_emvco_4 import extract_de032
from .scripts.emvco_filter_5 import filter_by_conditions
from .scripts.format_emvco_filter_6 import format_filtered_xml

logger = logging.getLogger(__name__)

def clear_previous_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'emvco_logs')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename in ["bm32_config.json"]:  # Skip important files
                continue
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")

def index(request):
    clear_previous_files()
    return render(request, 'emvco_logs/index.html')

@csrf_exempt    
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

            # Step 1: Split the uploaded XML
            split_file(save_path)

            # Step 2: Adjust unclosed OnlineMessage elements
            fix_unclosed_online_messages(save_path)

            # Step 3: Prepend and append header/footer
            adjust_elements(save_path)

            # Step 4: Extract DE032 summary
            extract_de032(save_path)

            return JsonResponse({'status': 'success', 'filename': uploaded_file.name})
        
        except Exception as e:
            logger.error(f"Error processing file: {e}")
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

            # Filter based on selected conditions
            zip_file_path = filter_by_conditions(json_path, conditions)

            # Format all generated filtered files
            output_base_path = os.path.dirname(json_path)
            uploaded_filename = None

            for filename in os.listdir(output_base_path):
                if filename.endswith('.xml') and '_filtered_' in filename:
                    uploaded_filename = filename.split('_filtered_')[0] + '.xml'
                    break

            if uploaded_filename:
                original_file_path = os.path.join(output_base_path, uploaded_filename)
                for condition in conditions:
                    filtered_file_path = os.path.join(
                        output_base_path,
                        f"{os.path.splitext(uploaded_filename)[0]}_filtered_{condition}.xml"
                    )
                    if os.path.exists(filtered_file_path):
                        format_filtered_xml(filtered_file_path, original_file_path)

            zip_filename = os.path.basename(zip_file_path)
            return FileResponse(open(zip_file_path, 'rb'), as_attachment=True, filename=zip_filename)

        except Exception as e:
            logger.error(f"Error downloading filtered data: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)
