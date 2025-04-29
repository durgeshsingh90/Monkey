from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import os
import json

# Import BASE_DIR from settings
BASE_DIR = settings.BASE_DIR
JSON_PATH = os.path.join(BASE_DIR, 'media','certifications', 'testcases.json')

def certifications_index(request):
    return render(request, 'certifications/index.html')

def get_structure(request):
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    return JsonResponse(data['protocol']['requests'])

def get_testcase_data(request):
    group = request.GET.get('group')
    user = request.GET.get('user')
    testcase = request.GET.get('testcase')

    try:
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)
        result = data['protocol']['requests'][group][user][testcase]['rq_msgs']
        return JsonResponse(result)
    except KeyError:
        return JsonResponse({'error': 'Test case not found'}, status=404)
