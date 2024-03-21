# Integration testing

`azimuth-ops` is able to generate integration tests for an [environment](../environments.md)
that can be executed against the deployed Azimuth to validate that it is working correctly.

Currently, the following tests can be generated:

  * Deploy and verify [CaaS clusters](../configuration/12-caas.md)
  * Deploy and verify [Kubernetes clusters](../configuration/10-kubernetes-clusters.md)
  * Deploy and verify [Kubernetes apps](../configuration/11-kubernetes-apps.md)

The generated test suites use [Robot Framework](https://robotframework.org/) to handle the
execution of the tests and gathering and reporting of results.

In Robot Framework,
[test cases](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#creating-test-cases)
are created by chaining together keywords imported from various
[libraries](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#using-test-libraries).
Robot Framework also allows the creation of
[custom keyword libraries](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#creating-test-libraries)
containing domain-specific keywords.

The tests generated by `azimuth-ops` use keywords from a
[custom library](https://github.com/stackhpc/azimuth-robotframework)
for interacting with Azimuth, which in turn uses the
[Azimuth Python SDK](https://github.com/stackhpc/azimuth-sdk) to interact with the
target Azimuth deployment.
The result is that a typical test case looks something like this:

```robotframework  title="Example of a generated test case"
*** Settings ***

Name          CaaS
Library       Azimuth
Test Tags     caas
Test Timeout  15 minutes


*** Test Cases ***


Create workstation
    [Tags]  workstation  create
    ${ctype} =  Find Cluster Type By Name  workstation
    ${params} =  Guess Parameter Values For Cluster Type  ${ctype}
    ${cluster} =  Create Cluster  test-rbe6w  ${ctype.name}  &{params}

Verify workstation
    [Tags]  workstation  verify
    ${cluster} =  Find Cluster By Name  test-rbe6w
    ${cluster} =  Wait For Cluster Ready  ${cluster.id}
    ${url} =  Get Cluster Service URL  ${cluster}  webconsole
    Open Zenith Service  ${url}
    Wait Until Page Title Contains  Apache Guacamole
    ${url} =  Get Cluster Service URL  ${cluster}  monitoring
    Open Zenith Service  ${url}
    Wait Until Page Title Contains  Grafana

Delete workstation
    [Tags]  workstation  delete
    ${cluster} =  Find Cluster By Name  test-rbe6w
    Delete Cluster  ${cluster.id}
```

This example will create a
[CaaS workstation](../configuration/12-caas.md#linux-workstation-appliance) using parameter
values that are guessed based on the cluster type and target Azimuth. It then waits for the
workstation to become `Ready` before verifying that the the Zenith services are behaving
as expected. Finally, the workstation is deleted.

## Generating and executing tests

Before tests can be generated and executed for an [environment](../environments.md), it must
be successfully deployed either [manually](../) or by [automation](./automation.md).

You must also have the Python dependencies installed on the machine that the tests will be
run from. The easiest way to do this is using the
[ensure-venv script](../deployment/index.md#python-dependencies), however the `requirements.txt`
can be used to install them into any Python environment:

```sh
pip install -U pip
pip install -r requirements.txt
```

The tests can then be generated and executed using the `run-tests` utility script:

```sh
# Activate the target environment
source ./bin/activate my-site

# Generate and run the tests
./bin/run-tests
```

## Configuring test generation

By default, tests cases are generated for:

  * All the installed CaaS cluster types
  * All the installed **active** (i.e. non-deprecated) Kubernetes cluster types
  * All the installed Kubernetes app templates

The following sections describe how to enable, disable and configure tests for the
different types of platform.

!!! tip

    The
    [generate_tests](https://github.com/stackhpc/ansible-collection-azimuth-ops/blob/main/roles/generate_tests/)
    role of `azimuth-ops` is responsible for generating the test cases.

    It has a
    [large number of variables](https://github.com/stackhpc/ansible-collection-azimuth-ops/blob/main/roles/generate_tests/defaults/main.yml)
    that can be used to tune the test generation. This document only discusses the most
    frequently used variables.

### CaaS cluster types

Test cases for CaaS cluster types perform the following steps:

  1. Build the cluster parameters using best-effort guesses plus overrides
  2. Create a cluster using the parameters
  3. Wait for the cluster to become `Ready`
  4. Check that the Zenith services for the cluster are accessible
  5. (Optional) Verify that the page title for the Zenith service contains some expected content
  6. Delete the cluster

!!! info  "Verification of Zenith service page titles"

    Step 5 is used to verify that the Zenith authentication loop brings you back to the
    correct service.

    Currently, no other verification of the behaviour of the service is performed.

!!! warning  "Best-effort guesses for parameter values"

    Best-effort guesses for parameter values are produced in the following way:

      * If the parameter has a default, use that.
      * For `cloud.size` parameters, use the smallest size that satisfies the constraints.
      * For `cloud.ip` parameters, find a free external IP or allocate one.

    All other parameters must be specified explicitly. Guesses can be overridden if not
    appropriate for the test environment.

By default, a test case is generated for all cluster types except those that are explicitly
disabled. This logic can be inverted, so that test cases are **only** generated for cluster
types where they are **explicitly enabled**, using the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
generate_tests_caas_default_test_case_enabled: false
```

The following variables are available to affect the test generation for each cluster type:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
# Indicates if the test case for the cluster type should be enabled
generate_tests_caas_test_case_{cluster_type}_enabled: true

# Used to override the value of the named parameter
generate_tests_caas_test_case_{cluster_type}_param_{parameter_name}: "<parameter_value>"

# Used to configure the expected title fragment for the named Zenith service
generate_tests_caas_test_case_{cluster_type}_service_{service_name}_expected_title: "<title fragment>"

# If a cluster takes a long time to deploy, the verify timeout can be increased
generate_tests_caas_test_case_{cluster_type}_verify_timeout: "45 minutes"
```

!!! warning

    If the cluster type or service name contain dashes (`-`), they will be replaced with
    underscores (`_`).

### Kubernetes cluster templates

For Kubernetes cluster templates, the generated test cases perform the following steps:

  1. Build the Kubernetes cluster configuration
  2. Create a Kubernetes cluster using the configuration
  3. Wait for the Kubernetes cluster to become `Ready`
  4. Check that the Zenith service for the Kubernetes Dashboard is working, if configured
  5. Check that the Zenith service for the monitoring is working, if configured
  6. Delete the Kubernetes cluster

!!! info  "Verification of Zenith services"

    Steps 4 and 5 use the same title-based verification as for CaaS clusters.

    No validation of actual behaviour is currently performed.

By default, a test case is generated for each **active**, i.e. non-deprecated, cluster template.

The following variables are available to affect the test generation for Kubernetes cluster
templates:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
# When false (the default), test cases are generated for all
# non-deprecated templates
#
# When true, test cases will only be generated for templates
# that target the latest Kubernetes version
generate_tests_kubernetes_test_cases_latest_only: false

# The ID of the flavors to use for control plane and worker nodes respectively
# By default, the smallest suitable size is used
generate_tests_kubernetes_test_case_control_plane_size:
generate_tests_kubernetes_test_case_worker_size:

# The number of workers that should be deployed for each test case
generate_tests_kubernetes_test_case_worker_count: 2

# Indicates whether the dashboard and monitoring should be enabled for tests
generate_tests_kubernetes_test_case_dashboard_enabled: true
generate_tests_kubernetes_test_case_monitoring_enabled: true
```

### Kubernetes app templates

For Kubernetes app templates, we first deploy a Kubernetes cluster to host the apps.
Once this cluster becomes `Ready`, the following steps are performed for each app:

  1. Create the app with inferred configuration
  2. Wait for the app to become `Deployed`
  3. For each specified Zenith service, check that it is accessible
  4. (Optional) Verify that the page title for the Zenith service contains some expected content
  5. Delete the app

!!! info  "Verification of Zenith services"

    As for other platform types, only title-based verification is performed for Zenith services.

!!! warning  "Overridding inferred configuration"

    Currently, it is not possible to override the inferred configuration for Kubernetes
    apps. This may mean it is not currently possible to test some Kubernetes apps that
    have required parameters.

!!! warning  "Specifying Zenith services"

    With Kubernetes apps, the expected Zenith services are not known up front as part
    of the app metadata, as they are for CaaS clusters.

    This means that the expected Zenith services for each app must be declared in config.

By default, a test case is generated for all app templates except those that are explicitly
disabled. This logic can be inverted, so that test cases are **only** generated for app
templates where they are **explicitly enabled**, using the following variable:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
generate_tests_kubernetes_apps_default_test_case_enabled: false
```

The Kubernetes cluster on which the apps will be deployed is configured using the
following variables:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
# The name of the Kubernetes cluster template to use
# If not given, the latest Kubernetes cluster template is used
generate_tests_kubernetes_apps_k8s_template:

# The ID of the flavors to use for control plane and worker nodes respectively
# By default, the smallest suitable size is used
generate_tests_kubernetes_apps_k8s_control_plane_size:
generate_tests_kubernetes_apps_k8s_worker_size:

# The number of workers that should be deployed for the cluster
generate_tests_kubernetes_apps_k8s_worker_count: 2
```

The following variables are available to affect the test generation for each app template:

```yaml  title="environments/my-site/inventory/group_vars/all/tests.yml"
# Indicates if the test case for the cluster type should be enabled
generate_tests_kubernetes_apps_test_case_{app_template}_enabled: true

# The names of the expected Zenith services for the app
generate_tests_kubernetes_apps_test_case_{app_template}_services:
  - service-1
  - service-2

# The expected title fragment for the named Zenith service
generate_tests_kubernetes_apps_test_case_{app_template}_service_{service_name}_expected_title: "<title fragment>"
```

!!! warning

    When used in variable names, dashes (`-`) in the app template name or Zenith service
    names will be replaced with underscores (`_`).

## Automated testing

If you are using [automated deployments](./automation.md), you can also automate tests
against your deployments.

As an example, the
[sample GitLab CI/CD configuration file](https://github.com/stackhpc/azimuth-config/blob/stable/.gitlab-ci.yml.sample)
includes jobs that run after each deployment to execute the configured tests against
the deployment.