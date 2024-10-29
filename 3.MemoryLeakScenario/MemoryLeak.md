## 3. Creating a Memory Leak Scenario
The following step in the implementation is creating a memory leak scenario to simulate data for the future sections. To do this the “stress-ng” command will be utilized to use up memory at specific intervals determined by CronJobs, the Unix job schedulers. To separate this simulation from the observability namespace, a new resource is defined. This described definition of the namespace is linked in the appendix (“Stress-test Namespace Resource”).

# 3.1. Creating a Custom Docker Image

Seeing the benefits of Docker containers, the stress testing application will be defined using such an image. The Docker image “Stress Container Docker Image” provided in the appendix describes the architecture of the memory leak scenario. First, all the dependencies are integrated into the container, meaning a lightweight Linux image called “Alpine Linux” is pulled, thus setting the base image of the Docker file, the tool packages required to run the application are installed (includes stress-ng). After the container is prepared a CronJob is designed to run a “stress_script.sh” every 30 minutes. This script defines how the application will run the stress test.

```bat
    C:\stress-ng-docker>docker build -t **********/stress-testing-image:latest .
  [+] Building 14.6s (8/8) FINISHED                               docker:default
  C:\stress-ng-docker>docker login
  Authenticating with existing credentials...
  Login Succeeded
  
  C:\stress-ng-docker>docker push *******************/stress-testing-image:latest
  The push refers to repository [docker.io/****************/stress-testing-image]
  f140: Pushed
  c59f: Pushed
  94e5: Mounted from library/alpine

```
# 3.2. Creating a Deployment to manage the Memory Leak Application

To perform the memory leak scenario, an application is built inside a container managed by a pod, which is managed by a deployment. Having the resource managed by a deployment provides the application with a key benefit, being able to repair itself if any errors occur. A total of 512 MB of memory were allocated to this container, the task of the stress script being to overshoot this limit so that the Linux out-of-memory (OOM) killer, will stop the process and restart the pod, thus simulating a memory leak in the application. Because of the restart policy set, namely “Always”, the pod will restart itself and conduct the same task repeatedly. Since the Shell script running the stressor is defined within a ConfigMap, it is also mounted to the deployment and an initialization container performs the task of converting the script to an executable one within the pod. The entire deployment manifest file (“Memory Leak Application Deployment”) is present within this folder section.
