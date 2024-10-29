## 1. Setting up the Environment

# 1.1. Constructing the Virtual Machine


This project involves setting up an Ubuntu Server (20.04) on a VMware Workstation Pro (v17) virtual machine. The setup process includes installing VMware Workstation Pro, which can be downloaded from the official website: https://www.vmware.com/. An Ubuntu Server distribution can be installed from the official Ubuntu website: https://ubuntu.com/download/server. Resource allocations for the VM include 48 GB of disk space, 16 GB of RAM, and 8 CPU cores. Detailed steps for creating the VM are illustrated in the accompanying figure.


![Screenshot 2023-10-03 012843](https://github.com/user-attachments/assets/4f814bd3-2d9c-4c5f-a381-703eb711aa58)


# 1.2. Installing Microk8s

After the machine is up and running the chosen Kubernetes distribution can be installed. Microk8s can be installed using the following commands. 


```bash
1.  sudo snap install microk8s --classic
2.  microk8s status # check installation status
```

To complete the Microk8s setup the username of the VM, “ubuntu”, must be added to Micork8s. Ensuring this, the user “ubuntu” will have permissions granted to interact with the cluster and to be able to manage it. By running the second command “chown”, meaning “change owner”, the owner of the “.kube” directory will be set as “ubuntu”, giving the user full permissions over it.

```bash
1.	sudo usermod -a -G microk8s ubuntu
2.	sudo chown -R ubuntu ~/.kube
```


# 1.3. Installing Microk8s

