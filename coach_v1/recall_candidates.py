"""New V6 hypotheses, separate from user approvals and the completed v2.1 packet."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .auto_review import FIELDS
from .state import digest

ROOT = Path(__file__).resolve().parents[1]
PACKET = 'knowledge_candidates/recall-v23.json'
REVIEWERS = {'EVIDENCE': '/root/recall_evidence', 'COUNTER': '/root/recall_counter'}


def load_packet():
    return json.loads((ROOT / PACKET).read_text(encoding='utf-8'))


def check_sources(row):
    reasons = []
    for source in row.get('sources', []):
        try:
            version = source['patch'];champion = row['champion']
            expected = f'data/official_catalog/versions/{version}/{champion}-{version}.ko_KR.json'
            if (not re.fullmatch(r'\d{1,3}\.\d{1,3}\.\d{1,3}', version)
                    or not re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,29}', champion)
                    or source['path'] != expected or (ROOT / expected).is_symlink()
                    or source['url'] != f'https://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion/{champion}.json'):
                raise ValueError('source identity')
            raw = (ROOT / expected).read_bytes()
            if hashlib.sha256(raw).hexdigest() != source['sha256']:
                raise ValueError('source hash')
            value = json.loads(raw)
            if value['version'] != version or not source['locator'].startswith(f'data.{champion}.'):
                raise ValueError('locator')
            for part in source['locator'].split('.'):
                value = value[int(part)] if isinstance(value, list) else value[part]
            # Authored quotes are literal archived descriptions, including markup.
            if not isinstance(value, str) or value != source['excerpt'] or not value.strip():
                raise ValueError('quote')
        except (OSError, ValueError, KeyError, TypeError, IndexError):
            reasons.append('SOURCE_LINK_HASH_PATCH_OR_EXCERPT_INVALID')
    if not row.get('sources'):
        reasons.append('SOURCE_REQUIRED')
    return list(dict.fromkeys(reasons))


def _receipts():
    directory = ROOT / 'evidence/queue/v23'
    try:
        manifest = json.loads((directory / 'candidate-review-manifest.json').read_text())
        if manifest['packet_sha256'] != hashlib.sha256((ROOT / PACKET).read_bytes()).hexdigest():
            return []
        result = []
        for filename in ('candidate-evidence-review.json', 'candidate-counter-review.json'):
            raw = (directory / filename).read_bytes()
            if hashlib.sha256(raw).hexdigest() == manifest['files'][filename]:
                result.append(json.loads(raw))
        return result
    except (OSError, ValueError, KeyError, TypeError):
        return []


def assess_candidates(packet=None, *, receipts=None):
    packet = load_packet() if packet is None else packet
    receipts = _receipts() if receipts is None else receipts
    packet_sha = hashlib.sha256((ROOT / PACKET).read_bytes()).hexdigest() if digest(packet) == digest(load_packet()) else None
    rows = []
    for row in packet['rows']:
        reasons = check_sources(row)
        if set(row.get('advice', {})) != FIELDS or any(not isinstance(v, str) or not v.strip() for v in row.get('advice', {}).values()):
            reasons.append('SEVEN_FIELDS_REQUIRED')
        # A known source gap is a veto, regardless of how many reviewers agree.
        # Authored pre-review notes remain in the frozen packet history. Once
        # receipts exist, current reasons come from the actual role outcomes.
        reasons.extend(r for r in row.get('hold_reasons', []) if '독립 근거 검사' not in r)
        if row.get('value') is not None and row['kind'] == 'CLASSIFICATION':
            reasons.append('COMPARATIVE_CLASSIFICATION_REQUIRES_MEASURED_SUPPORT')
        for role, reviewer in REVIEWERS.items():
            matching = [r for r in receipts if r.get('role') == role and r.get('reviewer') == reviewer and r.get('packet_sha256') == packet_sha]
            entries = [r for r in matching[0].get('reviews', []) if r.get('id') == row['id'] and r.get('candidate_sha256') == digest(row)] if len(matching) == 1 else []
            if len(entries) != 1:
                reasons.append(role + '_REVIEW_MISSING_OR_INVALID')
            elif entries[0].get('verdict') != 'PASS' or entries[0].get('counterexamples'):
                reasons.extend(entries[0].get('reasons', []) or [role + '_HOLD'])
        reasons = list(dict.fromkeys(reasons))
        rows.append(dict(id=row['id'], candidate_sha256=digest(row), state='HOLD' if reasons else 'AUTO_VERIFIED', reasons=reasons))
    return dict(passed=sum(r['state'] == 'AUTO_VERIFIED' for r in rows), held=sum(r['state'] == 'HOLD' for r in rows),
        reasons=dict(Counter(reason for row in rows for reason in row['reasons'])), rows=rows, user_decisions_created=0)


def cards_for_draft(server, draft):
    if draft['phase'] != 'PRE_GAME' or not draft['patch'] or not draft['my_champion']:
        return []
    from .pc_coach import _card
    packet = load_packet();assessment = assess_candidates(packet);states = {r['id']:r for r in assessment['rows']}
    names = {'wave_clear_speed':'웨이브 처리 속도', 'low_health_sustain':'저체력 라인 유지력', 'opponent_finishing':'상대 마무리 능력'}
    opponents = {s['champion'] for s in draft['slots'] if s['side'] == 'ENEMY' and s['position'] == draft['my_position']}
    cards = []
    for row in packet['rows']:
        if row['champion'] != draft['my_champion'] and not (row.get('dimension') == 'opponent_finishing' and row['champion'] in opponents):
            continue
        if not all('.'.join(s['patch'].split('.')[:2]) == draft['patch'] for s in row['sources']) or check_sources(row):
            continue
        # All new candidates are currently held. Preserve this invariant until a
        # complete evidence/counter/numeric/objection contract exists for promotion.
        state = states[row['id']]
        label = 'UNKNOWN' if row['status'] == 'UNKNOWN' else 'HYPOTHESIS'
        advice = row['advice']
        title = names.get(row.get('dimension'), '귀환 계획' if row.get('section') == 'RECALL' else '저체력 잔류·귀환 조건') + ' · ' + row['champion']
        details = '\n'.join(k + ': ' + value for k, value in advice.items())
        details += '\n검토 보류: ' + ' / '.join(state['reasons'])
        for group, conditions in row.get('macro_conditions', {}).items():
            for condition in conditions:
                details += '\n' + ('검토할 조건' if group == 'good' else '피할 조건') + ' (미검토 가설): ' + condition['text']
                if condition.get('opponent_right'):details += ' / 상대 권리: ' + condition['opponent_right']
                if condition.get('invalid_if'):details += ' / 무효 조건: ' + condition['invalid_if']
        details += '\n반례: ' + ' / '.join(row.get('counterarguments', []))
        cards.append(_card('candidate-' + row['id'], title, label,
            [advice['상황'], advice['할 것'], '근거 기전만 확인 · 전투 성능 등급과 유리한 행동은 미확인'],
            details, row['sources'], section=row.get('section', 'CLASSIFICATION'), hypothesis_id=row['id']))
    return cards
