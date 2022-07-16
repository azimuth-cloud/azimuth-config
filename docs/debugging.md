# Debugging Azimuth

### Accessing the AWX UI

In order to debug issues or to make changes to the Projects and Job Templates, it is often
useful to access the AWX UI.

With the default configuration the AWX UI is not exposed outside of the Kubernetes cluster,
but it can be accessed using
[Kubernetes Port Forwarding](https://kubernetes.io/docs/tasks/access-application-cluster/port-forward-access-application-cluster/).

First, you must retrieve the generated admin password:

```sh
kubectl -n azimuth get secret azimuth-awx-admin-password -o go-template='{{ .data.password | base64decode }}'
```

Then set up the forwarded port to the Azimuth UI service:

```sh
kubectl port-forward svc/azimuth-awx-service 8080:80
```

The AWX UI will now be available at `http://localhost:8080`, and you can sign in with the
username `admin` and the password from above.

It is also possible to configure AWX so that it provisions an `Ingress` resource for the
AWX UI - see [Customising the AWX deployment](#customising-the-awx-deployment) below.

