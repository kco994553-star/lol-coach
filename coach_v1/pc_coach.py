"""Evidence-labelled PC presentation over frozen plans and separate AI advice."""
from collections import Counter
from pathlib import Path
from .auto_review import AutoReviewStore, assess, load_bundle, machine_check
from .pregame_contract import parse_input, POSITIONS
from .pregame_evaluator import _Facts
from .storage import ServiceError

LABELS={'OFFICIAL':'공식 사실','STATISTICS':'통계','USER':'사용자 승인','AUTO_VERIFIED':'자동 검토됨','HYPOTHESIS':'미검토 가설(AI 작성, 근거 링크)','UNKNOWN':'미확인'}
SECTION_NAMES={'PROFILE':'챔피언 설명','MAP':'라인별 정보','JUNGLE':'정글 연계','COMPOSITION':'전체 조합','ROLE':'내 역할','LANE':'라인전 준비','FIGHT':'싸움 준비','CHANGES':'계획 변경','OPERATIONS':'팀 운영','MOVEMENT':'이동 계획'}


def review_store(server):
    return AutoReviewStore(server.pregame.dbpath+'.auto.sqlite')


def _card(cid,title,level,lines,details,sources,**extra):
    return dict(id=cid,title=title,evidence_level=level,evidence_label=LABELS[level],lines=lines[:3],details=details,sources=sources,patch_status='MATCHING_ARCHIVE',**extra)


def preview(server,body):
    if not isinstance(body,dict) or not {'input'}<=body.keys() or set(body)-{'input','draft_revision'}:raise ServiceError(422,'INVALID_PC_PREVIEW')
    revision=body.get('draft_revision')
    if revision is not None and (type(revision) is not int or revision<0):raise ServiceError(422,'INVALID_DRAFT_REVISION')
    draft=parse_input(body['input']).model_dump(mode='json')
    services=getattr(server,'pc_services',None)
    if services:
        live=services.snapshot()
        # A stale browser cannot use a manual PRE_GAME flag to bypass an actual
        # observed start. Failed connections permit newly confirmed manual input.
        if live.get('phase') not in (None,'ChampSelect'):
            draft['phase']='UNKNOWN'
        automatic=any(s['champion_source']['kind']=='AUTOMATIC' for s in draft['slots'])
        if automatic:
            current=live.get('input')
            if current is None:draft['phase']='UNKNOWN'
            elif any(draft.get(k)!=current.get(k) for k in ('my_champion','my_position','slots')):raise ServiceError(409,'AUTOMATIC_DRAFT_CHANGED')
    cards=[];champion=draft['my_champion'];position=draft['my_position'];slots=draft['slots']
    enemy={s['position']:s['champion'] for s in slots if s['side']=='ENEMY' and s['position']}
    stage='EMPTY' if not champion else 'COMPOSITION' if all(s['champion'] for s in slots) else 'JUNGLE' if enemy.get('JUNGLE') else 'LANER' if position and enemy.get(position) else 'OWN'
    names=list(dict.fromkeys([c for c in [champion,enemy.get(position),enemy.get('JUNGLE'),*[s['champion'] for s in slots]] if c]))
    from .official_catalog import facts_response
    official=facts_response(names,patch=draft['patch'])
    for row in official['champions']:
        facts=row['facts']
        cards.append(_card('official-'+row['champion'],row['name']+' 기술 설명','OFFICIAL',
            [f['name']+': '+f['text'] for f in facts[:3]],'\n'.join(f['name']+': '+f['text'] for f in facts),[f['source'] for f in facts],section='PROFILE',champion=row['champion']))
        cards[-1]['patch_status']=row['patch_status']
    packet,_=load_bundle();result=assess();states={r['id']:r for r in result['rows']};withdrawn=review_store(server).withdrawn()
    if draft['phase']=='PRE_GAME' and draft['patch']:
        facts=_Facts(draft,{})
        from .pregame_server import current_knowledge
        from .pregame_contract import binding_matches
        knowledge=current_knowledge(server.research)
        rejected={item['spec']['rule_id'] for item in knowledge if item.get('spec') and item['proposal']['review_state']=='REJECTED'}
        for row in packet['rows']:
            spec=row['spec'];rid=row['id']
            if rid in withdrawn or rid in rejected or draft['patch'] not in spec['patches'] or spec['scope']=='POSITION' and position not in spec['positions']:continue
            if any(facts.predicate(p)!='TRUE' for p in spec['conditions']):continue
            if any(facts.predicate(p)!='FALSE' for p in spec['counterconditions']+spec['stop_conditions']):continue
            if machine_check(row):continue
            state=states[rid];level='AUTO_VERIFIED' if state['state']=='AUTO_VERIFIED' else 'HYPOTHESIS'
            # USER overrides belong to the exact original source/spec binding;
            # revised AI lineage never borrows its approval.
            sources=spec['sources'];advice=row['advice']
            detail='\n'.join(k+': '+v for k,v in advice.items())+'\n조건은 경기 전 계획입니다. 기술 상태를 자동으로 확인하지 않습니다.'
            if state['reasons']:detail+='\n검토 보류: '+' / '.join(_reason(r) for r in state['reasons'])
            cards.append(_card('advice-'+rid,SECTION_NAMES.get(spec['section'],'경기 전 준비')+' · '+rid,level,
                [advice['상황'],advice['할 것'],advice['무효 조건']],detail,sources,candidate_id=rid,candidate_sha256=row['candidate_sha256'],section=spec['section']))
        # Source-bound USER cards continue to use the original frozen evaluator.
        from .pregame_v3 import evaluate_gameplan_v3
        plan=evaluate_gameplan_v3(draft,knowledge,server.movement_statistics,server.test_mode)
        for trace in plan['evaluations']:
            if trace.get('status')!='APPLIED' or not trace.get('spec'):continue
            spec=trace['spec'];rid=spec['rule_id']
            if rid in withdrawn:continue
            cards.append(_card('user-'+rid,SECTION_NAMES.get(spec['output']['section'],'사용자 조언'),'USER',spec['output']['text'].splitlines()[:3],spec['output']['text'],spec['sources'],section=spec['output']['section']))
        _statistics_cards(server,draft,cards)
        from .recall_pc import cards_for_draft
        cards.extend(cards_for_draft(server,draft))
        from .recall_candidates import cards_for_draft as candidate_cards
        cards.extend(candidate_cards(server,draft))
    if not cards:cards.append(_card('unknown','경기 전 준비','UNKNOWN',['내 챔피언부터 입력하세요.'],'근거가 없는 항목은 미확인으로 남습니다.',[],section='PROFILE'))
    rank={'USER':0,'AUTO_VERIFIED':1,'HYPOTHESIS':2,'STATISTICS':3,'OFFICIAL':4,'UNKNOWN':5}
    cards.sort(key=lambda c:(rank[c['evidence_level']],c.get('champion')!=champion))
    return dict(schema_version='pc-coach.v1',phase=draft['phase'],stage=stage,patch=draft['patch'],cards=cards,counts=dict(Counter(c['evidence_level'] for c in cards)),review_summary={k:result[k] for k in ('passed','held','reasons')},draft_revision=revision)


