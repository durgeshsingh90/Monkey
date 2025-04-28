import pandas as pd
import os

def excel_to_text(excel_path):
    try:
        # Get the filename without extension
        filename = os.path.splitext(os.path.basename(excel_path))[0]
        text_path = f"{filename}_output.txt"

        # Read the Excel file
        df = pd.read_excel(excel_path)

        # Open the text file for writing
        with open(text_path, 'w', encoding='utf-8') as f:
            # Optional: Write column headers first
            f.write('\t'.join(str(col) for col in df.columns) + '\n')

            # Write each row to the text file
            for index, row in df.iterrows():
                line = '\t'.join(str(value) for value in row)
                f.write(line + '\n')

        print(f"Successfully written to {text_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Provide your Excel file path
    excel_file = 'input.xlsx'
    excel_to_text(excel_file)
