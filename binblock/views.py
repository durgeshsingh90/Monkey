import os
import shutil
import json
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse

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

    return render(request, 'binblock/index.html', {'databases': databases})

def get_content(request):
    content_file_path = os.path.join(settings.MEDIA_ROOT, 'binblock', 'block_content.json')
    if os.path.exists(content_file_path):
        with open(content_file_path, 'r') as f:
            content = json.load(f)
    else:
        content = {}
    return JsonResponse({'content': content})
