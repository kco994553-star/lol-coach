"""Read-only, explicit manual assertions about an opponent's declared right.

Existing rule prose and resource curves do not encode tactical right/safety
semantics. Without a manually supplied assertion bound to an active reviewed
claim, this adapter deliberately returns UNKNOWN. It never writes decisions.
"""
from copy import deepcopy
import json
import re

from .pregame_contract import binding_matches, parse_input, parse_rule
from .pregame_evaluator import _current_flags, knowledge_fingerprint
from .power_stats import validate_power_dataset
from .state import digest

CARD_TITLES = {'MAP':'맵', 'JUNGLE':'정글', 'COMPOSITION':'조합', 'ROLE':'내 역할',
               'LANE':'라인/동선', 'FIGHT':'교전/생존', 'CHANGES':'변경/미확인',
               'OPERATIONS':'운영 중심·팀 의존도', 'MOVEMENT':'단계별 기본 움직임'}
LABELS = {'RISK_IF_OPPONENT_USES_RIGHT':'상대가 권리를 쓰면 위험',
          'SAFE_IF_OPPONENT_USES_RIGHT':'상대가 권리를 써도 안전', 'UNKNOWN':'미확인'}
ASSERTION_KIND = 'MANUAL_REVIEWED_RIGHT_ASSERTION'
LIMITATIONS = ['EXPLICIT_MANUAL_REVIEWED_ASSERTION_ONLY', 'STATISTICS_DESCRIPTIVE_NON_CAUSAL',
               'REFERENCE_PRIORITY_NOT_TACTICAL_PROOF', 'OPPONENT_ACTION_EXECUTION_UNKNOWN',
               'NO_LIVE_WAVE_VISION_OR_COOLDOWN_INFERENCE', 'NO_AUTOMATIC_KNOWLEDGE_APPROVAL']


def _require(ok):
    if not ok: raise ValueError('INVALID_OPPONENT_RIGHT_ANNOTATION')


def _hash(value, size=64):
    return isinstance(value,str) and re.fullmatch('[a-f0-9]{'+str(size)+'}', value) is not None


def validate_right_annotations(value):
    """Validate a user-maintained sidecar; its flags never grant approval."""
    _require(isinstance(value,list) and len(value)<=1000)
    try: _require(len(json.dumps(value,ensure_ascii=False,allow_nan=False).encode())<=1_000_000)
    except (TypeError,OverflowError): raise ValueError('INVALID_OPPONENT_RIGHT_ANNOTATION') from None
    for a in value:
        _require(isinstance(a,dict) and set(a)=={'card_key','rule_id','selected_version','spec_sha256','source_ref','assertion','statistics'})
        _require(a['card_key'] in CARD_TITLES and _hash(a['rule_id'],32) and _hash(a['selected_version'],32) and _hash(a['spec_sha256']))
        s=a['source_ref'];_require(isinstance(s,dict) and set(s)=={'resource_id','anchor','note_revision','kind','report_sha256','note_sha256'})
        _require(all(_hash(s[k]) for k in ('resource_id','report_sha256','note_sha256')) and type(s['note_revision']) is int and s['note_revision']>=1)
        _require(s['kind'] in ('RAW_DIAGNOSTIC','VIDEO'))
        _require(isinstance(s['anchor'],str) and re.fullmatch(r'overview|[0-9]+',s['anchor']) is not None)
        assertion=a['assertion'];_require(isinstance(assertion,dict) and set(assertion)=={'kind','right','claim','classification'})
        _require(assertion['kind']==ASSERTION_KIND and assertion['classification'] in set(LABELS)-{'UNKNOWN'})
        _require(all(isinstance(assertion[k],str) and 1<=len(assertion[k])<=2000 and assertion[k].strip() for k in ('right','claim')))
        refs=a['statistics'];_require(isinstance(refs,list) and 1<=len(refs)<=20)
        for r in refs:
            _require(isinstance(r,dict) and set(r)=={'dataset_sha256','cohort_sha256','minute'})
            _require(_hash(r['dataset_sha256']) and _hash(r['cohort_sha256']) and type(r['minute']) is int and 0<=r['minute']<=240)
    return deepcopy(value)


