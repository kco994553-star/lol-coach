"""Curated guide judgments. No statistical ranking, tactical approval, or network."""
from copy import deepcopy
from datetime import datetime
import hashlib
import re
from urllib.parse import urlsplit

POSITIONS = {'TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'}
CATEGORIES = {'Extreme', 'Major', 'Even', 'Minor', 'Tiny'}
HASH = re.compile(r'^[0-9a-f]{64}$')
LIMITS = [
    '공략 저자의 의견을 조건부로 풀어 쓴 참고 자료입니다. 전술 효과와 승패를 검증하지 않았습니다.',
    '승률이나 티어 필터로 계산한 상성이 아닙니다. 같은 분류 안의 순위는 확인되지 않았습니다.',
    '근거가 부족하면 다섯 개를 채우지 않습니다. 전체 구간 평가는 라인 상성 목록에서 제외합니다.',
    '공략의 26.x 표기와 공식 16.x 패치의 대응 및 개별 문단 갱신일은 미확인입니다.',
    '이유는 저자 설명의 요약이며 행동과 재검토 조건은 AI의 조건부 해석입니다.',
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, required, optional=()):
    _require(type(value) is dict and set(required) <= set(value)
             and set(value) <= set(required) | set(optional), 'invalid fields')


def _text(value):
    return type(value) is str and bool(value.strip()) and len(value) <= 2000


def _url(value):
    _require(type(value) is str, 'invalid source URL')
    u = urlsplit(value)
    _require(u.scheme == 'https' and u.hostname == 'www.mobafire.com'
             and u.username is None and u.password is None and u.port is None
             and not u.query and not u.fragment and u.path.startswith('/league-of-legends/build/'),
             'unsafe or unsupported public source')


def _select(records, champion, position):
    scoped = [deepcopy(r) for r in records if r['champion'] == champion and r['position'] == position]
    scope = 'JUNGLE' if position == 'JUNGLE' else 'LANING'
    eligible = [r for r in scoped if r['publication_eligibility'] == 'CONDITIONAL_CANDIDATE'
                and r['assessment_scope'] == scope]
    difficult = sorted((r for r in eligible if r['qualitative_difficulty'] == 'DIFFICULT'),
                       key=lambda r: (['Extreme', 'Major'].index(r['author_category']), r['opponent']))[:5]
    easier = sorted((r for r in eligible if r['qualitative_difficulty'] == 'RELATIVELY_EASIER_CONDITIONAL'),
                    key=lambda r: (['Tiny', 'Minor'].index(r['author_category']), r['opponent']))[:5]
    references = sorted((r for r in scoped if r['publication_eligibility'] == 'REFERENCE_ONLY'),
                        key=lambda r: r['opponent'])
    coverage = {'status': 'PARTIAL_RESEARCH' if scoped else 'NO_RESEARCH',
                'position': position, 'difficult_count': len(difficult), 'easier_count': len(easier),
                'reference_only_count': len(references),
                'difficult_opponents': [r['opponent'] for r in difficult],
                'easier_opponents': [r['opponent'] for r in easier],
                'fewer_than_five': len(difficult) < 5 or len(easier) < 5}
    return {'difficult': difficult, 'easier': easier, 'conditional': difficult + easier,
            'references': references, 'coverage': coverage, 'limits': list(LIMITS)}


def select_knowledge(index, champion, position):
    """Select at most five unranked examples per bucket, without tier context."""
    _require(type(index) is dict and index.get('schema_version') == 'champion-matchup-knowledge-v1',
             'invalid knowledge index')
    _require(type(champion) is str and champion in index['champion_ids']
             and type(position) is str and position in POSITIONS, 'canonical selection required')
    return _select(index['records'], champion, position)


