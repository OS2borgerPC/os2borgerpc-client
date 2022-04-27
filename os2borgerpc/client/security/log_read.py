"""log_read module."""

from datetime import datetime, timedelta


def read(sec, fname):
    """Search a log from within the last "sec" seconds to now."""
    data = ""
    now = datetime.now()

    with open(fname) as f:
        for line in reversed(f.readlines()):
            line = str(line.replace("\0", ""))
            line_date_portion = line[:15]
            log_entry_date = datetime.strptime(
                str(now.year) + " " + line_date_portion, "%Y %b  %d %H:%M:%S"
            )
            # Detect lines from within the last x seconds to now.
            if (datetime.now() - timedelta(seconds=sec)) <= log_entry_date <= now:
                data = line + data

    return data
