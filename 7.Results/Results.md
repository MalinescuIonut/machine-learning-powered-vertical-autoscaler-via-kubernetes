# 7.1. Memory Leak Scenario Results

As presented in the previous section of the paper, the mechanism of the memory leak was generated arbitrarily. This scenario was set to reoccur twice an hour, every 30 minutes and to stress the “stress-testing-container” by utilizing more memory than the one available to it. This way, the container will suffer a fatal OOM kill which would set a restart in motion. After deploying the container, it was monitored using Grafana dashboard, querying the data over the retention span set in Prometheus. Figure 14. presents the dynamics of this scenario over a couple hour time span. It is to be noted that the functionality of the application remains the same, despite the visible differences between the memory leaks in the picture. Differences between the visualized peaks are determined by the fact that the data scraping is performed at intervals of 10 seconds. This was one of the compromises described in the configuration of Prometheus. Having such a low resolution means that some of the relevant data is not subjected to scraping and depending on how fast the stress-command is enacted, and how quickly that memory is allocated, the memory leak might peak in amplitude at different time moments, which may not coincide exactly with the scarping moment. Despite this, the memory leaks are easy to detect as they present inconsistencies in memory usage, in contrast to the rest of the data.

![image](https://github.com/user-attachments/assets/03dc9568-5c19-4a40-8a55-0fcb3338ec98)

Inside the cluster, the effects of the pods can be also monitored directly. This can be done using the “microk8s kubectl describe” command, which will retrieve extensive information about the resource it is used on. By running it on the stress-tesitng-container, such an output is received:

```bat
  Containers:
    stress-testing-container:
      Image: ******************/stress-testing-image:latest
      Image ID: docker.io/***************/stress-testing-image@...
      State: Running
        Started: Tue, 02 Jul 2024 22:00:48 +0000
      Last State: Terminated
        Reason: OOMKilled
        Exit Code: 137
        Started: Tue, 02 Jul 2024 21:30:50 +0000
        Finished: Tue, 02 Jul 2024 22:00:45 +0000
      Ready: True
      Restart Count: 335
      Limits:
        memory: 512M
      Requests:
        memory: 512M
      Environment:
        MEMORY_LIMIT: 512 (limits.memory)

```
It can be determined from this output sequence, that the container running the custom Docker image, displayed in the previous section of the paper, has the last state as: “terminated”, the reason for that being the OOM Killer. The sequence provided also presents when the process was terminated and restarted, moments which coincide with the peaks in memory usage. Another hint to the termination of this container is its exit code, 137, which indicates the presence of a SIGKILL command, which would terminate the application immediately. Additionally, the restart count provides us with a measure of how many memory leaks have been encountered in this pod’s lifetime of 7 days, further proving the working state of the memory leak application. Additional insight to determine the consistent restarts of the pod, can be observed inside the “/var/log/syslog” path of the filesystem, by searching for the tag “killed process”. Same observations can be made regarding the output of this command, as the ones mentioned before, which are that the process running within the application (stress-ng) were marked with the highest score by OOM (the score of 1000), to be terminated immediately, as their memory limit has been surpassed.

```bat
  ubuntu@mvictor-vm-1:~$ grep -i 'killed process' /var/log/syslog
  Jul 4 05:30:46 mvictor-vm-1 kernel: [1895428.541743] Memory cgroup out of memory: Killed process 867167 (stress-ng-vm) total-vm:542000kB, anon-rss:502236kB, file-rss:672kB, shmem-rss:48kB, UID:0 pgtables:1048kB oom_score_adj:1000
  Jul 4 06:00:45 mvictor-vm-1 kernel: [1897227.445728] Memory cgroup out of memory: Killed process 911701 (stress-ng-vm) total-vm:542000kB, anon-rss:502236kB, file-rss:652kB, shmem-rss:44kB, UID:0 pgtables:1048kB oom_score_adj:1000

```

# 7.2. Extracted Data and Pre-Processing

With the memory leak generated, the data extraction and pre-processing scripts were the next step in the implementation. 

![image](https://github.com/user-attachments/assets/9fc6d5c2-3ce1-4594-9631-6b8c97a14315)

As seen in the Figure above, both of these applications were defined under a single container, managed by a deployment, named “data-processing-deployment”. Two CronJobs are tasked with running these sequentially, first the “fetch_memory_usage.sh” shell script queries the memory usage metrics for the “stress-testing-container”, with a step of 20 seconds and the data is saved in a JSON file (“output-metrics.json”). The second script retrieves the queried information and performs peak detection on it. This way the noise data is filtered out. This data is saved within a final CSV file (“all_peak_data.csv”), the one utilized as an input in the model’s training. Performing peak detection and plotting it provides the following results, which again displays the functionality of the memory leak application. Peaks may be observed periodically occurring, again not being identical as an effect of the scraping interval.

# 7.3. Time Forecasting Models Performance
## 7.3.1. ARIMA Model Performance

The ARIMA model was tuned using its three hyperparameters: “p”, “d”, “q”, corresponding to each part of its architecture: autoregressive part, integrated part, respectively moving average part. Each one, as said presents different opportunities for tunning the model: p may be tuned to determine past trends, but a balance is required, as too high of a value will lead to overfitting; the d parameter may improve the detection of more complex trends and the q parameter determines how many errors obtained through forecasting are utilized to predict the current value, which helps filtering out short-term variations in data. Generally, it is a good measure to not use too high of values, as they will present the model with overfitting.

![image](https://github.com/user-attachments/assets/65b0817c-3985-4f12-b264-255702d81a47)

After running a hyperparameter tunning script, a graph was generated to visualize the performance of different ARIMA order architectures. The MSE (mean squared error) is widely used to describe the performance of such models, as it directly quantifies how accurate the forecast is, in comparison to the actual data, which is done by computing the average squared difference between these two. After analyzing Figure 16, it can be determined that the models having a non-zero value of the parameters are able to more consistently follow trends and to achieve more consistent forecasts. To achieve a better balance between these, the order (1, 2, 1) was chosen for the final architecture of the model.

![image](https://github.com/user-attachments/assets/c347d428-7774-45a8-be15-36da07dabbfa)

The last Figure depicts the comparison between the predicted timestamps and the actual ones. This test has been conducted on a 300-sample dataset, containing the memory peaks pre-processed in the previous step, with a data split of 80% for training and 20% for testing. It is apparent that the model performs well when confronted with the test data, which is kept unknown during the training, as the forecast graph follows the actual data graph closely, both being aligned and similar in value. In the later part of the series, a slight deviation may be observed, which suggests that improvement is still possible. Despite this, when weighing in the performance of the model, the results are satisfactory for the scaling application, taking into consideration the low MSE values presented in the Figure above.

## 7.3.2. The Autoencoder – Forecaster LSTM Model – Performance 

The second model described in this paper was an LSTM model with an autoencoder – forecaster architecture. This architecture employed a 2000-point dataset for testing purposes, which was split 80% - 20% for training, respectively for testing. To achieve optimal result, the hyperparameters of this model (the learning rate, number of training epochs, batch size and also callbacks such as early stopping and adaptive learning), were also tuned. Another time series specific hyperparameter is the window size used to generate the sliding window dataset. Through testing, a window size of 100 inputs has been decided upon, as it provides plenty of past insight, vital to the model’s capability to detect trends. The initial learning rate was also chosen in such a manner, as to allow the model enough time to properly converge. To this contributes the number of training epochs too, which is under the control of an early stopping mechanism, to prevent unnecessary training, that would otherwise be degrading to the performance of the model. To assess this, the learning curve may be printed, which is a measure of how well the performance of a model does over time. The following figure depicts the training loss of the forecaster, which although set to train for more epochs, it is stopped after presenting consistency, regarding the loss over multiple iterations of the data, to prevent overfitting. The close alignment of both graphs after a few epochs exhibits the fact that the learning is efficient and that the model performs well, even with unknown data, as both graphs encounter very little loss. 

![image](https://github.com/user-attachments/assets/7f35e009-3e3c-4130-ac88-22a17f8f2ec3)

To further analyze the efficiency of the model a second graph can be utilized to describe it. This plot depicts the predicted timestamp plotted alongside the graph containing real points from the dataset. As in the case of the ARIMA model an 80% - 20% data split was performed.

![image](https://github.com/user-attachments/assets/a35169ca-deec-48d1-a2a2-7398c9cccf34)

The Figure above displays a similar performance to the one obtained by the ARIMA model. The prediction plot is aligned with the actual data plot but suffers from an increasing error at the end of the data, which still is a matter for improvement. It is also to state that the MAE and MSE are computed using the normalized value of the predicted timestamp, which means that any error present within might be greatly increased when applying the inverse transform to the final prediction. This is because the data used for training, the timestamps, are initially depicted using high values with high resolutions, meaning that even a small error might determine a large deviation from the expected value. This is evident in Figure 19, whereas said, despite the good alignment, errors might occur for the predicted values, which determine the increasing deviation, from the actual data graph over time. 

## 7.3.3. The BiLSTM-MF (Bidirectional LSTM with Minute Feature)

The second LSTM model presented in this paper, was designed with a different architecture in mind, and having an additional feature extracted, namely the minute part of the timestamp. Extracting additional features may help a model better converge upon a desirable output, but it also introduces uncertainty. As in the case of the previous model, the validation and training losses drop significantly after the first epochs and stabilize along the value of nearly 0, meaning that patterns are discovered correctly. The low value of the loss also describes a well-fitted model, able to generalize patterns from the input data.

![image](https://github.com/user-attachments/assets/0c6cd60b-9a9e-4d20-8828-ba71fe874e60)

Besides this, as previously discussed in the case of the previous LSTM model, another key graphical representation to determine the performance of a model, is the predicted graph in comparison to the actual data plot, as seen in the Figure below. When first taking in the graphical representation, it can be noticed, that the plot representing the predicted data presents clear irregularities. 

![image](https://github.com/user-attachments/assets/66273ab7-51a3-4f57-be0d-b73e697e80f6)

This can be attributed to the addition of a second feature to the training of the model; however, the overall trend is closely followed, meaning that the model is successful in forecasting accurate values. Despite any small fluctuations, time forecasting does not depend on the approximation of any individual irregularity, but on the adherence of the predicted values to the trend found within the input data, which is the case for this model. In comparison to the previous model, this architecture exhibits promising results in yielding closer forecasts to the actual data trend, as the deviation does not increase with the number of predictions, as observed in Figure 19.

## 7.3.4. Comparative Analysis of the Forecasting Models

After performing tests on all the presented models, Table 2 has been created to provide a comparative view between the performance of the presented models. Although, as presented previously, all the methods were able to follow the desired trend within the data, some demonstrated a superior ability in performing the forecasts. All the tests performed on the models were conducted on a 2000-point dataset, split 80% - 20%. As seen in the table below, the more analytical regression model performed best, with an MAE (computed for the normalized data) being an order of magnitude smaller than the other models. The same can be also said about the MSE, being the lowest value for the ARIMA model. Moreover, just by analyzing the target timestamp, which depicts what the subsequent data point in the input file should be, one can determine that the model which faired the best, was the ARIMA, followed by the BiLSTM-MF and trailed by the AE-LSTM. The prediction accuracy is by far the best for the auto-regression model, this is why it was used in the autoscaling application. In the interest of this paper, good accuracy was a requirement for the final scaling to be effective.

| Compared Metric                        | ARIMA (1,2,1)                | AE-LSTM          | BiLSTM-MF        |
|----------------------------------------|------------------------------|------------------|------------------|
| **Mean Absolute Error (MAE) – Normalized** | 0.00043                     | 0.06            | 0.063715        |
| **Mean Absolute Error (MAE)**          | 1558.18                      | 18283.25        | 9249.36         |
| **Mean Squared Error (MSE) – Normalized** | 2.502140e-07               | 0.01            | 0.006090        |
| **Next Predicted Time Stamp – Unix**   | 1716546594                   | 1716494720      | 1716553344      |
| **Next Predicted Time Stamp – HR (GMT)** | Friday, May 24, 2024, 10:29:54 AM | Thursday, May 23, 2024, 8:05:20 PM | Friday, May 24, 2024, 12:22:23 PM |
| **Target Timestamp**                   | 1716557400 / (Friday, May 24, 2024, 10:30:00 AM) | - | - |

Regardless of these results, the scenario enacted on these models was an ideal one, with a good periodicity, which would make the ARIMA preferable in this case, because this model types assumes the stationarity of data or that it can be made stationary, but this paper serves as a proof of concept, meaning that the other models also offer great insight in the domain of time forecasting. Although their results proved to be less satisfactory than desired in this case, they may yet still prove to be efficient in real-life situations, where periodicity between points of interest might not be so easy to determine and where larger amounts of data and more context regarding it, can be provided.

# 7.4. The Automatic Scaling Application - Effects 

Finally, it only remains to determine the performance of the entire scaling application. This can be done utilizing the log file created during scaling. While searching through the logs, two scenarios are apparent. The first is the normal operation of the scaler, which may be seen in Figure 22. This is described by the scale-up and scale-down time covering the target timestamp (the timestamp forecasted by the ML model), as well as the forecast coinciding with the detected timestamp (the timestamp retrieved after a peak detection operation), with a negligible error. 

![image](https://github.com/user-attachments/assets/a0abd298-2c18-4e4f-90b5-799a44c50465)

On the other hand, the presence of an error can also be observed in the log files, because of an erroneous forecast. This also leads to a subsequent erroneous prediction, but it is also notable that over a couple predictions, the normal functionality of the system is regained. The application rectifies itself and over two iterations, the normal operational status is regained.

![image](https://github.com/user-attachments/assets/5ae22f84-8004-48d3-a20c-0ad18a6854bd)

With over two continuous days of operation, a total of 100 scaling actions were attempted, out of which, only two encountered errors and the rest were successful. 

# 7.5. Conclusions

The key point of this paper revolves around the context of container-based infrastructure and orchestration to automate processes within a cluster. This paper provides extensive insight into the management of such a cluster, namely a Kubernetes cluster, starting with the setup of a VM running a Kubernetes distribution, observability features, memory leak scenarios, data extraction and processing and machine learning techniques for time forecasting. All of these are culminating in an application able to perform informed scaling decisions prior to their occurrence, based on forecasts generated by ML models.

As presented before, in a broader context, the key findings of this paper are the following: 
1.	The creation of VM and the importance of optimizing resource management within it, as resources always prove a limitation in realizing projects.
2.	The installation of lightweight Kubernetes distribution to manage the container infrastructure and its monitoring, which was performed by employing observability features.
3.	The integration of the two key components utilized in monitorization, those being Prometheus and Grafana and their customization, to make use of features such as, for data scraping or visualization and tools, for example email alerting
4.	The creation of a memory leak application defined using a custom Docker Image and tasked with simulating critical metrics over time and previewing the system’s response to this stress environment.
5.	Data extraction and processing scripts, utilizing scripting languages, such as Shell, as well as object-oriented programming languages, in the form of Python for the processing of the data and the creation of ML models.
6.	Machine Learning techniques such as ARIMA and LSTM, and other variations of said model (BiLSTM-MF, AE-LSTM), as well as the comparative analysis of the strengths and weaknesses of these models individually.
7.	An autoscaler application, able to dynamically adjust cluster resources based on the ML time forecasts, ensuring optimal cluster health.

Because of the multitude of diverse subjects, future implementations are still in measure and should be implemented to optimize these applications. Some of the proposed measures to enhance the capability of such a system are the following: 
1.	Defining custom Docker images for every additional resource deployed, to guarantee consistency, for all the instances of an application.
2.	Better cluster resource optimization, as currently tools such as Prometheus are too resource intensive and utilize a lot of cluster resources.
3.	The optimization of the current machine learning algorithms, as the LSTM models, despite having well – designed architectures, still present only lacking outputs; this could be done by collecting more data or further pre-processing it, fine tuning a more evolved architecture or by simply tuning the model using different parameter values. In the case of the LSTM models presented, a combined approach between the two, might provide more relevant outputs, because as it was showcased, both introduced different capabilities and pluses and by fine-tuning a combination of the two, it may lead to more accurate results.
4.	Implementing the scaling application using a LSTM model, able to depict trends within irregular data, where the ARIMA would not be able to do this.
5.	Implementing a ML model to also predict the amount of data that would be required for scaling, so that while scaling the limits of a resource, only necessary data will be utilized.

To conclude, this paper provided key insights into diverse technologies. By implementing these, it led to an automatic application able to perform informed scaling decisions for cluster management. As such, this paper provided the groundwork for future advancements in creating more self-sustainable and resilient IT infrastructures.

