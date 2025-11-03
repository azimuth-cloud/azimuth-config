#!/usr/bin/env python3

"""Generates release notes for a GitHub release by comparing the current and previous
releases, and fetching the release notes for each component in azimuth-ops."""

import argparse
import base64
import os

import easysemver
import requests
import yaml

API_URL = "https://api.github.com"
COMPONENTS = [
    {
        "name": "azimuth-images",
        # These keys define how to extract the version from azimuth-ops
        "path": "roles/community_images/defaults/main.yml",
        "version_key": "community_images_azimuth_images_version",
    },
    {
        "name": "azimuth",
        "path": "roles/azimuth/defaults/main.yml",
        "version_key": "azimuth_chart_version",
    },
    {
        "name": "azimuth-caas-operator",
        "path": "roles/azimuth_caas_operator/defaults/main.yml",
        "version_key": "azimuth_caas_operator_chart_version",
    },
    {
        "name": "azimuth-capi-operator",
        "path": "roles/azimuth_capi_operator/defaults/main.yml",
        "version_key": "azimuth_capi_operator_chart_version",
    },
    {
        "name": "azimuth-identity-operator",
        "path": "roles/azimuth_identity_operator/defaults/main.yml",
        "version_key": "azimuth_identity_operator_chart_version",
    },
    {
        "name": "azimuth-schedule-operator",
        "path": "roles/azimuth_schedule_operator/defaults/main.yml",
        "version_key": "azimuth_schedule_operator_chart_version",
    },
    {
        "name": "zenith",
        "path": "roles/zenith/defaults/main.yml",
        "version_key": "zenith_chart_version",
    },
    {
        "name": "cluster-api-addon-provider",
        "path": "roles/clusterapi/defaults/main.yml",
        "version_key": "clusterapi_addon_provider_chart_version",
    },
    {
        "name": "cluster-api-janitor-openstack",
        "path": "roles/clusterapi/defaults/main.yml",
        "version_key": "clusterapi_janitor_openstack_chart_version",
    },
    {
        "name": "capi-helm-charts",
        "path": "roles/capi_cluster/defaults/main.yml",
        "version_key": "capi_cluster_chart_version",
    },
    {
        "name": "caas-workstation",
        "path": "roles/azimuth_caas_operator/defaults/main.yml",
        "version_key": [
            "azimuth_caas_workstation_default_git_version",
            "azimuth_caas_stackhpc_workstation_git_version",
        ],
    },
    {
        "name": "caas-repo2docker",
        "path": "roles/azimuth_caas_operator/defaults/main.yml",
        "version_key": [
            "azimuth_caas_repo2docker_default_git_version",
            "azimuth_caas_stackhpc_repo2docker_git_version",
        ],
    },
    {
        "name": "caas-r-studio-server",
        "path": "roles/azimuth_caas_operator/defaults/main.yml",
        "version_key": [
            "azimuth_caas_rstudio_default_git_version",
            "azimuth_caas_stackhpc_rstudio_git_version",
        ],
    },
    {
        "name": "ansible-slurm-appliance",
        "org": "stackhpc",
        "path": "roles/azimuth_caas_operator/defaults/main.yml",
        "version_key": "azimuth_caas_stackhpc_slurm_appliance_git_version",
    },
]


def github_session(token):
    """
    Initialises a requests session for interacting with GitHub.
    """
    session = requests.Session()
    session.headers["Content-Type"] = "application/json"
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def github_fetch_list(session, url):
    """
    Generator that yields items from paginating a GitHub URL.
    """
    next_url = url
    while next_url:
        response = session.get(next_url)
        response.raise_for_status()
        yield from response.json()
        next_url = response.links.get("next", {}).get("url")


def is_stable(version):
    """
    Returns true unless the version is SemVer and has a prerelease.
    """
    try:
        semver = easysemver.Version(version)
    except TypeError:
        return True
    return not semver.prerelease


def fetch_releases(
    session,
    repo,
    min=None,  # pylint: disable=redefined-builtin
    inclusive_min=True,
    max=None,  # pylint: disable=redefined-builtin
    inclusive_max=True,
):  # pylint: disable=too-many-arguments, disable=too-many-positional-arguments
    """
    Returns the stable releases for the specified repo. It assumes that the GitHub
    API produces the releases in order (which it does).
    """
    seen_max = False
    for release in github_fetch_list(session, f"{API_URL}/repos/{repo}/releases"):
        version = release["tag_name"]
        # Deal with hitting the min version
        if min and version == min:
            if seen_max and inclusive_min and is_stable(version):
                yield release
            break
        # Deal with hitting the max version
        if not max or version == max:
            seen_max = True
            if max and not inclusive_max:
                continue
        # Only yield stable versions once we have seen the max
        if seen_max and is_stable(version):
            yield release


def fetch_release_by_tag(session, repo, tag):
    """
    Fetch the release for the specified repository and tag.
    """
    response = session.get(f"{API_URL}/repos/{repo}/releases/tags/{tag}")
    response.raise_for_status()
    return response.json()


