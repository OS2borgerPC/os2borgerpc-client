import os
import sys
import socket
import os.path
import stat
import urllib.parse
import urllib.request
import json
import glob
import re
import subprocess
import pkg_resources
import lsb_release
import traceback

from pathlib import Path
from datetime import datetime

from .config import OS2borgerPCConfig, has_config

from .admin_client import OS2borgerPCAdmin
from .utils import filelock


# Keep this in sync with package name in setup.py
OS2BORGERPC_CLIENT_VERSION = pkg_resources.get_distribution(
    "os2borgerpc_client"
).version
DEFAULT_JOB_TIMEOUT = 900

"""
Directory structure for storing OS2borgerPC jobs:
/var/lib/os2borgerpc/jobs/<id> - Files related to job with id <id>
/var/lib/os2borgerpc/jobs/<id>/attachments - files needed to execute the job
/var/lib/os2borgerpc/jobs/<id>/executable - the program that executes the job
/var/lib/os2borgerpc/jobs/<id>/parameters.json - json file with parameters
/var/lib/os2borgerpc/jobs/<id>/status - status file, created by runtime system
/var/lib/os2borgerpc/jobs/<id>/started - created when job is started
/var/lib/os2borgerpc/jobs/<id>/finished - created when job is finished/failed
/var/lib/os2borgerpc/jobs/<id>/sent - created when job is sent back to server
/var/lib/os2borgerpc/jobs/<id>/output.log - Logfile with output from the job
"""

"""
Directory structure for OS2borgerPC security events (for historical reasons):
/etc/os2borgerpc/security/securityevent.csv - Security event log file.
/etc/os2borgerpc/security/ - Scripts to be executed by the jobmanager.
/etc/os2borgerpc/security/security_check_YYYYMMDDHHmm.csv -
files containing the events to be sent to the admin system.
"""
SECURITY_DIR = "/etc/os2borgerpc/security"
JOBS_DIR = "/var/lib/os2borgerpc/jobs"
LOCK_FILE = JOBS_DIR + "/running"


