from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.models.user import User


def user_timezone(user: User) -> ZoneInfo:
    try:
        return ZoneInfo(user.timezone or "UTC")
    except Exception:
        return ZoneInfo("UTC")


def user_local_now(user: User) -> datetime:
    return datetime.now(UTC).astimezone(user_timezone(user))


def user_digest_times(user: User) -> list[tuple[int, int]]:
    morning = (user.digest_hour, user.digest_minute)
    evening = (user.digest_evening_hour, user.digest_evening_minute)
    if morning == evening:
        return [morning]
    return [morning, evening]


def is_user_digest_minute(user: User, now_utc: datetime | None = None) -> bool:
    now_utc = now_utc or datetime.now(UTC)
    local = now_utc.astimezone(user_timezone(user)).replace(second=0, microsecond=0)
    slot = (local.hour, local.minute)
    return slot in user_digest_times(user)
