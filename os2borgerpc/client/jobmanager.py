"""Module for jobmanager."""
import json
import os.path
import re
import socket
import stat
import subprocess
import sys
import traceback
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime

import chardet
import distro
import pkg_resources

from os2borgerpc.client.admin_client import OS2borgerPCAdmin
from os2borgerpc.client.config import has_config
from os2borgerpc.client.config import OS2borgerPCConfig
from os2borgerpc.client.security.security import check_security_events
from os2borgerpc.client.utils import filelock
from os2borgerpc.client.utils import get_url_and_uid


# Keep this in sync with package name in setup.py
OS2BORGERPC_CLIENT_VERSION = pkg_resources.get_distribution(
    "os2borgerpc_client"
).version
DEFAULT_JOB_TIMEOUT = 900

JOBS_DIR = "/var/lib/os2borgerpc/jobs"
LOCK_FILE = os.path.join(JOBS_DIR, "running")


class LocalJob(dict):
    """
    Job Model representing a job received from the server.

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

    Job statuses:
    SUBMITTED: Job has not been run yet
    RUNNING: Job execution was just started
    FAILED: Job ran, exiting with a nonzero status code (failure)
    DONE: Job ran, exiting with status code zero (success)
    """

    def __init__(self, id=None, path=None, data=None):
        """Primarily populates instance with data."""
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
            os.makedirs(self.path, mode=0o700, exist_ok=True)

        # Initialize with given data
        if data is not None:
            self.populate(data)

    @property
    def path(self):
        """Return the job root path."""
        return os.path.join(JOBS_DIR, str(self.id))

    @property
    def attachments_path(self):
        """Return the attachments path."""
        return os.path.join(self.path, "attachments")

    @property
    def executable_path(self):
        """Return the executable path."""
        return os.path.join(self.path, "executable")

    @property
    def parameters_path(self):
        """Return the parameters path."""
        return os.path.join(self.path, "parameters.json")

    @property
    def status_path(self):
        """Return the status path."""
        return os.path.join(self.path, "status")

    @property
    def started_path(self):
        """Return the started path."""
        return os.path.join(self.path, "started")

    @property
    def finished_path(self):
        """Return the finished path."""
        return os.path.join(self.path, "finished")

    @property
    def sent_path(self):
        """Return the sent path."""
        return os.path.join(self.path, "sent")

    @property
    def log_path(self):
        """Return the output log path."""
        return os.path.join(self.path, "output.log")

    @property
    def report_data(self):
        """Return the report data for the admin site."""
        self.load_from_path()
        result = {"id": self.id}
        for k in ["status", "started", "finished", "log_output"]:
            result[k] = self[k]
        return result

    def set_status(self, value):
        """Set job status."""
        self["status"] = value
        self.save_property_to_file("status", self.status_path)

    def mark_started(self):
        """Set started time."""
        self["started"] = str(datetime.now())
        self.save_property_to_file("started", self.started_path)

    def mark_finished(self):
        """Set finished time."""
        self["finished"] = str(datetime.now())
        self.save_property_to_file("finished", self.finished_path)

    def mark_sent(self):
        """Set sent time."""
        self["sent"] = str(datetime.now())
        self.save_property_to_file("sent", self.sent_path)

    def load_local_parameters(self):
        """Load local job parameters."""
        self.read_property_from_file("json_params", self.parameters_path)
        if "json_params" in self:
            self["local_parameters"] = json.loads(self["json_params"])
            del self["json_params"]
        else:
            self["local_parameters"] = []

    def load_from_path(self, full_info=False):
        """Load properties from a path."""
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

    def handle_unsupported_file_encoding(self, prop, file_path):
        """Error handling in case a file has an unsupported file encoding."""
        if file_path == self.log_path:  # If the current property is a log file
            self[
                prop
            ] = "The log had an unsupported file encoding (neither utf-8 nor latin-1)"
        else:
            self[prop] = ""

    def read_property_from_file(self, prop, file_path):
        """Read property from file."""
        try:
            with open(file_path, "rb") as file_detect:
                text_detect = file_detect.read()
                file_detect = chardet.detect(text_detect)

            if (
                file_detect["encoding"] == "windows-1252"
                or file_detect["encoding"] == "ISO-8859-1"
            ):
                try:
                    with open(file_path, "rt", encoding="latin-1") as fh:
                        self[prop] = fh.read()
                except Exception:
                    self.handle_unsupported_file_encoding(prop, file_path)
            else:  # Assuming utf-8
                try:
                    with open(file_path, "rt") as fh:
                        self[prop] = fh.read()
                except UnicodeDecodeError:
                    self.handle_unsupported_file_encoding(prop, file_path)

        except OSError:
            pass

    def save_property_to_file(self, prop, file_path):
        """Save property to file."""
        if prop in self:
            with open(file_path, "wt") as fh:
                fh.write(self[prop])

    def populate(self, data):
        """Populate instance with data."""
        for k in data.keys():
            self[k] = data[k]

    def save(self):
        """Save the instance."""
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
        """Translate job parameters from an url to a file or string value."""
        if "parameters" not in self:
            return

        config = OS2borgerPCConfig()
        admin_url = config.get_value("admin_url")

        local_params = []
        self["local_parameters"] = local_params
        params = self["parameters"]
        del self["parameters"]
        for index, param in enumerate(params):
            if param["type"] == "FILE" and param["value"]:
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
                local_params.append({"type": param["type"], "value": local_filename})
            else:
                local_params.append(param)

    def log(self, message):
        """Write message to log file."""
        with open(self.log_path, "at") as fh:
            fh.write(message)

    def logline(self, message):
        """Write a single line to log file."""
        self.log(message + "\n")

    def run(self):
        """Run the job."""
        self.read_property_from_file("status", self.status_path)
        if self["status"] != "SUBMITTED":
            sys.stderr.write(
                "Job %s: Will only run jobs with status %s\n"
                % (self.id, self["status"])
            )
            return
        log = open(self.log_path, "a")
        self.load_local_parameters()
        self.set_status("RUNNING")
        cmd = [self.executable_path]
        log_params = []

        for param in self["local_parameters"]:
            cmd.append(param["value"])
            if param["type"] == "PASSWORD":
                log_params.append("•••••")
            else:
                log_params.append(param["value"])

        self.mark_started()
        log.write(
            ">>> Starting process '%s' with arguments [%s] at %s\n"
            % (
                self.executable_path,
                ", ".join(log_params),
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
        os.remove(self.parameters_path)
        log.close()


def get_job_timeout():
    """Return the set job timeout, may be the default."""
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
    """Get instructions from the admin site server."""
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    try:
        instructions = remote.get_instructions(uid)
    except Exception as e:
        print("Error while getting instructions:" + str(e), file=sys.stderr)

        # No instructions likely = no network. Do not continue.
        raise

    return instructions


def import_jobs(jobs):
    """Import jobs from instructions and save them."""
    for j in jobs:
        local_job = LocalJob(data=j)
        local_job.save()
        local_job.logline("Job imported at %s" % datetime.now())


def update_configuration_from_server(configurations):
    """Update (local) configuration from admin site server."""
    config = OS2borgerPCConfig()
    local_config = {}
    for key, value in config.get_data().items():
        # We only care about string values
        if isinstance(value, str):
            local_config[key] = value

    for key, value in configurations.items():
        config.set_value(key, value)
        if key in local_config:
            del local_config[key]

    # Anything left in local_config needs to be removed
    for key in local_config.keys():
        config.remove_key(key)

    config.save()


def check_outstanding_packages():
    """
    Get number of packages with updates and number of security updates.

    This is really a wrapper for apt-check.
    """
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
    """Report job results back to the admin site server."""
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    # Sanitize log output so we're sure it's valid XML before XMLRPC request
    for job in joblist:
        # Remove terminal control characters except newlines
        job["log_output"] = "".join(
            ch
            for ch in job["log_output"]
            if unicodedata.category(ch)[0] != "C" or ch == "\n"
        )

    try:
        # This returns 0 on various interpretations of success
        return remote.send_status_info(
            uid, None, joblist, update_required=check_outstanding_packages()
        )
    except Exception:
        print("Failed to check in with the admin-site")
        traceback.print_exc()
        return 1


def flat_map(iterable, function):
    """Flatten an iterable."""
    for i in iterable:
        v = function(i)
        if v:
            yield v


def get_job_dirs(status_list):
    """Return the directories of jobs with a status in status_list."""
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
    """Run the submitted jobs."""
    dirs = get_job_dirs(status_list=["SUBMITTED"])
    results = []

    for d in dirs:
        job = LocalJob(path=d)
        job.run()
        results.append(job.report_data)

    report_job_results(results)


def send_unsent_jobs():
    """Send unsent done or failed jobs."""
    dirs = get_job_dirs(status_list=["DONE", "FAILED"])
    jobs = []

    for d in dirs:
        job = LocalJob(path=d)
        job.load_from_path()
        if "sent" not in job or not job["sent"]:
            jobs.append(job)

    if report_job_results([job.report_data for job in jobs]) == 0:
        for job in jobs:
            job.mark_sent()


def fail_unfinished_jobs():
    """Fail jobs that are stuck in running state."""
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
            job.logline(">>> Failed due to timeout at %s" % (job["finished"]))


def send_config_values(config_dict):
    """Send config value to admin site server."""
    (remote_url, uid) = get_url_and_uid()
    remote = OS2borgerPCAdmin(remote_url)

    remote.push_config_keys(uid, config_dict)


def update_and_run():
    """Run the main function for the jobmanager."""
    os.makedirs(JOBS_DIR, mode=0o700, exist_ok=True)
    config = OS2borgerPCConfig()
    # Get OS info for configuration
    os_name = distro.name()
    os_release = distro.version()
    try:
        ip_addresses = subprocess.run(
            ["hostname", "--all-ip-addresses"], capture_output=True, text=True
        ).stdout.strip()
    except subprocess.CalledProcessError:
        ip_addresses = ""
    if has_config("job_timeout"):
        try:
            job_timeout = int(config.get_value("job_timeout"))
        except ValueError:
            job_timeout = DEFAULT_JOB_TIMEOUT
    else:
        job_timeout = DEFAULT_JOB_TIMEOUT
        send_config_values({"job_timeout": job_timeout})
    try:
        with filelock(LOCK_FILE, max_age=job_timeout):
            try:
                send_config_values(
                    {
                        "_os2borgerpc.client_version": OS2BORGERPC_CLIENT_VERSION,
                        "_os_release": os_release,
                        "_os_name": os_name,
                        "_ip_addresses": ip_addresses,
                    }
                )
                instructions = get_instructions()
                if "jobs" in instructions:
                    import_jobs(instructions["jobs"])
                if "configuration" in instructions:
                    update_configuration_from_server(instructions["configuration"])
                run_pending_jobs()
                fail_unfinished_jobs()
                send_unsent_jobs()
                security_scripts = instructions.get("security_scripts", [])
                check_security_events(security_scripts)
            except (OSError, socket.error):
                print("Network error, exiting ...")
                traceback.print_exc()
    except OSError:
        print("Couldn't get lock")
        traceback.print_exc()


if __name__ == "__main__":
    update_and_run()
