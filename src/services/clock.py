from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


def local_now(tz_name: str, now_utc: datetime | None = None) -> datetime:
    now_utc = now_utc or datetime.now(timezone.utc)
    return now_utc.astimezone(ZoneInfo(tz_name))


def local_today(tz_name: str) -> date:
    return local_now(tz_name).date()
