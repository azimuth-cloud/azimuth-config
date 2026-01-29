# Debugging Zenith services

If a Zenith service does not become available, the most common causes are:

## Client not connecting to SSHD

The first thing that happens to connect a Zenith service is that the Zenith
client must connect to the Zenith SSHD. To see if a Zenith client is connecting,
check for the Zenith subdomain in the logs of the SSHD server:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth logs deploy/zenith-server-sshd [-f]
```

If there are no logs for the target Zenith subdomain, this usually indicates a
problem with the client. Check the logs for the client and restart it if
necessary. If problems persist, try restarting the Zenith SSHD:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/zenith-server-sshd
```

## Client not appearing in Zenith CRDs

The components of Zenith communicate using three
[Kubernetes CRDs](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/):

- `services.zenith.stackhpc.com` A reserved domain and associated SSH public
  key.
- `endpoints.zenith.stackhpc.com` The current endpoints for a Zenith service.
  This resource is updated to add the address, port and configuration of the
  Zenith SSH tunnel as the SSH tunnel is created.
- `leases.zenith.stackhpc.com` Heartbeat information for an individual SSH
  tunnel. Each Zenith SSH tunnel has its own lease resource that is regularly
  updated with a heartbeat.

If a Zenith service is not functioning as expected, check the state of the CRDs
for that service.

First, check that the service exists and has an SSH key associated:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get services.zenith
NAME                                   FINGERPRINT                                   AGE
igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn   WLo15SbKRadA5q1WIn6dToWT4Q+j05rZ5T+Zc/so4M0   13m
sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31   G6sdXwUfvdlosCB2yi40TEf5//ie2bgCxytrig4xpTA   13m
```

Next, check that there is at least one lease for the service and verify that it
is being regularly renewed:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get leases.zenith
NAME                                         RENEWED   TTL   REAP AFTER   AGE
sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-fn75d   7s        20    120          13m
igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-7tnqm   5s        20    120          14m
```

Finally, check that the endpoint is registered correctly in the endpoints
resource:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get endpoints.zenith igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn -o yaml
apiVersion: zenith.stackhpc.com/v1alpha1
kind: Endpoints
metadata:
  creationTimestamp: "2024-05-01T13:24:12Z"
  generation: 3
  name: igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn
  namespace: zenith-services
  ownerReferences:
  - apiVersion: zenith.stackhpc.com/v1alpha1
    blockOwnerDeletion: true
    kind: Service
    name: igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn
    uid: 378b39dc-9fce-4553-865e-edad2dd8d8b0
  resourceVersion: "7260"
  uid: 62badd6e-a5a7-452d-b346-04c2efd75a6c
spec:
  endpoints:
    7tnqm:
      address: 10.42.0.71
      config:
        backend-protocol: http
        skip-auth: false
      port: 42109
      status: passing
```

The address should be the pod IP of a Zenith SSHD pod, and the port should be
the allocated port reported by the client.

## OIDC credentials not created

Keycloak OIDC credentials for Zenith services for platforms deployed using
Azimuth are created by the
[azimuth-identity-operator](https://github.com/azimuth-cloud/azimuth-identity-operator).

To see if this step has happened, check the status of the `realm` and `platform`
resources created by the identity operator. They should all be in the `Ready`
phase:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl get realm,platform -A
NAMESPACE   NAME                                          PHASE   TENANCY ID      OIDC ISSUER                                           AGE
az-demo     realm.identity.azimuth.stackhpc.com/az-demo   Ready   xxxxxxxxxxxxx   https://identity.azimuth.example.org/realms/az-demo   4d2h

NAMESPACE   NAME                                                        PHASE   AGE
az-demo     platform.identity.azimuth.stackhpc.com/kube-mykubecluster   Ready   114s
```

If any of these resources stay in an unready state for more than a few minutes,
try restarting the identity operator:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/azimuth-identity-operator
```

If this doesn't work, check the logs for errors:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth logs deployment/azimuth-identity-operator [-f]
```

## Kubernetes resources for the Zenith service have not been created

If the CRDs for the service look correct, it is possible that the component that
watches the Zenith CRDs and creates the Kubernetes ingress for those services is
not functioning correctly.

This component creates Helm releases to deploy the resources for a service, so
first check that a Helm release exists for the service and is in the `deployed`
state:

