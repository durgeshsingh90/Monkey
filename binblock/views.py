import os
import shutil
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from runquery.db_connection import execute_query, CustomJSONEncoder

def clear_binblock_folder():
    binblock_path = os.path.join(settings.MEDIA_ROOT, 'binblock')
    if os.path.exists(binblock_path):
        for filename in os.listdir(binblock_path):
            file_path = os.path.join(binblock_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def index(request):
    databases = [db for db in settings.DATABASES.keys() if db != 'default']

    if request.method == "GET":
        clear_binblock_folder()

    if request.method == "POST":
        binblock_path = os.path.join(settings.MEDIA_ROOT, 'binblock')
        if not os.path.exists(binblock_path):
            os.makedirs(binblock_path)

        if 'fileUpload' in request.FILES:
            file = request.FILES['fileUpload']
            if file.name.endswith(('.sql', '.json')):
                fs = FileSystemStorage(location=binblock_path)
                fs.save(file.name, file)

        elif 'editorContent' in request.POST:
            content = request.POST.get('editorContent', '')
            with open(os.path.join(binblock_path, 'block_content.json'), 'w') as f:
                json.dump(content, f, indent=2)

        elif 'dropdown1' in request.POST:
            query = "SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN"
            table_name = "SHCEXTBINDB"

            try:
                result_data = execute_query(query, db_key=request.POST['dropdown1'], use_session=False)
                result = result_data.get('result', [])

                json_path = os.path.join(binblock_path, f"{table_name}.json")
                block_content_path = os.path.join(binblock_path, 'block_content.json')

                with open(json_path, 'w', encoding='utf-8') as json_file:
                    json_file.write('[\n')
                    for i, row in enumerate(result):
                        line = json.dumps(row, cls=CustomJSONEncoder, indent=2)
                        json_file.write(line)
                        if i < len(result) - 1:
                            json_file.write(',\n')
                    json_file.write('\n]')

                if result:
                    first_entry = result[0].copy()
                    first_entry.pop('LOWBIN', None)
                    first_entry.pop('HIGHBIN', None)
                    with open(block_content_path, 'w', encoding='utf-8') as block_file:
                        json.dump(first_entry, block_file, indent=2, cls=CustomJSONEncoder)

            except Exception as e:
                print(f'Error executing query or handling files: {e}')
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

    return render(request, 'binblock/index.html', {'databases': databases})

def get_content(request):
    content_file_path = os.path.join(settings.MEDIA_ROOT, 'binblock', 'block_content.json')
    if os.path.exists(content_file_path):
        with open(content_file_path, 'r') as f:
            content = json.load(f)
    else:
        content = {}
    return JsonResponse({'content': content})
