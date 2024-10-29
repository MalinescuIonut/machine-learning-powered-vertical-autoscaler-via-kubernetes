## 2.Setting up the Observability Features

# 2.1. Prometheus Package Installation 

The next step in this project’s setup is preparing its observability features. Data must be collected and saved to achieve the desired auto-scaler based on the ML script. To do this, the Prometheus toolkit will be installed, similarly to how Microk8s was installed previously.

```bash
1.	sudo snap install helm –classic
2.	sudo microk8s enable prometheus
```
Again, the first command is the one installing the Prometheus package, after which it must be enabled within the Microk8s cluster. After enabling it, all the resources installed from the package should be up and running, resources such as pods, deployments and services. After being enabled, the default credentials for using the observability tools, are returned. These are the following:

```bash
        Observability has been enabled (user/pass: admin/prom-operator)
```

# 2.2. Exposing the Observability Services

As depicted in the theoretical part of this paper, a service may be depicted in three ways: ClusterIP, NodePort and LoadBalancer, the default being ClusterIP. According to these settings, the DNS allocates an IP address for the service and in order for it to be accessible outside the cluster, this must be either NodePort or LoadBalancer. For the requirements of this paper, the NodePort option was chosen.


```bash
1.	microk8s kubectl get services --all-namespaces
2.	microk8s kubectl -n observability edit svc kube-prom-stack-kube-prome-prometheus 
3.	microk8s kubectl -n observability edit svc kube-prom-stack-grafana 
4.	microk8s kubectl -n observability edit svc kube-prom-stack-kube-prome-alertmanager
```
Using the “get services” command, all the services running inside the cluster will be displayed. With the information now displayed, the services which the user wants to expose to outside environments can be chosen. For this implementation, Prometheus, Grafana and Alertmanager were edited to serve as NodePort services by running the “edit svc” command, followed up by the name of the service, as presented above. The type of the section can be modified as follows:

```bash
        ubuntu@mvictor-vm-1:~$ microk8s kubectl get services -n observability
        NAME                                       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                                                                                                                       AGE
        alertmanager-operated                      ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP                                                                                                    9d
        kube-prom-stack-grafana                    NodePort    10.152.183.185   <none>        80:32612/TCP                                                                                                                  9d
        kube-prom-stack-kube-prome-alertmanager    NodePort    10.152.183.194   <none>        9093:30318/TCP                                                                                                                9d
        kube-prom-stack-kube-prome-operator        ClusterIP   10.152.183.131   <none>        443/TCP                                                                                                                       9d
        kube-prom-stack-kube-prome-prometheus      NodePort    10.152.183.253   <none>        9090:31628/TCP                                                                                                                9d
        kube-prom-stack-kube-state-metrics         ClusterIP   10.152.183.162   <none>        8080/TCP                                                                                                                      9d
```
# 2.3. Setting up Grafana Monitoring

## 2.3.1. Ensuring Data Persistency

The following step in the implementation is to properly set up Grafana itself. In order for modifications applied to the Grafana web interface to be saved through system reboots, a persistent volume must be created. To achieve this, a persistent volume (PV) resource must be defined. The file can be created using the UNIX command “touch” and then edited using any text editor like “cat” or “vi”. The grafana-pv.yaml file contained within the appendix part of this paper describes the configuration of the PV. Under the specification section, the following are defined: the amount of storage allocated, 5GB, the fact that only one node may have this volume mounted to itself and the path in which the data will be stored (“/mnt/data/grafana”). 

```bash
          spec:
          capacity:
            storage: 5Gi
          accessModes:
            - ReadWriteOnce
          storageClassName: standard
          hostPath:
            path: /mnt/data/grafana
          persistentVolumeReclaimPolicy: Retain
```

To access the PV previously a private volume claim (PVC) resource must be created. Its configuration is defined within a YAML file and can be found in the appendix of this paper as: grafana-pvc.yaml. The important specifications here are the amount of memory requested from the PV, being 5 GB, and the name of the volume, which is to be bound to the PVC, namely the one created previously, “grafana-storage”.

```bash
        metadata:
          name: grafana-storage-claim
          namespace: observability
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 5Gi
          storageClassName: standard
          volumeName: grafana-storage
```

After the configuration are saved, these must be applied using the “kuebctl apply -f” followed up by the name of the file. If everything is correct, when retrieving the PVC within the cluster, it should be bound to the PV.

```bash
        kube@kube:~$ microk8s kubectl get pvc --all-namespaces 
        NAMESPACE       NAME                    STATUS   VOLUME            CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE observability   grafana-storage-claim   Bound    grafana-storage   5Gi       RWO            standard       <unset>                 52d

```
The next step in ensuring the data persistency within the Grafana service is to modify its deployment running inside the cluster. The configuration file of the Grafana deployment should be retrieved locally and modified according to the created PVC and PV. This can be done utilizing the following command, which will save the file under the name “kube-prom-stack-grafana.yaml”, after which it can be edited using the vi text editor.

```bash
1.	microk8s kubectl get deployment kube-prom-stack-grafana -n observability -o yaml > kube-prom-stack-grafana.yaml
2.	vi kube-prom-stack-grafana.yaml
3.	microk8s kubectl apply -f kube-prom-stack-grafana.yaml

```

