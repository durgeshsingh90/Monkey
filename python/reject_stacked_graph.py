import json
import pandas as pd
import plotly.express as px
import plotly.offline as pyo

# Path to the JSON file (update accordingly)
json_file_path = r"C:\Users\f94gdos\Downloads\bcmc_reject_count.txt"

# Load JSON data from file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Process the JSON data
processed_data = []
for record in data:
    date = record['TRANSACTION_DATE']
    response_code_with_count = record['RESPONSE_CODE_WITH_COUNT']
    try:
        response_code, count = response_code_with_count.rsplit(': ', 1)
        count = int(count)
    except ValueError:
        continue

    processed_data.append({
        'TRANSACTION_DATE': date,
        'RESPONSE_CODE': response_code,
        'COUNT': count
    })

# Create DataFrame
df = pd.DataFrame(processed_data)

# Convert the 'TRANSACTION_DATE' field to datetime
df['TRANSACTION_DATE'] = pd.to_datetime(df['TRANSACTION_DATE'], format='%d-%b-%Y')

# Group by date and response code, and sum the counts
aggregated_df = df.groupby(['TRANSACTION_DATE', 'RESPONSE_CODE']).sum().reset_index()

# Generate a complete date range
date_range = pd.date_range(start=aggregated_df['TRANSACTION_DATE'].min(), 
                           end=aggregated_df['TRANSACTION_DATE'].max())

# Create a DataFrame with every date and response code combination
grid = pd.MultiIndex.from_product([date_range, aggregated_df['RESPONSE_CODE'].unique()], names=['TRANSACTION_DATE', 'RESPONSE_CODE'])

# Reindex the aggregated DataFrame to have every combination and fill missing values with 0
aggregated_df = aggregated_df.set_index(['TRANSACTION_DATE', 'RESPONSE_CODE']).reindex(grid, fill_value=0).reset_index()

# Create the stacked bar plot with Plotly
fig = px.bar(aggregated_df, x='TRANSACTION_DATE', y='COUNT', color='RESPONSE_CODE', 
             labels={
                 'TRANSACTION_DATE': 'Date',
                 'COUNT': 'Reject Count',
                 'RESPONSE_CODE': 'Response Code'
             },
             title='Reject Count Per Day',
             barmode='stack')

# Update layout for better display
fig.update_layout(
    autosize=False,
    width=1200,
    height=700,
    margin=dict(l=50, r=50, b=100, t=100, pad=4),
    legend=dict(title='Response Codes'),
    xaxis=dict(title='Date', tickangle=-45, tickmode='linear', dtick='D1'), # Set dtick to 'D1' to show every date tick
    yaxis=dict(title='Reject Count')
)

# Show the plot in an offline mode
pyo.plot(fig, filename='reject_count_per_day.html', auto_open=True)
