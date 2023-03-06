"""Module for update-related utilities."""

import traceback
import sys
import subprocess

import requests


def get_newest_client_version():
    """Get the newest client version from Pypi."""
    response = requests.get("https://pypi.org/pypi/os2borgerpc-client/json")
    json_object = response.json()
    newest_version = json_object["info"]["version"]

    return newest_version


def update_client():
    """Update the client via pip."""
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-U", "os2borgerpc-client"]
        )
        sys.exit(0)
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
