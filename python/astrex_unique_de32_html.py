import time
from bs4 import BeautifulSoup
from collections import Counter
from multiprocessing import Pool
import os

def process_chunk(chunk):
    values = []
    de032_values = []
    
    # Parse the HTML content of the chunk using BeautifulSoup
    soup = BeautifulSoup(chunk, 'html.parser')

    # Extract the text content of all cells with the class "cell7"
    cells = soup.find_all('td', class_='cell7')

    # Extract and clean the values from these cells
    values.extend([cell.get_text(strip=True) for cell in cells])

    # Extract DE032 values only
    for row in soup.find_all('tr'):
        cell1 = row.find('td', class_='cell1norm')
        if cell1 and 'DE032' in cell1.get_text(strip=True):
            cell7 = row.find('td', class_='cell7')
            if cell7:
                de032_values.append(cell7.get_text(strip=True))
    
    return values, de032_values


def split_html_file(filepath, delimiter='<br>'):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
    
    # Split the content by the delimiter
    parts = content.split(delimiter)
    
    # Append the delimiter back to the end of each part except the last one
    parts = [part + delimiter for part in parts[:-1]] + [parts[-1]]
    
    return parts

def main():
    # Start the timer
    start_time = time.time()

    # Path to your HTML file
    html_file_path = r"C:\Users\f94gdos\Desktop\New folder (4)\ID-7121-MasterCard_GCIS_(Standard)_Message_viewer_.html"
    
    # Set the number of parallel processes
    num_processes = os.cpu_count()  # Use the number of CPU cores available

    # Split the HTML file into parts
    parts = split_html_file(html_file_path)
    
    # Create a pool of processes and process each chunk
    with Pool(num_processes) as pool:
        results = pool.map(process_chunk, parts)
    
    values = []
    de032_values = []
    
    # Combine the results from all processes
    for result in results:
        values.extend(result[0])
        de032_values.extend(result[1])

    # Get the count of unique values using Counter
    value_counts = Counter(values)
    unique_values_count = len(value_counts)

    # Get the count of DE032 unique values
    de032_value_counts = Counter(de032_values)

    # End the timer
    end_time = time.time()
    execution_time = end_time - start_time

    # Calculate hour, minute and second components
    hours = int(execution_time // 3600)
    minutes = int((execution_time % 3600) // 60)
    seconds = execution_time % 60

    print(f"Execution time: {hours} hours, {minutes} minutes, {seconds:.2f} seconds")

    print("Count of unique DE032 values:", len(de032_value_counts))
    print("Unique DE032 values and their counts:")
    for value, count in de032_value_counts.items():
        print(f"{value}: {count} times")

if __name__ == "__main__":
    main()
