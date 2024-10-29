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


