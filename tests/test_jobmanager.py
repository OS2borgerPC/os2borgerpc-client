import stat
from datetime import (
    datetime,
    timedelta,
)
from pathlib import Path
from unittest import mock
from freezegun import freeze_time

from os2borgerpc.client.security import security
from os2borgerpc.client import (
    jobmanager,
    config,
)


class TestJobManager:
    def test_get_job_dirs(self, tmpdir):
        jobs = tmpdir.mkdir("jobs")
        job_1 = jobs.join("1")
        job_1.join("status").write("DONE", mode="w+", ensure=True)

        jobs.join("2").join("status").write("RUNNING", mode="w+", ensure=True)
        jobs.join("3").join("status").write("FAILED", mode="w+", ensure=True)

        job_4 = jobs.join("4")
        job_4.join("status").write("DONE", mode="w+", ensure=True)

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            job_dirs = jobmanager.get_job_dirs(["DONE"])

        assert job_dirs == [str(job_1), str(job_4)]

    @freeze_time("2022-01-01 12:00:00")
    def test_send_unsent_jobs(self, tmpdir):
        now = datetime.now()
        report_job_results_mock = mock.MagicMock()
        jobmanager.report_job_results = report_job_results_mock

        jobs = tmpdir.mkdir("jobs")

        sent_job = jobs.join("1")
        sent_job.join("status").write("DONE", mode="w+", ensure=True)
        sent_job.join("started").write(str(now), mode="w+", ensure=True)
        sent_job.join("finished").write(str(now), mode="w+", ensure=True)
        sent_job.join("sent").write(str(now), mode="w+", ensure=True)
        sent_job.join("output.log").write("test_log", mode="w+", ensure=True)

        unsent_job = jobs.join("2")
        unsent_job.join("status").write("DONE", mode="w+", ensure=True)
        unsent_job.join("started").write(str(now), mode="w+", ensure=True)
        unsent_job.join("finished").write(str(now), mode="w+", ensure=True)
        unsent_job.join("output.log").write("test_log", mode="w+", ensure=True)

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.send_unsent_jobs()

        assert report_job_results_mock.call_args == mock.call(
            [
                {
                    "id": "2",
                    "status": "DONE",
                    "started": str(now),
                    "finished": str(now),
                    "log_output": "test_log",
                }
            ]
        )
        assert unsent_job.join("sent").read() == "2022-01-01 12:00:00"

    @freeze_time(
        datetime(year=2022, month=1, day=1, hour=12, minute=0, second=0, microsecond=1)
    )
    def test_fail_unfinished_jobs(self, tmpdir):
        now = datetime.now()
        jobs = tmpdir.mkdir("jobs")

        unfinished_job = jobs.join("1")
        unfinished_job.join("status").write("RUNNING", mode="w+", ensure=True)
        unfinished_job.join("started").write(
            str(now - timedelta(seconds=jobmanager.DEFAULT_JOB_TIMEOUT + 1)),
            mode="w+",
            ensure=True,
        )

        finished_job = jobs.join("2")
        finished_job.join("status").write("DONE", mode="w+", ensure=True)
        finished_job.join("started").write(str(now), mode="w+", ensure=True)
        finished_job.join("finished").write(str(now), mode="w+", ensure=True)
        finished_job.join("output.log").write("test_log", mode="w+", ensure=True)
        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.fail_unfinished_jobs()

        assert unfinished_job.join("status").read() == "FAILED"
        assert unfinished_job.join("finished").read() == "2022-01-01 12:00:00.000001"
        assert (
            unfinished_job.join("output.log").read()
            == ">>> Failed due to timeout at 2022-01-01 12:00:00.000001\n"
        )

    @freeze_time(
        datetime(year=2022, month=1, day=1, hour=12, minute=0, second=0, microsecond=1)
    )
    def test_run_pending_jobs_success(self, tmpdir):
        report_job_results_mock = mock.MagicMock()
        jobmanager.report_job_results = report_job_results_mock

        jobs = tmpdir.mkdir("jobs")

        pending_job = jobs.join("1")
        pending_job.join("status").write("SUBMITTED", mode="w+", ensure=True)
        pending_job_executable = pending_job.join("executable")
        pending_job_executable.write(
            "#!/usr/bin/env sh\necho 'hello'", mode="w+", ensure=True
        )
        pending_job_executable.chmod(pending_job_executable.stat().mode | stat.S_IEXEC)

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.run_pending_jobs()

        assert pending_job.join("status").read() == "DONE"
        assert pending_job.join("finished").read() == "2022-01-01 12:00:00.000001"
        assert pending_job.join("output.log").read() == (
            f">>> Starting process '{str(pending_job_executable)}' with arguments []"
            " at 2022-01-01 12:00:00.000001\n"
            "hello\n"
            ">>> Succeeded at 2022-01-01 12:00:00.000001\n"
        )

    @freeze_time(
        datetime(year=2022, month=1, day=1, hour=12, minute=0, second=0, microsecond=1)
    )
    def test_run_pending_jobs_failed(self, tmpdir):
        report_job_results_mock = mock.MagicMock()
        jobmanager.report_job_results = report_job_results_mock

        jobs = tmpdir.mkdir("jobs")
        # Create a pending executable job.
        pending_job = jobs.join("1")
        pending_job.join("status").write("SUBMITTED", mode="w+", ensure=True)
        pending_job_executable = pending_job.join("executable")
        pending_job_executable.write(
            "#!/usr/bin/env sh\nexit 1", mode="w+", ensure=True
        )
        pending_job_executable.chmod(pending_job_executable.stat().mode | stat.S_IXUSR)

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.run_pending_jobs()

        assert pending_job.join("status").read() == "FAILED"
        assert pending_job.join("finished").read() == "2022-01-01 12:00:00.000001"
        assert pending_job.join("output.log").read() == (
            f">>> Starting process '{str(pending_job_executable)}' with arguments []"
            " at 2022-01-01 12:00:00.000001\n"
            ">>> Failed with exit status 1 at 2022-01-01 12:00:00.000001\n"
        )

    def test_collect_security_security_events(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        security_event_file = security_dir.join("securityevent.csv")

        security_event_lines = (
            "202201011156,Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0"
            " ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "202201011156,Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo:"
            " pam_unix(sudo:session): session opened for user root by (uid=0)\n"
        )
        # Write some generated security events.
        security_event_file.write(security_event_lines)

        with mock.patch(
            "os2borgerpc.client.security.security.SECURITY_EVENT_FILE",
            Path(security_event_file),
        ):
            last_check = datetime(year=2022, month=1, day=1, hour=11, minute=50)
            security_events = security.collect_security_events(last_check)

        # Assert the security_events are returned.
        assert security_events == [
            (
                "202201011156,"
                "Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
                " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            ),
            (
                "202201011156,"
                "Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
                " session opened for user root by (uid=0)\n"
            ),
        ]

    @mock.patch(
        "os2borgerpc.client.security.security.get_url_and_uid", lambda: ("url", "uid")
    )
    def test_send_security_events_success(self, tmpdir):
        # Mock OS2borgerPCAdmin and return a success value on 'push_security_events'.
        os2borgerpcadmin_mock = mock.MagicMock()
        security.OS2borgerPCAdmin = os2borgerpcadmin_mock
        os2borgerpcadmin_mock.return_value.push_security_events.return_value = 0

        security_events = [
            (
                "202201011156,"
                "Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
                " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            ),
            (
                "202201011156,"
                "Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
                " session opened for user root by (uid=0)\n"
            ),
        ]

        result = security.send_security_events(security_events)

        # Assert security events are pushed.
        security_events_mock = os2borgerpcadmin_mock.return_value.push_security_events

        assert security_events_mock.call_args_list == [
            mock.call("uid", security_events)
        ]

        assert result is True

    @mock.patch(
        "os2borgerpc.client.security.security.get_url_and_uid", lambda: ("url", "uid")
    )
    def test_send_security_events_failed(self, tmpdir):
        # Mock OS2borgerPCAdmin and return a failed value on 'push_security_events'.
        os2borgerpcadmin_mock = mock.MagicMock()
        security.OS2borgerPCAdmin = os2borgerpcadmin_mock
        # Server should return 1 or an integer other than 0.
        os2borgerpcadmin_mock.return_value.push_security_events.return_value = 1

        security_events = [
            (
                "202201011156,"
                "Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
                " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            ),
            (
                "202201011156,"
                "Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
                " session opened for user root by (uid=0)\n"
            ),
        ]
        result = security.send_security_events(security_events)

        # Assert security events are pushed.
        security_events_mock = os2borgerpcadmin_mock.return_value.push_security_events

        assert security_events_mock.call_args_list == [
            mock.call("uid", security_events)
        ]

        assert result is False

    @freeze_time("2022-01-01 12:00:00")
    @mock.patch("os2borgerpc.client.jobmanager.get_url_and_uid", lambda: ("url", "uid"))
    def test_import_new_security_scripts(self, tmpdir):
        # Mock OS2borgerPCAdmin and return instructions on 'get_instructions'.
        os2borgerpc_dir = tmpdir.mkdir("os2borgerpc")
        security_dir = tmpdir.mkdir("security")

        os2borgerpcadmin_mock = mock.MagicMock()
        jobmanager.OS2borgerPCAdmin = os2borgerpcadmin_mock
        os2borgerpc_conf = os2borgerpc_dir.join("os2borgerpc.conf").ensure()

        os2borgerpcconfig_mock = mock.MagicMock()
        jobmanager.OS2borgerPCConfig = os2borgerpcconfig_mock
        os2borgerpcconfig_mock.return_value = config.OS2borgerPCConfig(
            [str(os2borgerpc_conf)]
        )
        instructions = {
            "configuration": {
                "admin_url": "test.com",
                "distribution": "os2borgerpc20.04",
                "hostname": "shg-pc",
                "site": "magenta",
                "uid": "uid",
            },
            "jobs": [
                {
                    "id": 1,
                    "status": "SUBMITTED",
                    "parameters": [{"type": "string", "value": "hello parameter"}],
                    "executable_code": "#!/usr/bin/env\necho $1",
                },
            ],
            "security_scripts": [
                {
                    "name": "test_security_script.sh",
                    "executable_code": (
                        "#!/usr/bin/env\necho 'this is a security script'"
                    ),
                }
            ],
        }
        os2borgerpcadmin_mock.return_value.get_instructions.return_value = instructions

        with mock.patch(
            "os2borgerpc.client.security.security.SECURITY_DIR", Path(security_dir)
        ):
            security.import_new_security_scripts(instructions["security_scripts"])

        security_script = security_dir.join("s_test_security_script.sh")
        # Assert security script are created properly and are executable.
        assert (
            security_script.read() == "#!/usr/bin/env\necho 'this is a security script'"
        )
        assert security_script.stat().mode & stat.S_IXUSR

    @freeze_time("2022-01-01 12:00:00")
    @mock.patch("os2borgerpc.client.jobmanager.get_url_and_uid", lambda: ("url", "uid"))
    def test_update_configuration_and_import_jobs(self, tmpdir):
        # Mock OS2borgerPCAdmin and return instructions on 'get_instructions'.
        jobs = tmpdir.mkdir("jobs")
        os2borgerpc_dir = tmpdir.mkdir("os2borgerpc")

        os2borgerpcadmin_mock = mock.MagicMock()
        jobmanager.OS2borgerPCAdmin = os2borgerpcadmin_mock
        os2borgerpc_conf = os2borgerpc_dir.join("os2borgerpc.conf").ensure()

        os2borgerpcconfig_mock = mock.MagicMock()
        jobmanager.OS2borgerPCConfig = os2borgerpcconfig_mock
        os2borgerpcconfig_mock.return_value = config.OS2borgerPCConfig(
            [str(os2borgerpc_conf)]
        )
        instructions = {
            "configuration": {
                "admin_url": "test.com",
                "distribution": "os2borgerpc20.04",
                "hostname": "shg-pc",
                "site": "magenta",
                "uid": "uid",
            },
            "jobs": [
                {
                    "id": 1,
                    "status": "SUBMITTED",
                    "parameters": [{"type": "string", "value": "hello parameter"}],
                    "executable_code": "#!/usr/bin/env\necho $1",
                },
            ],
            "security_scripts": [
                {
                    "name": "test_security_script.sh",
                    "executable_code": (
                        "#!/usr/bin/env\necho 'this is a security script'"
                    ),
                }
            ],
        }
        os2borgerpcadmin_mock.return_value.get_instructions.return_value = instructions

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.update_configuration_from_server(instructions["configuration"])
            jobmanager.import_jobs(instructions["jobs"])

        job = jobs.join("1")
        # Assert job are created properly and are executable.
        assert job.check()
        assert job.join("status").read() == "SUBMITTED"
        assert job.join("executable").read() == "#!/usr/bin/env\necho $1"
        assert job.join("executable").stat().mode & stat.S_IXUSR
        assert job.join("output.log").read() == "Job imported at 2022-01-01 12:00:00\n"
