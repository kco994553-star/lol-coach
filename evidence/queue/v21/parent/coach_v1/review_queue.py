"""Read-only candidate projection and revision-bound local deferrals.

No approval authority is imported here. Source documents and rule schemas stay
immutable; the normal knowledge API remains the only decision write path.
"""
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import ipaddress
import json
from pathlib import Path
import sqlite3
from itertools import zip_longest
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

from .pregame_contract import POSITIONS, proposal_rule
from .state import digest
from .storage import ServiceError

GOLDEN = {'ALLY':dict(zip(POSITIONS,['Ornn','Sejuani','Ahri','Caitlyn','Lux'])),
          'ENEMY':dict(zip(POSITIONS,['Fiora','LeeSin','Zed','Ezreal','Nautilus']))}
PICKS = {'Yunara','Ashe','Kaisa','Caitlyn'}
LIMIT = 20


def _public_url(value):
    try:
        p=urlsplit(value)
        if p.scheme!='https' or not p.hostname or p.username or p.password:return None
        host=p.hostname.lower()
        if host=='localhost' or host.endswith(('.localhost','.local','.internal')) or '.' not in host:return None
        try:
            if not ipaddress.ip_address(host).is_global:return None
        except ValueError:pass
        query=urlencode([(k,v) for k,v in parse_qsl(p.query) if host in ('www.youtube.com','youtube.com','youtu.be') and k in ('v','t','start') and len(v)<100])
        return urlunsplit((p.scheme,p.netloc,p.path,query,''))
    except (ValueError,TypeError):return None


@lru_cache(maxsize=1)
def _archives():
    from .pregame_server import ROOT
    result={}
    for folder in (ROOT/'evidence/queue/q05/sources',ROOT/'evidence/queue/q05-expansion/sources'):
        for path in folder.glob('*.json'):
            raw=path.read_bytes()
            try:result[hashlib.sha256(raw).hexdigest()]=json.loads(raw)
            except (ValueError,UnicodeError):continue
    return result


def _sources(spec):
    result=[]
    for s in (spec or {}).get('sources',[]):
        value=_archives().get(s.get('sha256'));status='UNKNOWN';excerpt=None
        try:
            for part in s['locator'].split('.'):
                value=value[int(part)] if isinstance(value,list) else value[part]
            if value is not None:
                excerpt=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
                excerpt=excerpt[:3000];status='ARCHIVED_VERIFIED'
        except (TypeError,KeyError,IndexError,ValueError):pass
        result.append(dict(url=_public_url(s['url']),title=s['title'],locator=s['locator'],patch=s['patch'],excerpt=excerpt,excerpt_status=status))
    return result


def _source_statement(server,proposal):
    if not proposal:return None
    from .expert_contract import validate_expert_artifact
    for source in proposal.get('source_refs',[]):
        report=server.research.get(source['resource_id'])['report']
        if report.get('format')!='expert-video-summary.v1':continue
        artifact=validate_expert_artifact(report['artifact'])
        try:claim=artifact['claims'][int(source['anchor'])-1]
        except (IndexError,ValueError):continue
        if int(source['anchor'])<1:continue
        return dict(claim=claim,source=dict(url=_public_url(artifact['video']['url']+'&t='+str(claim['timestamp_seconds'])),
                   title=artifact['video']['title']+' · 저장된 의역 (원문 인용 아님)',locator=claim['timestamp'],patch=claim['patch_range'],
                   excerpt=claim['paraphrase'],excerpt_status='SOURCE_PARAPHRASE_UNVERIFIED'))
    return None


def _champions(spec):
    names=set()
    if (spec or {}).get('profile'):names.add(spec['profile']['champion'])
    for p in (spec or {}).get('conditions',[]):
        if p['field'].endswith('champion'):
            names.update([p['value']] if isinstance(p['value'],str) else p['value'])
    return names


def _golden_relevant(spec):
    if not spec:return False
    names=_champions(spec)
    if spec['profile'] and spec['profile']['champion'] not in {c for t in GOLDEN.values() for c in t.values()}:return False
    for p in spec['conditions']:
        parts=p['field'].split('.')
        if len(parts)==3 and parts[-1]=='champion' and parts[0].upper() in GOLDEN:
            actual=GOLDEN[parts[0].upper()].get(parts[1])
            if p['op']=='EQ' and actual!=p['value']:return False
    return bool(names & {c for t in GOLDEN.values() for c in t.values()}) or not names


def _inputs(server):
    records=[]
    for brief in server.pregame.list_inputs()[:50]:
        records.append(server.pregame.get_input(brief['session_id'])['input'])
    return records


