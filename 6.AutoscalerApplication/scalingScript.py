# ubuntu@mvictor-vm-1:~/python-scripts$ cat scaling.py 
import csv
import time
import subprocess
from datetime import datetime, timedelta

# Define file path
csv_file = 'next_peak_arima.csv'
log_file = 'scaling_operations.txt'
actual_peak_file = 'all_peak_data.csv'

# Function to write log messages to the text file
def write_log(message):
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now()} - {message}\n")

def read_last_row(file_path):
    with open(file_path, 'rb') as file:
        file.seek(-1, 2)  # Move to the end of the file
        while file.tell() > 0:
            char = file.read(1)
            if char == b'\n' and file.tell() != file.seek(-1, 1):
                break
            file.seek(-2, 1)
        last_line = file.readline().decode().strip()
    
    return last_line

# Read the CSV file to get the target timestamp
with open(csv_file, 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        target_timestamp = int(row['Forecasted Unix Timestamp'])
        break  # Only the first timestamp is required

# Calculate the scaling times
target_time = datetime.fromtimestamp(target_timestamp)
scale_up_time = target_time - timedelta(minutes=6)
scale_down_time = target_time + timedelta(minutes=6)

# Check if the target time is in the past, in regards to current time
if target_time < datetime.now():
    fail_message = "The target timestamp is in the past. No scaling operations will be performed."
    write_log(f"----------------------------------------")
    write_log(fail_message)
    print(fail_message)
    exit(1)

# Write the actual detected timestamp
# Write the actual detected timestamp
last_line = read_last_row(actual_peak_file)
last_row = next(csv.DictReader([last_line]))

detected_human_readable_timestamp = last_row['human_readable_time']
detected_timestamp = int(last_row['timestamp'])

# Convert the human-readable time to a datetime object
human_readable_time = datetime.strptime(detected_human_readable_timestamp, '%Y-%m-%d %H:%M:%S')
# Subtract 3 hours from the human-readable time, as it needs to be displayed in UTC, not UTC+3
adjusted_time = human_readable_time - timedelta(hours=3)

# Print the results inside the log file
write_log(f"Peak memory usage detected timestamp: {detected_timestamp}")
write_log(f"Detected Timestamp (HR format): {adjusted_time}")

# Define the scaling commands using the full path to kubectl
scale_up_command = (
    "/usr/local/bin/kubectl patch deployment stress-testing-deployment "
    "--namespace=stress-test "
    "--patch '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"stress-testing-container\","
    "\"resources\":{\"requests\":{\"memory\":\"1Gi\"}, \"limits\":{\"memory\":\"1.5Gi\"}}}]}}}}'"
)

scale_down_command = (
    "/usr/local/bin/kubectl patch deployment stress-testing-deployment "
    "--namespace=stress-test "
    "--patch '{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"stress-testing-container\","
    "\"resources\":{\"requests\":{\"memory\":\"512Mi\"}, \"limits\":{\"memory\":\"512Mi\"}}}]}}}}'"
)

# Write initial log messages
write_log(f"----------------------------------------")
write_log(f"Target timestamp: {target_timestamp}")
write_log(f"Target timestamp (HR format): {target_time}")
write_log(f"Scale-up time: {scale_up_time}")
write_log(f"Scale-down time: {scale_down_time}")

# Wait until the scale-up time
while datetime.now() < scale_up_time:
    time.sleep(10)  # Sleep in 10-second intervals

# Scale up
subprocess.run(scale_up_command, shell=True)
write_log("Scaled up to 1Gi allocated and 1.5Gi limit")

# Wait until the scale-down time
while datetime.now() < scale_down_time:
    time.sleep(10)  # Sleep in 10-second intervals

# Scale down
subprocess.run(scale_down_command, shell=True)
write_log("Scaled down to 512Mi allocated and 512Mi limit")

print("Scaling operations completed.")
