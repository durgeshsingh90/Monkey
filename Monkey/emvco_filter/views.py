from django.shortcuts import render
from django.http import JsonResponse
import os
from django.conf import settings
from .scripts.formatxml import format_xml
from datetime import datetime

def index(request):
    return render(request, 'emvco_filter/index.html')


def format_xml_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('xmlFile')
        gateway = request.POST.get('gateway')

        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded!"}, status=400)

        # Create app upload folder if not exist
        app_folder = os.path.join(settings.MEDIA_ROOT, 'emvco_filter')
        os.makedirs(app_folder, exist_ok=True)

        # Save original file
        raw_file_path = os.path.join(app_folder, f'original_{uploaded_file.name}')
        with open(raw_file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Generate datetime suffix
        now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

        # Extract name and extension from uploaded file
        base_name, ext = os.path.splitext(uploaded_file.name)

        # Create cleaned formatted filename with timestamp
        cleaned_filename = f'{base_name}_formatted_{now}{ext}'
        cleaned_file_path = os.path.join(app_folder, cleaned_filename)

        # Copy raw to cleaned
        with open(raw_file_path, 'rb') as original, open(cleaned_file_path, 'wb') as cleaned:
            cleaned.write(original.read())

        # Format the cleaned file
        format_xml(cleaned_file_path)

        # Return cleaned file URL
        file_url_cleaned = f"{settings.MEDIA_URL}emvco_filter/{cleaned_filename}"
        return JsonResponse({"download_link": file_url_cleaned})

    return JsonResponse({"error": "Invalid request"}, status=405)

import os
import json
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# ✅ Correct path to your settings.json
SETTINGS_JSON_PATH = os.path.join(
    settings.BASE_DIR, 'emvco_filter', 'static', 'emvco_filter', 'settings.json'
)

def settings_editor(request):
    return render(request, 'emvco_filter/settings.html')

def get_settings_json(request):
    try:
        with open(SETTINGS_JSON_PATH, 'r') as f:
            data = json.load(f)
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': f'Failed to load settings.json: {str(e)}'}, status=500)

@csrf_exempt
def save_settings_json(request):
    if request.method == 'POST':
        try:
            new_data = json.loads(request.body)
            with open(SETTINGS_JSON_PATH, 'w') as f:
                json.dump(new_data, f, indent=2)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def get_settings_list(request):
    try:
        with open(SETTINGS_JSON_PATH, 'r') as f:
            data = json.load(f)
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)