def _reason(reason):
    if re_korean(reason):return reason
    return {'EVIDENCE_REVIEW_MISSING_OR_INVALID':'근거 담당의 검사가 없거나 자료 버전이 다릅니다.','COUNTER_REVIEW_MISSING_OR_INVALID':'반론 담당의 검사가 없거나 자료 버전이 다릅니다.','SURVIVING_COUNTEREXAMPLE':'해결하지 못한 반례가 있습니다.'}.get(reason,'출처·검토 자료의 일치 확인이 필요합니다.')


def re_korean(value):return any('\uac00'<=c<='\ud7a3' for c in value)


def _statistics_cards(server,draft,cards):
    if not draft['my_champion'] or not draft['my_position']:return
    from .pregame_server import power_response
    response=power_response(server,dict(champion=draft['my_champion'],position=draft['my_position'],patch=draft['patch'],tier='CHALLENGER',opponent_champion=None))
    view=response['view']
    if view['status']!='KNOWN':return
    points=view.get('points',[])
    if not points:return
    # No win-rate or tactical claim inferred from descriptive gold/xp/cs.
    names={'gold_delta':'골드','xp_delta':'경험치','cs_delta':'미니언 처치'}
    lines=['챌린저 목록에서 모은 경기의 관측 자료입니다.','교전 승패나 이 조언의 효과를 검증한 수치가 아닙니다.']
    detail=['같은 포지션 표본과 비교한 분당 자원 성장 차이입니다. 현재 모집 목록의 등급이며 경기 당시 참가자 전원의 등급을 확인한 자료는 아닙니다.']
    for point in points:
        if not point.get('visible'):continue
        ci=point.get('ci95',{})
        detail.append(f"{point['minute']}분 · {names[point['metric']]} 평균 차이 {point['mean']:.2f} · 95% 구간 {ci['low']:.2f}~{ci['high']:.2f} · 챔피언 표본 {point['champion_n']}, 비교 표본 {point['reference_n']}")
    source=dict(url='https://developer.riotgames.com/apis#match-v5',title='Riot 경기 자료 · 익명 집계',patch=draft['patch'],sha256=view['dataset_digest'],locator=draft['my_champion']+' / '+draft['my_position'])
    cards.append(_card('statistics-own','관측된 자원 변화','STATISTICS',lines,'\n'.join(detail),[source],section='PROFILE'))


def objection(server,body):
    if not isinstance(body,dict) or set(body)!={'candidate_id','candidate_sha256','reason'}:raise ServiceError(422,'INVALID_OBJECTION')
    row=next((r for r in load_bundle()[0]['rows'] if r['id']==body['candidate_id'] and r['candidate_sha256']==body['candidate_sha256']),None)
    if row is None:raise ServiceError(409,'OBJECTION_VERSION_CHANGED')
    try:record=review_store(server).object(**body)
    except (TypeError,ValueError):raise ServiceError(422,'INVALID_OBJECTION') from None
    return dict(withdrawn=True,record=record,user_approval_created=False)
