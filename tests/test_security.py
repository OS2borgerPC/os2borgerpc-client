import stat
from datetime import datetime

from pathlib import Path
from unittest import mock
from freezegun import freeze_time

from os2borgerpc.client.security import security


class TestCollectSecurityEvents:
    def test_collect_security_security_events(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        security_event_file = security_dir.join("securityevent.csv")

        security_event_lines = (
            "20220101115601,Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0"
            " ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "20220101115601,Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo:"
            " pam_unix(sudo:session): session opened for user root by (uid=0)\n"
        )
        # Write some generated security events.
        security_event_file.write(security_event_lines)

        with mock.patch(
            "os2borgerpc.client.security.security.SECURITY_EVENT_FILE",
            Path(security_event_file),
        ):
            last_check = datetime(
                year=2022, month=1, day=1, hour=11, minute=50, second=0
            )
            security_events = security.collect_security_events(last_check)

        # Assert the security_events are returned.
        assert security_events == [
            (
                "20220101115601,"
                "Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
                " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            ),
            (
                "20220101115601,"
                "Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
                " session opened for user root by (uid=0)\n"
            ),
        ]


class TestSendSecurityEvents:
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


class TestImportNewSecurityScripts:
    @mock.patch("os2borgerpc.client.jobmanager.get_url_and_uid", lambda: ("url", "uid"))
    def test_import_new_security_scripts(self, tmpdir):
        security_dir = tmpdir.mkdir("security")

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


class TestCheckSecurityEvents:
    @mock.patch(
        "os2borgerpc.client.security.security.cleanup_security_scripts", lambda: None
    )
    @mock.patch(
        "os2borgerpc.client.security.security.import_new_security_scripts", lambda: None
    )
    @mock.patch(
        "os2borgerpc.client.security.security.run_security_scripts", lambda: None
    )
    def test_check_security_events_only_send_new_events(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        lastcheck = security_dir.join("lastcheck")
        security_event_file = security_dir.join("securityevent.csv")

        security_event_lines = (
            "20220101115601,Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: "
            "root : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "20220101115602,Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo:"
            " pam_unix(sudo:session): session opened for user root by (uid=0)\n"
        )
        # Write some generated security events.
        security_event_file.write(security_event_lines)
        # Set a lastcheck time in the past (11:55).
        lastcheck.write("20220101115500")

        send_security_events_mock = mock.MagicMock()
        with mock.patch.multiple(
            "os2borgerpc.client.security.security",
            cleanup_security_scripts=lambda: None,
            import_new_security_scripts=lambda scripts: None,
            run_security_scripts=lambda: None,
            send_security_events=send_security_events_mock,
            SECURITY_DIR=Path(security_dir),
            LAST_SECURITY_EVENTS_CHECKED_TIME=lastcheck,
            SECURITY_EVENT_FILE=security_event_file,
        ):
            # Return success on send_security_events.
            # These new events should be sent.
            send_security_events_mock.return_value = True
            with freeze_time(
                datetime(year=2022, month=1, day=1, hour=11, minute=56, second=2)
            ):
                security.check_security_events(["stub-security-script"])

            assert len(send_security_events_mock.call_args_list) == 1
            calls = [
                mock.call(
                    [
                        "20220101115601,Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root "
                        ": TTY=pts/0 ; PWD=/home/user ; USER=root ;"
                        " COMMAND=/usr/bin/ls\n",
                        "20220101115602,Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: "
                        "pam_unix(sudo:session): session opened for user "
                        "root by (uid=0)\n",
                    ]
                )
            ]
            assert send_security_events_mock.call_args_list == calls

            security_event_lines = (
                "20220101115601,Jan 01 11:56:05  shg-borgerpc-3-1-1 sudo: "
                "root : TTY=pts/0 ; PWD=/home/user ; USER=root "
                "; COMMAND=/usr/bin/ls\n"
                "20220101115602,Jan 01 11:56:06  shg-borgerpc-3-1-1 sudo: "
                "pam_unix(sudo:session): session opened for user root by (uid=0)\n"
            )
            security_event_file.write(security_event_lines)
            # These old events should not be sent.
            with freeze_time(
                datetime(year=2022, month=1, day=1, hour=12, minute=0, second=2)
            ):
                security.check_security_events(["stub-security-script"])

            assert len(send_security_events_mock.call_args_list) == 1
            calls = [
                mock.call(
                    [
                        "20220101115601,Jan 01 11:56:01  shg-borgerpc-3-1-1 sudo: root "
                        ": TTY=pts/0 ; PWD=/home/user ; USER=root ;"
                        " COMMAND=/usr/bin/ls\n",
                        "20220101115602,Jan 01 11:56:02  shg-borgerpc-3-1-1 sudo: "
                        "pam_unix(sudo:session): session opened for user "
                        "root by (uid=0)\n",
                    ]
                )
            ]
            assert send_security_events_mock.call_args_list == calls


class TestReadLastSecurityEventsCheckedTime:
    def test_read_last_security_events_checked_time_success(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        lastcheck = security_dir.join("lastcheck")
        # Set an example lastcheck time.
        lastcheck.write("20220101120000")

        with mock.patch(
            "os2borgerpc.client.security.security.LAST_SECURITY_EVENTS_CHECKED_TIME",
            lastcheck,
        ):
            time = security.read_last_security_events_checked_time()

        assert time == datetime(year=2022, month=1, day=1, hour=12, minute=0, second=0)

    def test_read_last_security_events_checked_time_returns_none_on_empty(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        lastcheck = security_dir.join("lastcheck")
        # Set an empty lastcheck time.
        lastcheck.write("")

        with mock.patch(
            "os2borgerpc.client.security.security.LAST_SECURITY_EVENTS_CHECKED_TIME",
            lastcheck,
        ):
            time = security.read_last_security_events_checked_time()

        assert time is None


class TestUpdateLastSecurityEventsCheckedTime:
    @freeze_time("2022-01-01 12:01:01")
    def test_update_last_security_events_checked_time_success(self, tmpdir):
        security_dir = tmpdir.mkdir("security")
        lastcheck = security_dir.join("lastcheck")
        now = datetime.now()

        with mock.patch(
            "os2borgerpc.client.security.security.LAST_SECURITY_EVENTS_CHECKED_TIME",
            lastcheck,
        ):
            security.update_last_security_events_checked_time(now)

        assert lastcheck.read() == "20220101120101"
