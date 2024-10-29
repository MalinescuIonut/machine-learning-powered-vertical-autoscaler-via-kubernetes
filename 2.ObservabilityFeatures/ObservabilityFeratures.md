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
Using the “get services” command, all the services running inside the cluster will be displayed. With the information now displayed, the services which the user wants to expose to outside environments can be chosen. For this implementation, Prometheus, Grafana and Alertmanager were edited to serve as NodePort services by running the “edit svc” command, followed up by the name of the service, as presented above. The type of the section can be modified as follows

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
