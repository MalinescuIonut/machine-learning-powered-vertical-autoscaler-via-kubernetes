## 5.1. Autoregressive Integrated Moving Average (ARIMA) Statistical Model

The next step in the implementation of this project was the creation of a model, capable of using past trends in data to forecast a future event. In this case, it should use peak data timestamps to predict an equivalent future event. This is why, as said before, an autoregressive model is appropriate for time series forecasting. The ARIMA statistical model is modeled by 3 hyperparameters, “p”, “d”, “q”, corresponding to each part of its architecture: autoregressive part, integrated part, respectively moving average part.

For the creation of this model, a python script has been devised to tune these hyperparameters and find the best ones for a testbed of 24 hours of data. The ARIMA model is imported from the “statsmodels” library. To increase the performance of the model, before feeding the data into it, it is first normalized between the values of 0 and 1, by the ”MinMaxScaler” from “scikit-learn” library. For the training of this model, the data is split like this: 80% for training and the remaining 20% used for testing. To test the performance of the model, the root mean squared error (RMSE) is also computed for this model. A grid test is performed to extract the best model architecture, by training the model for each architecture case and comparing the best RMSE. Finally, the best model is fitted, and the forecasting is performed. In the final implementation, only the model with the best hyperparameter-combination is run as a containerized application within the cluster. Identically to the previous cases, of the stress and the data processing applications, a deployment has been defined to manage the container running this model. Inside the container, a CronJob is yet again defined to run the ARIMA model training script twice an hour (at minute 20 & 50) and to generate a CSV file (“next_peak_arima.csv”) containing the forecasted timestamp for the next spike in memory usage. Using this output, scaling can be performed

```bat
  echo "*20,50 * * * * cd /python-scripts && /usr/local/bin/python arima_model.py >> forecast.log 2>&1" > /etc/cron.d/arima-forecast &&
  crontab /etc/cron.d/arima-forecast &&
  cron -f

```

# 5.2. Long – Short Term Memory (LSTM) Machine Learning Model

As an alternative to the ARIMA model, an LSTM model was built to do the time forecasting as well. This paper will analyze the differences in performance between the statistical and ML architectures. An LSTM is able to store data indefinitely and to drop it when unnecessary. This property of the model makes it very effective at discovering trends in time series data, over long and short periods of time [Aurélien Géron, “4. Recurrent Neural Networks - Neural networks and deep learning [Book]]. Two models will be presented presenting different architectures: an Autoencoder – Forecaster and a simpler LSTM architecture.

## 5.2.1. The Autoencoder – Forecaster LSTM model

This model has been designed using a Python script, utilizing the “Tensorflow” library for building and training. The timestamps scraped from the Ubuntu machine are in UNIX format, a format which measures the amount of time passed in seconds since the first of January 1970, 00:00 until current time represented in Coordinated Universal Time (UTC). As an example, 04:37:40 corresponds to 1719452260. Because of this, a function is implemented to display the final prediction in a readable format, as well, for debugging purposes (the converted time represents the timestamp converted to local time – UTC + 3). For training, a custom data resource has been utilized, which contains 2000 data points, each spaced approximately 30 minutes apart, as an error was also added to each data point to introduce non–linearity within the input data. Using this, a dataset was created for the model to be trained on. As forecasting is one of the goals of this paper, a time series dataset is required, which was created using a sliding window approach. Two lists, “X” and “Y” are loaded with data. For the model to be able to discover trends over time, a list of datapoints needs to be analyzed, which will determine one final point. The sliding window splits the data like this, it first collects n points from the time series and stores them inside the X list, then it takes the following point and stores it inside the Y list, point which acts as a result of the other n points. During the next iteration, it will increase its starting point and repeat the step above. This is how it is ensured that to each result in Y has one list in X is associated with it.

```bat
def create_sliding_window_dataset(data, input_window):
    X, Y = [], []
    for i in range(len(data) - input_window - 1):
        X.append(data[i:i + input_window, 0])
        Y.append(data[i + input_window, 0])
    return np.array(X), np.array(Y)

```
Having the dataset created, the data is split into 2 sections, one of 80% used for training while the rest of data, 20%, is utilized as unknown data for validation purposes. This last portion will remain unknown to the model until testing, giving a reliable measure of the model’s accuracy. Before utilizing these lists, they will be reshaped according to the proper shape expected by the network. The data-driven model was created by first determining a simple LSTM architecture and adding layers to it to increase its complexity. The resulting framework has an architecture inspired from the paper [Lap17], described by two large components, namely: an autoencoder and a forecaster, both complementing each other. The autoencoder is tasked with reducing the amount of information required for forecasting, by capturing precisely what is important for the forecasting task and dropping irrelevant information (noise). This is done by first encoding the data and then restoring it to its initial state, through the inverse operation. For this implementation only the encoder part of the architecture was used, as it provided better results, but the entire scheme has better potential of dealing with more complex data.

