import re
from collections import Counter

# Correct file path handling
file_path = r"C:\Users\f94gdos\Downloads\transaction.log.2025-04-07"

# Read the file
with open(file_path, 'r') as file:
    data = file.read()

# Extract the numbers using regular expression
pattern = re.compile(r'OMNIPAY \| 39\s+\| "(\d{2})"')
matches = pattern.findall(data)

# Count occurrences of each unique number
counter = Counter(matches)

# Sort the counter items by reject code (the number part)
sorted_counts = sorted(counter.items())

# Print the sorted results
for number, count in sorted_counts:
    print(f'{number}: {count}')
