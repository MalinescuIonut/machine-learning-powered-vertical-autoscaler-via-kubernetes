![image](https://github.com/user-attachments/assets/3745f68e-ed1c-474d-9715-2e938b0d2edd)# Kubernetes Memory Leak Detection and Auto-Scaling with Machine Learning
This repository focuses on Kubernetes processes and addresses the effects of memory leaks within a cluster. It introduces a novel auto-scaling method using machine learning (ML) techniques, including Long Short-Term Memory (LSTM) and Autoregressive Integrated Moving Average (ARIMA). The ML models are trained on data collected from simulated memory leak scenarios.

# Key Features
Virtual Machine Setup: Includes the setup of a virtual machine (VM) and a micro-Kubernetes distribution (Microk8s).
Observability Tools: Integrates Prometheus and Grafana for monitoring and visualization.
Memory Leak Simulation: Provides scripts to generate and manage memory leak scenarios.
Data Processing: Tools for processing collected data for training ML models.
ML Model Training: Implements time-series forecasting with LSTM and ARIMA models.
Auto-Scaling System: Deploys a machine learning-powered auto-scaling system based on forecasted resource usage.

# Performance Monitoring
The impact of this implementation is measured by analyzing forecasted scaling intervals compared to actual peak memory usage moments. The repository also includes a comparative analysis of different ML model types and suggestions for future improvements.

![Picture1](https://github.com/user-attachments/assets/f145efeb-0be7-458f-91b3-efb2b5e283da)
