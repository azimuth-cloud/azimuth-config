# Build your own Azimuth App

One of the main goals of Azimuth is to provide self-service platforms for advanced research computing. In order to achieve such a goal, it is unrealistic to expect that the default Azimuth apps created by StackHPC will fit the requirements of all users. Thankfully, due to the loosely coupled nature of the various components which make up an Azimuth deployment, it is relatively straightforward to develop and deploy custom, site-specific apps. A suggested workflow for carrying out such a task is outlined below.

## CaaS Appliances

The [azimuth-sample-appliance](https://github.com/stackhpc/azimuth-sample-appliance) provides a detailed and well documented example of the suggested structure for a custom CaaS appliance. The key components are:

- An entry point playbook (e.g [sample-appliance.yml](https://github.com/stackhpc/azimuth-sample-appliance/blob/main/sample-appliance.yml)) which is the top level Ansible invoked by Azimuth when launching an instance of the app.

- A [requirements.yml](https://github.com/stackhpc/azimuth-sample-appliance/blob/main/requirements.yml) to specific any required Ansible dependencies.

- Some Ansible-templated Terraform (e.g. the [example cluster-infra role](https://github.com/stackhpc/azimuth-sample-appliance/tree/main/roles/cluster_infra)) to provision the cloud resources required by the app.

- A [UI meta-data file](https://github.com/stackhpc/azimuth-sample-appliance/blob/main/ui-meta/sample-appliance.yml) to allow Azimuth to generate the input form for creating an instance of the app.


## Kubernetes Apps