from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SkillId = Literal['python','sql','presentation_design','spanish','excel_automation']
CATALOG = {'python':'Python','sql':'SQL','presentation_design':'Presentation design','spanish':'Spanish','excel_automation':'Excel automation'}

class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')

class ActorContext(Contract):
    model_config = ConfigDict(extra='forbid', frozen=True)
    cohort_id: str = 'global-2026'
    member_id: str
    run_id: str
    exclusions: tuple[str,...] = ()

class TeachingOffer(Contract):
    skill_id: SkillId
    proficiency: int = Field(ge=1,le=3)
    description: str
    styles: list[Literal['guided_project','discussion','exercises']]

class LearningGoal(Contract):
    skill_id: SkillId
    minimum_teacher_proficiency: int = Field(default=2,ge=1,le=3)

class LocalAvailabilityInput(Contract):
    start_local: str
    end_local: str
    timezone: str
    start_fold: Literal[0,1] | None = None
    end_fold: Literal[0,1] | None = None

class AvailabilityWindow(Contract):
    start_utc: str
    end_utc: str
    source: LocalAvailabilityInput

class MemberProfile(Contract):
    id: str
    cohort_id: str = 'global-2026'
    display_name: str
    city: str | None = None
    country_code: str | None = None
    timezone: str
    offer: TeachingOffer
    learning_goal: LearningGoal
    availability: list[AvailabilityWindow] = []
    active: bool = True
    source_record_id: str

class TeachingEdge(Contract):
    teacher_id: str
    learner_id: str
    skill_id: SkillId
    evidence_ids: list[str]

class ExchangeCycle(Contract):
    member_ids: list[str]
    edges: list[TeachingEdge]

class LocalSessionView(Contract):
    member_id: str
    timezone: str
    start_local: str
    end_local: str

class Session(Contract):
    teacher_id: str
    learner_id: str
    skill_id: SkillId
    start_utc: str
    end_utc: str
    local_views: list[LocalSessionView] = []

class ExchangePlan(Contract):
    cohort_id: str
    member_id: str
    goal: LearningGoal
    cycle: ExchangeCycle
    sessions: list[Session]
    participant_timezones: dict[str,str]
    dataset_revision: int
    fingerprint: str = ''
    evidence: list[str] = []
    reviewer_summary: str = ''

class ValidationResult(Contract):
    valid: bool
    plan: ExchangePlan | None = None
    issues: list[str] = []
