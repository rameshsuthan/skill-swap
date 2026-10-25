import json
import pytest
from skillswap.settings import Settings
from skillswap.models import ActorContext
from skillswap.mcp_router import MCPRouter
from skillswap.events import EventStore

@pytest.mark.asyncio
async def test_stdio_context_roundtrip(tmp_path):
    router = MCPRouter(Settings(domain_db=tmp_path/'domain.sqlite', checkpoint_db=tmp_path/'check.sqlite'))
    async with router:
        assert set(router.schemas) == {'get_learning_context','search_teachers','find_exchange_cycles','validate_and_schedule','save_proposal','get_proposal_status'}
        result = await router.call('skillswap','get_learning_context',{},ActorContext(member_id='maya',run_id='test'))
        assert len(result['profiles']) == 15
        assert result['member']['timezone'] == 'America/Chicago'
        assert result['member']['display_name'] == 'Maya'
        assert router.process_transport is not None

@pytest.mark.asyncio
async def test_scope_override_rejected(tmp_path):
    router=MCPRouter(Settings(domain_db=tmp_path/'domain.sqlite',checkpoint_db=tmp_path/'check.sqlite'))
    async with router:
        for field in ('ctx','member_id','cohort_id','run_id','exclusions'):
            with pytest.raises(ValueError,match='scope_override'):
                await router.call('skillswap','get_learning_context',{field:'other'},ActorContext(member_id='maya',run_id='test'))


def test_no_secret_in_events(tmp_path):
    events=EventStore(tmp_path/'events.sqlite')
    events.append('run',agent='interpreter',server='skillswap',tool='context',status='ok',duration_ms=1,summary={'api_key':'secret','profiles':[{'private':'hidden'}], 'count':15})
    data=json.dumps(events.list_after('run',0))
    assert 'secret' not in data and 'hidden' not in data
    assert events.list_after('run',0)[0]['sequence']==1
    assert events.list_after('run',1)==[]