```sh title="On the K3s node, targeting the HA cluster if deployed"
$ helm -n zenith-services list -a
NAME                                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                           APP VERSION
igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn    zenith-services 1               2024-05-01 13:24:13.36622944 +0000 UTC  deployed        zenith-service-0.1.0+846a545e   main
sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31    zenith-services 1               2024-05-01 13:24:41.219330845 +0000 UTC deployed        zenith-service-0.1.0+846a545e   main
```

Also check the state of the `Ingress`, `Service` and `EndpointSlice`s for the
service:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get ingress,service,endpointslice
NAME                                                                  CLASS   HOSTS                                                              ADDRESS        PORTS     AGE
ingress.networking.k8s.io/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-oidc   nginx   igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn.apps.45-135-57-238.sslip.io   192.168.3.49   80, 443   25m
ingress.networking.k8s.io/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn        nginx   igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn.apps.45-135-57-238.sslip.io   192.168.3.49   80, 443   25m
ingress.networking.k8s.io/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31        nginx   sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31.apps.45-135-57-238.sslip.io   192.168.3.49   80, 443   24m
ingress.networking.k8s.io/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-oidc   nginx   sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31.apps.45-135-57-238.sslip.io   192.168.3.49   80, 443   24m

NAME                                                TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)            AGE
service/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-oidc   ClusterIP   10.43.247.54    <none>        80/TCP,44180/TCP   25m
service/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn        ClusterIP   10.43.125.138   <none>        80/TCP             25m
service/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31        ClusterIP   10.43.234.107   <none>        80/TCP             24m
service/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-oidc   ClusterIP   10.43.7.75      <none>        80/TCP,44180/TCP   24m

NAME                                                                             ADDRESSTYPE   PORTS        ENDPOINTS    AGE
endpointslice.discovery.k8s.io/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-3010d        IPv4          42109        10.42.0.71   25m
endpointslice.discovery.k8s.io/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-oidc-kqx8h   IPv4          4180,44180   10.42.0.86   25m
endpointslice.discovery.k8s.io/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-f2086        IPv4          33857        10.42.0.71   24m
endpointslice.discovery.k8s.io/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-oidc-tkvqv   IPv4          4180,44180   10.42.0.88   24m
```

<!-- prettier-ignore-start -->
!!! tip "Ingress address not assigned"
    If an ingress resource does not have an address, this may be a sign that the ingress controller is not correctly configured or not functioning correctly.

!!! info "Services with OIDC authentication"
    When a service has OIDC authentication enabled, there will be two of each resource for each service, one of which will have the suffix `-oidc`.
<!-- prettier-ignore-end -->

Each service with OIDC authentication enabled gets a standalone service that is
responsible handling the interactions with the OIDC provider. To check the state
of these resources, use:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get deploy,po
NAME                                                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-oidc   1/1     1            1           33m
deployment.apps/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-oidc   1/1     1            1           33m

NAME                                                             READY   STATUS    RESTARTS   AGE
pod/igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn-oidc-7f6656bd98-9rrj2   1/1     Running   0          33m
pod/sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31-oidc-7ffbff4cd6-sr75w   1/1     Running   0          33m
```

If any of these resources look incorrect, try restarting the Zenith sync
component:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/zenith-server-sync
```

If this doesn't work, check the logs for errors:

```sh title="On the K3s node, targeting the HA cluster if deployed"
kubectl -n azimuth logs deployment/zenith-server-sync [-f]
```

## cert-manager fails to obtain a certificate

If you are using cert-manager to dynamically allocate certificates for Zenith
services it is possible that cert-manager has failed to obtain a certificate for
the service, e.g. because it has been rate-limited.

To check if this is the case, check the state of the certificates for the Zenith
services:

```command title="On the K3s node, targeting the HA cluster if deployed"
$ kubectl -n zenith-services get certificate
NAME                                       READY   SECRET                                     AGE
tls-igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn   True    tls-igxvo2okpkq834d1qbgtlhmm6xo4laj0dupn   30m
tls-sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31   True    tls-sh20tp1071hl3xtjw5cj4mwdy5t0v7qodj31   29m
```

If the certificate for the service is not ready, check the details for the
certificate using `kubectl describe` and check for any errors that have occured.