def _cards(plan):
    common=plan.get('common',{});personal=plan.get('personal',{})
    common=common if isinstance(common,dict) else {};personal=personal if isinstance(personal,dict) else {}
    rows=common.get('map',[])
    yield 'MAP', rows if isinstance(rows,list) and len(rows)==5 else []
    for key in ('JUNGLE','COMPOSITION'): yield key, [common.get(key.lower())]
    for key in ('ROLE','LANE','FIGHT'): yield key, [personal.get(key.lower())]
    for key in ('CHANGES','OPERATIONS','MOVEMENT'): yield key, [plan.get(key.lower())]


def _datasets(values,test_mode):
    values=list(values.values()) if isinstance(values,dict) else list(values or [])
    result=[]
    for data in values:
        if not isinstance(data,dict): continue
        if data.get('schema_version')=='pregame.power-data.v1':
            d=validate_power_dataset(data);kind=d['source']['sample_kind']
            if d['status']=='BLOCKED_EXTERNAL': continue
            group='LEAGUE_SEED_COHORT';tier=d['source']['tier']
            if tier not in ('CHALLENGER','GRANDMASTER'): continue
        elif data.get('schema_version')=='postgame.pro-reference.v1':
            from .pro_reference import validate_pro_reference
            d=validate_pro_reference(data);kind=d['sample_kind'];group='PRO_ROSTER';tier='UNKNOWN'
        else: continue
        if kind=='SYNTHETIC' and not test_mode: continue
        result.append(dict(data=d,sha256=digest(d),group=group,tier=tier))
    return result


def _statistic(ref,datasets,draft):
    """Exact compatible visible point; it supports context, not causality."""
    for row in datasets:
        if row['sha256']!=ref['dataset_sha256']: continue
        for c in row['data']['cohorts']:
            if digest(c)!=ref['cohort_sha256'] or (c['champion'],c['position'],c['patch'])!=(draft['my_champion'],draft['my_position'],draft['patch']): continue
            if c['comparison']=='MATCHUP':
                opponents=[s['champion'] for s in draft['slots'] if s['side']=='ENEMY' and s['position']==draft['my_position']]
                if opponents!=[c['opponent_champion']]: continue
            p=next((p for p in c['points'] if p['minute']==ref['minute'] and p['visible']),None)
            if p is None: continue
            # Grandmaster is an auxiliary for the exact missing Challenger point.
            if row['group']=='LEAGUE_SEED_COHORT' and row['tier']=='GRANDMASTER':
                identity=tuple(c[k] for k in ('champion','position','patch','comparison','metric','opponent_champion'))
                primary=any(tuple(q[k] for k in ('champion','position','patch','comparison','metric','opponent_champion'))==identity and
                    any(x['minute']==ref['minute'] and x['visible'] for x in q['points'])
                    for r in datasets if r['group']=='LEAGUE_SEED_COHORT' and r['tier']=='CHALLENGER' for q in r['data']['cohorts'])
                if primary: continue
            unit=c.get('units')
            if unit is None:
                metric=c['metric'].replace('_delta','');unit={'gold':'gold','xp':'XP','cs':'CS'}[metric]
                unit+=('/minute difference vs role population rate' if c['comparison']=='ROLE_POPULATION' else ' difference vs opposing same role')
            return dict(**ref,comparison_group=row['group'],tier=row['tier'],champion=c['champion'],position=c['position'],patch=c['patch'],
                metric=c['metric'],comparison=c['comparison'],unit=unit,point=deepcopy(p),inference='DESCRIPTIVE_NON_CAUSAL')
    return None


def _active_knowledge(knowledge):
    result={}
    for item,current in zip(knowledge,_current_flags(knowledge)):
        p=item['proposal'];raw=item.get('spec')
        if not current or p.get('review_state')!='REVIEWED' or raw is None: continue
        s=parse_rule(raw).model_dump(mode='json')
        if not binding_matches(p,s): continue
        result[(p['rule_id'],p['version'],digest(s))]=(p,s)
    return result


