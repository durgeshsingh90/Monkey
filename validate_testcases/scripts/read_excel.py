import pandas as pd
import os
import re

def contains_de_or_bm(cell):
    if not isinstance(cell, str):
        return False
    pattern = r'\b(?:DE|BM)[\s\-]?0?\d{1,3}(?:\.\d{1,3})?\b'
    return re.search(pattern, cell, re.IGNORECASE) is not None

def find_custom_header_row(df):
    for idx, row in df.iterrows():
        if any(contains_de_or_bm(str(cell)) for cell in row):
            return idx
    return None

def process_sheet(sheet_name, df):
    header_row_index = find_custom_header_row(df)
    if header_row_index is None:
        return f"--- Sheet: {sheet_name} ---\n❌ No DE/BM header found.\n"

    # Load headered data
    data = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row_index)

    # Build column index line
    col_indices = ["    "] + [f"{i:^15}" for i in range(len(data.columns))]
    header_line = "".join(col_indices)

    # Header names line
    headers = ["Idx "] + [f"{str(col):15.15}" for col in data.columns]
    header_names_line = "".join(headers)

    # Row-wise data
    data_lines = []
    for idx, row in data.iterrows():
        row_line = [f"{idx:<4}"] + [f"{str(val):15.15}" for val in row]
        data_lines.append("".join(row_line))

    result = f"--- Sheet: {sheet_name} ---\n{header_line}\n{header_names_line}\n" + "\n".join(data_lines)
    return result + "\n\n"

def excel_to_text_with_col_row_indices_all_sheets(filepath):
    try:
        sheets = pd.read_excel(filepath, sheet_name=None, header=None)  # All sheets, no headers
        all_output = []

        for sheet_name, raw_df in sheets.items():
            output = process_sheet(sheet_name, raw_df)
            all_output.append(output)

        # Write to output file
        base, ext = os.path.splitext(filepath)
        output_file = f"{base}_output.txt"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(all_output))

        print(f"✅ Output written to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage
if __name__ == "__main__":
    filepath = r"D:\Projects\VSCode\MangoData\VisaAFTTestcase.xlsx"
    excel_to_text_with_col_row_indices_all_sheets(filepath)
