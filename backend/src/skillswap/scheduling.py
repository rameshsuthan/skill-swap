from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import AvailabilityWindow, LocalAvailabilityInput, LocalSessionView, Session


class LocalTimeResolutionError(ValueError):
    pass


def zone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise LocalTimeResolutionError("profile_timezone_required") from None


def instant(local: str, tz: ZoneInfo, fold: int | None) -> datetime:
    wall = datetime.fromisoformat(local)
    if wall.tzinfo is not None or wall.second or wall.microsecond or wall.minute % 15:
        raise LocalTimeResolutionError("invalid_local_boundary")
    candidates = {}
    for f in (0, 1):
        utc = wall.replace(tzinfo=tz, fold=f).astimezone(timezone.utc)
        if utc.astimezone(tz).replace(tzinfo=None) == wall:
            candidates[f] = utc
    if not candidates:
        raise LocalTimeResolutionError("nonexistent_local_time")
    if len(set(candidates.values())) > 1 and fold is None:
        raise LocalTimeResolutionError("ambiguous_local_time")
    if fold is not None and fold not in candidates:
        raise LocalTimeResolutionError("invalid_fold")
    return candidates[fold if fold is not None else 0]


def normalize_window(value: LocalAvailabilityInput) -> AvailabilityWindow:
    tz = zone(value.timezone)
    start = instant(value.start_local, tz, value.start_fold)
    end = instant(value.end_local, tz, value.end_fold)
    if end <= start:
        raise LocalTimeResolutionError("invalid_window_duration")
    return AvailabilityWindow(start_utc=start.isoformat(), end_utc=end.isoformat(), source=value)


def utc(value: str) -> datetime:
    d = datetime.fromisoformat(value)
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("aware_timestamp_required")
    return d.astimezone(timezone.utc)


def local_session_views(
    session: Session, participant_timezones: dict[str, str]
) -> list[LocalSessionView]:
    return [
        LocalSessionView(
            member_id=i,
            timezone=participant_timezones[i],
            start_local=utc(session.start_utc)
            .astimezone(zone(participant_timezones[i]))
            .isoformat(),
            end_local=utc(session.end_utc).astimezone(zone(participant_timezones[i])).isoformat(),
        )
        for i in (session.teacher_id, session.learner_id)
    ]
