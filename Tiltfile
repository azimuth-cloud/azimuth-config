SETTINGS_FILE = "./tilt-settings.yaml"

# Paths to the required scripts
TILT_IMAGES_APPLY = os.path.abspath("./bin/tilt-images-apply")
TILT_IMAGES_UNAPPLY = os.path.abspath("./bin/tilt-images-unapply")


# Allow the use of the azimuth-dev context
allow_k8s_contexts("azimuth")


def deep_merge(dict1, dict2):
    """
    Deep merges two dictionaries, with values from dict2 taking precedence.
    """
    merged = dict(dict1)
    for key, value2 in dict2.items():
        if key in dict1:
            value1 = dict1[key]
            if type(value1) == "dict" and type(value2) == "dict":
                merged[key] = deep_merge(value1, value2)
            else:
                merged[key] = value2
        else:
            merged[key] = value2
    return merged


# The Tilt settings file is required
if not os.path.exists(SETTINGS_FILE):
    fail("settings file must exist at %s" % SETTINGS_FILE)


# Load the settings
settings = deep_merge(
    {
        # The components that will be managed by Tilt, if locally available
        # By default, we search for local checkouts as siblings of this checkout
        "components": {
            "azimuth": {
                # Indicates whether the component should be enabled or not
                # By default, a component is enabled if the corresponding location exists
                # "enabled": True,

                # The location where the component is checked out
                # The default location is "../<componentname>", i.e. siblings of azimuth-config
                # "location": "/path/to/component",

                # The name of the Helm release for the component
                # Defaults to the component name
                # "release_name": "azimuth",

                # The namespace of the Helm release for the component
                "release_namespace": "azimuth",
            },
            "azimuth-caas-operator": {
                "release_namespace": "azimuth",
            },
            "azimuth-capi-operator": {
                "release_namespace": "azimuth",
            },
            "azimuth-identity-operator": {
                "release_namespace": "azimuth",
            },
            "azimuth-schedule-operator": {
                "release_namespace": "azimuth",
            },
            "coral-credits": {
                "release_namespace": "coral-credits",
            },
            "cluster-api-addon-provider": {
                "release_namespace": "capi-addon-system",
            },
            "cluster-api-janitor-openstack": {
                "release_namespace": "capi-janitor-system",
            },
            "zenith": {
                "release_name": "zenith-server",
                "release_namespace": "azimuth",
            },
        },
    },
    read_yaml(SETTINGS_FILE)
)


# The user must define an image prefix
if "image_prefix" not in settings:
    fail("image_prefix must be specified in %s" % SETTINGS_FILE)


def image_name(name):
    """
    Returns the full image name with the prefix.
    """
    prefix = settings["image_prefix"].removesuffix("/")
    return "/".join([prefix, name])


def build_image(name, context, build_args = None):
    """
    Defines an image build and returns the image name.
    """
    image = image_name(name)
    # The Azimuth CaaS operator relies on the .git folder to be in the Docker build context
    # This is because it uses pbr for versioning
    # Unfortunately, Tilt's docker_build function _always_ ignores the .git directory :-(
    # So we use a custom build command
    build_command = [
        "docker",
        "build",
        "-t",
        "$EXPECTED_REF",
        "--platform",
        "linux/amd64",
        context,
    ]
    if build_args:
        for arg_name, arg_value in build_args.items():
            build_command.extend([
                "--build-arg",
                "'%s=%s'" % (arg_name, arg_value),
            ])
    custom_build(image, " ".join(build_command), [context])
    return image


def mirror_image(name, source_image):
    """
    Defines a mirrored image and returns the image name.
    """
    image = image_name(name)
    custom_build(
        image,
        (
            "docker pull --platform linux/amd64 {source_image} && " +
            "docker tag {source_image} $EXPECTED_REF"
        ).format(source_image = source_image),
        []
    )
    return image


def port_forward(name, namespace, kind, port):
    """
    Runs a port forward as a local resource.

    Could maybe be changed when https://github.com/tilt-dev/tilt/issues/5944 is addressed.
    """
    local_resource(
        "port-fwd-%s-%s-%s" % (namespace, kind, name),
        serve_cmd = "\n".join([
            "while true; do",
            " ".join([
                "kubectl",
                "port-forward",
                "--namespace",
                namespace,
                "%s/%s" % (kind, name),
                port,
            ]),
            "sleep 1",
            "done",
        ])
    )


def load_component(name, spec):
    """
    Loads a component from the spec.
    """
    # If the component is not enabled, we are done
    if not spec.get("enabled", True):
        print("[%s] component is disabled" % name)
        return

    # By default, we search for local checkouts as siblings of this checkout
    location = spec.get("location", "../%s" % name)
    # If the location does not exist, we are done
    if not os.path.exists(location):
        print("[%s] location '%s' does not exist - ignoring" % (name, location))
        return

    # Next, read the component file if present
    component_file = os.path.join(location, "tilt-component.yaml")
    component_spec = read_yaml(component_file, default = None) or {}

    # Define a docker build resource for each image, storing the paths as we go
    images = []
    image_paths = []
    if "images" in component_spec:
        # If there are images defined in the spec, use those
        for image_name, image_spec in component_spec["images"].items():
            if image_spec.get("action", "build") == "build":
                image = build_image(
                    image_name,
                    os.path.join(location, image_spec["context"]),
                    image_spec.get("build_args", {})
                )
            else:
                image = mirror_image(image_name, image_spec["source_image"])
            images.append(image)
            # By default, assume that images are set with a top-level 'image' variable
            image_paths.append(image_spec.get("chart_path", "image"))
    elif os.path.exists(os.path.join(location, "Dockerfile")):
        # If a Dockerfile exists at the top level, assume it is the only image and
        # that it is set in the chart with a top-level 'image' variable
        images.append(build_image(name, location))
        image_paths.append("image")

    # Get the chart path
    # We assume the chart is at './chart', but allow the component to override
    chart_path_rel = component_spec.get("chart", "./chart")
    chart_path = os.path.join(location, chart_path_rel)

    # Define a custom deploy to replace the images in an existing Helm release
    env = {
        "TILT_RELEASE_NAME": spec.get("release_name", name),
        "TILT_RELEASE_NAMESPACE": spec["release_namespace"],
        "TILT_CHART_PATH": chart_path,
    }
    for i, image_path in enumerate(image_paths):
        env["TILT_IMAGE_PATH_%s" % i] = image_path

    k8s_custom_deploy(
        name,
        apply_cmd = TILT_IMAGES_APPLY,
        apply_env = env,
        delete_cmd = TILT_IMAGES_UNAPPLY,
        delete_env = env,
        # Don't include the lock and subcharts
        deps = [
            os.path.join(chart_path, ".helmignore"),
            os.path.join(chart_path, "Chart.yaml"),
            os.path.join(chart_path, "values.yaml"),
            os.path.join(chart_path, "crds"),
            os.path.join(chart_path, "files"),
            os.path.join(chart_path, "templates"),
        ],
        image_deps = images
    )

    # Set up any port forwards for the component
    for pfwd_spec in component_spec.get("port_forwards", []):
        port_forward(
            pfwd_spec["name"],
            spec["release_namespace"],
            pfwd_spec["kind"],
            pfwd_spec["port"]
        )

    # Create any local resources for the component
    for name, lr_spec in component_spec.get("local_resources", {}).items():
        lr_spec.setdefault("dir", location)
        lr_spec.setdefault("serve_dir", location)
        local_resource(name, **lr_spec)


# Load the components defined in the settings
for name, spec in settings["components"].items():
    load_component(name, spec)
