import pytest
from skillswap.matching import enumerate_cycles, fingerprint_plan, make_plan
from skillswap.models import ActorContext, LearningGoal


def plan_for(repo, actor, profiles):
    goal = LearningGoal(skill_id="presentation_design")
    cycle = next(
        c
        for c in enumerate_cycles(profiles, actor.member_id, goal, set())
        if c.member_ids == ["maya", "leo", "nina"]
    )
    return make_plan(
        actor, cycle, goal, {p.id: p for p in profiles}, repo.get_context(actor)["dataset_revision"]
    ).plan


def test_same_key_returns_same_proposal(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    a = repo.save_proposal(actor, p, p.fingerprint, "test:" + p.fingerprint)
    b = repo.save_proposal(actor, p, p.fingerprint, "test:" + p.fingerprint)
    assert a["id"] == b["id"]
    assert a["status"] == "awaiting_participant_confirmation"
    assert repo.get_proposal_status(actor, proposal_id=a["id"]) == a
    with repo.connection() as db:
        assert db.execute("SELECT COUNT(*) FROM proposals").fetchone()[0] == 1


def test_same_key_different_plan_rejected(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    repo.save_proposal(actor, p, p.fingerprint, "key")
    changed = p.model_copy(deep=True)
    changed.dataset_revision += 1
    changed.fingerprint = fingerprint_plan(changed)
    with pytest.raises(ValueError, match="idempotency_conflict"):
        repo.save_proposal(actor, changed, changed.fingerprint, "key")


def test_stale_revision_requires_fresh_approval(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    repo.remove_availability("nina", "2026-10-27")
    with pytest.raises(ValueError, match="stale_revision"):
        repo.save_proposal(actor, p, p.fingerprint, "key")


def test_approved_times_never_silently_change(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    p.sessions[0].start_utc = "2026-10-26T18:15:00+00:00"
    with pytest.raises(ValueError, match="approval_mismatch"):
        repo.save_proposal(actor, p, p.fingerprint, "key")


def test_host_exclusions_cannot_be_removed_by_model(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    ctx = ActorContext(member_id="maya", run_id="test", exclusions=("nina",))
    with pytest.raises(ValueError, match="invalid_cycle"):
        repo.save_proposal(ctx, p, p.fingerprint, "key")


def test_run_local_goal_survives_save_validation(repo, actor, profiles):
    # Maya's stored goal differs; run-local goal remains authoritative.
    repo.update_profile("maya", learning_goal={"skill_id": "sql", "minimum_teacher_proficiency": 2})
    p = plan_for(repo, actor, profiles)
    result = repo.save_proposal(actor, p, p.fingerprint, "key")
    assert result["plan"]["goal"]["skill_id"] == "presentation_design"


def test_timezone_change_invalidates_staged_plan(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    repo.update_profile("maya", timezone="America/New_York", availability=[])
    with pytest.raises(ValueError, match="stale_revision"):
        repo.save_proposal(actor, p, p.fingerprint, "key")


def test_saved_local_views_survive_profile_timezone_change(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    saved = repo.save_proposal(actor, p, p.fingerprint, "key")
    repo.update_profile("maya", timezone="America/New_York", availability=[])
    assert repo.get_proposal_status(actor, proposal_id=saved["id"]) == saved
    assert repo.save_proposal(actor, p, p.fingerprint, "key") == saved
    assert saved["plan"]["sessions"][0]["local_views"][0]["timezone"] == "America/Chicago"


def test_lookup_is_scoped(repo, actor, profiles):
    p = plan_for(repo, actor, profiles)
    saved = repo.save_proposal(actor, p, p.fingerprint, "key")
    assert (
        repo.get_proposal_status(ActorContext(member_id="leo", run_id="x"), proposal_id=saved["id"])
        is None
    )
