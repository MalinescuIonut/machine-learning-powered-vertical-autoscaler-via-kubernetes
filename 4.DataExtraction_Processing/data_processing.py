import json
import pandas as pd
from datetime import datetime
import pytz
from scipy.signal import find_peaks
import numpy as np
import os

# Load the JSON data
with open('output-metrics.json') as f:
    data = json.load(f)

# Extract the results
results = data['data']['result']

# Prepare a list to store the data
data_list = []

# Define the UTC and EET time zones
utc_tz = pytz.utc
romania_tz = pytz.timezone('Europe/Bucharest')  # EET/EEST time zone for Romania

# Loop through the results
for result in results:
    metric = result['metric']
    values = result['values']

    # Loop through the values
    for value in values:
        # Prepare a dictionary to store the data
        data_dict = metric.copy()
        # Keep the Unix timestamp as is
        timestamp = value[0]
        data_dict['timestamp'] = timestamp
        # Convert memory usage to megabytes
        memory_usage_mb = int(value[1]) / 1024 / 1024
        data_dict['memory_usage_mb'] = memory_usage_mb
        # Convert Unix timestamp to human-readable format in UTC
        utc_time = datetime.fromtimestamp(timestamp, utc_tz)
        # Convert UTC time to Romania time
        romania_time = utc_time.astimezone(romania_tz)
        human_readable_time = romania_time.strftime('%Y-%m-%d %H:%M:%S')
        data_dict['human_readable_time'] = human_readable_time

        # Add the dictionary to the list
        data_list.append(data_dict)

# Create a DataFrame
df = pd.DataFrame(data_list, columns=['human_readable_time', 'timestamp', 'memory_usage_mb'])

# Sort DataFrame by 'timestamp'
df.sort_values(by='timestamp', inplace=True)

# Path to total_metrics.csv
total_metrics_path = 'total_metrics.csv'

# Check if total_metrics.csv exists
if os.path.exists(total_metrics_path):
    # Load existing total_metrics.csv
    total_metrics_df = pd.read_csv(total_metrics_path)
    # Concatenate new data
    total_metrics_df = pd.concat([total_metrics_df, df], ignore_index=True)
else:
    total_metrics_df = df

# Save updated total_metrics.csv
total_metrics_df.to_csv(total_metrics_path, index=False)

############# PEAK DETECTION ################

# Perform peak detection on the new data only
memory_usage = df['memory_usage_mb'].values

# Find peaks
peaks, _ = find_peaks(memory_usage, distance=30, height=40)

# Create a DataFrame containing only peak data from the new data
peaks_df = df.iloc[peaks].copy()

# Path to all_peak_data.csv
all_peaks_path = 'all_peak_data.csv'

# Check if all_peak_data.csv exists
if os.path.exists(all_peaks_path):
    # Load existing all_peak_data.csv
    all_peaks_df = pd.read_csv(all_peaks_path)
    # Concatenate new peak data
    all_peaks_df = pd.concat([all_peaks_df, peaks_df], ignore_index=True)
else:
    all_peaks_df = peaks_df

# Save updated all_peak_data.csv
all_peaks_df.to_csv(all_peaks_path, index=False)
