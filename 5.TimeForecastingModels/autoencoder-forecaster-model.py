# ml_model.py
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import LSTM, Dense, Input, RepeatVector, Bidirectional, Dropout
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
time_data_unix = df['timestamp'].values.reshape(-1, 1)

# Normalize data
scaler = MinMaxScaler(feature_range=(0, 1))
time_data_normalized = scaler.fit_transform(time_data_unix)

# Parameters for dataset creation
input_window = 100  # Number of time steps for input

# Create dataset with sliding window
def create_sliding_window_dataset(data, input_window):
    X, Y = [], []
    for i in range(len(data) - input_window - 1):
        X.append(data[i:i + input_window, 0])
        Y.append(data[i + input_window, 0])
    return np.array(X), np.array(Y)

X, Y = create_sliding_window_dataset(time_data_normalized, input_window)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, shuffle=False)

# Reshape input to be [samples, time steps, features]
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

# Build LSTM Autoencoder
input_seq = Input(shape=(input_window, 1))

# Encoder
encoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=True))(input_seq)
encoded = Bidirectional(LSTM(64, activation='tanh', return_sequences=False))(encoded)

#Decoder
decoded = RepeatVector(input_window)(encoded)
decoded = Bidirectional(LSTM(64, activation='tanh', return_sequences=True))(decoded)
decoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=True))(decoded)
decoded = Dense(1, activation='tanh')(decoded)

autoencoder = Model(input_seq, decoded)
encoder = Model(input_seq, encoded)

# Compile Autoencoder
autoencoder.compile(optimizer=Adam(learning_rate=0.0005), loss='mean_squared_error')

# Callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=20, min_lr=1e-6)

# Train Autoencoder
autoencoder.fit(X_train, X_train, epochs=50, batch_size=32, validation_split=0.2, verbose=1, callbacks=[early_stopping, lr_scheduler])

# Extract Features using Encoder part of Autoencoder
train_features = encoder.predict(X_train)
test_features = encoder.predict(X_test)

# Reshape features to fit LSTM Forecaster
train_features = np.expand_dims(train_features, axis=-1)
test_features = np.expand_dims(test_features, axis=-1)

# Build LSTM Forecaster
forecaster = Sequential([
    Bidirectional(LSTM(128, activation='tanh', return_sequences=True), input_shape=(train_features.shape[1], train_features.shape[2])),
    Dropout(0.2),
    LSTM(128, activation='tanh'),
    Dense(64, activation='relu'),
    Dense(1)
])

# Compile Forecaster
forecaster.compile(optimizer=Adam(learning_rate=0.0005), loss='mean_squared_error')

# Train Forecaster
history = forecaster.fit(train_features, y_train, epochs=100, batch_size=32, validation_split=0.2, verbose=1, callbacks=[early_stopping, lr_scheduler])

# Evaluate model
y_pred = forecaster.predict(test_features)
mae = np.mean(np.abs(y_test - y_pred))
mse = np.mean((y_test - y_pred)**2)

print(f"Mean Absolute Error (MAE): {mae:.2f}")
print(f"Mean Squared Error (MSE): {mse:.2f}")

# Convert predictions back to original scale
predicted_unix = scaler.inverse_transform(y_pred)
y_test_unix = scaler.inverse_transform(y_test.reshape(-1, 1))

# Compute absolute errors
absolute_errors = np.abs(y_test_unix.flatten() - predicted_unix.flatten())

# Save results to CSV
def moving_average(predictions, window_size=3):
    return np.convolve(predictions, np.ones(window_size)/window_size, mode='same')

# Assuming `predicted_unix` contains your forecasted outputs
smoothed_predictions = moving_average(predicted_unix.flatten())

# Save smoothed predictions to CSV
results_df = pd.DataFrame({
    "Actual Unix Time": y_test_unix.flatten(),
    "Predicted Unix Time": smoothed_predictions,
    "Absolute Error": absolute_errors
})
results_df.to_csv("next_peak_smoothed.csv", index=False)

# Calculate summary statistics
mean_diff = results_df['Absolute Error'].mean()
median_diff = results_df['Absolute Error'].median()
std_diff = results_df['Absolute Error'].std()

# Print the results
print(f"Mean Absolute Error: {mean_diff:.2f} seconds")
print(f"Median Absolute Error: {median_diff:.2f} seconds")
print(f"Standard Deviation of Absolute Error: {std_diff:.2f} seconds")

# Prepare the last window for prediction
last_window = time_data_normalized[-input_window:].reshape(1, input_window, 1)

# Make prediction
last_feature = encoder.predict(last_window)
last_feature = np.expand_dims(last_feature, axis=-1)
next_timestamp_normalized = forecaster.predict(last_feature)
next_timestamp_unix = scaler.inverse_transform(next_timestamp_normalized)

print(f"Next predicted Unix timestamp: {next_timestamp_unix[0][0]}")

# Plot learning curve
plt.figure(figsize=(12, 8))
plt.plot(history.history['loss'], label='Train Loss', color='blue')
plt.plot(history.history['val_loss'], label='Validation Loss', color='orange')
plt.title('Autoencoder - Forecaster Model Learning Curve', fontsize=16)
plt.xlabel('Epoch', fontsize=14)
plt.ylabel('Loss (MSE)', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.show()

# Plot actual vs predicted timestamps
plt.figure(figsize=(12, 8))
plt.plot(y_test_unix, label='Actual', color='blue')
plt.plot(predicted_unix, label='Predicted', color='orange', linestyle='dashed')
plt.title('Actual vs Predicted Timestamps', fontsize=16)
plt.xlabel('Index', fontsize=14)
plt.ylabel('Unix Timestamp', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True)
plt.show()
