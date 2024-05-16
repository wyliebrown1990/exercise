This project is an attempt to help simplify some of the work I was doing in another project and focus on delivering these core technologies:

**Docker-Compose deployment:**
1. Flask front end app -- complete
2. Postgres backend database (local) -- complete
3. Opentelemetry SDK and API instrumentation for tracing and metrics -- complete 
4. Opentelemetry Collector sending traces to Observe -- complete

docker buildx build --platform linux/amd64,linux/arm64 -t wyliebrown1990/exercise-app:1.0 --push .

docker-compose up --build

After making edits to application: 
docker-compose build app
docker-compose down
docker-compose up -d


**Kubernetes Deployment locally with miniKube: **
1. Deploy exercise-app -- complete
2. Deploy postgres -- Issue with config or connection TBD
3. Deploy otel-collector -- persistent error message and crashbackloop on pods "failed to create shim task: OCI runtime create failed: runc create failed: unable to start container process: exec: "/bin/sh": stat /bin/sh: no such file or directory: unknown" 

minikube start

docker buildx build --platform linux/amd64,linux/arm64 -t wyliebrown1990/exercise-app:1.0 --push .
docker buildx build --platform linux/amd64,linux/arm64 -t wyliebrown1990/otel/opentelemetry-collector-contrib:latest --push .
docker buildx build --platform linux/amd64,linux/arm64 -t postgres:13 --push .

kubectl apply -f postgres-deployment.yaml
kubectl apply -f otel-collector-deployment.yaml
kubectl apply -f app-deployment.yaml

kubectl get pods

How to debug: 
Otel-collector showed "RunContainerError" 
kubectl describe pod <ID>

**Kubernetes Deployment on AWS EKS:**
1. Deploy cluster, nodes and healty resources -- complete
2. Deploy exercise-ap, postgress and otel-collector -- pods keep crashing unclear what causes the error