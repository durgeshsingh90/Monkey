import os
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse

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

        # Convert Excel to JSON and save temporarily
        df = pd.read_excel(file_path)
        json_data = df.to_dict(orient='records')

        # Save to JSON file
        with open(os.path.join(UPLOAD_DIR, 'excel_data.json'), 'w') as f:
            json.dump(json_data, f, indent=2)

        return redirect('index')

    return JsonResponse({'error': 'Invalid Excel upload'}, status=400)

def upload_logs(request):
    if request.method == 'POST' and request.FILES.get('log_file'):
        log_file = request.FILES['log_file']
        fs = FileSystemStorage(location=UPLOAD_DIR)
        filename = fs.save(log_file.name, log_file)
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Read and convert logs to JSON (simplified logic — adjust as per your log format)
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        log_json = [{'line': line.strip()} for line in lines]

        # Save to JSON file
        with open(os.path.join(UPLOAD_DIR, 'log_data.json'), 'w') as f:
            json.dump(log_json, f, indent=2)

        return redirect('index')

    return JsonResponse({'error': 'Invalid log upload'}, status=400)
