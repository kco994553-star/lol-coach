import copy


def observation(oid='o1',field='position',value='lane',**changes):
    x=dict(observation_id=oid,session_id='synthetic-1',entity_id='self',field_key=field,value=value,kind='OBSERVED',event_time_ms=1000,received_at='2026-10-04T09:00:00+00:00',game_clock_basis='fixture-clock',source_id='synthetic-frame',source_version='1',source_location='fixture://synthetic/frame-1',source_hash='a'*64,lineage_ids=[],independent_group_id='frame-1',perspective='PLAYER',visibility_at_event='KNOWN',patch='SYNTHETIC-1',quality_state=dict(accuracy='VERIFIED',completeness='VERIFIED',freshness='VERIFIED'),validity='AT_EVENT')
    x.update(changes);return x


def request(**changes):
    x=dict(session_id='synthetic-1',patch='SYNTHETIC-1',as_of_event_time_ms=1000,knowledge_cutoff='2026-10-04T10:00:00+00:00',game_clock_basis='fixture-clock',view='PLAYER_REVIEW',required_keys=['self:position'],revision_parent=None)
    x.update(changes);return x


def action(aid,typ):
    return dict(action_id=aid,action_type=typ,feasibility='POSSIBLE',feasibility_refs=['o1'],required_keys=['self:position'],target='synthetic target',path='fixture path',entry_condition='verified in synthetic scene',resource_budget='preserve escape resource',exit_condition='return to initial position',abort_conditions=['enemy_arrives'],postcondition='retain return route',deadline_event='wave_arrives')


def fixture():
    from coach_v1.models import DIMENSIONS
    return dict(schema_version='r3.v1',evidence_kind='SYNTHETIC',mode='TEST',objective='합성 사례: 경험치와 다음 선택권 보존',scope_reason='Two fixture branches only: no reinforcement / reinforcement. Not a real match prediction.',snapshot_request=request(),observations=[observation()],scenarios=[dict(scenario_id='s1',description='합성 조건 A',support_refs=['o1'],conditions=['아군 지원 가능이라고 가정']),dict(scenario_id='s2',description='합성 조건 B',support_refs=['o1'],conditions=['아군 지원 불가라고 가정'])],actions=[action('wait','WAIT'),action('retreat','DISENGAGE')],assessments=[dict(action_id=a,scenario_id=s,assessment='CONTESTED',rationale='수동으로 정의한 합성 기대값; 게임 규칙 추론 아님',evidence_refs=['o1'],knowledge_status='REVIEWED',patch='SYNTHETIC-1',knowledge_ref='fixture://annotation/v1') for a in ('wait','retreat') for s in ('s1','s2')],comparisons=[dict(left_action_id='wait',right_action_id='retreat',scenario_id=s,dimensions=[dict(dimension=d,relation='SAME',rationale='합성 사례에서 동등하다고 제공한 관계',evidence_refs=['o1']) for d in DIMENSIONS]) for s in ('s1','s2')],information_requests=[],occurred_events=[],intended_plan=None,outcome_note=None)
