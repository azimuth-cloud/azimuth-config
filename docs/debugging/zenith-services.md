# Debugging Zenith services

If a Zenith service does not become available, the most common causes are:

## Client not connecting to SSHD

The first thing that happens to connect a Zenith service is that the Zenith client
must connect to the Zenith SSHD. To see if a Zenith client is connecting, check for the
Zenith subdomain in the logs of the SSHD server:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth logs deploy/zenith-server-sshd [-f]
```

If there are no logs for the target Zenith subdomain, this usually indicates a problem
with the client. Check the logs for the client and restart it if necessary. If problems
persist, try restarting the Zenith SSHD:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/zenith-server-sshd
```

## Client not registered in Consul

Once a client has connected to SSHD successfully, it should get registered in
[Consul](https://www.consul.io/).

To determine if this is the case, it is useful to access the Consul UI. As discussed
in [Monitoring and alerting](../configuration/14-monitoring.md), the Consul UI
is exposed as `consul.<ingress base domain>`, e.g. `consul.azimuth.example.org`,
and is protected by a username and password.

The default view shows Consul's view of the services, where you can check if the
service is being registered correctly.

Clients not registering correctly in Consul usually indicates an issue with Consul
itself. Futher information for debugging Consul issues is provided in
[Debugging Consul](consul.md).

If the issue persists once Consul issues are ruled out, try restarting SSHD:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/zenith-server-sshd
```

## OIDC credentials not created

Keycloak OIDC credentials for Zenith services for platforms deployed using Azimuth are created
by the [azimuth-identity-operator](https://github.com/stackhpc/azimuth-identity-operator).

To see if this step has happened, check the status of the `realm` and `platform` resources
created by the identity operator. They should all be in the `Ready` phase:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl get realm,platform -A
NAMESPACE   NAME                                          PHASE   TENANCY ID      OIDC ISSUER                                           AGE
az-demo     realm.identity.azimuth.stackhpc.com/az-demo   Ready   xxxxxxxxxxxxx   https://identity.azimuth.example.org/realms/az-demo   4d2h

NAMESPACE   NAME                                                        PHASE   AGE
az-demo     platform.identity.azimuth.stackhpc.com/kube-mykubecluster   Ready   114s
```

If any of these resources stay in an unready state for more than a few minutes, try restarting
the identity operator:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/azimuth-identity-operator
```

## Kubernetes resources for the Zenith service have not been created

If the service exists in Consul, it is possible that the process that synchronises Consul
services with Kubernetes resources is not functioning correctly. To check if Kubernetes
resources are being created, run the following command and check that the `Ingress`,
`Service` and `Endpoints` resources have been created for the service:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n zenith-services get ingress,service,endpoints
NAME                                                            CLASS   HOSTS                                                     ADDRESS         PORTS     AGE
ingress.networking.k8s.io/cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g   nginx   cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g.azimuth.example.org   96.241.100.96   80, 443   2d
ingress.networking.k8s.io/i03xvflgk1zmtcsdm2x5z5lz9qz05027euw   nginx   i03xvflgk1zmtcsdm2x5z5lz9qz05027euw.azimuth.example.org   96.241.100.96   80, 443   2d
ingress.networking.k8s.io/pxmvy7235x2ggfvf2op615gvz2v59wkqglc   nginx   pxmvy7235x2ggfvf2op615gvz2v59wkqglc.azimuth.example.org   96.241.100.96   80, 443   2d
ingress.networking.k8s.io/txn3zidfdnru5rg109voh848n51rvicmr1s   nginx   txn3zidfdnru5rg109voh848n51rvicmr1s.azimuth.example.org   96.241.100.96   80, 443   2d

NAME                                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g   ClusterIP   172.27.10.109    <none>        80/TCP    2d
service/i03xvflgk1zmtcsdm2x5z5lz9qz05027euw   ClusterIP   172.30.203.227   <none>        80/TCP    2d
service/pxmvy7235x2ggfvf2op615gvz2v59wkqglc   ClusterIP   172.28.51.148    <none>        80/TCP    2d
service/txn3zidfdnru5rg109voh848n51rvicmr1s   ClusterIP   172.29.136.245   <none>        80/TCP    2d

NAME                                            ENDPOINTS                                                     AGE
endpoints/cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g   172.18.152.99:34665                                           2d
endpoints/i03xvflgk1zmtcsdm2x5z5lz9qz05027euw   172.18.152.99:39409                                           2d
endpoints/pxmvy7235x2ggfvf2op615gvz2v59wkqglc   172.18.152.99:44761,172.18.152.99:36483,172.18.152.99:46449   2d
endpoints/txn3zidfdnru5rg109voh848n51rvicmr1s   172.18.152.99:45379                                           2d
```

!!! tip

    If an ingress resource does not have an IP, this may be a sign that the ingress controller
    is not correctly configured or not functioning correctly.

If they do not exist, try restarting the Zenith sync component:

```sh  title="On the K3S node, targetting the HA cluster if deployed"
kubectl -n azimuth rollout restart deployment/zenith-server-sync
```

## cert-manager fails to obtain a certificate

If you are using cert-manager to dynamically allocate certificates for Zenith services it
is possible that cert-manager has failed to obtain a certificate for the service, e.g. because
it has been rate-limited.

To check if this is the case, check the state of the certificates for the Zenith services:

```command  title="On the K3S node, targetting the HA cluster if deployed"
$ kubectl -n zenith-services get certificate
NAME                                      READY   SECRET                                    AGE
tls-cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g   True    tls-cjzm03yczuj6oqrj3h8htl4u1bbx96qd53g   2d
tls-i03xvflgk1zmtcsdm2x5z5lz9qz05027euw   True    tls-i03xvflgk1zmtcsdm2x5z5lz9qz05027euw   2d
tls-txn3zidfdnru5rg109voh848n51rvicmr1s   True    tls-txn3zidfdnru5rg109voh848n51rvicmr1s   2d
```

If the certificate for the service is not ready, check the details for the certificate using
`kubectl describe` and check for any errors that have occured.
