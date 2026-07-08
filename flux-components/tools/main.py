"""Build the final flux artifact directory from base config and a given environment"""

import argparse
import os
import shutil
from glob import glob
from pathlib import Path

import git
import literal_yaml
import yaml


def parse_args() -> argparse.Namespace:
    """Parse command line arguments provided.

    :returns: a namespace object containing all cli arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("environment", help="The environment to generate manifests for", nargs="*")
    parser.add_argument(
        "--base",
        "-b",
        default="flux-components/base/artifact",
        help="The path to the base manifests relative to repo root",
    )
    parser.add_argument(
        "--working",
        "-w",
        default="flux-components/working/artifact",
        help="The path to output the working manifests relative to repo root",
    )
    return parser.parse_args()


def get_git_root(path: str | Path) -> str:
    """Get the absolute root path of the parent git repo of given path

    :returns: The absolute path of the parent git repo
    """
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


def get_deployment_name(override: dict) -> str:
    """Get the name of the deployment to override from the override list element

    :param override: The element of the override list to get the name of
    :raises AssertionError: If the element has more than one key
    :returns: The name of the Flux deployment that is being overridden
    """
    # Check override dict has one key
    assert len(override.keys()) == 1, "Override list element should have one key"
    deployment_name = list(override.keys())[0]
    return deployment_name


def get_object_label(environment: str, deployment_name: str) -> dict:
    """Get the key-value label pair to apply to all manifests created for an
       override.

    :param environment: The name of the environment that the manifest is being
        rendered for
    :param deployment_name: The name of the deployment that the manifest is
        being rendered for
    :returns: A key-value pair to use as a Kubernetes object label
    """
    return {"azimuth/override-source": f"{environment}-{deployment_name}"}


def copy_yaml_manifest(src: Path, dest: Path, labels: dict = {}, annotations: dict = {}):
    """Copy a YAML manifest for a Kubernetes object(s) and inject metadata
       about the origin of the manifest, each manifest may be multiple YAML
       documents.

    :param src: Path of the source YAML file to copy
    :param dest: Path of the destination YAML file
    :param labels: Kubernetes labels to apply to the objects (optional)
    :param annotations: Kubernetes labels to apply to the objects (optional)
    """
    with open(src, "r", encoding="UTF-8") as source:
        with open(dest, "w", encoding="UTF-8") as destination:
            for document in yaml.safe_load_all(source):
                if "labels" in document["metadata"]:
                    document["metadata"]["labels"] = document["metadata"]["labels"] | labels
                else:
                    document["metadata"]["labels"] = labels
                if "annotations" in document["metadata"]:
                    document["metadata"]["annotations"] = document["metadata"]["annotations"] | annotations
                else:
                    document["metadata"]["annotations"] = annotations
                yaml.dump(document, destination)


def copy_explicit_manifests(src_path, dest_path, labels, annotations):
    """Copy all YAML manifests under a directory to the destination and inject metadata
       about the origin of the manifests

    :param src_path: Root path of the source YAML files to copy
    :param dest: Root path of the destination to copy to
    :param labels: Kubernetes labels to apply to the objects (optional)
    :param annotations: Kubernetes labels to apply to the objects (optional)
    """
    src_manifests = glob("**/*.yaml", root_dir=src_path, recursive=True)
    for manifest in src_manifests:
        source = src_path / Path(manifest)
        dest = dest_path / Path(manifest)
        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)
        copy_yaml_manifest(source, dest_path / Path(manifest), labels=labels)


def create_override_configmap(name: str, namespace: str, label: dict, values: dict, force_reload: bool = False) -> dict:
    """Create a configmap definition containing the given values

    The configmap needs to contain the values as an inlined YAML file under a
    values.yaml key.

    :param name: The name of the configmap
    :param namespace: The namespace the config map belongs in
    :param label: A Kubernetes object label to apply
    :param values: The helm chart values to write into the config map
    :param force_reload: Whether changing configmap forces a helm reconciliation
    """
    config_map = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": name, "namespace": namespace, "labels": label},
        "data": {
            "values.yaml": literal_yaml.LiteralString(yaml.dump(values, sort_keys=False, default_flow_style=False))
        },
    }
    if force_reload:
        config_map["metadata"]["labels"] = {"reconcile.fluxcd.io/watch": "Enabled"}
    return config_map


def write_override_configmap(configmap_path: str | Path, configmap_contents: dict):
    """Write the given configmap contents to the given configmap path as a YAML file

    :param configmap_path: The path to write the configmap to, including file extension
    :param configmap_contents: A dictionary of the full configmap definition
    """
    with open(configmap_path, "w", encoding="UTF-8") as fout:
        yaml.dump(configmap_contents, fout, default_flow_style=False)


def update_helm_release(new_release: dict, manifest_path: str | Path):
    """Read a full manifest file and replace the HelmRelease with the given new
       release definition.

    :param new_release: The new HelmRelease definition to replace the existing release
    :param manifest_path: The path of the manifest to update
    """
    yaml_docs = []
    with open(manifest_path, "r", encoding="UTF-8") as fin:
        for document in yaml.safe_load_all(fin):
            if document["kind"] == "HelmRelease":
                yaml_docs.append(new_release)
            else:
                yaml_docs.append(document)

    with open(manifest_path, "w", encoding="UTF-8") as fout:
        yaml.dump_all(yaml_docs, fout, sort_keys=False)


def get_helm_release(manifest_filepath: str | Path) -> dict:
    """Read all YAML documents at the given filepath and return the HelmRelease
    This assumes there is only one HelmRelease in each manifest as described in README

    :param manifest_filepath: The path of the manifest YAML file
    :returns: A dictionary containing the HelmRelease definition
    """
    with open(manifest_filepath, "r", encoding="UTF-8") as fin:
        for document in yaml.safe_load_all(fin):
            if document["kind"] == "HelmRelease":
                return document
    raise ValueError(f"Could not find HelmRelease in manifest at {manifest_filepath}")


def remove_manifest(deployment_name: str, working_path: Path):
    """Remove an entire deployment manifest, effectively disable the component in the cluster

    :param deployment_name: The deployment to remove
    :param working_path: The path of the working flux artifact directory
    """
    shutil.rmtree(working_path / "manifests" / deployment_name)


def create_override_manifest(override_dict: dict, deployment_name: str, label: dict, working_path: Path) -> dict:
    """Take an override definition, create the override configMap and update the
       relevant HelmRelease manifest to use the override values

    :param override_dict: An override dictionary as defined in the README
    :param deployment_name: The name of the deployment that the manifest is
        being rendered for
    :param label: A key-value pair to use as an object label
    :param working_path: The path of the working flux artifact directory
    :returns: The final rendered HelmRelease object
    """
    manifest_filepath = working_path / "manifests" / deployment_name / "manifest.yaml"
    config_map_name = override_dict["configMapName"]

    overridden_release = get_helm_release(manifest_filepath)
    namespace = overridden_release["metadata"]["namespace"]

    override_filepath = working_path / "manifests" / deployment_name / config_map_name
    override_filepath = override_filepath.with_suffix(".yaml")
    # if override["type"] == "ConfigMap":
    write_override_configmap(
        override_filepath,
        create_override_configmap(
            config_map_name, namespace, label, override_dict["values"], override_dict.get("forceReload", False)
        ),
    )
    overridden_release["spec"]["valuesFrom"].append({"kind": "ConfigMap", "name": config_map_name})
    update_helm_release(overridden_release, manifest_filepath)

    return overridden_release


def process_overlay(overlay_path: Path, working_path: Path):
    """Process an overlay and apply overrides and manifests to the working set

    :param overlay_path: The path to the overlay directory relative to the
        repository root
    :param working_path: The path to the working directory relative to the
        repository root
    """
    overlay_name = overlay_path.name
    # Create override configs and ingest them
    override_path = overlay_path / "overrides.yaml"

    if override_path.exists():
        with open(override_path, "r", encoding="UTF-8") as fin:
            overrides = yaml.safe_load(fin)

        # Process the helm chart values override file
        for override in overrides:
            deployment_name = get_deployment_name(override)
            label = get_object_label(overlay_name, deployment_name)
            if override[deployment_name].get("disabled", False):
                remove_manifest(deployment_name, working_path)
            else:
                create_override_manifest(override[deployment_name], deployment_name, label, working_path)

    # Copy any extra explicit manifests over
    if (overlay_path / "manifests").exists() and (overlay_path / "manifests").is_dir():
        explicit_deployments = [p for p in (overlay_path / "manifests").iterdir() if p.is_dir()]
        for deployment_path in explicit_deployments:
            label = get_object_label(overlay_name, deployment_path.name)
            copy_explicit_manifests(
                overlay_path / "manifests", working_path / "manifests", labels=label, annotations={}
            )

    # Copy any extra encrypted secrets in environment over
    if (overlay_path / "encrypted").exists() and (overlay_path / "encrypted").is_dir():
        explicit_deployments = [p for p in (overlay_path / "encrypted").iterdir() if p.is_dir()]
        for deployment_path in explicit_deployments:
            label = get_object_label(overlay_name, deployment_path.name)
            copy_explicit_manifests(
                overlay_path / "encrypted", working_path / "encrypted", labels=label, annotations={}
            )


def main():
    """Main entrypoint for script"""
    args = parse_args()
    root_path = Path(get_git_root(os.getcwd()))

    # can be cli args
    base_path = root_path / args.base
    working_path = root_path / args.working
    os.makedirs(working_path, exist_ok=True)

    # Clean and then copy base config to working directory
    shutil.rmtree(working_path)
    shutil.copytree(base_path, working_path, dirs_exist_ok=True)

    # If building the base environment then no overrides or extra secrets
    if args.environment == "base":
        exit(0)

    for environment in args.environment:
        print(environment)
        environment_path = root_path / "flux-components" / environment
        process_overlay(environment_path, working_path)


if __name__ == "__main__":
    main()
