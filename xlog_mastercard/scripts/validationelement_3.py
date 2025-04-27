import glob
import os

def validate_parts(base_file_path):
    """
    Validate that each part file:
    - Starts with XML header and <log>
    - Ends with </log>
    """
    base_path, _ = os.path.splitext(base_file_path)
    part_files = sorted(glob.glob(base_path + '_part*.xlog'))

    if not part_files:
        print("❌ No part files found.")
        return

    print(f"🔍 Validating {len(part_files)} part files...\n")

    all_good = True

    for part_file in part_files:
        with open(part_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                print(f"❌ {part_file}: File is empty.")
                all_good = False
                continue

            first_line = lines[0].strip()
            second_line = lines[1].strip() if len(lines) > 1 else ""

            last_line = lines[-1].strip()

            errors = []

            if not first_line.startswith('<?xml'):
                errors.append("Missing XML declaration (<?xml ...?>) at top.")

            if not second_line.startswith('<log>'):
                errors.append("Missing <log> tag at top.")

            if not last_line == '</log>':
                errors.append("Missing </log> tag at bottom.")

            if errors:
                print(f"❌ {part_file}:")
                for err in errors:
                    print(f"   - {err}")
                all_good = False
            else:
                print(f"✅ {part_file}: Valid.")

    if all_good:
        print("\n🎉 All part files are valid!")
    else:
        print("\n⚠️ Some part files have issues. Please fix them.")

if __name__ == "__main__":
    # Example usage:
    base_file = 'path_to_your_uploaded_xlog_file.xlog'
    validate_parts(base_file)
