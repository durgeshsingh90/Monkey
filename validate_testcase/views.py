import re
import pandas as pd
import requests
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

TIMESTAMP_REGEX = r"^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"

def split_log_blocks(log_content):
    """Split log file content into blocks based on timestamp lines."""
    lines = log_content.splitlines()
    blocks = []
    current_block = []

    for line in lines:
        if re.match(TIMESTAMP_REGEX, line):
            if current_block:
                blocks.append("\n".join(current_block))
                current_block = []
        current_block.append(line)

    if current_block:
        blocks.append("\n".join(current_block))

    return blocks


def validate_testcase_view(request):
    headers = []
    table_data = []
    log_content = ""
    parsed_log_results = []

    if request.method == 'POST':
        fs = FileSystemStorage(location='media/validate_testcase')

        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)
        
            # Read all sheets
            excel_data = pd.read_excel(file_path, sheet_name=None)
        
            all_sheets_data = []
            for sheet_name, df in excel_data.items():
                sheet_headers = df.columns.tolist()
                sheet_table = df.fillna("").astype(str).values.tolist()
                all_sheets_data.append({
                    'sheet_name': sheet_name,
                    'headers': sheet_headers,
                    'table_data': sheet_table
                })


        if 'log_file' in request.FILES:
            log_file = request.FILES['log_file']
            filename = fs.save(log_file.name, log_file)
            file_path = fs.path(filename)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()

            # Split log into blocks
            blocks = split_log_blocks(log_content)

            # Send each block to API
            for block in blocks:
                try:
                    response = requests.post(
    'http://localhost:8000/splunkparser/parse/',
                        json={'log_data': block}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        parsed_log_results.append(data.get('result', {'error': 'Empty result'}))
                    else:
                        parsed_log_results.append({'error': f"API error {response.status_code}"})
                except Exception as e:
                    parsed_log_results.append({'error': str(e)})

    return render(request, 'validate_testcase/index.html', {
    'excel_sheets': all_sheets_data,
    'log_content': log_content,
    'parsed_log_results': parsed_log_results,
})