class LocalJob(dict):
    def __init__(self, id=None, path=None, data=None):
        if id is None and data is not None and "id" in data:
            id = data["id"]
            del data["id"]

        if id is None and path is None:
            raise ValueError("You must specify either an id or a path")

        if id is not None:
            self.id = id
        else:
            # Remove trailing slash
            if path[-1] == "/":
                path = path[:-1]

            # Find id from last part of path
            m = re.match(r".*/(\d+)$", path)
            if m is None:
                raise ValueError("%s is not a valid path" % path)
            else:
                self.id = m.group(1)

        if not os.path.isdir(self.path):
            os.mkdir(self.path)

        # Initialize with given data
        if data is not None:
            self.populate(data)

    @property
    def path(self):
        return JOBS_DIR + "/" + str(self.id)

    @property
    def attachments_path(self):
        return self.path + "/attachments"

    @property
    def executable_path(self):
        return self.path + "/executable"

    @property
    def parameters_path(self):
        return self.path + "/parameters.json"

    @property
    def status_path(self):
        return self.path + "/status"

    @property
    def started_path(self):
        return self.path + "/started"

    @property
    def finished_path(self):
        return self.path + "/finished"

    @property
    def sent_path(self):
        return self.path + "/sent"

    @property
    def log_path(self):
        return self.path + "/output.log"

    @property
    def report_data(self):
        self.load_from_path()
        result = {"id": self.id}
        for k in ["status", "started", "finished", "log_output"]:
            result[k] = self[k]
        return result

    def set_status(self, value):
        self["status"] = value
        self.save_property_to_file("status", self.status_path)

    def mark_started(self):
        self["started"] = str(datetime.now())
        self.save_property_to_file("started", self.started_path)

    def mark_finished(self):
        self["finished"] = str(datetime.now())
        self.save_property_to_file("finished", self.finished_path)

    def mark_sent(self):
        self["sent"] = str(datetime.now())
        self.save_property_to_file("sent", self.sent_path)

    def load_local_parameters(self):
        self.read_property_from_file("json_params", self.parameters_path)
        if "json_params" in self:
            self["local_parameters"] = json.loads(self["json_params"])
            del self["json_params"]
        else:
            self["local_parameters"] = []

    def load_from_path(self, full_info=False):
        if not os.path.isdir(self.path):
            raise ValueError("%s is not a directory" % self.path)

        self.read_property_from_file("status", self.status_path)
        self.read_property_from_file("started", self.started_path)
        self.read_property_from_file("finished", self.finished_path)
        self.read_property_from_file("log_output", self.log_path)
        self.read_property_from_file("sent", self.sent_path)

        if full_info is not False:
            self.read_property_from_file("executable_code", self.executable_path)
            self.load_local_parameters()

    def read_property_from_file(self, prop, file_path):
        try:
            with open(file_path, "rt") as fh:
                self[prop] = fh.read()
        except OSError:
            pass

    def save_property_to_file(self, prop, file_path):
        if prop in self:
            with open(file_path, "wt") as fh:
                fh.write(self[prop])

    def populate(self, data):
        for k in data.keys():
            self[k] = data[k]

    def save(self):
        self.save_property_to_file("executable_code", self.executable_path)
        self.save_property_to_file("status", self.status_path)
        self.save_property_to_file("started", self.started_path)
        self.save_property_to_file("finished", self.finished_path)
        self.save_property_to_file("sent", self.sent_path)

        # Make sure executable is executable
        if os.path.exists(self.executable_path):
            os.chmod(self.executable_path, stat.S_IRWXU)

        self.translate_parameters()
        if "local_parameters" in self:
            with open(self.parameters_path, "wt") as param_fh:
                param_fh.write(json.dumps(self["local_parameters"]))

    def translate_parameters(self):
        if "parameters" not in self:
            return

        config = OS2borgerPCConfig()
        admin_url = config.get_value("admin_url")

        local_params = []
        self["local_parameters"] = local_params
        params = self["parameters"]
        del self["parameters"]
        for index, param in enumerate(params):
            if param["type"] == "FILE":
                # Make sure we have the directory
                if not os.path.isdir(self.attachments_path):
                    os.mkdir(self.attachments_path)

                value = param["value"]
                _, _, path, _, _, _ = urllib.parse.urlparse(value)
                basename = path[path.rfind("/") + 1 :] or "file"
                local_filename = os.path.join(
                    self.attachments_path, str(index) + "_" + basename
                )

                # urljoin does the right thing for both relative and absolute
                # values of, er, value
                full_url = urllib.parse.urljoin(admin_url, value)
                remote_file = urllib.request.urlopen(full_url)
                with open(local_filename, "wb") as attachment_fh:
                    attachment_fh.write(remote_file.read())
                local_params.append(local_filename)
            else:
                local_params.append(param["value"])

    def log(self, message):
        with open(self.log_path, "at") as fh:
            fh.write(message)

    def logline(self, message):
        self.log(message + "\n")

    def run(self):
        self.read_property_from_file("status", self.status_path)
        if self["status"] != "SUBMITTED":
            os.sys.stderr.write(
                "Job %s: Will only run jobs with status %s\n"
                % (self.id, self["status"])
            )
            return
        log = open(self.log_path, "a")
        self.load_local_parameters()
        self.set_status("RUNNING")
        cmd = [self.executable_path]
        cmd.extend(self["local_parameters"])
        self.mark_started()
        log.write(
            ">>> Starting process '%s' with arguments [%s] at %s\n"
            % (
                self.executable_path,
                ", ".join(self["local_parameters"]),
                self["started"],
            )
        )
        log.flush()
        ret_val = subprocess.call(
            cmd, stdout=log, stderr=log, timeout=get_job_timeout()
        )
        self.mark_finished()
        log.flush()
        if ret_val == 0:
            self.set_status("DONE")
            log.write(">>> Succeeded at %s\n" % self["finished"])
        else:
            self.set_status("FAILED")
            log.write(
                ">>> Failed with exit status %s at %s\n" % (ret_val, self["finished"])
            )
        log.close()


def get_url_and_uid():
    config = OS2borgerPCConfig()
    uid = config.get_value("uid")
    config_data = config.get_data()
    admin_url = config_data.get("admin_url")
    if not admin_url:
        print("Incorrect setup of OS2borgerPC admin client", file=sys.stderr)
        return (None, None)
    xml_rpc_url = config_data.get("xml_rpc_url", "/admin-xml/")
    rpc_url = urllib.parse.urljoin(admin_url, xml_rpc_url)
    return (rpc_url, uid)