def build_knowledge(config, catalog, retained_knowledge):
    """Validate the allowlisted paraphrase config and create a public projection."""
    _keys(config, ['schema_version', 'version', 'catalog_patch', 'sources', 'records'])
    _require(config['schema_version'] == 'champion-matchup-references-v1'
             and config['version'] == '1' and config['catalog_patch'] == catalog['source_patch'],
             'knowledge/catalog version mismatch')
    _require(type(catalog['champions']) is dict and all(
        re.fullmatch(r'[A-Za-z][A-Za-z0-9]{0,59}', c) and row['id'] == c
        for c, row in catalog['champions'].items()), 'invalid canonical catalog')
    champion_ids = sorted(catalog['champions'])
    existing = {s['url']: s['id'] for s in retained_knowledge['sources']}
    sources = {}
    _require(type(config['sources']) is list and type(config['records']) is list, 'lists required')
    for s in config['sources']:
        _keys(s, ['id', 'author', 'title', 'url', 'final_url', 'html_sha256', 'retrieved_at',
                  'access_status', 'author_patch_label', 'page_updated_at', 'paragraph_updated_at',
                  'patch_namespace_mapping', 'expertise', 'source_kind'])
        _url(s['url']); _url(s['final_url'])
        expected_id = existing.get(s['url'], 'matchup-guide:' + hashlib.sha256(s['url'].encode()).hexdigest()[:16])
        _require(s['id'] == expected_id and s['id'] not in sources, 'source identity conflict')
        _require(all(_text(s[k]) for k in ['author', 'title', 'expertise', 'author_patch_label'])
                 and type(s['html_sha256']) is str
                 and HASH.fullmatch(s['html_sha256']) is not None, 'source provenance required')
        try:
            retrieved = datetime.fromisoformat(s['retrieved_at'])
            _require(retrieved.tzinfo is not None, 'retrieval timezone required')
        except (TypeError, ValueError):
            raise ValueError('invalid source retrieval date') from None
        _require(s['access_status'] == 'PUBLIC_HTTPS_ORIGINAL_READ'
                 and s['source_kind'] == 'AUTHOR_GUIDE_OPINION'
                 and s['patch_namespace_mapping'] == 'UNVERIFIED_IF_DIFFERENT'
                 and s['paragraph_updated_at'] is None
                 and (s['page_updated_at'] is None or _text(s['page_updated_at'])), 'invalid source scope')
        sources[s['id']] = deepcopy(s)
    records, seen = [], set()
    for r in config['records']:
        _keys(r, ['id', 'champion', 'position', 'opponent', 'opponent_position', 'assessment_scope',
                  'author_category', 'qualitative_difficulty', 'publication_eligibility',
                  'assessment_origin', 'reason', 'action', 'change_if', 'evidence', 'patch_scope',
                  'scope_note', 'tactical_validation', 'source_refs'])
        _require(type(r['champion']) is str and r['champion'] in champion_ids
                 and type(r['opponent']) is str and r['opponent'] in champion_ids
                 and type(r['position']) is str and r['position'] in POSITIONS
                 and r['opponent_position'] == r['position'], 'canonical same-position record required')
        stable_id = ':'.join([r['champion'], r['position'], r['opponent']])
        _require(r['id'] == stable_id and stable_id not in seen, 'duplicate or unstable matchup identity')
        seen.add(stable_id)
        _require(type(r['author_category']) is str and r['author_category'] in CATEGORIES
                 and type(r['assessment_origin']) is str
                 and r['assessment_origin'] in ['SOURCE_PARAPHRASE', 'AI_INTERPRETATION']
                 and r['tactical_validation'] == 'UNREVIEWED' and _text(r['scope_note']), 'invalid assessment')
        _require(type(r['source_refs']) is list and bool(r['source_refs'])
                 and all(type(x) is str for x in r['source_refs'])
                 and len(set(r['source_refs'])) == len(r['source_refs'])
                 and all(x in sources for x in r['source_refs']), 'unknown source reference')
        expected_scope = 'JUNGLE' if r['position'] == 'JUNGLE' else 'LANING'
        if r['publication_eligibility'] == 'CONDITIONAL_CANDIDATE':
            _require(r['assessment_scope'] == expected_scope, 'wrong assessment phase')
            allowed = {'DIFFICULT': {'Extreme', 'Major'},
                       'RELATIVELY_EASIER_CONDITIONAL': {'Tiny', 'Minor'}}
            _require(type(r['qualitative_difficulty']) is str and r['qualitative_difficulty'] in allowed and
                     r['author_category'] in allowed[r['qualitative_difficulty']], 'conflicting bucket')
        else:
            _require(r['publication_eligibility'] == 'REFERENCE_ONLY'
                     and r['assessment_scope'] == 'OVERALL_UNSPECIFIED'
                     and r['qualitative_difficulty'] == 'UNKNOWN_FOR_SCOPE', 'invalid reference-only record')
        e = r['evidence']
        _keys(e, ['quote_id', 'locator', 'quote_sha256', 'paragraph_sha256', 'html_line',
                  'paragraph_id', 'quote_matching_status'])
        _require(e['quote_id'] == stable_id + ':q1' and e['paragraph_id'] == stable_id + ':paragraph'
                 and _text(e['locator']) and type(e['html_line']) is int and e['html_line'] > 0
                 and type(e['quote_sha256']) is str and HASH.fullmatch(e['quote_sha256'])
                 and type(e['paragraph_sha256']) is str and HASH.fullmatch(e['paragraph_sha256'])
                 and e['quote_matching_status'] == 'MATCHED_NORMALIZED_HTML_PARAGRAPH', 'invalid quote proof')
        for field in ['reason', 'action', 'change_if']:
            f = r[field]
            _keys(f, ['text_ko', 'origin', 'source_quote_refs'])
            _require(_text(f['text_ko']) and re.search('[가-힣]', f['text_ko'])
                     and len(f['text_ko']) <= 500
                     and f['origin'] in ['SOURCE_PARAPHRASE', 'AI_PARAPHRASE_OF_AUTHOR',
                                         'AI_CONDITIONAL_INTERPRETATION_OF_AUTHOR', 'AI_LIMITING_CONDITION']
                     and f['source_quote_refs'] == [e['quote_id']], 'invalid paraphrase provenance')
        patch = r['patch_scope']
        _keys(patch, ['riot_catalog', 'source_label', 'namespace_mapping', 'paragraph_refresh_date'])
        _require(patch['riot_catalog'] == config['catalog_patch'] and _text(patch['source_label'])
                 and patch['namespace_mapping'] == 'UNVERIFIED_IF_DIFFERENT'
                 and patch['paragraph_refresh_date'] is None, 'unverified source patch scope required')
        records.append(deepcopy(r))
    records.sort(key=lambda r: r['id'])
    coverage = {c: _select(records, c, p)['coverage'] for c, p in sorted(
        {(r['champion'], r['position']) for r in records})}
    return {'schema_version': 'champion-matchup-knowledge-v1', 'version': config['version'],
            'catalog_patch': config['catalog_patch'], 'tier_independent': True,
            'derived_from_statistics': False, 'coaching': False, 'tactical_validation': 'UNREVIEWED',
            'champion_ids': champion_ids, 'sources': [sources[k] for k in sorted(sources)],
            'records': records, 'coverage': coverage, 'limits': list(LIMITS)}