The autoencoder component consists of multiple LSTM layers, which described from the input side, are the following: 
1.	An input layer specifying the size of the input.
2.	A bidirectional layer of 128 LSTM units, analyzing the input window in both directions, thus discovering data trends more efficiently (the “return_sequences = True” parameter, specifies that all the, 128 forwards + 128 backwards, hidden layers will be returned).
3.	A second bidirectional layer of 64 LSTM units, which further reduces the size of the architecture, by returning only the final hidden layer that describes the encoded information (“return_sequences = False”). The two bidirectional layers act as an encoder which compresses the data and stores only the important information inside a vector of fixed size.
4.	The RepeatVector acts as a decoder for the fixed-size vector, by repeating it until it recovers its initial format (2-D).
5.	Now, the inverse operation is done to decode the restored sequence, by first feeding it through a 64-unit and then trough a 128-unit bidirectional LSTM layer.
6.	The final layer is a dense layer providing a sequence having the reconstructed format of the input.

```bat
  # LSTM Autoencoder
  input_seq = Input(shape=(input_window, 1))
  encoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=True))(input_seq)
  encoded = Bidirectional(LSTM(64, activation='tanh', return_sequences=False))(encoded)
  decoded = RepeatVector(input_window)(encoded)
  decoded = Bidirectional(LSTM(64, activation='tanh', return_sequences=True))(decoded)
  decoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=True))(decoded)
  decoded = Dense(1, activation='tanh')(decoded)
  autoencoder = Model(input_seq, decoded)
  encoder = Model(input_seq, encoded)
```
Early stopping measures are also in place to stop the model from unnecessary training and to reduce overfitting. This is done by monitoring the validation loss for each epoch (1 pass through the training data), loss which presents how well the model fairs against unknown data. Besides this, the learning rate is also monitored and dynamically adjusted. 

After training, the data features extracted by the autoencoder are fed to a LSTM forecaster composed of the following layers:
1.	One bidirectional 128-unit LSTM input layer specifying the shape of the input data.
2.	A dropout layer is used to prevent overfitting by setting 20% of the inputs to 0, thus introducing more uncertainty.
3.	A LSTM layer helps the model learn new features from the input data, despite it having the same number of units as the previous layer, it applies different weights and operations to the input, now only analyzing the data in one way.
4.	Two more dense/fully connected layers are used, the first one having less neurons, converges the information from the previous layer and applies weights to it, while the last layer provides the final output, which is the final forecast.

```bat
  forecaster = Sequential([
      Bidirectional(LSTM(128, activation='tanh', return_sequences=True), input_shape= (train_features.shape[1], train_features.shape[2])),
      Dropout(0.2),
      LSTM(128, activation='tanh'),
      Dense(64, activation='relu'),
      Dense(1)
  ])

```
Both models are compiled using an “Adaptive Movement Estimation” (ADAM) optimizer, which is used to enhance the learning process of the LSTM network, by reducing loss during training. The loss is determined by computing the means squared error (MSE) between actual values and predicted ones. After compiling the model, the training parameters such as: epochs, batch size, learning rate and the callbacks (early stopping, learning rate) were modeled by running a parameter tunning script which ran the code for multiple such combinations, performing a grid search for the best parameter combination. Metrics such as mean absolute error (MAE), MSE or the median difference are computed to determine the accuracy of the final prediction. The prediction is also done by using the last window of data from the initial dataset.

## 5.2.2. The Bidirectional LSTM with Minute Feature (BiLSTM-MF)

This model involves a similar architecture. For this implementation, only one model was built running a more complex architecture. First, another feature was introduced for the model training, which is the minute part of the timestamp. For consistency reasons, the normalization of the timestamp and minute features is done within the same range, [0;1]. 

The dataset is created the same way as in the previous model, namely using a sliding window approach. Having the dataset prepared also split precisely as before, the model can be defined as follows:
1.	An input layer, specifying the shape of the data introduced to the model.
2.	An LSTM bidirectional layer retrieving 128 + 128 features.
3.	A dropout layer used to reduce overfitting, by setting 10% of the data points to the 0 value.
4.	A fully connected layer implementing a rectified linear unit (ReLU) activation. This activation transforms the sum of the inputs, which are multiplied by weights at the entrance of a node, to either 0 or the max value of the sum. This is set to 0, if the sum is negative (because these values negatively impact the models learning) and to the max value, otherwise [Bro19].
5.	Another dropout layer is used to prevent overfitting.
6.	A further dense layer implementing the ReLU activation is introduced.
7.	The final layer is a convergence layer, which returns the forecast.

```bat
  input_seq = Input(shape=(input_window, len(feature_columns)))
  encoded = Bidirectional(LSTM(128, activation='tanh', return_sequences=False))(input_seq)
  dropout = Dropout(0.1)(encoded)
  dense_output = Dense(128, activation='relu')(dropout)
  dropout2 = Dropout(0.2)(dense_output)
  dense_output = Dense(64, activation='relu')(dropout)
  output = Dense(1)(dropout2)
```
Only the final window of data is utilized for the forecast and metrics such as the aforementioned, MAE, MSE or the median difference are used to determine the accuracy of the final prediction and the performance of the model.

