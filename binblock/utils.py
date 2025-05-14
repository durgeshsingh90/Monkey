def split_bin_ranges(json_data, bin_list, user_bin_data):
    """
    For each BIN in bin_list, find if it falls inside any LOWBIN–HIGHBIN range.
    If so, split that range into:
    - Before BIN
    - Exact BIN (using user_bin_data)
    - After BIN
    """
    new_data = []

    for entry in json_data:
        low = int(entry['LOWBIN'])
        high = int(entry['HIGHBIN'])

        matched = False
        for short_bin in bin_list:
            if not short_bin.strip().isdigit():
                continue  # skip invalid input

            bin_start = int(f"{short_bin}000000000")
            bin_end = int(f"{short_bin}999999999")

            if low <= bin_start <= high:
                matched = True

                # Part before BIN
                if low < bin_start:
                    before_entry = entry.copy()
                    before_entry['LOWBIN'] = str(low).zfill(15)
                    before_entry['HIGHBIN'] = str(bin_start - 1).zfill(15)
                    new_data.append(before_entry)

                # Exact BIN range using user input
                exact_entry = user_bin_data.copy()
                exact_entry['LOWBIN'] = str(bin_start).zfill(15)
                exact_entry['HIGHBIN'] = str(bin_end).zfill(15)
                new_data.append(exact_entry)

                # Part after BIN
                if bin_end < high:
                    after_entry = entry.copy()
                    after_entry['LOWBIN'] = str(bin_end + 1).zfill(15)
                    after_entry['HIGHBIN'] = str(high).zfill(15)
                    new_data.append(after_entry)

                break  # Only split once per entry

        if not matched:
            new_data.append(entry)

    return new_data
