"""Module for update-related utilities."""

import traceback
import sys
import subprocess

import requests

from os2borgerpc.client.config import get_config

def get_latest_version_from_github(repo_url):
    """Get the latest version tag from a GitHub repository."""
    try:
        response = requests.get(f"https://api.github.com/repos/{repo_url}/tags")
        response.raise_for_status()
        tags = response.json()
        if tags:
            return tags[0]["name"]
        else:
            return None
    except requests.RequestException as e:
        print(f"Failed to fetch tags from GitHub: {e}", file=sys.stderr)
        return None


def get_newest_client_version():
    """Get the newest client version from GitHub or PyPI based on configuration."""
    client_package = get_config("os2borgerpc_client_package")
    
    if client_package.startswith("https://github.com/"):
        repo_parts = client_package.split("/")
        if len(repo_parts) >= 5:
            repo_user = repo_parts[3]
            repo_name = repo_parts[4]
            repo_url = f"{repo_user}/{repo_name}"
            newest_version = get_latest_version_from_github(repo_url)
            if newest_version:
                return newest_version
            else:
                print("Could not determine the latest version from GitHub.", file=sys.stderr)
                return None
    else:
        try:
            response = requests.get(f"https://pypi.org/pypi/{client_package}/json")
            response.raise_for_status()
            json_object = response.json()
            newest_version = json_object["info"]["version"]
            return newest_version
        except requests.RequestException as e:
            print(f"Failed to fetch version from PyPI: {e}", file=sys.stderr)
            return None
        
def get_versioned_client_package(version):
    client_package = get_config("os2borgerpc_client_package")

    if client_package.startswith("https://github.com/"):
        return f"git+{client_package}@{version}"
    
    return f"{client_package}@{version}"

def update_client(version):
    """Update the client via pip based on the latest version."""
    try:
        versioned_client_package = get_versioned_client_package(version)
        if version:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-U", versioned_client_package]
            )
            sys.exit(0)
        else:
            print("Could not determine the latest version to update.", file=sys.stderr)
            sys.exit(1)
    except subprocess.CalledProcessError:
        print("update_client failed\n", file=sys.stderr)
        traceback.print_exc()


def update_client_test():
    """Install the latest client from testpypi via pip."""
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--force-reinstall",
                "--index-url",
                "https://test.pypi.org/simple/",
                "--extra-index-url",
                "https://pypi.org/simple/",
                "os2borgerpc-client",
            ]
        )
        sys.exit(0)
    except subprocess.CalledProcessError:
        print("update_client_test failed\n", file=sys.stderr)
        traceback.print_exc()
