#!/bin/bash

# Install MicroK8s
echo "Installing MicroK8s..."
sudo snap install microk8s --classic

# Check installation status
echo "Checking MicroK8s installation status..."
microk8s status

# Add the user to the microk8s group
echo "Adding user to microk8s group..."
sudo usermod -a -G microk8s $USER

# Change ownership of the .kube directory
echo "Changing ownership of .kube directory..."
sudo chown -R $USER ~/.kube

echo "MicroK8s installation and configuration complete!"