def fetch_ops_tag_for_release(session, repo, tag):
    """
    Returns the azimuth-ops tag used by the specified release.
    """
    response = session.get(
        f"{API_URL}/repos/{repo}/contents/requirements.yml",
        params={"ref": tag},
        headers={"Content-Type": "application/vnd.github.raw+json"},
    )
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"])
    return yaml.safe_load(content)["collections"][0]["version"]


def fetch_component_version_for_ops_tag(session, tag, component):
    """
    Returns the version of the specified component that is used in the specified azimuth-ops tag.
    """
    response = session.get(
        f"{API_URL}/repos/azimuth-cloud/ansible-collection-azimuth-ops/contents/{component['path']}",  # pylint: disable=line-too-long # noqa: E501
        params={"ref": tag},
        headers={"Content-Type": "application/vnd.github.raw+json"},
    )
    response.raise_for_status()
    content = base64.b64decode(response.json()["content"])
    data = yaml.safe_load(content)
    # In order to allow version keys to change between azimuth-ops versions, we support
    # specifying a list of keys which we try in order
    if isinstance(component["version_key"], list):
        version_keys = component["version_key"]
    else:
        version_keys = [component["version_key"]]
    return next(data[key] for key in version_keys if key in data)


def release_notes_for_component(session, name, org, from_version, to_version):
    """
    Produces the release notes for a component between the specified versions.
    """
    print(f"[INFO]   collecting release notes for {name}")
    release_notes = []
    for release in fetch_releases(
        session,
        f"{org}/{name}",
        min=from_version,
        inclusive_min=False,
        max=to_version,
        inclusive_max=True,
    ):
        print(f"[INFO]     found release - {release['tag_name']}")
        release_notes.extend(
            [
                "<details>",
                f"<summary><strong>{name}</strong> @ <code>{release['tag_name']}</code></summary>",
                "",
                # Knock the headers down by two levels for formatting
                *[
                    f"##{line}" if line.startswith("#") else line
                    for line in release["body"].splitlines()
                ],
                "",
                "</details>",
            ]
        )
    return release_notes


def main():
    """Main function to parse arguments and generate release notes."""
    parser = argparse.ArgumentParser(
        description="Gets the latest release in a GitHub repository."
    )
    # Allow the token to come from an environment variable
    # We use this particular form so that the empty string becomes None
    env_token = os.environ.get("GITHUB_TOKEN") or None
    parser.add_argument(
        "--token",
        help="The GitHub token to use (can be set using GITHUB_TOKEN envvar).",
        default=env_token,
    )
    parser.add_argument(
        "--repo",
        help="The config repository to target.",
        default="azimuth-cloud/azimuth-config",
    )
    parser.add_argument("tag", help="The tag to generate release notes for.")
    args = parser.parse_args()

    # Make sure that the YAML SafeLoader respects Ansible's !unsafe tag
    yaml.SafeLoader.add_constructor("!unsafe", yaml.SafeLoader.construct_scalar)

    session = github_session(args.token)

    print(f"[INFO] fetching release for tag - {args.tag}")
    current = fetch_release_by_tag(session, args.repo, args.tag)
    current_ops_tag = fetch_ops_tag_for_release(session, args.repo, current["tag_name"])
    print(f"[INFO]   found azimuth-ops tag - {current_ops_tag}")

    print("[INFO] fetching previous stable release")
    previous = next(
        fetch_releases(session, args.repo, max=current["tag_name"], inclusive_max=False)
    )
    print(f"[INFO]   found release - {previous['tag_name']}")
    previous_ops_tag = fetch_ops_tag_for_release(
        session, args.repo, previous["tag_name"]
    )
    print(f"[INFO]   found azimuth-ops tag - {previous_ops_tag}")

    print("[INFO] collecting release notes")
    release_notes = []
    # Start with the release notes that are attached to the release
    release_notes.append(current["body"])
    if current_ops_tag == previous_ops_tag:
        print("[WARN]   azimuth-ops version has not changed - skipping")
    else:
        # Add a new header to start the components section
        release_notes.append("### Changes to components")
        # Produce release notes for azimuth-ops changes
        release_notes.extend(
            release_notes_for_component(
                session,
                "ansible-collection-azimuth-ops",
                "azimuth-cloud",
                previous_ops_tag,
                current_ops_tag,
            )
        )
        # Produce release notes for each component in azimuth-ops
        for component in COMPONENTS:
            print(f"[INFO]   fetching versions for component - {component['name']}")
            component_vn_current = fetch_component_version_for_ops_tag(
                session, current_ops_tag, component
            )
            component_vn_previous = fetch_component_version_for_ops_tag(
                session, previous_ops_tag, component
            )
            if component_vn_current == component_vn_previous:
                print("[WARN]     found same version at both releases - skipping")
            release_notes.extend(
                release_notes_for_component(
                    session,
                    component["name"],
                    component.get("org", "azimuth-cloud"),
                    component_vn_previous,
                    component_vn_current,
                )
            )

    print(f"[INFO] updating release notes for release - {current['tag_name']}")
    response = session.patch(
        f"{API_URL}/repos/{args.repo}/releases/{current['id']}",
        json={"body": "\r\n".join(release_notes)},
    )
    response.raise_for_status()
    print("[INFO]   release notes updated successfully")


if __name__ == "__main__":
    main()
