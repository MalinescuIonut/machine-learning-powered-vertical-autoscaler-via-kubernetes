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

![Uploading image.png…]()



