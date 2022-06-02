from unittest.mock import (
    patch,
    mock_open,
)
from freezegun import freeze_time

from os2borgerpc.client.security import (
    log_read,
)


class TestLogRead:
    @freeze_time("2022-01-01 12:00:00")
    def test_log_read(self):
        data = (
            "Jan 01 11:53:01 shg-borgerpc-3-1-1 sudo: root : TTY=pts/0"
            " ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "Jan 01 11:54:02 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session opened for user root by (uid=0)\n"
            "Jan 01 11:55:32 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session closed for user root\n"
            "Jan 01 11:56:55 shg-borgerpc-3-1-1 CRON[11314]: "
            "pam_unix(cron:session): session opened for user root by (uid=0)\n"
        )
        returned_data = [
            (
                "202201011155",
                "Jan 01 11:55:32 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session): "
                "session closed for user root",
            ),
            (
                "202201011156",
                "Jan 01 11:56:55 shg-borgerpc-3-1-1 CRON[11314]: "
                "pam_unix(cron:session): session opened for user root by (uid=0)",
            ),
        ]

        with patch(
            "os2borgerpc.client.security.log_read.open", mock_open(read_data=data)
        ):
            five_minutes_ago = 5 * 60
            logs = log_read.read(five_minutes_ago, "testfilename.txt")

        assert logs == returned_data

    @freeze_time("2022-01-01 12:00:00")
    def test_log_read_old_logs_return_empty(self):
        data = (
            "Jan 01 11:54:32 shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
            " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "Jan 01 11:54:36 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session opened for user root by (uid=0)\n"
            "Jan 01 11:54:49 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session closed for user root\n"
            "Jan 01 11:54:55 shg-borgerpc-3-1-1 CRON[11314]: "
            "pam_unix(cron:session): session opened for user root by (uid=0)\n"
        )

        with patch(
            "os2borgerpc.client.security.log_read.open", mock_open(read_data=data)
        ):
            five_minutes_ago = 5 * 60
            logs = log_read.read(five_minutes_ago, "testfilename.txt")

        assert logs == []

    @freeze_time("2022-01-01 12:00:00")
    def test_log_read_does_not_return_future_logs(self):
        data = (
            "Feb 01 11:54:32 shg-borgerpc-3-1-1 sudo: root : TTY=pts/0 ;"
            " PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls\n"
            "Feb 01 11:54:36 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session opened for user root by (uid=0)\n"
            "Feb 01 11:54:49 shg-borgerpc-3-1-1 sudo: pam_unix(sudo:session):"
            " session closed for user root\n"
            "Feb 01 11:54:55 shg-borgerpc-3-1-1 CRON[11314]:"
            " pam_unix(cron:session): session opened for user root by (uid=0)\n"
        )

        with patch(
            "os2borgerpc.client.security.log_read.open", mock_open(read_data=data)
        ):
            five_minutes_ago = 5 * 60
            logs = log_read.read(five_minutes_ago, "testfilename.txt")

        assert logs == []