def get_job_timeout():
    config = OS2borgerPCConfig()

    if has_config("job_timeout"):
        try:
            job_timeout = int(config.get_value("job_timeout"))
        except ValueError:
            job_timeout = DEFAULT_JOB_TIMEOUT
    else:
        job_timeout = DEFAULT_JOB_TIMEOUT

    return job_timeout


def get_instructions():
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    try:
        instructions = remote.get_instructions(uid)
    except Exception as e:
        print("Error while getting instructions:" + str(e), file=sys.stderr)

        # No instructions likely = no network. Do not continue.
        raise

    if "configuration" in instructions:
        # Update configuration
        config = OS2borgerPCConfig()
        local_config = {}
        for key, value in config.get_data().items():
            # We only care about string values
            if isinstance(value, str):
                local_config[key] = value

        for key, value in instructions["configuration"].items():
            config.set_value(key, value)
            if key in local_config:
                del local_config[key]

        # Anything left in local_config needs to be removed
        for key in local_config.keys():
            config.remove_key(key)

        config.save()

    # Import jobs
    if "jobs" in instructions:
        for j in instructions["jobs"]:
            local_job = LocalJob(data=j)
            local_job.save()
            local_job.logline("Job imported at %s" % datetime.now())

    security_dir = Path(SECURITY_DIR)
    # if security dir exists
    if security_dir.is_dir():
        # Always remove the old security scripts -- perhaps this PC has been
        # moved to another group and no longer needs them
        for old_script in security_dir.glob("s_*"):
            old_script.unlink()

        # Import the fresh security scripts
        if "security_scripts" in instructions:
            for s in instructions["security_scripts"]:
                script = security_dir.joinpath("s_" + s["name"].replace(" ", ""))
                with script.open("wt") as fh:
                    fh.write(s["executable_code"])
                script.chmod(stat.S_IRWXU)


def check_outstanding_packages():
    # Get number of packages with updates and number of security updates.
    # This is really a wrapper for apt-check.
    try:
        proc = subprocess.Popen(
            ["/usr/lib/update-notifier/apt-check"],
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        _, err = proc.communicate()
        package_updates, security_updates = [int(x) for x in err.split(";")]
        return (package_updates, security_updates)
    except Exception:
        print("apt-check failed\n", file=sys.stderr)
        traceback.print_exc()
        return None


def report_job_results(joblist):
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)
    remote.send_status_info(
        uid, None, joblist, update_required=check_outstanding_packages()
    )


def flat_map(iterable, function):
    for i in iterable:
        v = function(i)
        if v:
            yield v


def get_job_dirs(status_list):
    result = []
    # Return job directories sorted by job ID, to make sure they get executed
    # in a predictable order

    def _numbered_dir(item):
        try:
            dirpath = os.path.join(JOBS_DIR, item)
            if os.path.isdir(dirpath):
                return int(item)
        except ValueError:
            pass
        return None

    job_ids = sorted(flat_map(os.listdir(JOBS_DIR), _numbered_dir))
    for job_id in job_ids:
        dirpath = os.path.join(JOBS_DIR, str(job_id))
        filename = os.path.join(dirpath, "status")
        if os.path.exists(filename):
            with open(filename, "r") as fh:
                if fh.read() in status_list:
                    result.append(dirpath)
    return result


def run_pending_jobs():
    dirs = get_job_dirs(status_list=["SUBMITTED"])
    results = []

    for d in dirs:
        job = LocalJob(path=d)
        job.run()
        results.append(job.report_data)

    report_job_results(results)


def send_unsent_jobs():
    dirs = get_job_dirs(status_list=["DONE", "FAILED"])
    jobs = []

    for d in dirs:
        job = LocalJob(path=d)
        job.load_from_path()
        if "sent" not in job or not job["sent"]:
            jobs.append(job)

    report_job_results([job.report_data for job in jobs])

    for job in jobs:
        job.mark_sent()


def fail_unfinished_jobs():
    dirs = get_job_dirs(status_list=["RUNNING"])
    now = datetime.now()

    for d in dirs:
        job = LocalJob(path=d)
        job.load_from_path()
        if (
            "started" in job
            and (
                now - datetime.strptime(job["started"], "%Y-%m-%d %H:%M:%S.%f")
            ).seconds
            > get_job_timeout()
        ):
            job.mark_finished()
            job.set_status("FAILED")
            job.logline(">>> Failed due to timeout at %s\n" % (job["finished"]))


