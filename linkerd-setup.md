## Step1: Add Linkerd Helm Repository

```
helm repo add linkerd https://helm.linkerd.io/stable
helm repo update
```

## Step 2: Install Linkerd CRDs

This installs the Custom Resource Definitions (CRDs) that Linkerd needs. CRDs extend Kubernetes API to support Linkerd-specific resources like ServiceProfiles. 

```
helm install linkerd-crds linkerd/linkerd-crds -n linkerd --create-namespace
``` 

## Step 3: Manually Generate Certificates

```
mkdir -p linkerd-certs && cd linkerd-certs
```

* Generate the root CA certificate (valid for 1 year)

```
step certificate create root.linkerd.cluster.local ca.crt ca.key \
  --profile root-ca --no-password --insecure \
  --not-after 8760h
```

* Generate the issuer certificate (valid for 1 year)

```
step certificate create identity.linkerd.cluster.local issuer.crt issuer.key \
  --profile intermediate-ca --no-password --insecure \
  --not-after 8760h --ca ca.crt --ca-key ca.key
```

These commands generate a Certificate Authority (CA) and an issuer certificate signed by that CA. These will enable Linkerd to:

* Secure communication between services with mTLS
* Verify the identity of each service
* Encrypt all internal traffic

# Step 4: Install Linkerd Control Plane with Manual Certificates

```
helm install linkerd-control-plane \
  --namespace linkerd \
  --set-file identityTrustAnchorsPEM=ca.crt \
  --set-file identity.issuer.tls.crtPEM=issuer.crt \
  --set-file identity.issuer.tls.keyPEM=issuer.key \
  linkerd/linkerd-control-plane
```
This installs the Linkerd control plane using the certificates you generated. You can verify installation via:

```
kubectl get pods -n linkerd
```

# Step 5: Install Linkerd Visualization Tools

```
helm install linkerd-viz \
  --namespace linkerd \
  linkerd/linkerd-viz
```

## Step6: Linkerd dashboard deployment patch:

```
# Edit the web deployment to modify the enforced-host parameter
kubectl patch deployment web -n linkerd --type=json -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args/6", "value": "-enforced-host=^(localhost|127\\.0\\.0\\.1|web\\.linkerd\\.svc\\.cluster\\.local|web\\.linkerd\\.svc|\\[::1\\]|linkerd\\.ecommerce\\.local)(:\\d+)?$"}]'
```

also add the following to your host file:

```
127.0.0.1 ecommerce.local linkerd.ecommerce.local
```

---------------installing via cli-----------------------

## Step1: install the cli:

```
curl -sL https://run.linkerd.io/install | sh
export PATH="$PATH:$HOME/.linkerd2/bin"
```

## Step2: Check cluster compatibility:

```
linkerd check --pre
```

## Step3: Install linkerd CRD:

```
linkerd install --crds | kubectl apply -f -
```

## Step4: Install linkerd:

local container is running using the Docker container runtime

```
linkerd install --set proxyInit.runAsRoot=true | kubectl apply -f -
```

----

next step investigate:

kubectl get pods -n linkerd
NAME                                      READY   STATUS    RESTARTS   AGE
linkerd-destination-55f66c5bc5-n2wmh      4/4     Running   0          4m14s
linkerd-identity-5fdc96c5f8-dfvmc         2/2     Running   0          4m15s
linkerd-proxy-injector-6df56b8bdf-z7d55   2/2     Running   0          4m14s
kubectl logs -n linkerd linkerd-destination-55f66c5bc5-n2wmh