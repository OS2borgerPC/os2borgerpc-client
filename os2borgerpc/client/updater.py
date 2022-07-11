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
