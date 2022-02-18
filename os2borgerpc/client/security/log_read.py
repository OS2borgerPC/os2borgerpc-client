from datetime import date, datetime, timedelta
import calendar

# Search syslog from the end to a certain time
# Syslog is by Ubuntu default rotated daily


def read(sec, fname):
    data = ""
    today = date.today()
    today_year = today.year
    today_month_num = today.month

    with open(fname) as f:
        for line in reversed(f.readlines()):
            line = str(line.replace("\0", ""))
            date_object = datetime.strptime(
                str(today_year) + " " + line[:15], "%Y %b  %d %H:%M:%S"
            )
            # Since auth.log contains no year, the current year is assumed
            # That leaves a problem: Log entries from e.g. December will in January seem
            # like they're in the future, as thus give a security alert.
            # Therefore we only include logentries from the month numbers equal to or
            # lower than the current
            log_entry_month_name = line[:3]
            log_entry_month_num = list(calendar.month_abbr).index(log_entry_month_name)
            # Detect lines from within the last x seconds
            if (
                today_month_num >= log_entry_month_num
                and (datetime.now() - timedelta(seconds=sec)) <= date_object
            ):
                data = line + data

    return data
