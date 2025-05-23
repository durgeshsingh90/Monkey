import os
import json
import logging
from django.conf import settings
from django.shortcuts import render
from django.apps import apps
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# Logger setup
logger = logging.getLogger(__name__)

def index(request):
    testcase_dir = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')
    os.makedirs(testcase_dir, exist_ok=True)

    filenames = [
        f.replace('.json', '')
        for f in os.listdir(testcase_dir)
        if f.endswith('.json')
    ]

    logger.info("Loaded index page with %d JSON files.", len(filenames))
    return render(request, 'junglewire/index.html', {
        'json_files': filenames
    })


def admin(request):
    return render(request, 'junglewire/admin.html')


@csrf_exempt
def api_schedule(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        logger.info(" Schedule requested: %s", json.dumps(payload, indent=2))
        return JsonResponse({'message': 'Task scheduled!'})
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def save_testcases_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info(" Save request received:\n%s", json.dumps(data, indent=2))

            json_path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcases.json')
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(" Test cases saved to: %s", json_path)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            logger.exception(" Error saving test cases")
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def load_testcase_file(request, name):
    try:
        path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase', f'{name}.json')
        if not os.path.exists(path):
            logger.warning(" File not found: %s", path)
            return JsonResponse({'error': 'File not found'}, status=404)

        with open(path, 'r') as f:
            data = json.load(f)

        logger.info(" Loaded test case file: %s", name)
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.exception(" Error loading test case file")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def delete_testcases(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    try:
        data = json.loads(request.body)
        to_delete = data.get('to_delete', {})
        logger.info("Received delete request:\n%s", json.dumps(to_delete, indent=2))

        base_dir = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')

        for filename, roots in to_delete.items():
            json_path = os.path.join(base_dir, f"{filename}.json")  # <-- FIXED
            logger.info("Processing file: %s", json_path)

            if not os.path.exists(json_path):
                logger.warning(" File not found: %s", json_path)
                continue

            with open(json_path, 'r') as f:
                try:
                    content = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error("JSON decode error in %s: %s", filename, str(e))
                    continue

            modified = False

            # Case 1: Single-root file
            if 'testcases' in content and 'name' in content:
                suite_name = content['name']
                ids_to_remove = roots.get(suite_name, [])
                logger.info(" Single-suite: %s — Removing %s", suite_name, ids_to_remove)

                before = len(content['testcases'])
                content['testcases'] = [
                    tc for tc in content['testcases']
                    if tc.get('id') not in ids_to_remove
                ]
                after = len(content['testcases'])

                if after < before:
                    modified = True
                    logger.info("Removed %d test case(s)", before - after)

                if not content['testcases']:
                    os.remove(json_path)
                    logger.info("Deleted file (empty after removal): %s", filename)
                    continue

            else:
                # Case 2: Multi-root
                for root_name, ids_to_remove in roots.items():
                    if root_name in content and 'testcases' in content[root_name]:
                        logger.info("🔸 Multi-suite: %s — Removing %s", root_name, ids_to_remove)

                        before = len(content[root_name]['testcases'])
                        content[root_name]['testcases'] = [
                            tc for tc in content[root_name]['testcases']
                            if tc.get('id') not in ids_to_remove
                        ]
                        after = len(content[root_name]['testcases'])

                        if after < before:
                            modified = True
                            logger.info(" Removed %d test case(s) from %s", before - after, root_name)

                        if not content[root_name]['testcases']:
                            del content[root_name]
                            logger.info("Removed empty root: %s", root_name)

                if not content:
                    os.remove(json_path)
                    logger.info("Deleted file (all roots removed): %s", filename)
                    continue

            if modified:
                with open(json_path, 'w') as f:
                    json.dump(content, f, indent=2)
                    logger.info("Saved updated file: %s", filename)
            else:
                logger.info("ℹNo changes made to file: %s", filename)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.exception("Unexpected error during delete operation")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def create_testcase_file(request):
    if request.method == 'POST':
        try:
            filename = request.POST.get('filename', '').strip()
            rootname = request.POST.get('rootname', '').strip()
            if not filename or not filename.endswith('.json') or not rootname:
                return JsonResponse({'error': 'Invalid input'}, status=400)

            base_path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')
            file_path = os.path.join(base_path, filename)

            if os.path.exists(file_path):
                return JsonResponse({'error': 'File already exists'}, status=409)

            with open(file_path, 'w') as f:
                json.dump({
                    "name": rootname,
                    "description": "",
                    "testcases": []
                }, f, indent=2)

            return JsonResponse({'status': 'created'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def upload_testcase_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            file = request.FILES['file']
            filename = file.name
            base_path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')
            file_path = os.path.join(base_path, filename)

            if os.path.exists(file_path) and request.POST.get('overwrite') != 'true':
                return JsonResponse({'error': 'exists'}, status=409)

            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)

            return JsonResponse({'status': 'uploaded'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid upload'}, status=400)

from django.http import JsonResponse
import os

def list_testcase_files(request):
    base_dir = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase')
    files = [
        f.replace('.json', '')
        for f in os.listdir(base_dir)
        if f.endswith('.json')
    ]
    return JsonResponse(files, safe=False)

@csrf_exempt
def save_testcases_file(request, filename):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            path = os.path.join(settings.MEDIA_ROOT, 'junglewire', 'testcase', f'{filename}.json')
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
