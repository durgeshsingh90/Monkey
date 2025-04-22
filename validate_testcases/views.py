import os
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .read_logs import read_and_process_uploaded_log
from .compare import run_comparison_from_web

def index(request):
    folder = 'media/validate_testcases'
    if os.path.exists(folder):
        for f in os.listdir(folder):
            os.unlink(os.path.join(folder, f))
    return render(request, 'validate_testcases/index.html')

@csrf_exempt
def upload_and_compare(request):
    if request.method == 'POST' and request.FILES.get('excel') and request.FILES.get('log'):
        log_file = request.FILES['log']
        excel_file = request.FILES['excel']

        os.makedirs("media/validate_testcases", exist_ok=True)
        log_path = "media/validate_testcases/uploaded_log.log"
        excel_path = "media/validate_testcases/uploaded_excel.xlsx"
        log_json_path = "media/validate_testcases/grouped_rrn_logs.json"
        comparison_log_path = "media/validate_testcases/comparison_result.log"

        with open(log_path, 'wb+') as f:
            for chunk in log_file.chunks():
                f.write(chunk)
        with open(excel_path, 'wb+') as f:
            for chunk in excel_file.chunks():
                f.write(chunk)

        read_and_process_uploaded_log(log_path)

        styled_dfs, comparison_text = run_comparison_from_web(excel_path, log_json_path, comparison_log_path)

        html_tabs = {}
        for sheet, styled_df in styled_dfs.items():
            def format_val(val): return val['value'] if isinstance(val, dict) else val
            def highlight(val):
                if isinstance(val, dict):
                    if val['match'] is True:
                        return "background-color: #dcfce7;"  # ✅ green
                    elif val['match'] is False:
                        return "background-color: #fee2e2;"  # ❌ red
                    elif val['match'] is None:
                        return ""  # no background
                return ""
                
            html = styled_df.style.format(format_val).applymap(highlight).to_html(escape=False)
            html_tabs[sheet] = html

        return JsonResponse({
            'status': 'success',
            'excel_preview': html_tabs,
            'comparison_preview': comparison_text,
            'download_log': '/media/validate_testcases/comparison_result.log'
        })

    return JsonResponse({'status': 'error', 'message': 'Both files are required'})
