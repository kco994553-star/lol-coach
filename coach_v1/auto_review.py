"""Separate automatic-review provenance. Never writes KnowledgeStore/USER rows."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import sqlite3

from .state import digest, canonical

ROOT=Path(__file__).resolve().parents[1]
FIELDS={'상황','할 것','하지 말 것','상대 권리','무효 조건','근거','패치'}
REVIEWERS={'EVIDENCE':'/root/v21_evidence_check','COUNTER':'/root/v21_counter_check'}


def candidate_hash(row):
    return digest({k:v for k,v in row.items() if k not in ('candidate_sha256','source_excerpts')})


def load_bundle():
    directory=ROOT/'evidence/queue/v21'
    packet=json.loads((directory/'packet.json').read_text())
    receipts=[]
    for filename in ('evidence-review.json','counter-review.json'):
        try:receipts.append(json.loads((directory/filename).read_text()))
        except (OSError,ValueError):pass
    return packet,receipts


def _source_material(source):
    from .review_queue import _public_url
    if not _public_url(source['url']):raise ValueError('source')
    value=None
    for directory in ('q05','q05-expansion'):
        folder=ROOT/'evidence/queue'/directory
        receipts=json.loads((folder/'source-receipts.json').read_text())
        receipts=receipts if isinstance(receipts,list) else receipts.get('sources',receipts.get('receipts',[]))
        for receipt in receipts:
            if receipt.get('sha256')!=source['sha256'] or receipt.get('requested_url')!=source['url']:continue
            for path in (folder/'sources').glob('*.json'):
                raw=path.read_bytes()
                if hashlib.sha256(raw).hexdigest()==source['sha256']:
                    value=json.loads(raw);break
            if value is not None:break
        if value is not None:break
    if value is None:raise ValueError('source provenance')
    version=value.get('version')
    if source['patch']!=version or f'/cdn/{version}/' not in source['url']:raise ValueError('version')
    # Enforce CDN origin, exact locale/champion path and internal document identity.
    match=re.fullmatch(r'https://ddragon\.leagueoflegends\.com/cdn/([0-9.]+)/data/(en_US|ko_KR)/champion/([A-Za-z0-9]+)\.json',source['url'])
    if source['kind']=='DATA_DRAGON' and (not match or match[1]!=version or match[3] not in value.get('data',{})):raise ValueError('origin')
    excerpt=value
    for part in source['locator'].split('.'):
        excerpt=excerpt[int(part)] if isinstance(excerpt,list) else excerpt[part]
    if not isinstance(excerpt,str) or not excerpt.strip():raise ValueError('excerpt')
    return value,excerpt


def machine_check(row):
    reasons=[]
    if set(row.get('advice',{}))!=FIELDS or any(not isinstance(v,str) or not v.strip() for v in row.get('advice',{}).values()):reasons.append('SEVEN_FIELDS_REQUIRED')
    if candidate_hash(row)!=row.get('candidate_sha256'):reasons.append('CANDIDATE_HASH_MISMATCH')
    try:
        originals=json.loads((ROOT/'knowledge_candidates/practical-review-v1.json').read_text())
        original=next(r for r in originals if r['id']==row['id'])
        if row['original_candidate_id']!=original['original_candidate_id'] or row['original_spec_sha256']!=original['original_spec_sha256'] or row['previous_practical_spec_sha256']!=digest(original['spec']):raise ValueError('lineage')
    except (OSError,ValueError,KeyError,TypeError,StopIteration):reasons.append('ORIGINAL_LINEAGE_MISMATCH')
    try:
        from .pregame_contract import Predicate,POSITIONS
        spec=row['spec']
        if spec['schema_version']!='auto-advice.v1' or spec['automatic_state_checks'] is not False or spec['manual_checks']!=[row['advice']['상황'],row['advice']['무효 조건']]:raise ValueError('advice boundary')
        if set(spec['positions'])-set(POSITIONS) or spec['scope'] not in ('COMMON','POSITION'):raise ValueError('scope')
        for p in spec['conditions']+spec['counterconditions']+spec['stop_conditions']:Predicate.model_validate(p)
    except (ValueError,KeyError,TypeError):reasons.append('STATIC_ADVICE_CONTRACT_INVALID')
    sources=row.get('spec',{}).get('sources',[]);excerpts=[]
    if not sources:reasons.append('SOURCE_REQUIRED')
    for index,source in enumerate(sources):
        try:
            _,excerpt=_source_material(source)
            bound=row['source_excerpts'][index]
            if bound['excerpt']!=excerpt or bound['sha256']!=source['sha256'] or bound['url']!=source['url'] or bound['patch']!=source['patch']:raise ValueError('bound excerpt')
            if '.'.join(source['patch'].split('.')[:2]) not in row['spec']['patches']:raise ValueError('game patch')
            excerpts.append(excerpt)
        except (OSError,KeyError,ValueError,TypeError,IndexError):reasons.append('SOURCE_LINK_HASH_PATCH_OR_EXCERPT_INVALID')
    numbers=set(re.findall(r'\d+(?:\.\d+)?',' '.join(v for k,v in row.get('advice',{}).items() if k!='패치')))
    supported=set(re.findall(r'\d+(?:\.\d+)?',' '.join(excerpts)))
    # Token overlap is not numeric evidence ("3 minutes" cannot borrow "3 dashes").
    # This first authored batch deliberately has no quantitative gameplay claim;
    # future numeric statements need an explicit independently reviewed contract.
    if numbers:reasons.append('UNSUPPORTED_NUMBER')
    expert=[s for s in sources if s.get('kind') not in ('DATA_DRAGON','RIOT_OFFICIAL')]
    if expert and len({s.get('speaker_id') for s in expert if s.get('speaker_id')})<2:reasons.append('TWO_DISTINCT_EXPERT_SPEAKERS_REQUIRED')
    return list(dict.fromkeys(reasons))


def assess(packet=None,receipts=None):
    if packet is None:packet,receipts=load_bundle()
    receipts=receipts or []
    run={'files':{}}
    # Receipts are immutable, audited executions by distinct role agents, not
    # caller declarations of PASS. No HTTP API accepts arbitrary reviewer input.
    try:
        directory=ROOT/'evidence/queue/v21'
        run=json.loads((directory/'review-manifest.json').read_text())
        allowed=[]
        for filename in ('evidence-review.json','counter-review.json'):
            raw=(directory/filename).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=run['files'][filename]:continue
            allowed.append(digest(json.loads(raw)))
        receipts=[r for r in receipts if digest(r) in allowed]
    except (OSError,ValueError,KeyError,TypeError):receipts=[]
    try:
        packet_raw=(ROOT/'evidence/queue/v21/packet.json').read_bytes()
        packet_sha=hashlib.sha256(packet_raw).hexdigest() if digest(json.loads(packet_raw))==digest(packet) and hashlib.sha256(packet_raw).hexdigest()==run['files']['packet.json'] else None
    except (OSError,ValueError,KeyError,TypeError):packet_sha=None
    rows=[]
    for row in packet['rows']:
        reasons=machine_check(row)
        for role,reviewer in REVIEWERS.items():
            matching=[r for r in receipts if r.get('schema_version')=='auto-review.agent.v1' and r.get('role')==role and r.get('reviewer')==reviewer and r.get('packet_sha256')==packet_sha]
            checked=[r for r in matching[0].get('reviews',[]) if r.get('id')==row['id'] and r.get('candidate_sha256')==row['candidate_sha256']] if len(matching)==1 else []
            if len(checked)!=1:
                reasons.append(role+'_REVIEW_MISSING_OR_INVALID');continue
            review=checked[0]
            if review.get('verdict')!='PASS':reasons.extend([role+': '+str(s) for s in review.get('reasons',[])] or [role+'_HOLD'])
            if role=='EVIDENCE':
                claims=review.get('claims',[])
                if not claims:reasons.append('FACT_CLAIM_COVERAGE_MISSING')
                for claim in claims:
                    try:
                        index=claim['source_index']
                        if type(index) is not int or index<0:raise ValueError('source index')
                        original,excerpt=_source_material(row['spec']['sources'][index])
                        text='\n'.join(row['advice'].values())
                        quote=claim['quote']
                        version_quote=quote==original['version'] and claim['claim']=='공식 설명 자료: '+original['version']+'.'
                        if not claim['claim'] or claim['claim'] not in text or not quote or quote not in excerpt and not version_quote:raise ValueError('quote')
                    except (OSError,KeyError,ValueError,TypeError,IndexError):reasons.append('AGENT_QUOTE_NOT_IN_ORIGINAL')
            else:
                try:q15_sha=hashlib.sha256((ROOT/packet['q15_path']).read_bytes()).hexdigest()
                except OSError:q15_sha=None
                if not q15_sha or matching[0].get('q15_sha256')!=q15_sha or packet.get('q15_sha256')!=q15_sha:reasons.append('Q15_SOURCE_HASH_MISMATCH')
                if review.get('counterexamples'):reasons.append('SURVIVING_COUNTEREXAMPLE')
                if not review.get('statistic_checks') or any(c.get('status') not in ('MATCH','NOT_APPLICABLE') for c in review.get('statistic_checks',[])):reasons.append('STATISTICS_CHECK_MISSING_OR_CONFLICT')
        reasons=list(dict.fromkeys(reasons))
        rows.append(dict(id=row['id'],candidate_sha256=row['candidate_sha256'],state='HOLD' if reasons else 'AUTO_VERIFIED',reasons=reasons))
    counts=Counter(reason for row in rows for reason in row['reasons'])
    return dict(schema_version='auto-review.result.v1',passed=sum(r['state']=='AUTO_VERIFIED' for r in rows),held=sum(r['state']=='HOLD' for r in rows),reasons=dict(counts),rows=rows,user_decisions_created=0)


class AutoReviewStore:
    def __init__(self,path):
        self.path=str(path)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS objections (id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL,candidate_sha256 TEXT NOT NULL,reason TEXT NOT NULL,actor TEXT NOT NULL,created_at TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS weekly (week TEXT PRIMARY KEY,payload TEXT NOT NULL)')

    def _db(self):return sqlite3.connect(self.path,timeout=10)

    def object(self,candidate_id,candidate_sha256,reason):
        if not re.fullmatch(r'KR-\d{3}',candidate_id) or not re.fullmatch('[a-f0-9]{64}',candidate_sha256) or not isinstance(reason,str) or not reason.strip() or len(reason)>2000:raise ValueError('objection')
        row=dict(id=secrets.token_hex(16),candidate_id=candidate_id,candidate_sha256=candidate_sha256,reason=reason.strip(),actor='USER_OBJECTION',created_at=datetime.now(timezone.utc).isoformat())
        with self._db() as db:db.execute('INSERT INTO objections VALUES(?,?,?,?,?,?)',tuple(row.values()))
        return row

    def objections(self):
        with self._db() as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM objections ORDER BY created_at,id')]

    def withdrawn(self):return {r['candidate_id'] for r in self.objections()}

    def weekly(self,rows):
        week=datetime.now(timezone.utc).strftime('%G-W%V')
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            withdrawn={r[0] for r in db.execute('SELECT candidate_id FROM objections')}
            existing=db.execute('SELECT payload FROM weekly WHERE week=?',(week,)).fetchone()
            if existing:
                report=json.loads(existing[0]);report['items']=[r for r in report['items'] if r['id'] not in withdrawn]
                return report
            eligible=[r for r in rows if r['state']=='AUTO_VERIFIED' and r['id'] not in withdrawn]
            selected=secrets.SystemRandom().sample(eligible,min(5,len(eligible)))
            catalog={r['id']:r for r in load_bundle()[0]['rows']}
            items=[dict(id=r['id'],candidate_sha256=r['candidate_sha256'],summary=catalog.get(r['id'],{}).get('advice',{}).get('할 것','자동 검토 기록')) for r in selected]
            report=dict(week=week,created_at=datetime.now(timezone.utc).isoformat(),items=items,selection='RANDOM_WITHOUT_REPLACEMENT',optional_user_review=True)
            if items:db.execute('INSERT INTO weekly VALUES(?,?)',(week,canonical(report)))
            return report
