import pytest
from skillswap.models import LocalAvailabilityInput, Session
from skillswap.scheduling import local_session_views, normalize_window


def window(start, end, zone="America/Chicago", **kw):
    return normalize_window(
        LocalAvailabilityInput(start_local=start, end_local=end, timezone=zone, **kw)
    )


def test_gaps_and_ambiguities():
    with pytest.raises(ValueError, match="nonexistent_local_time"):
        window("2026-03-08T02:30", "2026-03-08T03:30")
    with pytest.raises(ValueError, match="ambiguous_local_time"):
        window("2026-11-01T01:30", "2026-11-01T02:30")
    assert (
        window("2026-11-01T01:30", "2026-11-01T02:30", start_fold=0).start_utc
        == "2026-11-01T06:30:00+00:00"
    )
    assert (
        window("2026-11-01T01:30", "2026-11-01T02:30", start_fold=1).start_utc
        == "2026-11-01T07:30:00+00:00"
    )


@pytest.mark.parametrize(
    "local,zone,utc",
    [
        ("2026-10-26T13:00", "America/Chicago", "2026-10-26T18:00:00+00:00"),
        ("2026-10-26T18:30", "Asia/Kolkata", "2026-10-26T13:00:00+00:00"),
        ("2026-10-26T18:00", "Asia/Kathmandu", "2026-10-26T12:15:00+00:00"),
        ("2026-10-26T09:00", "America/Chicago", "2026-10-26T14:00:00+00:00"),
        ("2026-11-02T08:00", "America/Chicago", "2026-11-02T14:00:00+00:00"),
    ],
)
def test_date_specific_offsets(local, zone, utc):
    from datetime import datetime, timedelta

    end = (datetime.fromisoformat(local) + timedelta(minutes=30)).isoformat()
    assert window(local, end, zone).start_utc == utc


@pytest.mark.parametrize("zone", ["", "Not/AZone"])
def test_missing_invalid_zone(zone):
    with pytest.raises(ValueError, match="profile_timezone_required"):
        window("2026-10-26T13:00", "2026-10-26T13:30", zone)


def test_midnight_local_views():
    s = Session(
        teacher_id="a",
        learner_id="b",
        skill_id="python",
        start_utc="2026-10-26T23:00:00+00:00",
        end_utc="2026-10-26T23:30:00+00:00",
    )
    v = local_session_views(s, {"a": "America/Chicago", "b": "Asia/Kolkata"})
    assert v[0].start_local == "2026-10-26T18:00:00-05:00"
    assert v[1].start_local == "2026-10-27T04:30:00+05:30"
