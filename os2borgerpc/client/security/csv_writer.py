"""csv_writer module."""


def write_data(security_events):
    """Write security event line to security events file."""
    with open("/etc/os2borgerpc/security/securityevent.csv", "at") as csvfile:
        for timestamp, event in security_events:
            event_line = event.replace("\n", " ").replace("\r", "").replace(",", "")
            csvfile.write(f"{timestamp},{event_line}\n")
