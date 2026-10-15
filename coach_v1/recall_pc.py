"""Read-only V6 projection. Shop events describe observed purchases, not advice."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

from .storage import ServiceError

ROOT = Path(__file__).resolve().parents[1]
POPULATIONS = ('CHALLENGER', 'PRO_REFERENCE')
NAMES = {'CHALLENGER': '챌린저 모집 경기', 'PRO_REFERENCE': '선택한 프로 기준 선수'}
LIMITATION = '구매 시각으로 추정한 귀환입니다. 구매 없는 귀환·웨이브·상대 의도는 알 수 없습니다. 마지막 수신 프레임 이전까지만 집계하며 끝 구간은 제외합니다.'


def validate_request(body):
    fields = {'champion', 'position', 'patch', 'opponent_champion'}
    if not isinstance(body, dict) or set(body) != fields:
        raise ServiceError(422, 'INVALID_RECALL_REQUEST')
    def champion(value, nullable=False):
        return nullable and value is None or isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,99}', value)
    if (not champion(body['champion']) or not champion(body['opponent_champion'], True)
            or body['position'] not in ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')
            or body['patch'] is not None and (not isinstance(body['patch'], str) or not re.fullmatch(r'\d{1,3}\.\d{1,3}(?:\.\d{1,3})?', body['patch']))):
        raise ServiceError(422, 'INVALID_RECALL_REQUEST')
    return dict(body, patch='.'.join(body['patch'].split('.')[:2]) if body['patch'] else None)


def load_datasets(server):
    """Local files only; newest valid archive per population, no provider calls."""
    from .recall_stats import validate_dataset
    datasets = {}
    statuses = {}
    folders = sorted((ROOT / 'data/recall').glob('20??-??-??'), reverse=True)
    for population, name in [('CHALLENGER', 'challenger'), ('PRO_REFERENCE', 'pro')]:
        for folder in folders:
            path = folder / name / 'recall-data.json'
            if not path.exists():
                continue
            try:
                if path.is_symlink() or path.stat().st_size > 12_000_000:
                    raise ValueError('bounded archive required')
                data = validate_dataset(json.loads(path.read_text(encoding='utf-8')))
                if data['population'] != population:
                    raise ValueError('population mismatch')
                datasets[population] = data
                statuses[population] = 'AVAILABLE'
            except (OSError, ValueError, KeyError, TypeError):
                statuses[population] = 'INVALID_NEWEST_ARCHIVE'
            # An invalid newest archive cannot silently select old evidence.
            break
    server.recall_datasets = datasets
    server.recall_data_status = statuses
    return statuses


def _unknown(population, request, reason):
    return dict(status='UNKNOWN', population=population, patch=request['patch'],
                champion=request['champion'], position=request['position'], scope='UNKNOWN', reason=reason,
                sample=dict(matches=0, participant_observations=0), first_recall=None, low_health=None,
                sensitivity=[], limitations=[LIMITATION])


def purchase_summary(purchases, items):
    """Nominal full costs only. Unknown owned components prohibit exact target."""
    result = dict(item_ids=[], item_names=[], reference_gold=None, count=0, exact_required_gold_known=False,
                  limitation='보유 부품·할인·기존 골드를 알 수 없어 구매 순간 필요 골드는 미확인입니다.')
    if not purchases:
        return result
    selected = sorted(purchases, key=lambda p: (-p['count'], tuple(p['item_ids'])))[0]
    result.update(item_ids=selected['item_ids'], count=selected['count'])
    if not items.get('prices_usable'):
        return result
    index = {str(i['id']): i for i in items.get('items', [])}
    rows = [index.get(str(i)) for i in selected['item_ids']]
    result['item_names'] = [r['name'] if r else '아이템 ' + str(i) for i, r in zip(selected['item_ids'], rows)]
    if rows and all(r is not None for r in rows):
        result['reference_gold'] = sum(r['gold']['total'] for r in rows)
    return result


def reference_response(server, body):
    request = validate_request(body)
    services = getattr(server, 'pc_services', None)
    if services and services.snapshot().get('phase') not in (None, 'ChampSelect'):
        return dict(schema_version='recall-reference.v1',own=[],opponent=[],markers=[],items={},
            suppressed=True,reason='NOT_CHAMP_SELECT',descriptive_only=True,coaching_accuracy=None)
    from .official_items import items_response
    items = items_response(request['patch'])
    if not hasattr(server, 'recall_datasets'):
        load_datasets(server)
    from .recall_stats import recall_view
    result = dict(schema_version='recall-reference.v1', own=[], opponent=[], markers=[], items=items,
                  descriptive_only=True, coaching_accuracy=None)
    for population in POPULATIONS:
        data = server.recall_datasets.get(population)
        for who, champion in [('own', request['champion']), ('opponent', request['opponent_champion'])]:
            if not champion:
                continue
            query = dict(request, champion=champion)
            if data is None:
                view = _unknown(population, query, getattr(server, 'recall_data_status', {}).get(population, 'RECALL_DATA_NOT_AVAILABLE'))
            elif request['patch'] is None:
                view = _unknown(population, query, 'PATCH_UNKNOWN')
            else:
                view = recall_view(data, champion=champion, position=request['position'], patch=request['patch'])
                # Bind the precise immutable public dataset, never just its title.
                view = dict(view, dataset_sha256=hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest())
            first = view.get('first_recall')
            if view['status'] == 'AVAILABLE' and first:
                view['purchase_summary'] = purchase_summary(first.get('purchases', []), items)
                timing = first.get('timing', {})
                minute = _minutes(timing.get('median'), timing.get('unit'))
                if minute is not None and timing.get('status') == 'AVAILABLE':
                    result['markers'].append(dict(minute=minute, who=who.upper(), population=population,
                        label=('내 챔피언' if who == 'own' else '맞라이너') + ' 첫 구매 중앙값 · ' + NAMES[population] + ' · 귀환 추정'))
            result[who].append(view)
    return result


def _minutes(value, unit):
    if type(value) not in (int, float) or not math.isfinite(value):
        return None
    return value / 60000 if unit in ('MILLISECONDS', 'MS', 'MILLISECOND') else value / 60 if unit in ('SECONDS', 'SECOND') else value if unit in ('MINUTES', 'MINUTE') else None


def _number(value):
    return str(round(value, 1)) if type(value) in (int, float) and math.isfinite(value) else '미확인'


def outcome_lines(group):
    names = {'self_deaths':'본인 사망', 'opponent_other_lane_involvements':'맞라이너의 다른 라인 킬 관여',
        'opponent_plates':'상대 팀 방패 파괴', 'opponent_jungle_objectives':'상대 팀 정글 오브젝트'}
    result = []
    for key, label in names.items():
        metric = group.get('outcomes', {}).get(key, {})
        value = metric.get('mean') if metric.get('status') == 'AVAILABLE' else None
        result.append(label + ': 관측 창당 평균 ' + _number(value) + '건 · 유효 ' + str(metric.get('n', 0))
            + '경기 / ' + str(metric.get('participant_n', 0)) + '참가자 창 · 누락 ' + str(metric.get('missing_n', 0)))
    return result


def _sources(view, items):
    result = []
    if view.get('dataset_sha256'):
        result.append(dict(url='https://developer.riotgames.com/apis#match-v5', title='Riot 경기 타임라인 · 익명 집계',
            patch=view['patch'], sha256=view['dataset_sha256'], locator=view['population'] + ' / ' + view['scope'] + ' / ' + view['position']))
    source = items.get('source')
    if source and source.get('sha256'):
        result.append(dict(url=source['url'], title='공식 한국어 아이템 가격', patch=source.get('version'), sha256=source['sha256']))
    return result


def cards_for_draft(server, draft):
    if draft['phase'] != 'PRE_GAME' or not draft['patch'] or not draft['my_champion'] or not draft['my_position']:
        return []
    from .pc_coach import _card
    opponent = next((s['champion'] for s in draft['slots'] if s['side'] == 'ENEMY' and s['position'] == draft['my_position']), None)
    response = reference_response(server, dict(champion=draft['my_champion'], position=draft['my_position'], patch=draft['patch'], opponent_champion=opponent))
    cards = []
    for who, views in [('own', response['own']), ('opponent', response['opponent'])]:
        for view in views:
            population = view['population']
            cid = 'recall-' + population + '-' + who
            title = ('내 챔피언' if who == 'own' else '맞라이너') + ' 첫 귀환 · ' + NAMES[population]
            sources = _sources(view, response['items'])
            if view['status'] != 'AVAILABLE' or not view.get('first_recall'):
                cards.append(_card(cid, title, 'UNKNOWN', ['귀환 시각·골드·첫 구매는 미확인입니다.', '같은 패치와 포지션의 유효 표본이 필요합니다.', '비어 있는 자료를 0으로 바꾸지 않습니다.'],
                    '미확인 사유: ' + str(view.get('reason')) + '\n' + LIMITATION, sources, section='RECALL'))
                continue
            first = view['first_recall'];timing = first['timing'];gold = first['current_gold'];purchase = view['purchase_summary']
            minute = _minutes(timing.get('median'), timing.get('unit')) if timing.get('status') == 'AVAILABLE' else None
            lines = ['첫 구매 중앙값 ' + _number(minute) + '분 · 귀환 추정',
                     '직전 수신 골드 중앙값 ' + _number(gold.get('median') if gold.get('status') == 'AVAILABLE' else None) + ' · 구매 순간은 미확인',
                     ('포지션 전체로 보충 · ' if view['scope'] == 'ROLE' else '동일 챔피언 · ') + str(view['sample']['matches']) + '경기 · 좋은 시점 판정 아님']
            detail = [LIMITATION, '시각 Q1~Q3: ' + _number(_minutes(timing.get('q1'), timing.get('unit')) if timing.get('status') == 'AVAILABLE' else None) + '~' + _number(_minutes(timing.get('q3'), timing.get('unit')) if timing.get('status') == 'AVAILABLE' else None) + '분',
                      '첫 구매 표본: ' + str(timing['n']) + ' · 누락: ' + str(timing['missing_n']),
                      '직전 수신 골드 Q1~Q3: ' + _number(gold.get('q1') if gold.get('status') == 'AVAILABLE' else None) + '~' + _number(gold.get('q3') if gold.get('status') == 'AVAILABLE' else None),
                      '골드 유효 ' + str(gold['match_n']) + '경기 / ' + str(gold['n']) + '참가자 · 누락 ' + str(gold['missing_n']),
                      '관측 최빈 구매 묶음: ' + (', '.join(purchase['item_names']) or ', '.join(str(i) for i in purchase['item_ids']) or '미확인'),
                      '공식 기본 가격 합계(참고): ' + _number(purchase['reference_gold']), purchase['limitation'],
                      '먼저 구매한 뒤 120초 동안의 관측(실제 주도권 공백은 미확인):',
                      *outcome_lines(first.get('priority_gap', {})),
                      '최소 표본은 유효 5경기라는 출력 규칙이며 충분한 통계 표본을 보장하지 않습니다. 모집단과 패치를 합치지 않습니다.']
            card = _card(cid, title, 'STATISTICS', lines, '\n'.join(detail), sources, section='RECALL')
            card['graph'] = _resource_graph(server, dict(draft,my_champion=view['champion']), response['markers'], population)
            if card['graph'].get('source'):
                card['sources'].append(card['graph']['source'])
            cards.append(card)
            if who == 'own':
                low = view.get('low_health') or {}
                details = ['이후 결과의 관측 경향이며 귀환과 잔류 중 정답을 판정하지 않습니다.',
                    '저체력은 수신 시점 체력 30% 이하, 결과 창은 120초라는 분석 규칙입니다. 게임 권장 수치가 아닙니다.',
                    '분 단위 체력 사이의 변화·웨이브·상대 의도는 미확인입니다.',
                    '저체력 관측 뒤 120초 중 구매가 관측된 구간(구매 전 사건도 포함):', *outcome_lines(low.get('purchase', {})),
                    '저체력 관측 뒤 120초 중 다음 프레임 라인 잔류가 관측된 구간:', *outcome_lines(low.get('stay', {})),
                    '제외된 관측: ' + str(sum(r['count'] for r in low.get('excluded', []))) + '개 · 체력·위치 누락과 사망 뒤 구매 등을 제외합니다.',
                    '같은 사건이 여러 참가자의 관측 창에 잡힐 수 있습니다. 경기별 평균을 먼저 계산합니다.',
                    '민감도: 체력 20%·30%·40%, 이후 60·120·180초로 구간을 바꾼 집계도 보존합니다. 선택 편향이 있어 행동의 효과로 읽지 않습니다.']
                low_level = 'STATISTICS' if low.get('purchase', {}).get('matches', 0) or low.get('stay', {}).get('matches', 0) else 'UNKNOWN'
                cards.append(_card('low-health-' + population, '저체력 귀환·잔류 관측 · ' + NAMES[population], low_level,
                    ['체력이 낮았던 수신 프레임 이후의 관측입니다.', '귀환은 구매로 추정하고, 잔류는 다음 라인 위치로 확인합니다.', '사망·상대 관여·방패·오브젝트를 따로 비교합니다.'], '\n'.join(details), sources, section='LOW_HEALTH'))
    if not any(c['section'] == 'LOW_HEALTH' for c in cards):
        cards.append(_card('low-health-unknown', '저체력 귀환·잔류 관측', 'UNKNOWN', ['체력과 구매 이벤트가 있는 실제 표본을 기다립니다.', '현재 체력이나 상대의 의도를 추측하지 않습니다.', '경기 전 계획과 경기 후 복기에만 사용합니다.'], LIMITATION, [], section='LOW_HEALTH'))
    for card in cards:
        card['patch_status'] = response['items'].get('patch_status', 'GAME_PATCH_UNKNOWN')
    return cards


def _resource_graph(server, draft, markers, population):
    from .pregame_server import power_response
    response = power_response(server, dict(champion=draft['my_champion'], position=draft['my_position'], patch=draft['patch'], tier='CHALLENGER', opponent_champion=None))
    view = response['view'];points = view.get('points', [])
    plotted = {p['minute']:p.get('mean') if p.get('visible') else None for p in points if p['metric'] == 'gold_delta'}
    for reason in view.get('reasons', []):
        match = re.fullmatch(r'INSUFFICIENT_AT_MINUTE:(\d+):gold_delta', reason)
        if match:
            plotted[int(match[1])] = None
    source = dict(url='https://developer.riotgames.com/apis#match-v5',title='Q15 챌린저 모집 경기 · 자원 변화',
        patch=draft['patch'],sha256=view['dataset_digest'],locator=draft['my_champion']+' / '+draft['my_position']) if view.get('dataset_digest') else None
    return dict(title=draft['my_champion'] + ' · Q15 챌린저 자원 변화 · ' + NAMES[population] + ' 귀환 구매 시각 참고', units='골드/분 차이',source=source,
        points=[dict(minute=minute, value=value) for minute,value in sorted(plotted.items())],
        markers=[m for m in markers if m['population'] == population])


def private_context(match, timeline, participant_id):
    """Individual observations never masquerade as a Challenger/pro sample."""
    from .recall_stats import extract_private_context
    observation = extract_private_context(match, timeline, participant_id)
    signals = []
    first = observation['first_recall'];gap = first.get('priority_gap') or {}
    if gap.get('status') == 'OBSERVED':
        signals.append(dict(type='FIRST_RECALL_PRIORITY_GAP', label='선귀환 주도권 공백 후보',
            minute=first['timestamp_ms']/60000, inference='OBSERVED_CONTEXT_NOT_MISTAKE',
            description='맞라이너보다 먼저 구매한 기록입니다. 웨이브와 실제 주도권은 미확인입니다.'))
    low = observation['low_health'];outcomes = low.get('outcomes') or {}
    if low['status'] == 'OBSERVED':
        kind = None
        if low['action'] == 'STAY' and (outcomes.get('self_deaths', {}).get('value') or 0) > 0:
            kind = ('LOW_HEALTH_STAY_DEATH','저체력 잔류 후 사망','다음 라인 위치와 이후 사망이 관측되었습니다. 잔류가 사망의 원인이라는 판정은 아닙니다.')
        elif low['action'] == 'PURCHASE' and (low.get('post_action_outcomes', {}).get('opponent_other_lane_involvements', {}).get('value') or 0) > 0:
            kind = ('LOW_HEALTH_RECALL_OPPONENT_ROAM','저체력 귀환 중 상대 다른 라인 관여','구매로 추정한 귀환 뒤 맞라이너의 다른 라인 킬 관여가 관측되었습니다. 의도는 알 수 없습니다.')
        if kind:
            signals.append(dict(type=kind[0],label=kind[1],minute=low['timestamp_ms']/60000,
                inference='OBSERVED_CONTEXT_NOT_MISTAKE',description=kind[2]))
    return dict(status='OBSERVED',first_recall=first,low_health=low,signals=signals,
        limitations=[LIMITATION,'체력·위치는 분 단위 수신 자료이며 정확한 순간이나 의도를 복원하지 않습니다.'])
