from fastmcp import FastMCP
from .models import ActorContext, ExchangeCycle, LearningGoal, ExchangePlan, Session, MemberProfile
from .repository import Repository
from .settings import Settings
from .matching import enumerate_cycles, make_plan

def create_mcp_server(repository: Repository):
    server=FastMCP('SkillSwap')
    def context(ctx):
        raw=repository.get_context(ctx)
        return {p['id']:MemberProfile.model_validate(p) for p in raw['profiles']},raw['dataset_revision']
    @server.tool
    def get_learning_context(ctx: ActorContext) -> dict:
        """Read authoritative fictional cohort profiles and canonical skill catalog."""
        return repository.get_context(ctx)
    @server.tool
    def search_teachers(ctx: ActorContext,goal: LearningGoal,excluded_member_ids: list[str]=[]) -> dict:
        """Find teachers with the declared skill and minimum proficiency."""
        profiles,_=context(ctx)
        excluded=set(ctx.exclusions)|set(excluded_member_ids)|{ctx.member_id}
        return {'teachers':[p.model_dump(mode='json') for p in profiles.values() if p.id not in excluded and p.offer.skill_id==goal.skill_id and p.offer.proficiency>=goal.minimum_teacher_proficiency]}
    @server.tool
    def find_exchange_cycles(ctx: ActorContext,goal: LearningGoal,excluded_member_ids: list[str]=[],preferred_member_ids: list[str]=[],limit: int=5) -> dict:
        """Find reciprocal two or three member exchanges and feasible pairwise schedules."""
        profiles,revision=context(ctx)
        cycles=enumerate_cycles(list(profiles.values()),ctx.member_id,goal,set(ctx.exclusions)|set(excluded_member_ids))
        cycles.sort(key=lambda c:(min((preferred_member_ids.index(i) for i in c.member_ids if i in preferred_member_ids),default=len(preferred_member_ids)),len(c.member_ids),c.member_ids))
        plans=[]
        for cycle in cycles:
            result=make_plan(ctx,cycle,goal,profiles,revision)
            if result.valid:
                plans.append(result.plan.model_dump(mode='json'))
        return dict(plans=plans[:max(1,min(limit,5))],diagnostics={'eligible_cycles':len(cycles),'feasible_cycles':len(plans)},issues=[] if plans else ['no_shared_availability' if cycles else 'no_reciprocal_cycle'])
    @server.tool
    def validate_and_schedule(ctx: ActorContext,cycle: ExchangeCycle,goal: LearningGoal,proposed_sessions: list[Session] | None=None) -> dict:
        """Independently validate reciprocity and exact sessions, or compute a feasible schedule."""
        profiles,revision=context(ctx)
        valid_cycles=enumerate_cycles(list(profiles.values()),ctx.member_id,goal,set(ctx.exclusions))
        if cycle not in valid_cycles:
            return {'valid':False,'plan':None,'issues':['invalid_cycle']}
        return make_plan(ctx,cycle,goal,profiles,revision,proposed_sessions).model_dump(mode='json')
    @server.tool
    def save_proposal(ctx: ActorContext,plan: ExchangePlan,approval_fingerprint: str,idempotency_key: str) -> dict:
        """HOST ONLY: atomically save the exact approved proposal; does not book sessions."""
        try:
            return {'proposal':repository.save_proposal(ctx,plan,approval_fingerprint,idempotency_key)}
        except ValueError as exc:
            return {'proposal':None,'issues':str(exc).split(',')}
    @server.tool
    def get_proposal_status(ctx: ActorContext,idempotency_key: str | None=None,proposal_id: str | None=None) -> dict:
        """HOST ONLY: recover an existing proposal after a retry or restart."""
        proposal=repository.get_proposal_status(ctx,idempotency_key=idempotency_key,proposal_id=proposal_id)
        return {'proposal':proposal,'status':'found' if proposal else 'not_found'}
    return server

if __name__=='__main__':
    repo=Repository(Settings().domain_db)
    repo.ensure_seeded()
    create_mcp_server(repo).run(transport='stdio',show_banner=False)
