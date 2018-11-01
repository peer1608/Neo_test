# Neo Test

Neo software test

## Test Challenge

Create an application to store, retrieve, delete images 
Manage images into albums
UI page to shows store, retrieve, delete image/albums events
Data need to be available even after the service restarts
Optionally UI page to display images of album
Benchmark performance of http end points.
Data need to be available even after the service restarts

### Prerequisites

Minikube 
Docker

### Album manager application implementation

- Web application is created using Flask framework in Python language
- Prometheus is deployed in Kubernetes
- Web Application will be monitored by Prometheus
- Data will be retained even after the service restarts. This is achieved using Persistent Volumes & Persistent Volumes Claims option in kubernetes. Have used 'host path' as Persistent Volume.

####Application Functionality

- Uploading & store an image inside album
- List names all available album(s) & images stored inside the album
- List names all images stored inside the given album
- View an image inside the given album
- Delete an image inside the given album
- View the list of events received by the application

### Deploying the application in Kubernetes

Check out https://github.com/peer1608/Neo_test.git

- Navigate to Neo_test folder
	cd Neo_test

- Build docker image using files from album_manager_docker/
	docker build -t album_manager_docker/neo_test_album:v28 .

- Deploy Metrics server & Prometheus server and configure the same
	kubectl create -f prometheus-operator.yaml
	kubectl create -f metrics_server.yml
	kubectl create configmap prometheus-server-conf --from-file=prometheus.yml  
	kubectl create -f deployment.yml  
	kubectl create -f promethous-service.yml  

- Create a Persistent volume & Persistent volume claim
	kubectl create -f pv-volume.yaml
	kubectl create -f pv-claim.yaml

- Deploy the application & service
	kubectl create -f app_deployment.yml 
	kubectl create -f app_service.yml

## Application usage

- Find the Application IP & port from Kubernetes. http://<IPAddress>:<port>
- Launch the application

- Uploading & store an image inside album
	- URL: http://<IPAddress>:<port>/api/v1/resources/upload
	- Method: GET, POST
	- Arguments: Album Name, Image file

- List names all available album(s) & images stored inside the album
	- URL: http://<IPAddress>:<port>/api/v1/resources/listalbum/all
	- Method: GET

- List names all images stored inside the given album
	- URL: http://<IPAddress>:<port>/api/v1/resources/listalbum?albumName=<album_Name>
	- Method: GET

- View an image inside the given album
	- URL: http://<IPAddress>:<port>/api/v1/resources/view?imageName=<album_Name>:<image_Name>
	- Method: GET

- Delete an image inside the given album
	- URL: http://<IPAddress>:<port>/api/v1/resources/delete?imageName=<album_Name>:<image_Name>
	- Method: GET

- View the list of events received by the application
	- URL: http://<IPAddress>:<port>/api/v1/resources/events
	- Method: GET
		
