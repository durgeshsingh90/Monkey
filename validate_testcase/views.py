import os
import re
import pandas as pd
from django.conf import settings
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

def is_iso8583_header(cell):
    pattern = r"(DE|BM)\s?0?\d{1,3}(?:\.\d{1,3})?(?:\s?\([^)]+\))?"
    return bool(re.fullmatch(pattern.strip(), str(cell).strip()))

def find_valid_header_row(df):
    for idx, row in df.iterrows():
        count = sum(1 for cell in row if is_iso8583_header(cell))
        if count >= 5:
            return idx
    return None

def clear_uploaded_files():
    folder = os.path.join(settings.MEDIA_ROOT, 'validate_testcase')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def upload_excel(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'validate_testcase'))
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)

        df = pd.read_excel(file_path, header=None)
        header_row_idx = find_valid_header_row(df)

        if header_row_idx is not None:
            df.columns = df.iloc[header_row_idx]
            df = df[(header_row_idx + 1):].reset_index(drop=True)
        else:
            df = pd.DataFrame({"Error": ["No valid ISO8583 header row found."]})

        return render(request, 'validate_testcase/index.html', {'df': df})

    # For GET: clean old uploaded files and show fresh form
    clear_uploaded_files()
    return render(request, 'validate_testcase/index.html', {'df': None})
