import pandas as pd
import json
import os
import plotly.express as px
import plotly.offline as pyo

# Function to read JSON data from a file
def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# File path to your JSON data
file_path = r"C:\Users\f94gdos\Downloads\dr_external_bcmc_reject_count.txt"

# Read JSON data from the file
data = read_json_file(file_path)

# Create DataFrame from JSON data
df = pd.DataFrame(data)

# Print DataFrame columns to debug
print("DataFrame columns:", df.columns)

# Print sample data to debug
print("DataFrame sample data:")
print(df.head())

# Correct column names based on debug output
expected_index = 'DESTINATION_RESPONSE_CODE_RSP'
expected_columns = 'TRANSACTION_DATE'
expected_values = 'RESPONSE_CODE_COUNT'

# Pivot DataFrame to get the desired format, if columns match
if expected_index in df.columns and expected_columns in df.columns and expected_values in df.columns:
    pivot_df = df.pivot(index=expected_index, columns=expected_columns, values=expected_values)

    # Reset index to get expected_index as a column
    pivot_df.reset_index(inplace=True)

    # Print the DataFrame
    print("Pivoted DataFrame:")
    print(pivot_df)

    # Construct the output file path with the same location and base name but different extension
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(os.path.dirname(file_path), f"{base_name}.xlsx")

    # Save to an Excel file
    pivot_df.to_excel(output_file, index=False)

    # Prepare data for plotting
    melted_df = pivot_df.melt(id_vars=[expected_index], var_name='TRANSACTION_DATE', value_name='RESPONSE_CODE_COUNT')

    # Generate interactive plot with plotly
    fig = px.bar(melted_df, x=expected_index, y='RESPONSE_CODE_COUNT', color='TRANSACTION_DATE',
                 title='Response Code Counts by Date',
                 labels={'RESPONSE_CODE_COUNT': 'Response Code Count', 'DESTINATION_RESPONSE_CODE_RSP': 'Response Code'},
                 barmode='group')

    # Save the plot as an HTML file
    plot_file = os.path.join(os.path.dirname(file_path), f"{base_name}.html")
    pyo.plot(fig, filename=plot_file, auto_open=False)

    print(f"Data has been successfully exported to {output_file}")
    print(f"Graph has been successfully saved to {plot_file}")

else:
    print(f"One or more expected columns are missing in the DataFrame: {df.columns}")



# Query i ran:
# SELECT 
#   TO_CHAR(HOST_START_TIME, 'DD-MON-YYYY') AS transaction_date,
#   INTERNAL_RESPONSE_CODE_RSP,
#   COUNT(INTERNAL_RESPONSE_CODE_RSP) AS response_code_count
# --  destination_response_code_rsp,
#   --COUNT(destination_response_code_rsp) AS response_code_count
# FROM 
#   NOVATE.TRANSACTION_LOG
# WHERE 
#   HOST_START_TIME BETWEEN TO_DATE('10-May-2025 00:01:00', 'DD-MON-YYYY HH24:MI:SS') 
#   AND TO_DATE('19-May-2025 23:59:00', 'DD-MON-YYYY HH24:MI:SS')
#   AND (DESTINATION_KEY IN ('BCMC-BSAU', 'BCMC_BSAD') OR DESTINATION_KEY IS NULL)
#   AND INTERNAL_RESPONSE_CODE_RSP <> 'approved'
# GROUP BY 
#   TO_CHAR(HOST_START_TIME, 'DD-MON-YYYY'),
#   INTERNAL_RESPONSE_CODE_RSP
# --  destination_response_code_rsp
# ORDER BY 
#   transaction_date,
#   response_code_count DESC;
