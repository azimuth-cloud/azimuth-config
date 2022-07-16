# Prerequisites

In order to deploy Azimuth, a small number of prerequisites must be fulfilled.

Firstly, there must be an OpenStack cloud onto which you will deploy Azimuth and which
the Azimuth installation will target.

The target cloud must support IPv4 and have an "external" network that floating IPs can be
allocated on. The target cloud must also support
[load-balancers via Octavia](https://docs.openstack.org/octavia/latest/index.html) if you
want to use the highly-available deployment mode or support
[Kubernetes Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
or
[LoadBalancer services](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
on tenant Kubernetes clusters.

There must be an OpenStack project into which Azimuth will be deployed, with appropriate
quotas. In particular, for a high-availability deployment the project should be permitted
to use **three** floating IPs - one for accessing the "management node", one for the
[Kubernetes Ingress controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
and one for the Zenith SSHD server.

You should create an
[Application Credential](https://docs.openstack.org/keystone/latest/user/application_credentials.html)
for the project and save the resulting `clouds.yaml` as `./environments/<name>/clouds.yaml`.

As discussed in the Azimuth Architecture document, Azimuth and Zenith expect to be given
control of a entire subdomain, e.g. `*.apps.example.org`, where Azimuth will be exposed as
`portal.apps.example.org` and Zenith services will have domains of the form
`<subdomain>.apps.example.org`. `azimuth-ops` does **not** manage DNS records, so you must
allocate a floating IP to the project and ensure that a **wildcard** DNS entry exists for
your chosen subdomain that points to the allocated IP. This IP will be used for the
Kubernetes Ingress controller.
