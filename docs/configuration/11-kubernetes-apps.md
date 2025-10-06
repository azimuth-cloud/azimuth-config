# Kubernetes apps

Azimuth allows operators to provide a catalog of applications (apps) that users are able to
install onto their Kubernetes clusters via the Azimuth user interface. Multiple apps can
be installed on the same Kubernetes cluster, and each app gets its own namespace.

A Kubernetes app in Azimuth essentially consists of a
[Helm chart](https://helm.sh/docs/topics/charts/). Azimuth manages specially annotated instances
of the `HelmRelease` resource from the
[Cluster API addon provider](https://github.com/azimuth-cloud/cluster-api-addon-provider) to install
and upgrade apps on the target cluster. These apps can be [integrated with Zenith](#zenith-integration)
to expose services to the user without requiring the use of
[LoadBalancer services](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
or [Kubernetes ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/).

The available apps and the available versions of those apps are determined by instances of a
[custom resource](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
provided by the
[Azimuth Kubernetes operator](https://github.com/azimuth-cloud/azimuth-capi-operator) -
`apptemplates.azimuth.stackhpc.com` - which references a chart in a
[Helm chart repository](https://helm.sh/docs/topics/chart_repository/). Azimuth uses the
[chart metadata](https://helm.sh/docs/topics/charts/#the-chartyaml-file) to generate the user
interface for the app template, and the [values schema](https://helm.sh/docs/topics/charts/#schema-files)
for the chart to generate a form for collecting input from the user.

Azimuth also renders the output of the [NOTES.txt](https://helm.sh/docs/chart_template_guide/notes_files/)
file in the user interface, so this can be used to describe how to consume the application.

<!-- prettier-ignore-start -->
!!! warning
    If the chart does not have a values schema, the generated form will be blank and the chart will be deployed with the default values.

!!! tip
    In addition, a file called `azimuth-ui.schema.yaml` can be included to apply some small customisations to the generated form, like selecting different controls.
    See the [azimuth-charts](https://github.com/azimuth-cloud/azimuth-charts) for examples.
<!-- prettier-ignore-end -->

## Default app templates

Azimuth comes with the following app templates enabled by default:

`jupyterhub`
: Allows the user to deploy [JupyterHub](https://jupyter.org/hub) on their clusters. JupyterHub
provides a multi-user environment for using [Jupyter notebooks](https://jupyter.org/) where
each user gets their own dynamically-provisioned notebook server and storage. The JupyterHub
notebook profiles can be customised by the Azimuth administrator to provide users with required
environments - see
[user notebook profiles](https://github.com/azimuth-cloud/azimuth-charts/blob/54a06cfc08acf5a9147e56a23de2d018261d1f82/jupyterhub-azimuth/values.yaml#L7-L15).
The Jupyter notebook interface is exposed using [Zenith](./08-zenith.md).

`daskhub`
: A JupyterHub instance with [Dask](https://www.dask.org/) integration. Dask is a library that aims
to simplify the process of scaling data-intensive Python applications, such as those using
[Numpy](https://numpy.org/) or [pandas](https://pandas.pydata.org/). DaskHub installs
[Dask Gateway](https://gateway.dask.org/) alongside JupyterHub and configures them so that
they integrate seamlessly. This allows users to easily create Dask clusters in their notebooks
that scale out by creating pods on the underlying Kubernetes cluster. As with `jupyterhub`
above, the notebook interface is exposed using Zenith.

`binderhub`
: A JupyterHub instance with [Binder](https://mybinder.readthedocs.io/en/latest/) integration.
BinderHub allows you to create custom computing environments that can be shared and used by
many remote users. As with `jupyterhub` above, the notebook interface is exposed using Zenith.

`kubeflow`
: Allows users to deploy the [Kubeflow](https://www.kubeflow.org/) machine learning toolkit
on their clusters. Kubeflow provides an interface for easily accessing best-of-breed machine
learning systems using Jupyter notebooks and [TensorFlow](https://www.tensorflow.org/).

`huggingface-llm`
: A generative AI chatbot service backed by a [HuggingFace](https://huggingface.co) large language
model. A convenient web interface is exposed via Zenith and the backend API is directly accessible
to other applications running on the same Kubernetes cluster for programmatic use cases. For
further details, see [this blog post](https://stackhpc.com/running-large-language-models-on-openstack.html).

These can be disabled by setting the following variables:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_capi_operator_app_templates_jupyterhub_enabled: false
azimuth_capi_operator_app_templates_daskhub_enabled: false
azimuth_capi_operator_app_templates_binderhub_enabled: false
azimuth_capi_operator_app_templates_kubeflow_enabled: false
azimuth_capi_operator_app_templates_huggingface_llm_enabled: false
```

## Custom app templates

If you have Helm charts that you want to make available as apps, you can define them as follows:

```yaml title="environments/my-site/inventory/group_vars/all/variables.yml"
azimuth_capi_operator_app_templates_extra:
  # The key is the name of the app template
  my-custom-app:
    # Access control annotations
    annotations: {}
    # The cluster template specification
    spec:
      # This is the only required field, and determines the chart that is used
      chart:
        # The chart repository containing the chart
        repo: https://my.company.org/helm-charts
        # The name of the chart that the template is for
        name: my-custom-app
```

<!-- prettier-ignore-start -->
!!! info "Access control"
    See access control for more details on the access control annotations.
    [Access control](./13-access-control.md)
<!-- prettier-ignore-end -->

By default, Azimuth will use the last 5 stable versions of the chart (i.e. versions without a
prerelease part, see [semver.org](https://semver.org/)) and the `name`, `icon` and `description`
from the [Chart.yaml file](https://helm.sh/docs/topics/charts/#the-chartyaml-file) in the chart
to build the user interface. A chart annotation is also supported to define the human-readable
label:

```yaml title="my-chart/Chart.yaml"
annotations:
  azimuth.stackhpc.com/label: My Custom App
```

This behaviour can be customised for each app template using the following optional fields:

`label`
: The human-readable label for the app template, instead of the annotation from `Chart.yaml`.

`logo`
: The URL of the logo for the app template, instead of the `icon` from `Chart.yaml`.

`description`
: A short description of the app template, instead of the `description` from `Chart.yaml`.

`versionRange`
: **Default:** `>=0.0.0` (stable versions only).  
 The range of chart versions to consider.  
 Must be a comma-separated list of constraints, where each constraint is an operator followed
by a [SemVer version](https://semver.org). The supported operators are `==`, `!=`, `>`, `>=`,
`<`and `<=`.  
 Prerelease versions are only considered if the _lower bound_ includes a prerelease part.
If no lower bound is given, an implicit lower bound of `>=0.0.0` is used.  
 Some examples of valid ranges:

  <ul>
    <li><code>>=0.0.0-0</code> - all versions, including prerelease versions like <code>1.0.0-alpha.1</code></li>
    <li>
      <code><2.0.0</code> - all stable versions matching <code>0.X.Y</code> and <code>1.X.Y</code> (implicit lower bound)
    </li>
    <li>
        <code>>=1.0.0,<3.0.0,!=2.1.5</code> - all stable versions matching <code>1.X.Y</code> or
        <code>2.X.Y</code> except <code>2.1.5</code> (useful for excluding specific versions with
        known issues)
  </ul>

`keepVersions`
: **Default:** 5.  
 The number of versions to keep.  
 This is used to limit the size of the `AppTemplate` resource, because etcd has limits on the
maximum size of objects (usually approx. 1MB). This will need to be smaller if the chart
has a large values schema.

`syncFrequency`
: **Default:** 86400 (24 hours).  
 The number of seconds to wait before checking for new versions of the chart.

`defaultValues`
: **Default:** `{}`.  
 Default values for deployments of the app, on top of the chart defaults.

## Zenith integration

When [Zenith is enabled](./08-zenith.md), every Kubernetes cluster created by Azimuth has an
instance of the [Zenith operator](https://github.com/azimuth-cloud/zenith/tree/main/operator) watching
it. This operator makes two Kubernetes custom resources available that can be used to expose a
[Kubernetes service](https://kubernetes.io/docs/concepts/services-networking/service/) to users
without using `type: NodePort`, `type: LoadBalancer` or
[Kubernetes ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/):

`reservations.zenith.stackhpc.com`
: Represents the reservation of a Zenith domain, and results in the generation of a
Kubernetes secret containing an SSH keypair associated with the allocated domain.

`clients.zenith.stackhpc.com`
: Defines a Zenith client, pointing at a Zenith reservation and upstream Kubernetes service.

In addition, services can benefit from the project-level authentication and authorization
that is performed by Zenith at it's proxy to prevent unauthorised users from accessing the
service. The Zenith services associated with an app are monitored and made available in the
Azimuth user interface, making the apps easy to use.

Azimuth supports the following annotations on the reservation to determine how the service
is rendered in the user interface:

```yaml
annotations:
  azimuth.stackhpc.com/service-label: "My Fancy Service"
  azimuth.stackhpc.com/service-icon-url: https://my.company.org/images/my-fancy-service-icon.png
```

It is possible to add Zenith integration to an existing chart by creating a new parent chart
with the existing chart as a [dependency](https://helm.sh/docs/chart_best_practices/dependencies/).
You can define templates for the Zenith resources in the parent chart, pointing at services
created by the child chart.

This is the approach taken by the [azimuth-charts](https://github.com/azimuth-cloud/azimuth-charts)
that provide the default `jupyterhub` and `daskhub` apps.