def build_rights(plan,knowledge,power_datasets,annotations=None,test_mode=False):
    """Return nine conditional card labels without inferring prose semantics.

The caller supplies a checked immutable CURRENT plan and coherent current
knowledge. Invalid or missing contextual bindings never yield risk/safety.
"""
    annotations=validate_right_annotations([] if annotations is None else annotations)
    plan=plan if isinstance(plan,dict) else {}
    knowledge=list(knowledge or [])
    cards=[dict(key=k,title=v,status='UNKNOWN',label=LABELS['UNKNOWN'],reasons=[],evidence=[],statistics=[]) for k,v in CARD_TITLES.items()]
    result=dict(schema_version='pregame.opponent-rights.v1',status='UNKNOWN',cards=cards,
        plan_id=plan.get('id'),coaching_accuracy=None,limitations=list(LIMITATIONS))
    reason=None
    if plan.get('validity')!='CURRENT': reason='CURRENT_PLAN_REQUIRED'
    elif plan.get('knowledge_fingerprint')!=knowledge_fingerprint(knowledge): reason='CURRENT_KNOWLEDGE_BINDING_REQUIRED'
    try:
        draft=parse_input(plan.get('input')).model_dump(mode='json')
        if not all(draft.get(k) for k in ('patch','my_champion','my_position')): reason=reason or 'EXPLICIT_CHAMPION_POSITION_PATCH_REQUIRED'
    except (ValueError,TypeError): reason=reason or 'VALID_PLAN_INPUT_REQUIRED';draft=None
    if reason:
        for card in cards: card['reasons']=[reason]
        return result
    active=_active_knowledge(knowledge);datasets=_datasets(power_datasets,test_mode)
    by_key=dict(_cards(plan))
    for card in cards:
        cells=by_key[card['key']]
        if not cells or any(not isinstance(c,dict) or c.get('status')!='KNOWN' for c in cells):
            card['reasons']=['APPLICABLE_REVIEWED_CARD_REQUIRED'];continue
        eligible=[a for a in annotations if a['card_key']==card['key']]
        if not eligible:
            card['reasons']=['EXPLICIT_REVIEWED_RIGHT_ASSERTION_REQUIRED'];continue
        all_evidence=[];all_stats=[];classifications=set();complete=True
        for cell in cells:
            supported=False
            for trace in cell.get('rules',[]):
                if not isinstance(trace,dict) or trace.get('status')!='APPLIED' or trace.get('condition')!='TRUE' or trace.get('review_state')!='REVIEWED': continue
                identity=(trace.get('proposal',{}).get('rule_id'),trace.get('version'),trace.get('spec_sha256'))
                current=active.get(identity)
                if current is None: continue
                p,s=current
                if trace.get('spec')!=s or trace.get('output',{}).get('text') not in cell.get('texts',[]): continue
                if draft['patch'] not in s['patches']: continue
                for a in eligible:
                    if (a['rule_id'],a['selected_version'],a['spec_sha256'])!=identity or a['source_ref'] not in p.get('source_refs',[]): continue
                    assertion=a['assertion']
                    if assertion['claim']!=p['claim'] or assertion['right'] not in p['claim']: continue
                    stats=[_statistic(r,datasets,draft) for r in a['statistics']]
                    if any(r is None for r in stats): continue
                    supported=True;classifications.add(assertion['classification']);all_stats.extend(stats)
                    all_evidence.append(dict(rule_id=p['rule_id'],selected_version=p['version'],spec_sha256=digest(s),
                        source_ref=deepcopy(a['source_ref']),sources=deepcopy(s['sources']),kind=ASSERTION_KIND,
                        claim=assertion['claim'],right=assertion['right'],conditions=deepcopy(s['conditions']),
                        counterconditions=deepcopy(s['counterconditions']),stop_conditions=deepcopy(s['stop_conditions']),
                        required_fields=deepcopy(s['required_fields']),patches=deepcopy(s['patches'])))
            complete=complete and supported
        if len(classifications)>1: card['reasons']=['RIGHT_ASSERTION_CONFLICT']
        elif not complete or not classifications: card['reasons']=['MATCHING_REVIEWED_ASSERTION_AND_ELIGIBLE_STATISTICS_REQUIRED']
        else:
            status=next(iter(classifications));card.update(status=status,label=LABELS[status],reasons=['MANUAL_REVIEWED_CONDITIONAL_ASSERTION'],
                evidence=list({digest(e):e for e in all_evidence}.values()),statistics=list({digest(s):s for s in all_stats}.values()))
    if any(c['status']!='UNKNOWN' for c in cards): result['status']='ANNOTATED'
    return result


def opponent_rights_response(server,plan):
    """Server integration; the optional sidecar is read, never promoted/written."""
    from .pregame_server import current_knowledge
    datasets=list(server.validated_power_datasets().values())
    pro=getattr(server,'pro_reference_data',None)
    if pro is not None and pro['roster_sha256']==server.current_pro_roster_digest(): datasets.append(pro)
    return build_rights(plan,current_knowledge(server.research),datasets,
        annotations=getattr(server,'opponent_right_annotations',[]),test_mode=server.test_mode)
