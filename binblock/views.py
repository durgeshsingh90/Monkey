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
                        try:
                            line = json.dumps(row, cls=CustomJSONEncoder, indent=2)
                            json_file.write(line)
                            if i < len(result) - 1:
                                json_file.write(',\n')
                        except Exception as e:
                            print(f"❌ Failed to serialize row {i}: {e}")
                            print(f"Offending row: {row}")
                            raise  # Optional: re-raise or skip
                    json_file.write('\n]')


                if result:
                    first_entry = result[0].copy()
                    first_entry['LOWBIN'] = ''
                    first_entry['HIGHBIN'] = ''
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

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import os
import json
from django.conf import settings
from .utils import split_bin_ranges
from runquery.db_connection import CustomJSONEncoder

@csrf_exempt
@require_POST
def generate_output(request):
    try:
        payload = json.loads(request.body)
        bin_list = payload.get('bin_list', [])
        edited_bin = payload.get('edited_bin', {})

        # Load original data from DB or upload file
        # ❗ If it doesn’t exist, create an empty list instead of failing
        input_path = os.path.join(settings.MEDIA_ROOT, 'binblock', 'SHCEXTBINDB.json')
        if os.path.exists(input_path):
            with open(input_path, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
        else:
            print("⚠️ SHCEXTBINDB.json not found. Creating blank input.")
            original_data = []

        # Process into updated structure
        updated_data = split_bin_ranges(original_data, bin_list, edited_bin)

        binblock_path = os.path.join(settings.MEDIA_ROOT, 'binblock')
        os.makedirs(binblock_path, exist_ok=True)

        # ✅ Always (re)create generated_output.json
        output_json_path = os.path.join(binblock_path, 'generated_output.json')
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, indent=2, cls=CustomJSONEncoder)

        # ✅ Always (re)create generated_output.sql
        output_sql_path = os.path.join(binblock_path, 'generated_output.sql')
        with open(output_sql_path, 'w', encoding='utf-8') as f:
            for row in updated_data:
                columns = ', '.join(row.keys())
                values = ', '.join([
                    f"'{str(v).replace('\'', '\'\'')}'" if v is not None else 'NULL'
                    for v in row.values()
                ])
                f.write(f"INSERT INTO SHCEXTBINDB ({columns}) VALUES ({values});\n")

        return JsonResponse({
            'status': 'success',
            'generated_count': len(updated_data)
        })

    except Exception as e:
        print(f"❌ generate_output error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
