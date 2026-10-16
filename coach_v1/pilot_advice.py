"""Seven conditional revisions. Source support never becomes tactical approval."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKET='knowledge_candidates/coaching-quality-pilot.json'
LEGACY='evidence/queue/v21/packet.json'
IDS={'KR-001','KR-005','KR-008','KR-015','KR-021','KR-022','KR-026'}
TOPICS={'SKILL_INTERACTION':'스킬 상호작용','LINE_PLAN':'라인 계획','OPERATIONS':'운영'}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _require(value):
    if not value:raise ValueError('INVALID_QUALITY_ADVICE')


def _texts(value):
    _require(isinstance(value,list) and value and all(isinstance(x,str) and x.strip() for x in value))


def validate_packet(packet):
    _require(isinstance(packet,dict) and set(packet)=={'schema_version','version','condition_logic','rows'})
    _require(packet['schema_version']=='quality-advice.v1' and packet['version']=='2026-10-16.2')
    _require(packet['condition_logic']==dict(choose_if='ALL',stop_if='ANY',uncertain_alternative='OPTIONS_NOT_SAFETY_GUARANTEE'))
    rows=packet['rows'];_require(isinstance(rows,list) and len(rows)==7)
    originals={r['id']:r for r in json.loads((ROOT/LEGACY).read_text())['rows']}
    _require({r['legacy_id'] for r in rows}==IDS)
    for row in rows:
        old=originals[row['legacy_id']]
        _require(row['id']=='QP-20261016-'+row['legacy_id']+'-v2')
        _require(row['legacy_candidate_sha256']==old['candidate_sha256'])
        _require(row['previous_advice']==old['advice'] and row['sources']==old['spec']['sources'] and row['source_excerpts']==old['source_excerpts'])
        _require(row['evidence_level']=='HYPOTHESIS' and row['review_state']=='HOLD' and row['approval_inherited'] is False)
        _require(row['topic'] in TOPICS and isinstance(row['scenario'],str) and row['scenario'].strip())
        for key in ('limitations','needed_evidence'):_texts(row[key])
        facts=row['source_facts'];_require(isinstance(facts,list) and facts)
        for fact in facts:
            index=fact['source_index'];_require(type(index) is int and 0<=index<len(row['source_excerpts']))
            _require(fact['kind']=='SOURCE_FACT' and isinstance(fact['claim'],str) and fact['claim'].strip())
            _require(isinstance(fact['quote'],str) and fact['quote'].strip() and fact['quote'] in row['source_excerpts'][index]['excerpt'])
        actions=row['actions'];_require(isinstance(actions,list) and 1<=len(actions)<=3)
        for number,action in enumerate(actions,1):
            _require(action['id']=='A'+str(number) and action['interpretation']=='UNVALIDATED_CONDITIONAL_PROPOSAL')
            _require(isinstance(action['text'],str) and action['text'].strip())
            for key in ('choose_if','stop_if','uncertain_alternative'):_texts(action[key])
            refs=action['source_fact_refs'];_require(isinstance(refs,list) and refs and all(type(i) is int and 0<=i<len(facts) for i in refs))
    return deepcopy(packet)


def load_packet():
    return validate_packet(json.loads((ROOT/PACKET).read_text(encoding='utf-8')))


def review_receipts(packet):
    """Receipt roles have different jobs; no voting or promotion operation."""
    raw_sha=hashlib.sha256((ROOT/PACKET).read_bytes()).hexdigest()
    _require(digest(packet)==digest(load_packet()))
    result={}
    for role,filename,reviewer in [('EVIDENCE','evidence-review.json','/root/pilot_data_scope'),('TACTICAL','tactical-review.json','/root/pilot_tactical_review')]:
        receipt=json.loads((ROOT/'evidence/quality-pilot'/filename).read_text())
        _require(receipt['schema_version']=='quality-pilot.review.v1' and receipt['role']==role and receipt['reviewer']==reviewer and receipt['packet_sha256']==raw_sha)
        _require(len(receipt['rows'])==7 and {r['id'] for r in receipt['rows']}=={r['id'] for r in packet['rows']})
        for row in packet['rows']:
            matches=[r for r in receipt['rows'] if r['id']==row['id']]
            _require(len(matches)==1 and matches[0]['candidate_sha256']==digest(row))
            if role=='EVIDENCE':_require(matches[0]['facts_verdict']=='PASS' and not matches[0]['unsupported_claims'])
            else:_require(matches[0]['tactical_verdict']=='HOLD' and matches[0]['conditions_review']=='PASS')
        result[role]=receipt
    return result


def cards_for_draft(draft,*,packet=None,withdrawn=None,rejected=None):
    """Static draft applicability; the app never claims observed skill states."""
    if draft['phase']!='PRE_GAME' or draft['patch']!='16.20':return [],set()
    try:
        packet=validate_packet(packet) if packet is not None else load_packet()
        receipts=review_receipts(packet)
    except (OSError,ValueError,KeyError,TypeError,IndexError):
        return [],set()
    from .pregame_evaluator import _Facts
    from .pc_coach import _card
    originals={r['id']:r for r in json.loads((ROOT/LEGACY).read_text())['rows']}
    facts=_Facts(draft,{})
    blocked=set(withdrawn or ())|set(rejected or ())
    cards=[];replaced=set()
    for row in packet['rows']:
        old=originals[row['legacy_id']];spec=old['spec']
        if row['legacy_id'] in blocked or draft['my_position'] not in spec['positions']:continue
        if any(facts.predicate(p)!='TRUE' for p in spec['conditions']):continue
        if any(facts.predicate(p)!='FALSE' for p in spec['counterconditions']+spec['stop_conditions']):continue
        details=['상황: '+row['scenario']]
        for action in row['actions']:
            details += ['선택 '+action['id']+': '+action['text'],'선택 조건(모두): '+' / '.join(action['choose_if']),
                '중단 조건(하나라도): '+' / '.join(action['stop_if']),'불확실할 때: '+' / '.join(action['uncertain_alternative'])]
        details += ['상대 권리: '+row['opponent_right'],'출처가 확인한 사실: '+' / '.join(f['claim'] for f in row['source_facts']),
            '행동 해석: 미검토 조건부 후보입니다. 사실 확인은 전술 효용·안전·실경기 효과 검증이 아닙니다.',
            '보류 이유·필요한 자료: '+' / '.join(row['needed_evidence']),'한계: '+' / '.join(row['limitations']),
            '이전 조언: '+row['legacy_id']+' · 새 문장은 기존 자동 검토나 사용자 승인을 승계하지 않습니다.']
        card=_card(row['id'],'선택과 대안 · '+row['legacy_id'],'HYPOTHESIS',
            [row['scenario'],row['actions'][0]['text'],'불확실할 때: '+row['actions'][0]['uncertain_alternative'][0]],
            '\n'.join(details),row['sources'],section=spec['section'],revision_of=row['legacy_id'],
            candidate_id=row['id'],candidate_sha256=digest(row),topic=row['topic'],topic_label=TOPICS[row['topic']])
        cards.append(card);replaced.add(row['legacy_id'])
    return cards,replaced
