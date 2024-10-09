from datetime import datetime, timezone

from dateutil import parser


def parse_date_to_utc_timestamp(date_string: str) -> int:
    """Convert a date string to a UTC timestamp (integer)."""
    try:
        dt = parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError:
        return int(datetime.now(timezone.utc).timestamp())
