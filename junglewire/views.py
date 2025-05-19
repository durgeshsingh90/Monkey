import os
import json
from django.conf import settings
from django.shortcuts import render
from django.apps import apps

def index(request):
    media_dir = os.path.join(settings.MEDIA_ROOT, 'junglewire')
    os.makedirs(media_dir, exist_ok=True)
    json_path = os.path.join(media_dir, 'testcases.json')

    if not os.path.exists(json_path):
        # Read from sample file
        app_path = apps.get_app_config('junglewire').path
        sample_path = os.path.join(app_path, 'samples', 'testcases_sample.json')
        with open(sample_path, 'r') as sample_file:
            sample_data = json.load(sample_file)
        with open(json_path, 'w') as f:
            json.dump(sample_data, f, indent=2)

    with open(json_path, 'r') as f:
        testcases = json.load(f)

    return render(request, 'junglewire/index.html', {'testcases': testcases})

def admin(request):
    return render(request, 'junglewire/admin.html')
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def api_schedule(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        # Example: log or queue the schedule task
        print("Schedule requested:", payload)
        return JsonResponse({'message': 'Task scheduled!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings

@csrf_exempt
def save_testcases_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            json_path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcases.json')
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print('Save failed:', e)
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)
