"""log_read module."""

from datetime import datetime, timedelta


def read(sec, fname):
    """Search a log from within the last "sec" seconds to now."""
    data = []
    now = datetime.now()

    with open(fname) as f:
        for line in f.readlines():
            line = str(line.replace("\0", ""))
            source_log_event_timestamp = line[:15]
            source_log_event_content = line[16:]
            source_log_event_timestamp = datetime.strptime(
                str(now.year) + " " + source_log_event_timestamp, "%Y %b  %d %H:%M:%S"
            )
            security_event_log_timestamp = datetime.strftime(source_log_event_timestamp, "%Y%m%d%H%M")
            # Detect lines from within the last x seconds to now.
            if (datetime.now() - timedelta(seconds=sec)) <= source_log_event_timestamp <= now:
                data.append((security_event_log_timestamp, source_log_event_content))

    return data
