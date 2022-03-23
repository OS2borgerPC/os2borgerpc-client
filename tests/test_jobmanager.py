import stat
from datetime import (
    datetime,
    timedelta,
)
from unittest import mock
from freezegun import freeze_time

from os2borgerpc.client import jobmanager


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
        now = datetime.now()
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
        now = datetime.now()
        report_job_results_mock = mock.MagicMock()
        jobmanager.report_job_results = report_job_results_mock

        jobs = tmpdir.mkdir("jobs")

        pending_job = jobs.join("1")
        pending_job.join("status").write("SUBMITTED", mode="w+", ensure=True)
        pending_job_executable = pending_job.join("executable")
        pending_job_executable.write(
            "#!/usr/bin/env sh\nexit 1", mode="w+", ensure=True
        )
        pending_job_executable.chmod(pending_job_executable.stat().mode | stat.S_IEXEC)

        with mock.patch("os2borgerpc.client.jobmanager.JOBS_DIR", jobs):
            jobmanager.run_pending_jobs()

        assert pending_job.join("status").read() == "FAILED"
        assert pending_job.join("finished").read() == "2022-01-01 12:00:00.000001"
        assert pending_job.join("output.log").read() == (
            f">>> Starting process '{str(pending_job_executable)}' with arguments []"
            " at 2022-01-01 12:00:00.000001\n"
            ">>> Failed with exit status 1 at 2022-01-01 12:00:00.000001\n"
        )