def _coverage(knowledge,patch=None):
    from .pregame_v3 import evaluate_gameplan_v3
    manual=dict(kind='MANUAL',reference='Golden10 example only',observed_at=None,verification='UNVERIFIED')
    slots=[dict(side=side,slot=i+1,champion=champion,position=position,position_candidates=[],uncertainty='Example',
                champion_source=manual,position_source=manual,runes=dict(status='UNKNOWN',values=[],source=manual),
                summoners=dict(status='UNKNOWN',values=[],source=manual))
           for side,team in GOLDEN.items() for i,(position,champion) in enumerate(team.items())]
    filled=0
    for position in POSITIONS:
        draft=dict(title='Golden10 example',patch=patch,phase='PRE_GAME',observed_at=None,my_position=position,
                   my_champion=GOLDEN['ALLY'][position],my_slot=POSITIONS.index(position)+1,slots=slots,source=manual,original_capture=None)
        plan=evaluate_gameplan_v3(draft,knowledge)
        cells=[*plan['common']['map'],plan['common']['jungle'],plan['common']['composition'],*plan['personal'].values(),plan['changes'],plan['operations'],plan['movement']]
        # The map is one card comprising five position rows.
        filled+=int(all(c['status']=='KNOWN' for c in cells[:5]))+sum(c['status']=='KNOWN' for c in cells[5:])
    return filled


def _deferred(server):
    path=Path(server.pregame.dbpath+'.review.sqlite')
    if not path.exists():return set()
    with sqlite3.connect(path) as db:return set(db.execute('SELECT candidate_id,selected_version FROM deferrals'))


def _statistics(datasets,names):
    groups=[]
    for data in datasets:
        rows=[]
        for c in data.get('cohorts',[]):
            if c['champion'] not in names:continue
            points=[dict(minute=p['minute'],n=p['n'],mean=p['mean'],ci95=p['ci95']) for p in c['points'] if p['visible']]
            if points:
                base={'gold_delta':'gold','xp_delta':'XP','cs_delta':'CS'}[c['metric']]
                unit=base+' (champion minus opponent)' if c['comparison']=='MATCHUP' else base+'/min (champion rate minus role population rate)'
                rows.append({k:c[k] for k in ('champion','position','patch','tier','comparison','metric')}|dict(points=points[:8],unit=unit,sample_kind=data['source']['sample_kind']))
        groups.append(rows)
    # Round robin keeps independent patch/tier cohorts visible without merging
    # means or summing overlapping match samples.
    rows=[row for group in zip_longest(*groups) for row in group if row is not None]
    return dict(status='DESCRIPTIVE_ONLY' if rows else 'UNKNOWN',comparisons=rows[:6],available_comparisons=len(rows),limitations=['통계는 기술적·비인과 비교이며 주장 승인이나 전투 강도를 증명하지 않습니다.'])


def _all(server):
    from .pregame_server import current_knowledge,candidate_specs
    knowledge=current_knowledge(server.research);catalog=candidate_specs()
    from .practical_review import advice_catalog
    practical=advice_catalog()
    # Original catalogs remain readable via /candidates. Review only the newly
    # written batch when the complete original source catalog is available.
    if {r['original_candidate_id'] for r in practical} <= {s['rule_id'] for s in catalog}:
        catalog=[r['spec'] for r in practical]
        ids={s['rule_id'] for s in catalog}
        visible=[r for r in knowledge if r['spec'] and r['spec']['rule_id'] in ids]
    else:visible=knowledge
    represented={r['spec']['rule_id'] for r in visible if r['spec']}
    rows=[dict(proposal=r['proposal'],spec=r['spec']) for r in visible]
    rows.extend(dict(proposal=None,spec=s) for s in catalog if s['rule_id'] not in represented)
    return rows,knowledge


def _focus_context(inputs):
    if inputs:
        draft=inputs[0];champion=draft.get('my_champion');position=draft.get('my_position');patch=draft.get('patch')
        team={s['position']:s['champion'] for s in draft['slots'] if s['side']=='ENEMY' and s.get('position') and s.get('champion')}
        kind='SAVED_PICK'
    else:
        champion='Caitlyn';position='BOTTOM';patch=None;team=GOLDEN['ENEMY'];kind='EXAMPLE'
    nearby={'TOP':['TOP','JUNGLE'],'JUNGLE':['JUNGLE','TOP'],'MID':['MID','JUNGLE'],'BOTTOM':['BOTTOM','SUPPORT'],'SUPPORT':['SUPPORT','BOTTOM']}.get(position,[])
    names=list(dict.fromkeys([c for c in [champion,*[team.get(p) for p in nearby]] if c]))
    return dict(kind=kind,champion=champion,position=position,patch=patch,enemy=team,nearby_positions=nearby,reference_champions=names)


