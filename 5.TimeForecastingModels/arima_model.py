import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import datetime

def unix_to_hr(unix_timestamp):
    date_time = datetime.datetime.fromtimestamp(unix_timestamp)
    human_readable = date_time.strftime('%Y-%m-%d %H:%M:%S')
    return human_readable

# Load the dataset
data_path = 'all_peak_data.csv'
data = pd.read_csv(data_path)

# 'timestamp' is a column of Unix timestamps
timestamps = data['timestamp'].values.reshape(-1, 1)

# Normalize timestamp data
scaler = MinMaxScaler()
timestamps_normalized = scaler.fit_transform(timestamps).flatten()  # Flatten to convert from 2D back to 1D

# Best ARIMA model parameters (p, d, q)
best_order = (1, 2, 1)

# Fit the best ARIMA model on the entire normalized dataset
model = ARIMA(timestamps_normalized, order=best_order)
arima_model = model.fit()

# Forecast next timestamp (forecast will be in normalized scale)
forecast_normalized = arima_model.forecast()[0]  # Ensure correct indexing if needed

# Inverse transform to get the forecasted value in original Unix timestamp scale
forecast = scaler.inverse_transform([[forecast_normalized]])[0][0]

# Convert forecast to integer Unix timestamp
forecast_unix = int(forecast)

# Convert forecast to human-readable format
forecast_hr = unix_to_hr(forecast_unix)

# Save the forecasted timestamp to a CSV file
output_data = pd.DataFrame({
    'Forecasted Unix Timestamp': [forecast_unix],
    'Forecasted HR Timestamp': [forecast_hr]
})

print('Forecasted Unix Timestamp',forecast_unix) 
print('Forecasted HR Timestamp', forecast_hr)

output_data.to_csv('next_peak_arima.csv', index=False)
