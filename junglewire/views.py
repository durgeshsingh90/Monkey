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
