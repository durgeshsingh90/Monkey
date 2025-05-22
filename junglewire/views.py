import os
import json
from django.conf import settings
from django.shortcuts import render
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def index(request):
    testcase_dir = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')
    os.makedirs(testcase_dir, exist_ok=True)

    filenames = [
        f.replace('.json', '')
        for f in os.listdir(testcase_dir)
        if f.endswith('.json')
    ]

    return render(request, 'junglewire/index.html', {
        'json_files': filenames
    })


def admin(request):
    return render(request, 'junglewire/admin.html')

@csrf_exempt
def api_schedule(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        # Example: log or queue the schedule task
        print("Schedule requested:", payload)
        return JsonResponse({'message': 'Task scheduled!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def save_testcases_api(request):
    if request.method == 'POST':
        try:
            print("✅ Backend received save request")
            data = json.loads(request.body)
            print("✅ Data content:", data)

            json_path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcases.json')
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print("❌ Error saving test cases:", e)
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def load_testcase_file(request, name):
    try:
        path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase', f'{name}.json')
        if not os.path.exists(path):
            return JsonResponse({'error': 'File not found'}, status=404)

        with open(path, 'r') as f:
            data = json.load(f)

        return JsonResponse(data, safe=False)  # list of test cases
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
