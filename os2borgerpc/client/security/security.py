"""Security module."""
from datetime import datetime
from pathlib import Path
import os
import os.path
import stat
import subprocess
import sys
import traceback

from os2borgerpc.client.admin_client import OS2borgerPCAdmin
from os2borgerpc.client.utils import get_url_and_uid

# Main folder for the security module.
SECURITY_DIR = Path("/etc/os2borgerpc/security")
# Time continuously updated with the last security events run.
# Start time for collecting security events.
LAST_SECURITY_EVENTS_CHECKED_TIME = SECURITY_DIR / "lastcheck.txt"
# CSV-formatted data with a line for each security event.
SECURITY_EVENT_FILE = SECURITY_DIR / "securityevent.csv"
# Log file for the output of the security scripts.
SECURITY_SCRIPTS_LOG_FILE = SECURITY_DIR / "security_log.txt"


def cleanup_security_scripts():
    """Cleanup existing security scripts."""
    if SECURITY_DIR.is_dir():
        # Always remove the security scripts -- perhaps this PC has been
        # moved to another group and no longer needs them
        for script in SECURITY_DIR.glob("s_*"):
            script.unlink()


def import_new_security_scripts(security_scripts):
    """Import the new security scripts received from the server."""
    for s in security_scripts:
        script = SECURITY_DIR.joinpath("s_" + s["name"].replace(" ", ""))
        with script.open("wt") as fh:
            fh.write(s["executable_code"])
        script.chmod(stat.S_IRWXU)


def run_security_scripts():
    """
    Run the received security scripts.

    Run the security scripts and log them to SECURITY_SCRIPTS_LOG_FILE.
    The security scripts write to SECURITY_EVENT_FILE themselves.
    """
    if not os.path.exists(SECURITY_SCRIPTS_LOG_FILE):
        os.mknod(SECURITY_SCRIPTS_LOG_FILE)
    if os.path.getsize(SECURITY_SCRIPTS_LOG_FILE) > 10000:
        os.remove(SECURITY_SCRIPTS_LOG_FILE)

    with open(SECURITY_SCRIPTS_LOG_FILE, "a") as log:
        for script in SECURITY_DIR.glob("s_*"):
            print(">>>" + str(script), file=log)
            cmd = [script]
            ret_val = subprocess.call(cmd, shell=True, stdout=log, stderr=log)
            if ret_val == 0:
                print(">>>" + str(script) + " Succeeded", file=log)
            else:
                print(">>>" + str(script) + " Failed", file=log)


def collect_security_events(now):
    """Collect the security events from SECURITY_EVENT_FILE newer than last_check."""
    last_check = read_last_security_events_checked_time()
    if not last_check:
        last_check = now

    # File does not exist. No events occured, since last check.
    if not os.path.exists(SECURITY_EVENT_FILE):
        return ""
    with open(SECURITY_EVENT_FILE, "r") as csv_file:
        csv_file_lines = csv_file.readlines()

    new_security_events = []
    for line in csv_file_lines:
        csv_split = line.split(",")
        if datetime.strptime(csv_split[0], "%Y%m%d%H%M%S") > last_check:
            new_security_events.append(line)

    return new_security_events


def send_security_events(security_events):
    """
    Send security events to the server.

    Return True/False for success/error.
    """
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)
    try:
        result = remote.push_security_events(uid, security_events)
        return result == 0
    except Exception:
        print("Error while sending security events", file=sys.stderr)
        traceback.print_exc()
        return False


def update_last_security_events_checked_time(datetime_obj):
    """Update LAST_SECURITY_EVENTS_CHECKED_TIME from a datetime object."""
    with open(LAST_SECURITY_EVENTS_CHECKED_TIME, "wt") as f:
        f.write(datetime_obj.strftime("%Y%m%d%H%M%S"))


def read_last_security_events_checked_time():
    """
    Read LAST_SECURITY_EVENTS_CHECKED_TIME.

    Read LAST_SECURITY_EVENTS_CHECKED_TIME to a datetime object
    or None.
    """
    if os.path.exists(LAST_SECURITY_EVENTS_CHECKED_TIME):
        with open(LAST_SECURITY_EVENTS_CHECKED_TIME, "r") as f:
            content = f.read()
        if not content:
            return None
        try:
            datetime_obj = datetime.strptime(content, "%Y%m%d%H%M%S")
        except ValueError:
            return None
        return datetime_obj
    return None


def check_security_events(security_scripts):
    """Entrypoint for security events checking."""
    os.makedirs(SECURITY_DIR, mode=0o700, exist_ok=True)

    now = datetime.now()

    # If no security scripts exist simply update the last checked time
    # So the security event collection only includes new security events.
    if not security_scripts:
        update_last_security_events_checked_time(now)
        return

    cleanup_security_scripts()
    import_new_security_scripts(security_scripts)
    run_security_scripts()
    new_security_events = collect_security_events(now)

    # Only update last checked time in case sending security events is successful
    # or none is found.
    if new_security_events:
        result = send_security_events(new_security_events)
        if result:
            os.remove(SECURITY_EVENT_FILE)
            update_last_security_events_checked_time(now)
    else:
        update_last_security_events_checked_time(now)