def run_security_scripts():
    try:
        if os.path.getsize(SECURITY_DIR + "/security_log.txt") > 10000:
            os.remove(SECURITY_DIR + "/security_log.txt")

        log = open(SECURITY_DIR + "/security_log.txt", "a")
    except (OSError):
        # File does not exists, so we create it.
        os.mknod(SECURITY_DIR + "/security_log.txt")
        log = open(SECURITY_DIR + "/security_log.txt", "a")

    for filename in glob.glob(SECURITY_DIR + "/s_*"):
        print(">>>" + filename, file=log)
        cmd = [filename]
        ret_val = subprocess.call(cmd, shell=True, stdout=log, stderr=log)
        if ret_val == 0:
            print(">>>" + filename + " Succeeded", file=log)
        else:
            print(">>>" + filename + " Failed", file=log)

    log.close()


def collect_security_events(now):
    # execute scripts
    run_security_scripts()

    try:
        check_file = open(SECURITY_DIR + "/lastcheck.txt", "r")
    except OSError:
        # File does not exists, so we create it.
        os.mknod(SECURITY_DIR + "/lastcheck.txt")
        check_file = open(SECURITY_DIR + "/lastcheck.txt", "r")

    last_security_check = datetime.strptime(now, "%Y%m%d%H%M")
    last_check = check_file.read()
    if last_check:
        last_security_check = datetime.strptime(last_check, "%Y%m%d%H%M")

    check_file.close()

    try:
        csv_file = open(SECURITY_DIR + "/securityevent.csv", "r")
    except OSError:
        # File does not exist. No events occured, since last check.
        return False

    data = ""
    for line in csv_file:
        csv_split = line.split(",")
        if datetime.strptime(csv_split[0], "%Y%m%d%H%M") >= last_security_check:
            data += line

    # Check if any new events occured
    if data != "":
        with open(SECURITY_DIR + "/security_check_" + now + ".csv", "wt") as (
            check_file
        ):
            check_file.write(data)

    csv_file.close()


def send_security_events(now):
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    try:
        with open(SECURITY_DIR + "/security_check_" + now + ".csv", "r") as fh:
            csv_data = [line for line in fh]

        try:
            result = remote.push_security_events(uid, csv_data)
            if result == 0:
                with open(SECURITY_DIR + "/lastcheck.txt", "wt") as check_file:
                    check_file.write(now)
                os.remove(SECURITY_DIR + "/securityevent.csv")

            return result
        except Exception:
            print("Error while sending security events", file=sys.stderr)
            traceback.print_exc()
            return False
        finally:
            os.remove(SECURITY_DIR + "/security_check_" + now + ".csv")
    except OSError:
        # File does not exist. No events occured, since last check.
        return False


def handle_security_events():
    # if security dir exists
    if os.path.isdir(SECURITY_DIR):
        now = datetime.now().strftime("%Y%m%d%H%M")
        collect_security_events(now)
        send_security_events(now)


def send_config_value(key, value):
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    remote.push_config_keys(uid, {key: value})


def update_and_run():
    for folder in (
        JOBS_DIR,
        SECURITY_DIR,
    ):
        os.makedirs(folder, mode=0o700, exist_ok=True)
    config = OS2borgerPCConfig()
    # Get OS info for configuration
    release = lsb_release.get_distro_information()
    if "ID" in release:
        os_name = release["ID"]
    if "RELEASE" in release:
        os_release = release["RELEASE"]
    if has_config("job_timeout"):
        try:
            job_timeout = int(config.get_value("job_timeout"))
        except ValueError:
            job_timeout = DEFAULT_JOB_TIMEOUT
    else:
        job_timeout = DEFAULT_JOB_TIMEOUT
        send_config_value("job_timeout", job_timeout)
    try:
        with filelock(LOCK_FILE, max_age=job_timeout):
            try:
                send_config_value(
                    "_os2borgerpc.client_version", OS2BORGERPC_CLIENT_VERSION
                )
                send_config_value("_os_release", os_release)
                send_config_value("_os_name", os_name)
                get_instructions()
                fail_unfinished_jobs()
                send_unsent_jobs()
                run_pending_jobs()
                handle_security_events()
            except (OSError, socket.error):
                print("Network error, exiting ...")
                traceback.print_exc()
    except OSError:
        print("Couldn't get lock")
        traceback.print_exc()


if __name__ == "__main__":
    update_and_run()
