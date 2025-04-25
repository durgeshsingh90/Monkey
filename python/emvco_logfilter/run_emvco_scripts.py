import subprocess
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("processing.log"),
        logging.StreamHandler()
    ]
)

# List of Python files to run in sequence
scripts = [
    "1_breakemvco.py",
    "2_adjustemvco.py",
    "3_adjustelements.py",
    "4_unique_de32_emvco.py",
    "5_emvco_filter.py",
    "6_format_emv_filter.py"
]

def run_script(script_name):
    start_time = time.time()
    try:
        logging.info(f"Running script: {script_name}")
        subprocess.run(["python", script_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"An error occurred while running {script_name}: {e}")
        return False, 0
    end_time = time.time()
    elapsed_time = end_time - start_time
    return True, elapsed_time

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = seconds % 60
    return f"{hours} hours, {minutes} minutes, {sec:.2f} seconds"

total_start_time = time.time()

script_times = {}

for script in scripts:
    success, elapsed_time = run_script(script)
    script_times[script] = elapsed_time
    if success:
        logging.info(f"{script} ran successfully in {format_time(elapsed_time)}.")
    else:
        logging.error(f"Failed to run {script}, stopping the sequence.")
        break

total_end_time = time.time()
total_elapsed_time = total_end_time - total_start_time

logging.info("\nDetailed Execution Times:")
for script, elapsed_time in script_times.items():
    logging.info(f"{script}: {format_time(elapsed_time)}")

logging.info(f"\nTotal time to run all scripts: {format_time(total_elapsed_time)}.")