def _focus_rank(candidate,focus):
    spec=candidate['spec'];own=False;nearby=False
    if focus['position'] and spec['positions'] and focus['position'] not in spec['positions']:return None
    if focus['patch'] and spec['patches'] and focus['patch'] not in spec['patches']:return None
    for predicate in spec['conditions']:
        if predicate['op']!='EQ':continue
        field=predicate['field'];value=predicate['value']
        if field=='my.champion':
            if value!=focus['champion']:return None
            own=True
        elif field.startswith('enemy.') and field.endswith('.champion'):
            position=field.split('.')[1]
            if focus['enemy'].get(position)!=value:return None
            if position in focus['nearby_positions']:nearby=True
    return 0 if own else 1 if nearby else 2


def queue_response(server,page=0,later_page=0,*,focused=False):
    if any(type(v) is not int or not 0<=v<=10000 for v in (page,later_page)):raise ServiceError(422,'INVALID_REVIEW_PAGE')
    rows,knowledge=_all(server);inputs=_inputs(server)
    from .practical_review import advice_catalog
    practical={r['id']:r for r in advice_catalog()}
    frequency=Counter(s['champion'] for d in inputs for s in d['slots'] if s['champion'])
    recent={d.get('my_champion') for d in inputs[:10]}|{c for d in inputs[:10] for c in d.get('frequent_champions',[])}
    datasets=list(server.validated_power_datasets().values())
    # Observations are distinct within each cohort; do not multiply by metric.
    for c in [c for data in datasets for c in data.get('cohorts',[])]:
        frequency[c['champion']]=max(frequency[c['champion']],max((p.get('champion_n',p['n']) for p in c['points']),default=0))
    deferred=_deferred(server);ready=[];later=[];reviewed=rejected=0
    for row in rows:
        p=row['proposal'];s=row['spec'];state=p['review_state'] if p else 'EXPLORATORY'
        if state=='REVIEWED':reviewed+=1;continue
        if state=='REJECTED':rejected+=1;continue
        statement=_source_statement(server,p) if not s else None
        names=_champions(s)
        if not s and p and p['applicability']['champion'] not in ('UNKNOWN','TYPE_BASED'):names.add(p['applicability']['champion'])
        tier=0 if _golden_relevant(s) else 1 if names&(PICKS|recent) else 2 if any(frequency[n] for n in names) else 3
        candidate_id=p['rule_id'] if p else s['rule_id'];version=p['version'] if p else digest(s)
        rule=p or proposal_rule(s)
        reasons=['USER_REVIEW_REQUIRED']
        if not (s or {}).get('patches'):reasons.append('GAME_PATCH_UNKNOWN')
        if not s:reasons.append('UNBOUND_SPEC')
        item=dict(candidate_id=candidate_id,selected_version=version,proposal=p,spec=s,priority=dict(tier=tier,
              conditional_card_targets=(5 if s and s['scope']=='COMMON' and s['output']['section']!='PROFILE' else len(s['positions']) if s and s['scope']=='POSITION' else 0) if tier==0 else 0,reason=['Golden10 카드 조건 검토','우선·최근 챔피언','관측 빈도','나머지'][tier],observed_frequency=max((frequency[n] for n in names),default=0)),
              claim=rule['claim'],conditions=dict(patches=(s or {}).get('patches',[]),applicability=rule['applicability'],
              required_fields=rule['required_fields'],predicates=(s or {}).get('conditions',[]),counterconditions=(s or {}).get('counterconditions',[]),stop_conditions=(s or {}).get('stop_conditions',[]),source_conditions=statement['claim']['conditions'] if statement else []),
              sources=[statement['source']] if statement else _sources(s),patch_range=rule['patch_range'],counterexamples=rule['counterexamples'],statistics=_statistics(datasets,names),
              preview=dict(status='CONDITIONAL_PREVIEW',section=(s or {}).get('output',{}).get('section'),target=(s or {}).get('output',{}).get('target'),
                           text=(s or {}).get('output',{}).get('text',rule['claim']),conditions=(s or {}).get('conditions',[]),reasons=reasons,coaching_enabled=False))
        practical_row=practical.get((s or {}).get('rule_id'))
        if practical_row:
            item['practical_advice']=practical_row['advice'] if rule['claim']==practical_row['spec']['output']['text'] else None
            item['original_candidate_id']=practical_row['original_candidate_id']
            item['user_decision_only']=True
        (later if (candidate_id,version) in deferred else ready).append(item)
    order=lambda c:(c['priority']['tier'],-c['priority']['conditional_card_targets'],-c['priority']['observed_frequency'],c['candidate_id'])
    ready.sort(key=order);later.sort(key=order)
    policy=None;focus=None;official=None;optional_archive=0
    # Keep the historical complete projection for archive access and fixtures.
    # The ordinary product route uses focused=True for the practical catalog.
    if focused and rows and all((r['spec'] or {}).get('rule_id') in practical for r in rows):
        focus=_focus_context(inputs)
        eligible=[c for c in ready if _focus_rank(c,focus) is not None]
        eligible.sort(key=lambda c:(_focus_rank(c,focus),c['candidate_id']))
        selected=[];seen=set()
        for c in eligible:
            key=(practical[c['spec']['rule_id']]['champion'],c['spec']['output']['section'])
            if key in seen:continue
            selected.append(c);seen.add(key)
            if len(selected)==5:break
        optional_archive=len(ready)-len(selected);ready=selected
        policy=dict(mode='REFERENCE_FIRST',review_required_for_reference=False,tactical_review_optional=True,focus_limit=5)
        from .official_reference import facts_response
        official=facts_response(focus['reference_champions'],patch=focus['patch'])
    page_limit=5 if policy else LIMIT
    export=[]
    for c in ready[:LIMIT]:
        export.extend(['주장: '+c['claim'],'조건: '+json.dumps(c['conditions'],ensure_ascii=False),'출처: '+', '.join(s['url'] for s in c['sources'] if s['url']),''])
    result=dict(schema_version='pregame.review-queue.v1',candidates=ready[page*page_limit:(page+1)*page_limit],deferred_candidates=later[later_page*LIMIT:(later_page+1)*LIMIT],page_limit=page_limit,
                pagination=dict(page=page,later_page=later_page,ready_pages=(len(ready)+page_limit-1)//page_limit,later_pages=(len(later)+LIMIT-1)//LIMIT),
                progress=dict(total=len(rows),pending=len(ready)+len(later),ready=len(ready),deferred=len(later),reviewed=reviewed,rejected=rejected,
                              example_card_filled=_coverage(knowledge),example_card_total=45,example_card_status='UNKNOWN_PATCH_CONDITIONAL',
                              example_card_by_patch={'16.20':_coverage(knowledge,patch='16.20')}),export_text='\n'.join(export))
    if policy:
        result.update(operating_policy=policy,focus=focus,official_reference=official)
        result['progress']['optional_archive']=optional_archive
    # Full source schemas are unbounded in aggregate. Send fewer candidates when
    # a large specification would otherwise exceed the authenticated limit.
    budget=getattr(server.limits,'body_bytes',1_000_000)
    while len(json.dumps(result,ensure_ascii=False).encode())>budget and (result['candidates'] or result['deferred_candidates']):
        target='deferred_candidates' if result['deferred_candidates'] else 'candidates';result[target].pop()
    if len(json.dumps(result,ensure_ascii=False).encode())>budget:raise ServiceError(413,'REVIEW_QUEUE_TOO_LARGE')
    return result


def defer_candidate(server,body):
    if not isinstance(body,dict) or set(body)!={'candidate_id','selected_version'} or any(not isinstance(v,str) or not v or len(v)>200 for v in body.values()):
        raise ServiceError(422,'INVALID_REVIEW_DEFERRAL')
    rows,_=_all(server);found=None
    for row in rows:
        p,s=row['proposal'],row['spec'];rid=p['rule_id'] if p else s['rule_id']
        if rid==body['candidate_id']:
            if (p['version'] if p else digest(s))!=body['selected_version']:raise ServiceError(409,'REVISION_CONFLICT')
            if p and p['review_state']!='EXPLORATORY':raise ServiceError(409,'CANDIDATE_ALREADY_DECIDED')
            found=row;break
    if found is None:raise ServiceError(404,'REVIEW_CANDIDATE_NOT_FOUND')
    path=Path(server.pregame.dbpath+'.review.sqlite')
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS deferrals(candidate_id TEXT NOT NULL, selected_version TEXT NOT NULL, deferred_at TEXT NOT NULL, PRIMARY KEY(candidate_id,selected_version))')
        db.execute('INSERT OR REPLACE INTO deferrals VALUES (?,?,?)',(body['candidate_id'],body['selected_version'],datetime.now(timezone.utc).isoformat()))
    path.chmod(0o600)
    return dict(schema_version='pregame.review-later.v1',**body,state='DEFERRED')
