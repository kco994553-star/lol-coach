"""Deterministic public references to the existing learning registry.

No network, private store, ingestion, claim creation or review mutation lives here.
Index publication is discoverability only and never enables tactical coaching.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit

FORMAT = 'lol-coach-learning-room-v1'
REGISTRY_URL = './loading-knowledge.json'
QUESTION = '기존 적용 조건 하나가 달라지면 어떤 중단·대안을 다시 확인해야 할까요?'
CARD_FIELDS = ('question', 'goal', 'threat', 'action', 'reason', 'required_conditions',
               'stop_or_switch', 'waiting_cost', 'alternative_or_recovery', 'practice_id', 'source_refs')


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _url(value):
    parsed = urlsplit(value or '')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('INVALID_PUBLIC_SOURCE_URL')
    return value


def _unique(rows, key):
    ids = [row[key] for row in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('DUPLICATE_OR_INVALID_' + key.upper())
    return set(ids)


def _fold(value):
    return unicodedata.normalize('NFC', str(value)).casefold().strip()


def _ref(claim, field):
    return dict(claim_id=claim['id'], field=field) if claim.get(field) else None


def validate_segment(segment):
    """Project a permitted reference interval; game clock is an independent clock.

    Unknown rights permit links only, never a transcript or frame reference.
    This validator does not establish the authenticity of supplied evidence.
    """
    if segment.get('license_or_access_state') != 'PERMITTED' or segment.get('access_state') != 'PERMITTED':
        raise ValueError('SEGMENT_ACCESS_NOT_PERMITTED')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', segment.get('video_id', '')):
        raise ValueError('INVALID_VIDEO_ID')
    start, end, clock = (segment.get(k) for k in ('video_start_ms', 'video_end_ms', 'game_clock_ms'))
    if type(start) is not int or start < 0 or type(end) is not int or end <= start:
        raise ValueError('INVALID_VIDEO_INTERVAL')
    if clock is not None and (type(clock) is not int or clock < 0):
        raise ValueError('INVALID_GAME_CLOCK')
    kind = segment.get('evidence_kind')
    if kind not in ('TRANSCRIPT', 'VISUAL', 'AI_INTERPRETATION'):
        raise ValueError('INVALID_EVIDENCE_KIND')
    cues = segment.get('transcript_cue_ids', [])
    if not isinstance(cues, list) or any(not isinstance(c, str) or not c for c in cues):
        raise ValueError('INVALID_TRANSCRIPT_CUE_IDS')
    if kind == 'TRANSCRIPT' and not cues:
        raise ValueError('TRANSCRIPT_REQUIRES_CUE_REFERENCE')
    if kind == 'VISUAL' and segment.get('scene_verified') is not True:
        raise ValueError('VISUAL_REQUIRES_REVIEW')
    source_hash = segment.get('source_hash')
    if source_hash is not None and not re.fullmatch(r'[a-f0-9]{64}', source_hash):
        raise ValueError('INVALID_SOURCE_HASH')
    return dict(segment_id=segment['segment_id'], video_id=segment['video_id'], video_start_ms=start,
                video_end_ms=end, game_clock_ms=clock, transcript_cue_ids=list(cues),
                scene_verified=segment.get('scene_verified') is True,
                viewer_perspective=segment.get('viewer_perspective', 'UNKNOWN'), source_hash=source_hash,
                evidence_kind=kind, access_state='PERMITTED', license_or_access_state='PERMITTED')


def validate_index(index):
    """Check identity and references without treating them as review authority."""
    if index.get('format') != FORMAT or index.get('coaching_enabled') is not False:
        raise ValueError('LEARNING_CANNOT_ENABLE_COACHING')
    source_ids = _unique(index['sources'], 'source_id')
    video_ids = _unique(index['videos'], 'video_id')
    segment_ids = _unique(index['segments'], 'segment_id')
    lesson_ids = _unique(index['lessons'], 'lesson_id')
    practice_ids = _unique(index['practices'], 'practice_id')
    taxonomy_ids = set()
    leaves = set()
    groups = index['taxonomy']['groups']
    if len(groups) != 4:
        raise ValueError('INVALID_TAXONOMY')
    for group in groups:
        if len(group['topics']) != 5:
            raise ValueError('INVALID_TAXONOMY')
        for item in [group] + group['topics']:
            if item['id'] in taxonomy_ids:
                raise ValueError('DUPLICATE_TOPIC_ID')
            taxonomy_ids.add(item['id'])
        for topic in group['topics']:
            if len(topic['leaves']) != 4:
                raise ValueError('INVALID_TAXONOMY')
            for leaf in topic['leaves']:
                if leaf['id'] in taxonomy_ids:
                    raise ValueError('DUPLICATE_TOPIC_ID')
                taxonomy_ids.add(leaf['id'])
                leaves.add(leaf['id'])
    for source in index['sources']:
        _url(source['canonical_url'])
    for video in index['videos']:
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video['video_id']):
            raise ValueError('INVALID_VIDEO_ID')
        if video['canonical_url'] != 'https://www.youtube.com/watch?v=' + video['video_id']:
            raise ValueError('VIDEO_URL_ID_MISMATCH')
    for segment in index['segments']:
        validate_segment(segment)
        if segment['video_id'] not in video_ids:
            raise ValueError('UNKNOWN_VIDEO_REFERENCE')
    for lesson in index['lessons']:
        if lesson['coaching_enabled'] is not False:
            raise ValueError('LEARNING_CANNOT_ENABLE_COACHING')
        if lesson['primary_topic_id'] is not None and lesson['primary_topic_id'] not in leaves:
            raise ValueError('UNKNOWN_TOPIC_REFERENCE')
        if any(t not in leaves for t in lesson['secondary_topic_ids']):
            raise ValueError('UNKNOWN_TOPIC_REFERENCE')
        if not set(lesson['segment_ids']) <= segment_ids or not set(lesson['source_ids']) <= source_ids:
            raise ValueError('UNKNOWN_SOURCE_REFERENCE')
        if lesson['practice_id'] is not None and lesson['practice_id'] not in practice_ids:
            raise ValueError('UNKNOWN_PRACTICE_REFERENCE')
        if any(field not in lesson for field in CARD_FIELDS):
            raise ValueError('MISSING_CARD_FIELD')
    for practice in index['practices']:
        if practice['lesson_id'] not in lesson_ids or practice['auto_grade'] is not False or practice['coaching_enabled'] is not False:
            raise ValueError('INVALID_REFLECTION_PRACTICE')
    return index


def build_index(root, *, knowledge=None, candidates=None):
    """Read public checked-in files only; optional dicts support offline validation."""
    root = Path(root)
    topics = json.loads((root / 'config/learning_topics.json').read_text())
    if knowledge is None:
        knowledge = json.loads((root / 'web_r4/loading-knowledge.json').read_text())
    if candidates is None:
        candidates = json.loads((root / 'config/user_lesson_candidates.json').read_text())
    sources = []
    for source in knowledge['sources']:
        sources.append(dict(source_id=source['id'], title=source.get('title'),
                            canonical_url=_url(source['url']), source_patch=source.get('patch'),
                            publication_time=source.get('date'), access_state=source.get('access') or 'UNKNOWN',
                            license_or_access_state='UNKNOWN_LINK_ONLY', kind=source.get('kind') or 'SOURCE_TEXT_REFERENCE',
                            registry_ref=dict(collection='sources', id=source['id']),
                            source_hash=_hash(source), patch_compatible=None))
    source_by_id = {s['source_id']: s for s in sources}
    lessons, practices, claim_ids = [], [], set()
    for matchup in knowledge['matchups']:
        for claim in matchup['claims']:
            claim_id = claim['id']
            if claim_id in claim_ids:
                raise ValueError('DUPLICATE_CLAIM_ID')
            claim_ids.add(claim_id)
            refs = sorted(set(claim.get('source_ids', [])))
            if any(s not in source_by_id for s in refs):
                raise ValueError('UNKNOWN_CLAIM_SOURCE')
            patches = sorted({source_by_id[s]['source_patch'] for s in refs if source_by_id[s]['source_patch']})
            lesson_id = 'claim:' + claim_id
            practice_id = 'practice:' + lesson_id if claim.get('conditions') else None
            lesson = dict(lesson_id=lesson_id, title=matchup['title'] + ' · ' + claim_id,
                          primary_topic_id=topics['claim_topics'].get(claim_id), secondary_topic_ids=[],
                          champions=list(matchup.get('allies', [])), roles=[matchup['role']],
                          opponents=list(matchup.get('enemies', [])), ally_support=None, enemy_support=None,
                          situation_tags=[], phase=None, question=QUESTION if practice_id else None,
                          question_origin='APP_AUTHORED_REFLECTION_NOT_SOURCE_QUOTE' if practice_id else None,
                          goal=None, threat=None, action=_ref(claim, 'display_text' if claim.get('display_text') else 'text'),
                          reason=None, required_conditions=_ref(claim, 'conditions'),
                          stop_or_switch=_ref(claim, 'counterexamples'), waiting_cost=None,
                          alternative_or_recovery=_ref(claim, 'counterexamples'), practice_id=practice_id,
                          source_refs=[dict(source_id=s) for s in refs], claim_ids=[claim_id], source_ids=refs,
                          segment_ids=[], registry_url=REGISTRY_URL,
                          review_state=claim.get('review') or 'UNKNOWN', evidence_state='SOURCE_REFERENCE',
                          evidence_kinds=['SOURCE_TEXT_REFERENCE', 'AI_INTERPRETATION'],
                          source_patches=patches, patch_state='DECLARED_UNVERIFIED' if patches else 'UNKNOWN',
                          patch_compatible=None, patch_limits=_ref(claim, 'patch_limits'), coaching_enabled=False)
            lessons.append(lesson)
            if practice_id:
                practices.append(dict(practice_id=practice_id, lesson_id=lesson_id, claim_ids=[claim_id],
                                      kind='CONDITION_CHANGE_REFLECTION', question=QUESTION,
                                      question_origin='APP_AUTHORED_REFLECTION_NOT_SOURCE_QUOTE',
                                      condition_ref=_ref(claim, 'conditions'),
                                      counterexample_ref=_ref(claim, 'counterexamples'), auto_grade=False, coaching_enabled=False))
    videos = []
    metadata = candidates.get('metadata_attempts', {})
    attempted_ids = set(metadata.get('urls', []))
    for candidate in candidates['candidates']:
        video_id = candidate['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise ValueError('INVALID_VIDEO_ID')
        url = 'https://www.youtube.com/watch?v=' + video_id
        if candidate['url'] != url:
            raise ValueError('VIDEO_URL_ID_MISMATCH')
        attempted = video_id in attempted_ids or candidate['url'] in attempted_ids
        videos.append(dict(video_id=video_id, canonical_url=url, title=None, channel_id=None,
                           publication_time=None, source_patch=None, language=None,
                           license_or_access_state='UNKNOWN_LINK_ONLY', access_state='UNKNOWN',
                           transcript_state='UNKNOWN', scene_state='UNKNOWN', patch_state='UNKNOWN',
                           acquisition=dict(state='NOT_ACQUIRED', attempted=attempted,
                                            reason=metadata.get('result', 'UNKNOWN') if attempted else 'NOT_ATTEMPTED'),
                           source_hash=_hash(candidate)))
        sid = 'youtube:' + video_id
        sources.append(dict(source_id=sid, title=None, canonical_url=url, source_patch=None,
                            publication_time=None, access_state='UNKNOWN', license_or_access_state='UNKNOWN_LINK_ONLY',
                            kind='YOUTUBE_LINK_ONLY', source_hash=_hash(candidate), patch_compatible=None))
        lessons.append(dict(lesson_id='video:' + video_id, title='강의 후보 · ' + video_id,
                            primary_topic_id=None, secondary_topic_ids=[], champions=[], roles=[], opponents=[],
                            ally_support=None, enemy_support=None, situation_tags=[], phase=None,
                            question=None, goal=None, threat=None, action=None, reason=None, required_conditions=None,
                            question_origin=None,
                            stop_or_switch=None, waiting_cost=None, alternative_or_recovery=None, practice_id=None,
                            source_refs=[dict(source_id=sid)], claim_ids=[], source_ids=[sid], segment_ids=[],
                            video_id=video_id, registry_url=REGISTRY_URL, review_state='LINK_ONLY', evidence_state='LINK_ONLY',
                            evidence_kinds=['LINK_ONLY'], source_patches=[], patch_state='UNKNOWN', patch_compatible=None,
                            patch_limits=None, coaching_enabled=False))
    index = dict(format=FORMAT, taxonomy=dict(groups=deepcopy(topics['groups'])),
                 registry_url=REGISTRY_URL, sources=sorted(sources, key=lambda s: s['source_id']),
                 videos=sorted(videos, key=lambda v: v['video_id']), segments=[],
                 lessons=sorted(lessons, key=lambda l: l['lesson_id']), practices=sorted(practices, key=lambda p: p['practice_id']),
                 provenance=dict(hash_format='SORTED_COMPACT_UTF8_JSON_SHA256',
                                 input_hashes={'config/learning_topics.json': _hash(topics),
                                               'web_r4/loading-knowledge.json': _hash(knowledge),
                                               'config/user_lesson_candidates.json': _hash(candidates)},
                                 registry_claim_n=len(claim_ids), link_only_video_n=len(videos),
                                 new_visual_review_n=0, new_provider_calls=0,
                                 scope='READ_ONLY_INDEX_NOT_TACTICAL_APPROVAL'), coaching_enabled=False)
    return validate_index(index)


def search_index(index, query='', *, topic_id=None, role=None, champion=None, opponent=None,
                 situation=None, evidence_state=None, patch=None, limit=100, offset=0):
    """Pure AND-filtered, NFC/casefold search with a copied, deterministic page.

    Text covers public titles, topic labels, identities, and IDs, not a second
    copy of tactical text. A patch match is a source label, never compatibility.
    """
    if type(limit) is not int or not 1 <= limit <= 500 or type(offset) is not int or offset < 0:
        raise ValueError('INVALID_SEARCH_PAGE')
    descendants, labels = {}, {}
    for group in index['taxonomy']['groups']:
        descendants[group['id']] = set()
        for topic in group['topics']:
            ids = {leaf['id'] for leaf in topic['leaves']}
            descendants[topic['id']] = ids
            descendants[group['id']].update(ids)
            for leaf in topic['leaves']:
                descendants[leaf['id']] = {leaf['id']}
                labels[leaf['id']] = ' '.join([group['label'], topic['label'], leaf['label']])
    def has(value, values):
        return value is None or _fold(value) in {_fold(x) for x in values}
    selected, unknown, mismatch = [], 0, 0
    terms = _fold(query).split()
    for lesson in index['lessons']:
        lesson_topics = {lesson['primary_topic_id'], *lesson['secondary_topic_ids']}
        if topic_id == 'UNCLASSIFIED' and lesson['primary_topic_id'] is not None:
            continue
        if topic_id and topic_id != 'UNCLASSIFIED' and not lesson_topics.intersection(descendants.get(topic_id, set())):
            continue
        if not (has(role, lesson['roles']) and has(champion, lesson['champions']) and has(opponent, lesson['opponents'])
                and has(situation, lesson['situation_tags']) and has(evidence_state, [lesson['evidence_state']])):
            continue
        haystack = _fold(' '.join([lesson['title'], lesson['lesson_id'], *lesson['champions'], *lesson['opponents'],
                                   *lesson['claim_ids'], *lesson['roles'], *lesson['situation_tags'],
                                   *(labels.get(t, '') for t in lesson_topics)]))
        if not all(term in haystack for term in terms):
            continue
        if not lesson['source_patches']:
            unknown += 1
        if patch is not None and not has(patch, lesson['source_patches']):
            if lesson['source_patches']:
                mismatch += 1
            continue
        selected.append(lesson)
    facets = {key: sorted({v for l in selected for v in l[field]}) for key, field in
              [('roles', 'roles'), ('champions', 'champions'), ('opponents', 'opponents'), ('situations', 'situation_tags')]}
    facets['evidence_states'] = sorted({l['evidence_state'] for l in selected})
    return dict(format=FORMAT + '-search', total=len(selected), offset=offset, limit=limit,
                lessons=deepcopy(selected[offset:offset + limit]), facets=facets,
                unknown_patch_count=unknown, patch_mismatch_count=mismatch, coaching_enabled=False)
