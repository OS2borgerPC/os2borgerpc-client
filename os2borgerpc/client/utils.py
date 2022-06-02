#!/usr/bin/env python3
"""This file contains utilities for communicating with the OS2borgerPC admin site."""

import os
import sys
import fcntl
import urllib
import contextlib
import time
import signal
import errno

from .config import OS2borgerPCConfig


@contextlib.contextmanager
def filelock(file_name, max_age=None):
    """
    File lock context manager.

    Acquires the named lock for the lifetime of the context. If the named
    lock was acquired with this function by another process more than max_age
    seconds ago, then that process will be forcibly terminated.
    """
    pid_file = file_name + ".pid"
    with open(file_name, "w") as fd:
        try:
            # Try to take the lock in the usual way
            fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as lock_ex:
            # If this lock has a maximum age, then check if it's been exceeded.
            # If it has, then forcibly terminate the locking process and take
            # the lock
            if lock_ex.errno == errno.EAGAIN and max_age is not None:
                lock_age = time.time() - os.stat(pid_file).st_mtime
                if lock_age >= max_age:
                    try:
                        msg = (
                            "warning: " + f'forcibly acquiring lock file "{file_name}"'
                        )
                        print(msg, file=sys.stderr)
                        with open(pid_file, "rt") as fp:
                            pid = int(fp.read().strip())
                        os.kill(pid, signal.SIGKILL)
                        fcntl.lockf(fd, fcntl.LOCK_EX)
                    except ValueError:
                        raise lock_ex
                else:
                    raise lock_ex
            else:
                raise lock_ex

        # XXX RACE BEGINS: we have the lock but haven't written our PID to the
        # corresponding pidfile yet
        with open(pid_file, "wt") as fp:
            fp.write(str(os.getpid()))
        # XXX RACE ENDS: other processes started after this point will behave
        # as expected

        try:
            yield
        finally:
            os.unlink(pid_file)
            fcntl.lockf(fd, fcntl.LOCK_UN)
            os.unlink(file_name)


def get_url_and_uid():
    """Get the Admin site RPC URL and BorgerPC UID as tuple."""
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