Inside the file, the following modifications should be made to ensure data persistency. Under the volumeMounts section the mount path should be changed to the one defined within the PV, as seen below.

```bash
        ubuntu@mvictor-vm-1:~$ cat kube-prom-stack-grafana.yaml
        ...
        volumeMounts:
            - mountPath: /etc/grafana/grafana.ini
              name: config
              subPath: grafana.ini
            - mountPath: /mnt/data/grafana
              name: grafana-storage
```

The path defined within the PV, namely “/mnt/data/grafana” should also be added under the “GF_PATHS_DATA” section.

```bash
        ubuntu@mvictor-vm-1:~$ cat kube-prom-stack-grafana.yaml
        ... 
        - name: GF_PATHS_DATA
                  value: /mnt/data/grafana
```

The final modification required for the Grafana deployment file is to specify that the volume defined in the volumeMounts section (grafana-storage) is backed up by the PVC resource named “grafana-storage-claim” defined previously. This modification is done under the volumes section of the configuration.

```bash
        ubuntu@mvictor-vm-1:~$ cat kube-prom-stack-grafana.yaml
        ... 
        volumes:
        - configMap:
            defaultMode: 420
            name: kube-prom-stack-grafana
          name: config
        - name: grafana-storage
            persistentVolumeClaim:
            claimName: grafana-storage-claim

```

## 2.3.2. Managing Grafana Dashboard

After ensuring Grafana’s data persistency, modifications can be now made to its Dashboard UI that will be kept through reboots. The UI can be accessed by using the IP address of the machine combined with port provided to the service. To access it, such a link may be composed: http://10.8.8.188:32612/.

When accessing this link, the user will be greeted with a Log-in screen, the credentials for which were provided during the installation of the Prometheus package (user/pass: admin/prom-operator). After logging into the UI, a custom dashboard can be created to display all the relevant information required to monitor the cluster.

```bash
        ubuntu@mvictor-vm-1:~$ microk8s kubectl get services -n observability
        NAME                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)         AGE                                                                                                           
        ...
        kube-prom-stack-grafana       NodePort   10.152.183.185   <none>        80:32612/TCP    9d                                                                                               
```

![Screenshot 2024-10-29 184751](https://github.com/user-attachments/assets/351fecb9-8d89-4131-8f37-00e015685ff0)

The figure above describes how a dashboard can be customized by creating individual panels, each displaying distinct data. By making use of PromQL, the query language specifically designed for querying Prometheus, different metrics can be displayed. In the case above, the total memory usage across the node is graphically presented over time, by querying both the free memory and the total memory of the node. The interval between data points may also be chosen to display more or less points. It is also possible to display older data, since data scraped by Prometheus is saved over a longer period. This is done by selecting the querying time range. For this implementation the following metrics are displayed inside the dashboard: the Prometheus Memory Usage, the Stress-Testing Pods memory usage, the total memory usage and the CPU usage. These are displayed using the PromQL syntaxes found in the following table:

| Metric Displayed                  | PromQL Syntax                                                                                                                                                                            |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Prometheus Memory Usage           | `sum(container_memory_usage_bytes{namespace="observability", pod="prometheus-kube-prom-stack-kube-prome-prometheus-0"}) by (pod) / 1024 / 1024`                                         |
| Stress – Testing Pod Memory Usage | `sum(container_memory_usage_bytes{namespace="stress-test", pod=~"stress-testing-deployment-.*"}) by (pod) / 1024 / 1024`                                                                 |
| Stress – Testing Pod Memory Usage % | `(sum(container_memory_usage_bytes{namespace="stress-test", pod=~"stress-testing-deployment-.*"})  by (pod) / 1024 / 1024) / 512 * 100`                                               |
| Memory Usage %                    | `100 * (1 - (node_memory_MemFree_bytes / node_memory_MemTotal_bytes))`                                                                             |
| CPU Usage                         | `100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`                                                                                |

## 2.3.3. Setting up Grafana SMTP

Automated alerting systems are an important tool for maintaining optimal cluster health. By transmitting alerts, problems that may occur can be brought into the forefront, so that they are dealt with in real-time. Grafana provides this functionality. This paper also presents email alerting, which can be configured as follows. To enable this, the Grafana ConfigMap must contain a configured Simple Mail Transfer Protocol (SMTP). The ConfigMap can be configured using the “kubectl edit” command, which will also automatically apply the changes done to it.   

```bash
1.	microk8s kubectl get configmaps -n observability
2.	microk8s kubectl edit configmap kube-prom-stack-grafana -n observability 

```

The SMTP field is configured as follows. For email alerting to be possible, an SMTP service is required to process and automate the alerting. For this implementation, Twilio’s SendGrid API has been used, which can be accessed via their official website: https://www.twilio.com/en-us/sendgrid/email-api, this will act as the host, namely (“smtp.sendgrid.net” – via port 465, which is associated to SMTP services). After registering on Twilio’s website, a secret API key will be generated required to access the service. The fields need to be configured with this key, which acts as a password, as well as with the email address utilized by SendGrid to send the alerting emails. The name for the sender address can also be customized here.

```bash
    [smtp]
    enabled = true
    host = smtp.sendgrid.net:465
    user = apikey
    password = ********************
    skip_verify = true
    from_address = alertgrafanalic@gmail.com
    from_name = Grafana 
```

