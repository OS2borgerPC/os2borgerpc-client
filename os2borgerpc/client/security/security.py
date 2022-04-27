from datetime import datetime
from os2borgerpc.client.admin_client import OS2borgerPCAdmin
from os2borgerpc.client.utils import get_url_and_uid
from pathlib import Path
import glob
import os
import os.path
import stat
import subprocess
import sys
import traceback

"""
Directory structure for OS2borgerPC security events
/etc/os2borgerpc/security/securityevent.csv - Security event log file.
/etc/os2borgerpc/security/ - Scripts to be executed by the jobmanager.
/etc/os2borgerpc/security/security_check_YYYYMMDDHHmm.csv -
files containing the events to be sent to the admin system.
"""

SECURITY_DIR = "/etc/os2borgerpc/security"
LAST_SECURITY_EVENTS_CHECKED_TIME = os.path.join(SECURITY_DIR, "lastcheck.txt")
SECURITY_EVENT_FILE = os.path.join(SECURITY_DIR, "securityevent.csv")
SECURITY_SCRIPTS_LOG_FILE = os.path.join(SECURITY_DIR, "security_log.txt")


def cleanup_old_import_new_security_scripts(security_scripts):
    security_dir = Path(SECURITY_DIR)
    # if security dir exists
    if security_dir.is_dir():
        # Always remove the old security scripts -- perhaps this PC has been
        # moved to another group and no longer needs them
        for old_script in security_dir.glob("s_*"):
            old_script.unlink()

        # Import the fresh security scripts
        for s in security_scripts:
            script = security_dir.joinpath("s_" + s["name"].replace(" ", ""))
            with script.open("wt") as fh:
                fh.write(s["executable_code"])
            script.chmod(stat.S_IRWXU)


def run_security_scripts():
    """
    Run the received security scripts and log them
    to SECURITY_SCRIPTS_LOG_FILE.
    Security scripts write to SECURITY_EVENT_FILE themselves.
    """
    if not os.path.exists(SECURITY_SCRIPTS_LOG_FILE):
        os.mknod(SECURITY_SCRIPTS_LOG_FILE)
    if os.path.getsize(SECURITY_SCRIPTS_LOG_FILE) > 10000:
        os.remove(SECURITY_SCRIPTS_LOG_FILE)

    with open(SECURITY_SCRIPTS_LOG_FILE, "a") as log:
        for filename in glob.glob(SECURITY_DIR + "/s_*"):
            print(">>>" + filename, file=log)
            cmd = [filename]
            ret_val = subprocess.call(cmd, shell=True, stdout=log, stderr=log)
            if ret_val == 0:
                print(">>>" + filename + " Succeeded", file=log)
            else:
                print(">>>" + filename + " Failed", file=log)


def collect_security_events(now):
    """
    Filters security events from SECURITY_EVENT_FILE newer than last_check.
    """
    last_check = read_last_security_events_checked_time()
    if not last_check:
        last_check = datetime.strptime(now, "%Y%m%d%H%M")

    # File does not exist. No events occured, since last check.
    if not os.path.exists(SECURITY_EVENT_FILE):
        return ""
    with open(SECURITY_EVENT_FILE, "r") as csv_file:
        csv_file_lines = csv_file.readlines()

    new_security_events = []
    for line in csv_file_lines:
        csv_split = line.split(",")
        if datetime.strptime(csv_split[0], "%Y%m%d%H%M") >= last_check:
            new_security_events.append(line)

    return new_security_events


def send_security_events(security_events):
    """
    Send security events to the server and return True/False for success/error.
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
        f.write(datetime_obj)


def read_last_security_events_checked_time():
    """
    Read LAST_SECURITY_EVENTS_CHECKED_TIME to a datetime object
    or an empty string.
    """
    if os.path.exists(LAST_SECURITY_EVENTS_CHECKED_TIME):
        with open(LAST_SECURITY_EVENTS_CHECKED_TIME, "r") as f:
            content = f.read()
        datetime_obj = datetime.strptime(content, "%Y%m%d%H%M")
        return datetime_obj
    return ""


def check_security_events(security_scripts):
    """
    Entrypoint for security events checking.
    """
    for folder in (
        SECURITY_DIR,
    ):
        os.makedirs(folder, mode=0o700, exist_ok=True)

    now = datetime.now()
    if not os.path.isdir(SECURITY_DIR):
        raise FileNotFoundError

    cleanup_old_import_new_security_scripts(security_scripts)
    run_security_scripts()
    new_security_events = collect_security_events(now)
    if new_security_events:
        result = send_security_events(new_security_events)
        if result:
            os.remove(SECURITY_EVENT_FILE)
            update_last_security_events_checked_time(now)
    else:
        update_last_security_events_checked_time(now)
