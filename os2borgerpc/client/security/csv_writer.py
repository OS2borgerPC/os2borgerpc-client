"""csv_writer module."""

from datetime import datetime


def write_data(data):
    """Write security event line to security events file."""
    if not data:
        return

    line = datetime.now().strftime("%Y%m%d%H%M")

    for d in data:
        line += "," + d.replace("\n", " ").replace("\r", "").replace(",", "")

    with open("/etc/os2borgerpc/security/securityevent.csv", "at") as csvfile:
        csvfile.write(line + "\n")
