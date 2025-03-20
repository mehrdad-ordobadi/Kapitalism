. convert capitalism deployment to kubernetes
. add metrics and logs scraping using Loki and Prometheus
. Grafana server must be served outside of the cluster

## Phase1:
> Adjust microservices source code to be ck8s compatible
> deploy locally using kustomazation
> containers can be stored on dockerhob

## Phase2:
> Deploy Grafana on an ec2 server using terraform and ansible
> adjust source code to add promethus capanility

## Phase3:
> deployment is to be kept locally
> Change manifest to helm chart templates

## Phase5:
> Migrate deployment to AWS
> Secrets must be pulled from AWS secrets manager and mounted into pods
> Add encryption (KMS)
> integrate TLS into load balancing

## Phase5: 
> Integrate ArgoCD into cluster


---------------------------------new plan----------------------------
## Phase1: 
> deploy microservices locally

## Phase2:
> Integrate linkerd with the local cluster - the following features will be added:
* set up linkerd in the cluster
* Need: hpa, health checks
* mTLS
* Tracing, Metrics, etc
* set up circuit-breakers, automatic retries
* Internal Loadbalancer