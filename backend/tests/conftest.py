import json

import pytest
from skillswap.models import ActorContext, MemberProfile
from skillswap.repository import Repository
from skillswap.settings import ROOT


@pytest.fixture
def repo(tmp_path):
    r = Repository(tmp_path / "domain.sqlite")
    r.seed_demo(json.loads((ROOT / "data/demo_cohort.json").read_text()))
    return r


@pytest.fixture
def actor():
    return ActorContext(member_id="maya", run_id="test")


@pytest.fixture
def profiles(repo, actor):
    return [MemberProfile.model_validate(p) for p in repo.get_context(actor)["profiles"]]
