from datetime import datetime

from skillswap.matching import enumerate_cycles, schedule_cycle
from skillswap.models import LearningGoal


def test_three_cycle_needs_no_group_slot(profiles):
    cycles = enumerate_cycles(profiles, "maya", LearningGoal(skill_id="presentation_design"), set())
    cycle = next(c for c in cycles if c.member_ids == ["maya", "leo", "nina"])
    sessions = schedule_cycle(cycle, {p.id: p for p in profiles})
    assert [(s.teacher_id, s.learner_id, s.start_utc) for s in sessions] == [
        ("maya", "leo", "2026-10-26T18:00:00+00:00"),
        ("leo", "nina", "2026-10-26T13:00:00+00:00"),
        ("nina", "maya", "2026-10-27T14:00:00+00:00"),
    ]


def test_direct_swap_has_two_sessions(profiles):
    cycles = enumerate_cycles(profiles, "amelia", LearningGoal(skill_id="excel_automation"), set())
    c = next(c for c in cycles if c.member_ids == ["amelia", "bruno"])
    s = schedule_cycle(c, {p.id: p for p in profiles})
    assert len(s) == 2
    assert all(
        (datetime.fromisoformat(x.end_utc) - datetime.fromisoformat(x.start_utc)).total_seconds()
        == 1800
        for x in s
    )
    assert s[0].end_utc <= s[1].start_utc


def test_proficiency_and_reciprocity_required(profiles):
    assert not enumerate_cycles(
        profiles, "maya", LearningGoal(skill_id="sql", minimum_teacher_proficiency=3), set()
    )


def test_host_exclusions(profiles):
    cycles = enumerate_cycles(
        profiles, "maya", LearningGoal(skill_id="presentation_design"), {"nina", "olivia", "zara"}
    )
    assert cycles == []


def test_no_exchange_is_explicit(profiles):
    cycles = enumerate_cycles(profiles, "maya", LearningGoal(skill_id="excel_automation"), set())
    assert not any(schedule_cycle(c, {p.id: p for p in profiles}) for c in cycles)


def test_quarter_hour_grid(profiles):
    c = next(
        c
        for c in enumerate_cycles(profiles, "asha", LearningGoal(skill_id="sql"), set())
        if c.member_ids == ["asha", "samir"]
    )
    s = schedule_cycle(c, {p.id: p for p in profiles})
    assert s[0].start_utc == "2026-10-26T12:15:00+00:00"


def test_member_sessions_do_not_overlap(profiles):
    c = next(
        c
        for c in enumerate_cycles(
            profiles, "amelia", LearningGoal(skill_id="excel_automation"), set()
        )
        if len(c.member_ids) == 2
    )
    subset = {p.id: p.model_copy(deep=True) for p in profiles}
    for name in c.member_ids:
        subset[name].availability[0].end_utc = (
            subset[name].availability[0].start_utc.replace("12:00", "12:30")
        )
    assert schedule_cycle(c, subset) is None
