import os
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .read_logs import read_and_process_uploaded_log
from .compare import run_comparison_from_web



def index(request):
    return render(request, 'validate_testcases/index.html')

@csrf_exempt
def upload_and_compare(request):
    if request.method == 'POST' and request.FILES.get('log') and request.FILES.get('excel'):
        log_file = request.FILES['log']
        excel_file = request.FILES['excel']

        os.makedirs("media/validate_testcases", exist_ok=True)

        log_path = "media/validate_testcases/uploaded_log.log"
        excel_path = "media/validate_testcases/uploaded_excel.xlsx"
        log_json_path = "media/validate_testcases/grouped_rrn_logs.json"
        comparison_output_path = "media/validate_testcases/comparison_result.log"

        # Save uploaded log
        with open(log_path, 'wb+') as f:
            for chunk in log_file.chunks():
                f.write(chunk)

        # Save uploaded Excel
        with open(excel_path, 'wb+') as f:
            for chunk in excel_file.chunks():
                f.write(chunk)

        # Step 1: Parse log using read_logs.py
        try:
            read_and_process_uploaded_log(log_path)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Log parsing failed: {str(e)}'}, status=500)

        # Step 2: Show how pandas reads Excel
        try:
            dfs = pd.read_excel(excel_path, sheet_name=None)
            excel_preview = ""
            for sheet, df in dfs.items():
                excel_preview += f"\n--- Sheet: {sheet} ---\n"
                excel_preview += df.to_string(index=False)
                excel_preview += "\n"
        except Exception as e:
            excel_preview = f"❌ Failed to read Excel: {e}"

        # Step 3: Run comparison using compare.py
        try:
            result_path = run_comparison_from_web(excel_path, log_json_path, comparison_output_path)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Comparison failed: {str(e)}'}, status=500)

        # Read comparison result
        comparison_preview = ""
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as f:
                comparison_preview = f.read()

        return JsonResponse({
            'status': 'success',
            'excel_preview': excel_preview,
            'comparison_preview': comparison_preview,
            'download_log': '/media/validate_testcases/comparison_result.log'
        })

    return JsonResponse({'status': 'error', 'message': 'Both Excel and Log files are required.'}, status=400)
