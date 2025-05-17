#!/bin/bash

# Function to collect log content based on timestamp
process_file() {
    local debug_file="$1"
    local merged_file="$2"
    
    # Initialize current_timestamp as empty
    local current_timestamp=""
    local unknown_logs=""
    
    # Read each line of the file
    while IFS= read -r line; do
        # Check if the line starts with a timestamp
        if [[ $line =~ ^([0-9]{2}\.[0-9]{2}\.[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}).* ]]; then
            # Update the current timestamp
            current_timestamp="${BASH_REMATCH[1]}"
            
            # If there's any unknown log collected previously, write them to merged file
            if [ -n "$unknown_logs" ]; then
                printf "%s" "$unknown_logs" >> "$merged_file"
                unknown_logs=""
            fi
        fi
        
        # Append the line to the corresponding timestamp in the array if current_timestamp is not empty
        if [ -n "$current_timestamp" ]; then
            printf "%s\n" "$line" >> "$merged_file"
        else
            # Collect initial lines without timestamp
            unknown_logs+="$line"$'\n'
        fi
    done < "$debug_file"
    
    # Append any remaining unknown logs to the merged file
    if [ -n "$unknown_logs" ]; then
        printf "%s" "$unknown_logs" >> "$merged_file"
    fi
}

# Create the merged log file
merged_file="merged_debug.log"
> "$merged_file"

# Temporary sorted file
sorted_file="sorted_debug.log"
> "$sorted_file"

# Create an array to hold all log entries with timestamps
declare -A log_entries

# Process all .debug files in the current directory
for debug_file in *.debug; do
    if [ -f "$debug_file" ]; then
        echo "Processing $debug_file..."
        process_file "$debug_file" "$merged_file"
    else
        echo "No .debug files found in the current directory."
    fi
done

# Sort the entries in the merged file
sort -o "$sorted_file" "$merged_file"

# Rename sorted file to merged file
mv "$sorted_file" "$merged_file"

# Notify the user that the merged file has been created
echo "Merged log file created as $merged_file"
