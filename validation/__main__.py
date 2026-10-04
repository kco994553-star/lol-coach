from pathlib import Path
import copy
import hashlib
import json
import platform
import sys
import traceback
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'legacy'))
results=[]
class NotRun(Exception): pass

def check(name,fn):
    try:
        detail=fn()
        results.append(dict(id=name,status='PASS',detail=detail))
    except NotRun as e:
        results.append(dict(id=name,status='NOT_RUN',detail=str(e)))
    except Exception as e:
        results.append(dict(id=name,status='FAIL',detail=f'{type(e).__name__}: {e}'))

def load(p): return json.loads((ROOT/p).read_text())
def need(b,msg):
    if not b: raise AssertionError(msg)

def source_bytes():
    m=load('evidence/source_manifest.json')
    z=ROOT/'evidence/lol-coach-v0.1-core.zip'
    need(hashlib.sha256(z.read_bytes()).hexdigest()==m['zip_sha256'],'ZIP changed')
    for n,h in m['files'].items():
        need(hashlib.sha256((ROOT/'legacy'/n).read_bytes()).hexdigest()==h,f'legacy changed {n}')
    actual={p.relative_to(ROOT/'legacy').as_posix() for p in (ROOT/'legacy').rglob('*.py')}
    need(actual=={n for n in m['files'] if n.endswith('.py')},'core file set changed')
    return {'source_files':len(m['files']),'python_files':len(actual),'historical_identity':'UNKNOWN'}

def traceability():
    req=load('contracts/requirements.json'); sc=load('contracts/scenarios.json')
    rids=[r['id'] for r in req]; sids=[s['id'] for s in sc]
    need(len(set(rids))==len(rids),'duplicate requirement IDs')
    need(len(set(sids))==len(sids),'duplicate scenario IDs')
    for r in req:
        need(r['id'].startswith('REC-REQ-'),'namespace')
        file,section=r['contract'].split('#')
        need('\n## '+section+'\n' in (ROOT/file).read_text(),'missing contract '+r['contract'])
        need(bool(r['scenario_ids']),'uncovered requirement '+r['id'])
        for sid in r['scenario_ids']:
            need(sid in sids,'dangling scenario '+sid)
            need(r['id'] in sc[sids.index(sid)]['requirement_ids'],'asymmetric ref')
    for s in sc:
        need(s['evidence_kind']=='DESIGN_EXPECTATION' and s['runtime_status']=='NOT_RUN','synthetic runtime claim')
        for field in ('input_summary','expected','variation'): need(bool(s[field]),'empty scenario field')
        for rid in s['requirement_ids']:
            need(rid in rids and s['id'] in req[rids.index(rid)]['scenario_ids'],'dangling/asymmetric requirement')
    return {'requirements':len(req),'scenarios':len(sc),'scope':'reference integrity only; semantics independently reviewed'}

def history_ids():
    hist=load('contracts/reserved_history_ids.json')
    current={x['id'] for name in ('requirements','scenarios') for x in load('contracts/'+name+'.json')}
    need(not current.intersection(hist['ids']),'historical IDs reassigned')
    need(hist['status']=='UNRECOVERED_DO_NOT_REASSIGN','lost uncertainty status')
    return 'Historical IDs reserved, no claim of original 32/32 reproduction.'

def core_case(jungle,permission,short,extended,chase,recommended):
    from backend.state.models import GameState
    from backend.decision.engine import analyze
    state=GameState.model_validate(dict(power={'matchup':'FAVORABLE'},wave={},jungle={'enemy':jungle},opponent={'action':'CS_APPROACH'},risk={}))
    before=state.model_dump(mode='json')
    d=analyze(state); actions={a.action.value:a for a in d.actions}
    need(d.permission.name==permission,'permission mismatch')
    for name,status in [('SHORT_TRADE',short),('EXTENDED_TRADE',extended),('CHASE',chase)]:
        need(actions[name].validity.value==status,name+' mismatch')
    need([a.action.value for a in d.actions if a.recommended]==[recommended],'recommendation mismatch')
    need(before==state.model_dump(mode='json'),'mutated input')
    need(any(t.stage=='PERMISSION' and t.code==permission for t in d.trace),'trace mismatch')
    return {'jungle':jungle,'permission':permission,'recommended':recommended,'classification':'legacy behavior, not v1 coaching correctness'}

