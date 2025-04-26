import os
import json
import logging
import time

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Import your new XLOG processing scripts
from .scripts.breakxlog_1 import process_file as split_file
from .scripts.adjustxlog_2 import adjust_file as fix_unclosed_online_messages
from .scripts.adjustelements_3 import adjust_elements
from .scripts.unique_de32_xlog_4 import extract_de032
from .scripts.xlog_filter_5 import filter_by_conditions

logger = logging.getLogger(__name__)

def clear_previous_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'xlog_mastercard')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if filename in ["bm32_config.json"]:
                continue
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting {file_path}: {e}")

def index(request):
    logger.info("Rendering XLOG index page")
    clear_previous_files()
    return render(request, 'xlog_mastercard/index.html')

@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            logger.info("File upload request received for XLOG")
            clear_previous_files()

            uploaded_file = request.FILES['file']
            save_path = os.path.join(settings.MEDIA_ROOT, 'xlog_mastercard', uploaded_file.name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            logger.info(f"File saved to {save_path}")

            start_time = time.time()

            # Step 1: Split the uploaded XLOG
            split_file(save_path)
            logger.info("Step 1: XLOG split")

            # Step 2: Adjust unclosed OnlineMessage elements
            fix_unclosed_online_messages(save_path)
            logger.info("Step 2: Unclosed OnlineMessage elements adjusted")

            # Step 3: Prepend and append header/footer
            adjust_elements(save_path)
            logger.info("Step 3: Header and footer adjusted")

            # Step 4: Extract DE032 summary
            extract_de032(save_path)
            logger.info("Step 4: DE032 summary extracted")

            end_time = time.time()
            processing_time = end_time - start_time
            hours, remainder = divmod(processing_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_processing_time = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

            summary_file_path = os.path.join(os.path.dirname(save_path), "unique_bm32_xlog.json")
            with open(summary_file_path, 'r') as summary_file:
                summary_data = json.load(summary_file)
            logger.info("Summary data loaded")

            return JsonResponse({
                'status': 'success',
                'filename': uploaded_file.name,
                'processing_time': formatted_processing_time,
                'start_time': summary_data.get('start_time'),
                'end_time': summary_data.get('end_time'),
                'time_difference': summary_data.get('time_difference')
            })

        except Exception as e:
            logger.error(f"Error processing XLOG file: {e}")
            return JsonResponse({'status': 'error', 'error': str(e)}, status=500)

    logger.warning("Invalid request method or missing file")
    return JsonResponse({'status': 'error', 'error': 'Invalid request'}, status=400)

@csrf_exempt
def download_filtered_by_de032(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conditions = data.get('conditions', [])
            filename = data.get('filename')

            if not conditions or not filename:
                return JsonResponse({'status': 'error', 'error': 'Missing conditions or filename'})

            uploaded_file_path = os.path.join(settings.MEDIA_ROOT, 'xlog_mastercard', filename)
            zip_file_path = filter_by_conditions(conditions, uploaded_file_path)

            if zip_file_path and os.path.exists(zip_file_path):
                relative_zip_path = f"xlog_mastercard/{os.path.basename(zip_file_path)}"
                return JsonResponse({
                    'status': 'success',
                    'filtered_file': relative_zip_path
                })
            else:
                return JsonResponse({'status': 'error', 'error': 'Filtered ZIP not created.'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'error': f'Error: {str(e)}'})

    return JsonResponse({'status': 'error', 'error': 'Invalid request'})
