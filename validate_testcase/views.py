import re
import pandas as pd
import requests
import logging
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)
TIMESTAMP_REGEX = r"^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}"

def split_log_blocks(log_content):
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

def normalize_header(header):
    header = header.strip().upper().replace(" ", "")
    if header.startswith("BM"):
        header = header.replace("BM", "DE")
    if header.startswith("DE") and len(header) == 4:
        header = header[:2] + header[2:].zfill(3)  # DE35 → DE035
    return header

def validate_testcase_view(request):
    excel_sheets = []
    parsed_log_results = []
    comparison_results = []

    if request.method == 'POST':
        fs = FileSystemStorage(location='media/validate_testcase')

        # ✅ Handle Excel
        if 'excel_file' in request.FILES:
            excel_file = request.FILES['excel_file']
            logger.info(f"Excel file uploaded: {excel_file.name}")
            filename = fs.save(excel_file.name, excel_file)
            file_path = fs.path(filename)

            excel_data = pd.read_excel(file_path, sheet_name=None, header=None)

            for sheet_name, df in excel_data.items():
                df = df.fillna("").astype(str)
                header_row_index = None

                for i, row in df.iterrows():
                    de_like_count = sum(
                        1 for val in row.values
                        if re.match(r'^(DE|BM)?\s*\d{1,3}$', val.strip().upper())
                    )
                    if de_like_count >= 5:
                        header_row_index = i
                        break

                if header_row_index is None:
                    logger.warning(f"No valid header row found in sheet: {sheet_name}")
                    continue

                raw_headers = df.iloc[header_row_index].tolist()
                headers = [normalize_header(col) for col in raw_headers]

                data_rows = df.iloc[header_row_index + 1:].values.tolist()
                sheet_dict_rows = [dict(zip(headers, row)) for row in data_rows]

                excel_sheets.append({
                    'sheet_name': sheet_name,
                    'headers': headers,
                    'table_data': data_rows,
                    'dict_rows': sheet_dict_rows,
                })

                logger.info(f"Parsed sheet '{sheet_name}' with header row {header_row_index}, rows: {len(data_rows)}")

        # ✅ Handle log and parse using SplunkParser
        if 'log_file' in request.FILES:
            log_file = request.FILES['log_file']
            logger.info(f"Log file uploaded: {log_file.name}")
            file_path = fs.save(log_file.name, log_file)
            file_path = fs.path(file_path)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                log_content = f.read()

            blocks = split_log_blocks(log_content)
            logger.info(f"Total log blocks identified: {len(blocks)}")

            for idx, block in enumerate(blocks):
                try:
                    response = requests.post('http://localhost:8000/splunkparser/parse/', json={'log_data': block})
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            parsed_log_results.append(result["result"])
                            logger.debug(f"Block {idx + 1} parsed successfully.")
                        else:
                            logger.warning(f"Block {idx + 1} returned error: {result}")
                    else:
                        logger.error(f"Block {idx + 1} failed with HTTP {response.status_code}")
                except Exception as e:
                    logger.exception(f"Error while parsing block {idx + 1}: {e}")
                    parsed_log_results.append({'error': str(e)})

        logger.info(f"Total parsed log messages: {len(parsed_log_results)}")

        # ✅ Compare logs with test cases
        for parsed in parsed_log_results:
            log_de = parsed.get("data_elements", {})
            log_rrn = log_de.get("DE037", "")
            log_mti = str(parsed.get("mti", ""))
            log_proc_code = log_de.get("DE003", "")
            log_amount = str(log_de.get("DE004", ""))

            logger.debug(f"Evaluating log with RRN={log_rrn}, MTI={log_mti}, DE003={log_proc_code}, DE004={log_amount}")

            best_match = None
            potential_matches = []

            for sheet in excel_sheets:
                for row in sheet["dict_rows"]:
                    excel_rrn = row.get("DE037", "") or row.get("RRN", "")
                    if excel_rrn == log_rrn:
                        potential_matches.append(row)

            logger.debug(f"Found {len(potential_matches)} potential matches for RRN {log_rrn}")

            for row in potential_matches:
                if log_mti and row.get("MTI", "") != log_mti:
                    continue
                if log_proc_code and row.get("DE003", "") != log_proc_code:
                    continue
                if log_amount and row.get("DE004", "") != log_amount:
                    continue
                best_match = row
                logger.debug("Best match found using MTI + DE003 + DE004 filters")
                break

            if not best_match and potential_matches:
                best_match = potential_matches[0]
                logger.debug("Fallback: using first match from RRN candidates")

            if best_match:
                differences = {}
                for key, val in best_match.items():
                    if not key.upper().startswith("DE") and not key.upper().startswith("BM"):
                        continue
                    de = key.split()[0].replace("BM", "DE").replace(" ", "").upper()
                    if len(de) == 4:  # e.g., DE35
                        de = de[:2] + de[2:].zfill(3)  # DE035
                    expected = val.strip()
                    actual = str(log_de.get(de, "")).strip()

                    if expected and expected != "Client-defined" and expected != actual:
                        differences[de] = {
                            "expected": expected,
                            "actual": actual
                        }
                        logger.debug(f"Mismatch: {de} → Expected: {expected}, Actual: {actual}")

                comparison_results.append({
                    "rrn": log_rrn,
                    "mti": log_mti,
                    "differences": differences,
                    "test_case_row": best_match
                })
            else:
                logger.warning(f"No Excel match found for RRN: {log_rrn}")

    return render(request, 'validate_testcase/index.html', {
        'excel_sheets': excel_sheets,
        'parsed_log_results': parsed_log_results,
        'comparison_results': comparison_results,
    })