def counterfactual():
    from backend.state.models import GameState
    from backend.decision.engine import analyze
    from backend.decision.actions import ActionType
    from backend.decision.reason_codes import ReasonCode
    p=dict(power={'matchup':'FAVORABLE'},wave={},jungle={'enemy':'UNKNOWN'},opponent={'action':'CS_APPROACH'},risk={})
    near=copy.deepcopy(p);near['jungle']['enemy']='CONFIRMED_NEAR'
    far=copy.deepcopy(p);far['jungle']['enemy']='CONFIRMED_FAR'
    ds=[analyze(GameState.model_validate(x)) for x in (near,p,far)]
    need([int(d.permission) for d in ds]==[2,3,4],'legacy jungle relation')
    a=next(x for x in ds[1].actions if x.action==ActionType.CHASE)
    need(ReasonCode.ENEMY_JUNGLE_UNKNOWN in a.reasons,'missing reason')
    p2=copy.deepcopy(p);p2['opponent']['action']='NEUTRAL'
    d2=analyze(GameState.model_validate(p2))
    need(not d2.opportunities and [a.action.value for a in d2.actions if a.recommended]==['WAIT'],'opportunity removal')
    return 'Controlled jungle-state changes and removing CS-approach opportunity; new REC check.'

def migration_claims():
    from backend.decision.actions import ActionType,ACTION_DEFINITIONS
    from backend.state.models import GameState
    from backend.decision.engine import analyze
    need(len(ActionType)==16 and len(ACTION_DEFINITIONS)==9,'migration action counts changed')
    p=dict(power={'matchup':'FAVORABLE'},wave={},jungle={'enemy':'UNKNOWN'},opponent={'action':'CS_APPROACH'},risk={'return_path':'SAFE'})
    q=copy.deepcopy(p);q['risk']['return_path']='UNSAFE'
    a,b=analyze(GameState.model_validate(p)),analyze(GameState.model_validate(q))
    need(a==b,'return-path insensitivity claim changed')
    return 'Verified known legacy gaps: 16 enums / 9 definitions; return_path does not affect output. Not a desired v1 invariant.'

def frozen_payload():
    manifest=ROOT/'FREEZE_MANIFEST.json'
    if not manifest.exists(): raise NotRun('PRE_FREEZE: payload manifest not yet issued')
    m=load('FREEZE_MANIFEST.json')
    for p,h in m['payload_sha256'].items():
        need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen payload mismatch '+p)
    return {'payload_files':len(m['payload_sha256']),'scope':'frozen payload integrity'}

check('REC-CHECK-SOURCE',source_bytes)
check('REC-CHECK-TRACEABILITY',traceability)
check('REC-CHECK-HISTORY',history_ids)
check('REC-CORE-UNKNOWN',lambda:core_case('UNKNOWN','P3','VALID','CONDITIONAL','INVALID','SHORT_TRADE'))
check('REC-CORE-FAR',lambda:core_case('CONFIRMED_FAR','P4','VALID','VALID','VALID','SHORT_TRADE'))
check('REC-CORE-NEAR',lambda:core_case('CONFIRMED_NEAR','P2','CONDITIONAL','CONDITIONAL','CONDITIONAL','THREAT'))
check('REC-CORE-COUNTERFACTUAL',counterfactual)
check('REC-CHECK-MIGRATION',migration_claims)
check('REC-CHECK-FROZEN-PAYLOAD',frozen_payload)
try:
    import pydantic
    pv=pydantic.__version__
except ImportError: pv=None
report=dict(at_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),pydantic=pv,evidence_kind='FRESH_EXECUTION',historical_R1_reproduced=False,v1_runtime_tested=False,passed=sum(r['status']=='PASS' for r in results),failed=sum(r['status']=='FAIL' for r in results),checks=results)
out=ROOT/'evidence/validation.json'
if out.exists():
    old=out.read_bytes();history=ROOT/'evidence/validation-history';history.mkdir(exist_ok=True)
    (history/(hashlib.sha256(old).hexdigest()+'.json')).write_bytes(old)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(report['failed']))
