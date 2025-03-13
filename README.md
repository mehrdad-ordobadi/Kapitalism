## in order to run deploy this locally into minikube:

### 1.From /deployment/kubernetes run:

```
kubectl apply -k base/
```

### 2. Add ecommerce.local to hosts:

```
sudo echo "127.0.0.1 ecommerce.local" >> /etc/hosts
```
### 3. Create a tunnel to the ingress:

```
minikube service ingress-nginx-controller -n ingress-nginx
```

This will return the tunnelling address for the ingress. e.g.:
```
[ingress-nginx ingress-nginx-controller  http://127.0.0.1:55269
http://127.0.0.1:55270]
```

The tunnelling address for the ingress will be ecommerce.local:55269. You can access the dashboard page via http://ecommerce.local:55269/

#### Note:
Make sure ingress-nginx addon is enabled on minikube:

You can check the addons on minikube via:

```
minikube addons list
```

And you can enable the addon via:

```
minikube addons enable ingress
```