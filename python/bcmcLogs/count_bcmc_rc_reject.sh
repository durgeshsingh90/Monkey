#!/bin/bash

start_time=$(date +%s)

input_file="transaction.log"  
output_file="${input_file}_output"

# Define search blocks
declare -a search_blocks=("BCMC | 1.1        | \"1\" BCMC | 1.2        | \"2\" BCMC | 1.3        | \"3\" BCMC | 1.4        | \"0\""
                          "BCMC | 1.1        | \"1\" BCMC | 1.2        | \"1\" BCMC | 1.3        | \"3\" BCMC | 1.4        | \"0\""
                          "BCMC | 1.1        | \"1\" BCMC | 1.2        | \"1\" BCMC | 1.3        | \"1\" BCMC | 1.4        | \"0\""
                          "OMNIPAY | 39         | \"09\"")

# Create an output file
> "$output_file"

reading_entry=false
entry=""

while IFS= read -r line; do
    if [[ $line =~ ^[0-9]{2}-[0-9]{2}-[0-9]{2} ]]; then
        if $reading_entry; then
            for block in "${search_blocks[@]}"; do
                block_terms=($block)
                all_terms_present=true
                for term in "${block_terms[@]}"; do
                    if ! grep -q "$term" <<< "$entry"; then
                        all_terms_present=false
                        break
                    fi
                done
                if $all_terms_present; then
                    echo "$entry" >> "$output_file"
                    break
                fi
            done
            entry=""
        fi
        reading_entry=true
    fi
    entry+="$line"$'\n'
done < "$input_file"

if $reading_entry; then
    for block in "${search_blocks[@]}"; do
        block_terms=($block)
        all_terms_present=true
        for term in "${block_terms[@]}"; do
            if ! grep -q "$term" <<< "$entry"; then
                all_terms_present=false
                break
            fi
        done
        if $all_terms_present; then
            echo "$entry" >> "$output_file"
            break
        fi
    done
fi

count_unique_strings() {
    pattern="$1"
    echo "Pattern: $pattern"
    grep -o "$pattern" "$output_file" | sort | uniq -c
}

patterns=("BCMC\s*\|\s*39\s*\|\s*\".*?\""
          "OMNIPAY\s*\|\s*39\s*\|\s*\".*?\"")

for pattern in "${patterns[@]}"; do
    count_unique_strings "$pattern"
    echo "----------------------------------------"
done

rm -f "$output_file"
echo "Deleted the output file: $output_file"

end_time=$(date +%s)
elapsed_time=$((end_time - start_time))

minutes=$((elapsed_time / 60))
seconds=$((elapsed_time % 60))
echo "Total script execution time: ${minutes} minutes and ${seconds} seconds"
