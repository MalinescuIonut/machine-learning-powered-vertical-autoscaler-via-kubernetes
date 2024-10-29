# BiLSTM-MF (Bidirectional LSTM with Minute Feature)

import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import LSTM, Dense, Input, Dropout, Bidirectional
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# Set seed for reproducibility
seed = 47
np.random.seed(seed)
tf.random.set_seed(seed)

# Read data from CSV
df = pd.read_csv("fake_metrics_30_2000.csv")

# Extract minute feature from the timestamp
df['minute'] = pd.to_datetime(df['timestamp'], unit='s').dt.minute

# Subtract the first timestamp from all timestamps
initial_timestamp = df['timestamp'].iloc[0]
df['timestamp'] -= initial_timestamp

# Normalize minute data
scaler = MinMaxScaler(feature_range=(0, 1))
df[['timestamp', 'minute']] = scaler.fit_transform(df[['timestamp', 'minute']])

# Parameters for dataset creation
input_window = 100

# Create dataset with sliding window
def create_sliding_window_dataset(data, input_window):
    X, Y = [], []
    for i in range(len(data) - input_window - 1):
        X.append(data[i:i + input_window])
        Y.append(data[i + input_window, 0])  # Target is the normalized timestamp
    return np.array(X), np.array(Y)

# Include timestamp and minute
feature_columns = ['timestamp', 'minute']
X, Y = create_sliding_window_dataset(df[feature_columns].values, input_window)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, shuffle=False)

# Reshape input to be [samples, time steps, features]
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], len(feature_columns)))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], len(feature_columns)))

# Build the LSTM model
input_seq = Input(shape=(input_window, len(feature_columns)))
encoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=False))(input_seq)
dropout = Dropout(0.1)(encoded)
dense_output = Dense(128, activation='relu')(dropout)
dropout2 = Dropout(0.2)(dense_output)
dense_output = Dense(64, activation='relu')(dropout)
output = Dense(1)(dropout2)

model = Model(input_seq, output)

# Compile the model
model.compile(optimizer=Adam(learning_rate=0.0001), loss='mean_squared_error')

# Callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-6)

# Train the model
history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_split=0.2, 
                    callbacks=[early_stopping, lr_scheduler], verbose=1)

# Use only the last window for final prediction
last_window = df[feature_columns].values[-input_window:].reshape(1, input_window, len(feature_columns))
next_timestamp_normalized = model.predict(last_window)
next_timestamp = scaler.inverse_transform(
    np.hstack([next_timestamp_normalized, np.zeros((next_timestamp_normalized.shape[0], 1))])
)[:, 0]

# Add the initial timestamp to get the full Unix timestamp
next_timestamp_unix = next_timestamp + initial_timestamp

print(f"Next predicted Unix timestamp: {next_timestamp_unix[0]}")

# Compute errors on the test set
y_pred = model.predict(X_test)
y_pred_unix = scaler.inverse_transform(
    np.hstack([y_pred, np.zeros((y_pred.shape[0], 1))])
)[:, 0] + initial_timestamp
y_true_unix = scaler.inverse_transform(
    np.hstack([y_test.reshape(-1, 1), np.zeros((y_test.shape[0], 1))])
)[:, 0] + initial_timestamp

mae = np.mean(np.abs(y_true_unix - y_pred_unix))
mse = np.mean((y_true_unix - y_pred_unix) ** 2)
mape = np.mean(np.abs((y_true_unix - y_pred_unix) / y_true_unix)) * 100
rmse = np.sqrt(mse)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")
print(f"Mean Absolute Percentage Error (MAPE): {mape:.4f}%")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f}")

# Compute absolute errors
absolute_errors = np.abs(y_true_unix - y_pred_unix)

# Use the last computed absolute error value for final prediction adjustment
last_absolute_error = absolute_errors[-1]

# Compute the final predicted Unix peak
if next_timestamp_unix[0] > y_true_unix[-1]:
    final_next_peak = next_timestamp_unix[0] + last_absolute_error
else:
    final_next_peak = next_timestamp_unix[0] - last_absolute_error

print(f"Final next predicted Unix peak: {final_next_peak}")

# Plot learning curve
plt.figure(figsize=(10, 6))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Learning Curve')
plt.xlabel('Epoch')
plt.ylabel('Loss (MSE)')
plt.legend()
plt.grid(True)
plt.show()

# Plot actual vs predicted timestamps
plt.figure(figsize=(10, 6))
plt.plot(y_true_unix, label='Actual', color='blue')
plt.plot(y_pred_unix, label='Predicted', color='orange', linestyle='dashed')
plt.title('Actual vs Predicted Timestamps')
plt.xlabel('Index')
plt.ylabel('Unix Timestamp')
plt.legend()
plt.show()

# Plot absolute errors
plt.figure(figsize=(10, 6))
plt.plot(absolute_errors, label='Absolute Errors', color='red')
plt.title('Prediction Errors')
plt.xlabel('Index')
plt.ylabel('Error')
plt.legend()
plt.show()
