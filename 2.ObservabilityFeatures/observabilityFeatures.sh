#!/bin/bash

# Install Helm
echo "Installing Helm..."
sudo snap install helm --classic

# Enable Prometheus in MicroK8s
echo "Enabling Prometheus..."
sudo microk8s enable prometheus

# Check the status of all services
echo "Listing all services..."
microk8s kubectl get services --all-namespaces

# Edit Prometheus service to change to NodePort
echo "Editing Prometheus service to NodePort..."
microk8s kubectl -n observability edit svc kube-prom-stack-kube-prome-prometheus # Change the service type to NodePort in the editor

# Edit Grafana service to change to NodePort
echo "Editing Grafana service to NodePort..."
microk8s kubectl -n observability edit svc kube-prom-stack-grafana # Change the service type to NodePort in the editor

# Edit Alertmanager service to change to NodePort
echo "Editing Alertmanager service to NodePort..."
microk8s kubectl -n observability edit svc kube-prom-stack-kube-prome-alertmanager # Change the service type to NodePort in the editor

# Export Grafana deployment to YAML file
echo "Exporting Grafana deployment to YAML file..."
microk8s kubectl get deployment kube-prom-stack-grafana -n observability -o yaml > kube-prom-stack-grafana.yaml

# Open the YAML file in vi for editing
echo "Opening kube-prom-stack-grafana.yaml for editing..."
vi kube-prom-stack-grafana.yaml

# Apply the updated YAML configuration
echo "Applying the updated Grafana configuration..."
microk8s kubectl apply -f kube-prom-stack-grafana.yaml

echo "Script execution complete!"
