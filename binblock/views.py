# binblock/views.py

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

    # Clear files in the binblock folder
    clear_binblock_folder()

    if request.method == "POST":
        if 'fileUpload' in request.FILES:
            file = request.FILES['fileUpload']
            if file.name.endswith(('.sql', '.json')):
                binblock_path = os.path.join(settings.MEDIA_ROOT, 'binblock')
                if not os.path.exists(binblock_path):
                    os.makedirs(binblock_path)
                fs = FileSystemStorage(location=binblock_path)
                filename = fs.save(file.name, file)
                return redirect('index')
        elif 'editorContent' in request.POST:
            content = request.POST.get('editorContent', '')
            with open(os.path.join(settings.MEDIA_ROOT, 'binblock', 'block_content.json'), 'w') as f:
                json.dump(content, f)
            return JsonResponse({'status': 'success'})
        elif 'dropdown1' in request.POST:
            query = "SELECT * FROM oasis77.SHCEXTBINDB ORDER BY LOWBIN"
            table_name = "SHCEXTBINDB"
            binblock_path = os.path.join(settings.MEDIA_ROOT, 'binblock')
            if not os.path.exists(binblock_path):
                os.makedirs(binblock_path)
            try:
                result_data = execute_query(query, db_key=request.POST['dropdown1'])
                result = result_data.get('result', [])
                if not result:
                    return JsonResponse({'status': 'error', 'message': 'Query failed or returned no results'})
                json_path = os.path.join(binblock_path, f"{table_name}.json")
                sql_path = os.path.join(binblock_path, f"{table_name}.sql")
                with open(json_path, 'w') as json_file:
                    json.dump(result, json_file, cls=CustomJSONEncoder, indent=2)
                    
                    # Save the first entry to block_content.json
                    if result:
                        first_entry = result[0]
                        block_content_path = os.path.join(binblock_path, 'block_content.json')
                        with open(block_content_path, 'w') as block_content_file:
                            json.dump(first_entry, block_content_file, cls=CustomJSONEncoder, indent=2)

                with open(sql_path, 'w') as sql_file:
                    for row in result:
                        columns = ', '.join(row.keys())
                        values = ', '.join([f"'{v}'" for v in row.values()])
                        sql_file.write(f"INSERT INTO {table_name} ({columns}) VALUES ({values});\n")
                return JsonResponse({'status': 'success', 'message': 'Query executed and files saved'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})

    return render(request, 'binblock/index.html', {'databases': databases})

def get_content(request):
    content_file_path = os.path.join(settings.MEDIA_ROOT, 'binblock', 'block_content.json')
    if os.path.exists(content_file_path):
        with open(content_file_path, 'r') as f:
            content = json.load(f)
    else:
        content = {}
    return JsonResponse({'content': content})
