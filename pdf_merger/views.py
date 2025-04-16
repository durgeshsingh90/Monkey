import os
import shutil
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from PyPDF2 import PdfMerger

# Define media path
PDF_FOLDER = os.path.join(settings.MEDIA_ROOT, 'pdf_merger')

import os
import shutil
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from PyPDF2 import PdfMerger

PDF_FOLDER = os.path.join(settings.MEDIA_ROOT, 'pdf_merger')

def merge_pdfs(request):
    if request.method == 'GET':
        if os.path.exists(PDF_FOLDER):
            shutil.rmtree(PDF_FOLDER)
        os.makedirs(PDF_FOLDER, exist_ok=True)
        return render(request, 'pdf_merger/merge_pdfs.html')

    if request.method == 'POST':
        file_order = request.POST.get('file_order', '').split(',')
        if not file_order or file_order == ['']:
            return render(request, 'pdf_merger/merge_pdfs.html', {
                'error': 'No files uploaded.'
            })

        merger = PdfMerger()

        original_filename = None  # We'll extract the base name from the first file
        for i, filename in enumerate(file_order):
            file_path = os.path.join(PDF_FOLDER, filename)
            if os.path.exists(file_path):
                if i == 0:
                    original_filename = os.path.splitext(filename)[0]  # remove extension
                merger.append(file_path)

        if not original_filename:
            original_filename = "merged_file"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_filename = f"{original_filename}_merged_{timestamp}.pdf"
        merged_path = os.path.join(PDF_FOLDER, merged_filename)

        merger.write(merged_path)
        merger.close()

        return FileResponse(open(merged_path, 'rb'), as_attachment=True, filename=merged_filename)


@csrf_exempt
def upload_pdf_ajax(request):
    if request.method == 'POST' and request.FILES.get('file'):
        os.makedirs(PDF_FOLDER, exist_ok=True)

        uploaded_file = request.FILES['file']
        filename = uploaded_file.name

        save_path = os.path.join(PDF_FOLDER, filename)
        with open(save_path, 'wb+') as dest:
            for chunk in uploaded_file.chunks():
                dest.write(chunk)

        return JsonResponse({'status': 'success', 'filename': filename})

    return JsonResponse({'status': 'error'}, status=400)
