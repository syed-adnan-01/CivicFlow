from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo
from app.core.config import settings

KOLKATA_TZ = ZoneInfo(settings.DEFAULT_TIMEZONE)


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC (normalizing naive datetimes from DB drivers like SQLite)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def to_office_date(dt: datetime, tz_name: str = settings.DEFAULT_TIMEZONE) -> date:
    """Convert a UTC or timezone-aware datetime to the office local date."""
    if dt.tzinfo is None:
        raise ValueError("Cannot convert naive datetime to office date; tzinfo required")
    tz = ZoneInfo(tz_name)
    return dt.astimezone(tz).date()


def get_current_office_date(tz_name: str = settings.DEFAULT_TIMEZONE) -> date:
    """Get today's local date for the specified office timezone."""
    return to_office_date(utc_now(), tz_name)
