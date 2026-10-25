import hashlib
import itertools
import json
import math
from datetime import datetime,timedelta,timezone
from .models import ExchangeCycle,ExchangePlan,LearningGoal,MemberProfile,Session,TeachingEdge,ValidationResult
from .scheduling import local_session_views,utc

DURATION=timedelta(minutes=30)

def enumerate_cycles(profiles: list[MemberProfile],actor_id: str,goal: LearningGoal,excluded: set[str]) -> list[ExchangeCycle]:
    members={p.id:p for p in profiles if p.active and p.id not in excluded}
    if actor_id not in members:
        return []
    actor=members[actor_id]
    members={k:p for k,p in members.items() if p.cohort_id==actor.cohort_id}
    def edge(t,l):
        need=goal if l==actor_id else members[l].learning_goal
        offer=members[t].offer
        if offer.skill_id==need.skill_id and offer.proficiency>=need.minimum_teacher_proficiency:
            return TeachingEdge(teacher_id=t,learner_id=l,skill_id=offer.skill_id,evidence_ids=[members[t].source_record_id,members[l].source_record_id])
    result=[]
    others=sorted(set(members)-{actor_id})
    for size in (1,2):
        for tail in itertools.permutations(others,size):
            ids=[actor_id,*tail]
            edges=[edge(t,l) for t,l in zip(ids,ids[1:]+ids[:1])]
            if all(edges):
                result.append(ExchangeCycle(member_ids=ids,edges=edges))
    return result

def schedule_cycle(cycle: ExchangeCycle,profiles: dict[str,MemberProfile]) -> list[Session] | None:
    options=[]
    for edge in cycle.edges:
        starts=set()
        for a in profiles[edge.teacher_id].availability:
            for b in profiles[edge.learner_id].availability:
                start=max(utc(a.start_utc),utc(b.start_utc))
                end=min(utc(a.end_utc),utc(b.end_utc))
                t=datetime.fromtimestamp(math.ceil(start.timestamp()/900)*900,timezone.utc)
                while t+DURATION<=end:
                    starts.add(t)
                    t+=timedelta(minutes=15)
        options.append(sorted(starts))
    chosen=[]
    def assign(index):
        if index==len(cycle.edges):
            return list(chosen)
        edge=cycle.edges[index]
        people={edge.teacher_id,edge.learner_id}
        for start in options[index]:
            end=start+DURATION
            if any(people & {s.teacher_id,s.learner_id} and start<utc(s.end_utc) and utc(s.start_utc)<end for s in chosen):
                continue
            session=Session(teacher_id=edge.teacher_id,learner_id=edge.learner_id,skill_id=edge.skill_id,start_utc=start.isoformat(),end_utc=end.isoformat())
            session.local_views=local_session_views(session,{i:profiles[i].timezone for i in people})
            chosen.append(session)
            result=assign(index+1)
            if result is not None:
                return result
            chosen.pop()
        return None
    return assign(0)

def fingerprint_plan(plan: ExchangePlan) -> str:
    data=plan.model_dump(mode='json',exclude={'fingerprint','evidence','reviewer_summary'})
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def validate_plan(plan: ExchangePlan,profiles: dict[str,MemberProfile],revision: int,excluded: set[str] | None=None) -> ValidationResult:
    issues=[]
    if revision!=plan.dataset_revision:
        issues.append('stale_revision')
    possible=enumerate_cycles(list(profiles.values()),plan.member_id,plan.goal,excluded or set())
    if plan.cycle not in possible:
        issues.append('invalid_cycle')
    ids=plan.cycle.member_ids
    if any(i not in profiles or profiles[i].cohort_id!=plan.cohort_id for i in ids):
        return ValidationResult(valid=False,issues=[*issues,'scope_mismatch'])
    zones={i:profiles[i].timezone for i in ids}
    if plan.participant_timezones!=zones:
        issues.append('timezone_changed')
    if len(plan.sessions)!=len(plan.cycle.edges):
        issues.append('session_count')
    seen=set()
    for s in plan.sessions:
        identity=(s.teacher_id,s.learner_id,s.skill_id)
        if identity in seen or identity not in {(e.teacher_id,e.learner_id,e.skill_id) for e in plan.cycle.edges}:
            issues.append('invalid_session_edge')
            continue
        seen.add(identity)
        try:
            start,end=utc(s.start_utc),utc(s.end_utc)
            if end-start!=DURATION or start.timestamp()%900:
                issues.append('invalid_session_duration_or_grid')
            for i in (s.teacher_id,s.learner_id):
                if i not in profiles or not any(utc(w.start_utc)<=start and end<=utc(w.end_utc) for w in profiles[i].availability):
                    issues.append('outside_availability')
            if s.local_views!=local_session_views(s,zones):
                issues.append('invalid_local_views')
        except (ValueError,KeyError):
            issues.append('invalid_timestamp_or_scope')
    for a,b in itertools.combinations(plan.sessions,2):
        try:
            if {a.teacher_id,a.learner_id}&{b.teacher_id,b.learner_id} and utc(a.start_utc)<utc(b.end_utc) and utc(b.start_utc)<utc(a.end_utc):
                issues.append('participant_overlap')
        except ValueError:
            issues.append('invalid_timestamp_or_scope')
    if plan.fingerprint and fingerprint_plan(plan)!=plan.fingerprint:
        issues.append('fingerprint_mismatch')
    return ValidationResult(valid=not issues,plan=plan if not issues else None,issues=sorted(set(issues)))

def make_plan(ctx,cycle,goal,profiles,revision,sessions=None):
    sessions=sessions if sessions is not None else schedule_cycle(cycle,profiles)
    if sessions is None:
        return ValidationResult(valid=False,issues=['no_shared_availability'])
    if any(i not in profiles for i in cycle.member_ids):
        return ValidationResult(valid=False,issues=['invalid_cycle'])
    plan=ExchangePlan(cohort_id=ctx.cohort_id,member_id=ctx.member_id,goal=goal,cycle=cycle,sessions=sessions,participant_timezones={i:profiles[i].timezone for i in cycle.member_ids},dataset_revision=revision,evidence=[f'{e.teacher_id} offers {e.skill_id} to {e.learner_id}; sources: {", ".join(e.evidence_ids)}' for e in cycle.edges])
    plan.fingerprint=fingerprint_plan(plan)
    return validate_plan(plan,profiles,revision,set(ctx.exclusions))
