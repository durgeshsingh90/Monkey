from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import os
from django.conf import settings
import logging

logger = logging.getLogger('splunkparser')

output_file_path = os.path.join(settings.MEDIA_ROOT, 'splunkparser', 'output.json')

@csrf_exempt
def clear_output_file(request):
    if request.method == 'POST':
        try:
            with open(output_file_path, 'w') as f:
                f.write('{}')
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def save_output_file(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            output_data = data.get('output_data', '{}')
            with open(output_file_path, 'w') as f:
                f.write(output_data)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
