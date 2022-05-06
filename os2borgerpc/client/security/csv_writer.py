"""csv_writer module."""


def write_data(data):
    """Write security event line to security events file."""
    if not data:
        return

    line = ""
    for timestamp, event_content in data:
        line = f"{timestamp}," + event_content.replace("\n", " ").replace("\r", "").replace(",", "")

    with open("/etc/os2borgerpc/security/securityevent.csv", "at") as csvfile:
        csvfile.write(line + "\n")
