# Hardware-specific Kubernetes Configuration

Additional configuration may be required to utilise specialised hardware in Kubernetes clusters provisioned through Azimuth.

## Multiple GPUs per-node

If running flavors with multiple GPUs per node, additional image properties may be required for cards to be recognised seperately with Azimuth's community images, for example:
```
community_images_custom_properties:
  - hw_machine_type=q35
  - hw_architecture=x86_64
  - hw_vif_multiqueue_enabled=true
  - hw_firmware_type=uefi
  - os_type=linux
  - hw_disk_bus=virtio
```

## Vendor-specific config

Addons to manage resources such as GPUs are provided in `capi-helm-charts` for supported hardware, however some of these components
are not enabled by default and assume vendor-specific drivers to be installed on the host machines. 

### Nvidia

The Nvidia GPU operator and Mellanox operator are enabled by default for Kubernetes clusters and should require no additional configuration.

### Intel GPU Drivers (i915)

The Intel Device Plugin is provided as an addon to manage Intel GPUs inside the Kubernetes cluster, it can be enabled with:
```
azimuth_capi_operator_capi_helm_values_overrides:
  addons:
    intelDevicePlugin:
      enabled: true
```
The device plugin requires drivers to be installed on the host. Due to licensing restrictions, Azimuth cannot include these drivers in upstream images, but they can be
installed at boot for flavors using Intel GPU nodes with the `flavorSpecificNodeGroupOverrides` of `azimuth-capi-operator`, which can override `capi-helm-charts` values for
flavors matching a specified `fnmatch` string. This can be used to inject pre-KubeADM commands to install host packages. For example, to install Intel drivers on flavors
with '.intel.' in their name:
```
azimuth_capi_operator_release_overrides:
  config:
    capiHelm:
      flavorSpecificNodeGroupOverrides:
        '*.intel.*': # This assumes your Intel GPU flavors contain '.intel.' in their name
          kubeadmConfigSpec:
            preKubeadmCommands:
              - |
                # Adapted from https://dgpu-docs.intel.com/driver/installation.html#ubuntu
                sudo apt update
                sudo apt install -y gpg-agent wget
                . /etc/os-release
                if [[ ! " jammy " =~ " ${VERSION_CODENAME} " ]]; then
                    echo "Ubuntu version ${VERSION_CODENAME} not supported"
                else
                    wget -qO - https://repositories.intel.com/gpu/intel-graphics.key | \
                    sudo gpg --yes --dearmor --output /usr/share/keyrings/intel-graphics.gpg
                    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/intel-graphics.gpg] https://repositories.intel.com/gpu/ubuntu ${VERSION_CODENAME}/lts/2350 unified" | \
                    sudo tee /etc/apt/sources.list.d/intel-gpu-${VERSION_CODENAME}.list
                    sudo apt update
                fi
                sudo apt install -y \
                    linux-headers-$(uname -r) \
                    linux-modules-extra-$(uname -r) \
                    flex bison \
                    intel-fw-gpu intel-i915-dkms xpu-smi
                # Avoids reboot
                sudo modprobe i915
```

### AMD GPU drivers

Similarly to installing Intel GPUs as above, enable the AMD GPU operator addons for `capi-helm-charts`:
```
azimuth_capi_operator_capi_helm_values_overrides:
  addons:
    amdGPUOperator:
      enabled: true
```
and set up flavor-specific pre-KubeADM commands to install the appropriate drivers:
```
azimuth_capi_operator_release_overrides:
  config:
    capiHelm:
      flavorSpecificNodeGroupOverrides:
        'ec1.*':
          kubeadmConfigSpec:
            preKubeadmCommands:
              - |
                wget https://repo.radeon.com/amdgpu-install/7.0.2/ubuntu/jammy/amdgpu-install_7.0.2.70002-1_all.deb
                sudo apt install -y ./amdgpu-install_7.0.2.70002-1_all.deb
                sudo apt install -y python3-setuptools python3-wheel
                sudo usermod -a -G render,video $LOGNAME # Add the current user to the render and video groups
                sudo apt install -y rocm
                sudo apt install -y "linux-headers-$(uname -r)" "linux-modules-extra-$(uname -r)"
                sudo apt install -y amdgpu-dkms
```
