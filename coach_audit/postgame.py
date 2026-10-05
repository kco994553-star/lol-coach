"""Pinned Match/Timeline archive diagnostics, never a player-state importer.

Only the public ``diagnose_postgame`` entry authenticates the bytes against the
preserved R7 range receipts. A supported publisher schema is not an authenticated
Riot response, a player view, or permission to run the coaching engine.
"""
import re

from coach_intake.io import sha, strict_json


SOURCE_SCHEMA = 'MATCH_V5_BSON_POST_GAME_V1'
MATCH_ID = 'EUW1_7095952008'
SOURCE_REVISION = '477404f532b1014b7fc61c3b1c024e988f883a26'
PINNED_SOURCES = {
    'match': {
        'sha256': '767330c58d9f9168c5ea4a6f0827bde7b0890eeae2317ea19ae52812a3792b14',
        'bytes': 113459, 'source_file': 'match_v5.json',
        'requested_range': 'bytes=9334672-9448130',
        'content_range': 'bytes 9334672-9448130/1341990851',
        'record_index_zero_based': 82,
    },
    'timeline': {
        'sha256': '9fb74d4ce6cd16f3e04aa0953638e0e18cd80c5cce652eac83126ed55050d51a',
        'bytes': 1199490, 'source_file': 'timeline_v5.json',
        'requested_range': 'bytes=1-1199490',
        'content_range': 'bytes 1-1199490/14493943155',
        'record_index_zero_based': 0,
    },
}
SOURCE_ORIGIN = 'PUBLISHER_ATTESTED_RIOT_COLLECTION_NOT_INDEPENDENTLY_AUTHENTICATED'
_INT64_MAX = (1 << 63) - 1
_INT64_MIN = -(1 << 63)


class PostGameInputRejected(ValueError):
    """Invalid binding, identity join or requested archive time."""


class UnsupportedSourceSchema(PostGameInputRejected):
    """Different from an absent value in a supported archive schema."""


def _unsupported(path):
    raise UnsupportedSourceSchema('UNSUPPORTED_SOURCE_SCHEMA:' + path)


def _object(value, path):
    if type(value) is not dict:
        _unsupported(path)
    return value


def _int(value, *, minimum=0):
    return type(value) is int and minimum <= value <= _INT64_MAX


def _number_long(value, path):
    """Exact BSON signed int64 only at the explicitly called metadata paths."""
    if type(value) is not dict or set(value) != {'$numberLong'}:
        _unsupported(path)
    encoded = value['$numberLong']
    if type(encoded) is not str or not re.fullmatch(r'-?(0|[1-9][0-9]*)', encoded):
        _unsupported(path)
    # Length bound avoids converting an arbitrary length hostile integer string.
    if len(encoded.lstrip('-')) > 19:
        _unsupported(path)
    decoded = int(encoded)
    if not _INT64_MIN <= decoded <= _INT64_MAX:
        _unsupported(path)
    return decoded


def _read(data, path):
    current = data
    for key in path:
        if current is None:
            return None, 'NULL_ANCESTOR'
        if type(current) is not dict:
            return None, 'WRONG_CONTAINER'
        if any(str(k).startswith('$') for k in current):
            return None, 'UNSUPPORTED_BSON_WRAPPER'
        if key not in current:
            return None, 'MISSING'
        current = current[key]
    return current, 'NULL' if current is None else 'PRESENT'


def _fact(field, data, path, *, pointer, source, provenance, timestamp,
          participant_id=None, kind='integer', missing_reason=None):
    value, reason = _read(data, path)
    if missing_reason:
        value, reason = None, missing_reason
    if reason == 'UNSUPPORTED_BSON_WRAPPER':
        _unsupported(pointer)
    if reason == 'PRESENT':
        # Wrappers are not scalars. Do not recursively unwrap or coerce them.
        if type(value) is dict and any(str(k).startswith('$') for k in value):
            _unsupported(pointer)
        valid = _int(value) if kind == 'integer' else type(value) is str and bool(value)
        if not valid:
            value, reason = None, 'INVALID_SCALAR'
    return dict(field=field, layer='L0', state='PRESENT' if reason == 'PRESENT' else 'UNKNOWN',
                value=value, missing_reason=None if reason == 'PRESENT' else reason,
                pointer=pointer, source=source, source_sha256=provenance[source]['sha256'],
                source_schema=SOURCE_SCHEMA, frame_timestamp_ms=timestamp,
                participant_id=participant_id, scope='POST_GAME_DATASET',
                knowledge_scope='POST_GAME_ONLY', player_known=False,
                decision_eligible=False, coaching_eligible=False)


def _roster(match, timeline):
    match_meta = _object(match.get('metadata'), '/match/metadata')
    timeline_meta = _object(timeline.get('metadata'), '/timeline/metadata')
    for name, metadata in (('match', match_meta), ('timeline', timeline_meta)):
        if type(metadata.get('matchId')) is not str or not metadata['matchId']:
            _unsupported('/' + name + '/metadata/matchId')
        participants = metadata.get('participants')
        if type(participants) is not list or not participants or any(type(p) is not str or not p for p in participants):
            _unsupported('/' + name + '/metadata/participants')
        if len(set(participants)) != len(participants):
            raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:DUPLICATE_METADATA_IDENTITY')
    if match_meta['matchId'] != timeline_meta['matchId']:
        raise PostGameInputRejected('MATCH_JOIN_REJECTED:MATCH_ID')
    if match_meta['participants'] != timeline_meta['participants']:
        raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:METADATA_ORDER')
    match_info = _object(match.get('info'), '/match/info')
    timeline_info = _object(timeline.get('info'), '/timeline/info')
    game_ids = [_number_long(info.get('gameId'), '/' + name + '/info/gameId')
                for name, info in (('match', match_info), ('timeline', timeline_info))]
    if game_ids[0] != game_ids[1] or game_ids[0] < 0:
        raise PostGameInputRejected('MATCH_JOIN_REJECTED:GAME_ID')
    if match_meta['matchId'].rsplit('_', 1)[-1] != str(game_ids[0]):
        raise PostGameInputRejected('MATCH_JOIN_REJECTED:GAME_ID_MATCH_ID')
    rosters = []
    for name, info in (('match', match_info), ('timeline', timeline_info)):
        participants = info.get('participants')
        if type(participants) is not list or not participants:
            _unsupported('/' + name + '/info/participants')
        roster = {}
        for participant in participants:
            participant = _object(participant, '/' + name + '/info/participants/*')
            pid, identity = participant.get('participantId'), participant.get('puuid')
            if not _int(pid, minimum=1) or pid > 10 or type(identity) is not str or not identity:
                raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:INVALID_IDENTITY')
            if pid in roster:
                raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:DUPLICATE_PARTICIPANT')
            roster[pid] = participant
        if set(roster) != set(range(1, len(match_meta['participants']) + 1)):
            raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:ROSTER_IDS')
        if any(roster[pid]['puuid'] != match_meta['participants'][pid - 1] for pid in roster):
            raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:ROSTER_IDENTITY')
        rosters.append(roster)
    if {pid: row['puuid'] for pid, row in rosters[0].items()} != {pid: row['puuid'] for pid, row in rosters[1].items()}:
        raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:ROSTER_IDENTITY')
    return match_meta, match_info, timeline_info, rosters[0], game_ids[0]


def _diagnose_records(match, timeline, *, expected_match_id, participant_id,
                      archive_cutoff_ms, clock_basis, provenance):
    """Schema helper; only diagnose_postgame establishes pinned byte provenance."""
    if type(expected_match_id) is not str or not expected_match_id:
        raise PostGameInputRejected('MATCH_JOIN_REJECTED:INVALID_REQUEST')
    if not _int(participant_id, minimum=1) or participant_id > 10:
        raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:INVALID_REQUEST')
    if not _int(archive_cutoff_ms) or clock_basis != 'ELAPSED_GAME_MS':
        raise PostGameInputRejected('TIME_JOIN_REJECTED:INVALID_CUTOFF_OR_CLOCK_BASIS')
    match = _object(match, '/match')
    timeline = _object(timeline, '/timeline')
    metadata, match_info, timeline_info, roster, game_id = _roster(match, timeline)
    patch_version = match_info.get('gameVersion')
    if type(patch_version) is not str or not patch_version:
        _unsupported('/match/info/gameVersion')
    if metadata['matchId'] != expected_match_id:
        raise PostGameInputRejected('MATCH_JOIN_REJECTED:REQUESTED_MATCH_ID')
    if participant_id not in roster:
        raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:REQUESTED_PARTICIPANT')
    interval = timeline_info.get('frameInterval')
    if not _int(interval, minimum=1):
        _unsupported('/timeline/info/frameInterval')
    frames = timeline_info.get('frames')
    if type(frames) is not list:
        _unsupported('/timeline/info/frames')
    selected = None
    previous = -1
    for index, frame in enumerate(frames):
        frame = _object(frame, '/timeline/info/frames/' + str(index))
        timestamp = frame.get('timestamp')
        if not _int(timestamp):
            _unsupported('/timeline/info/frames/' + str(index) + '/timestamp')
        if timestamp <= previous:
            raise PostGameInputRejected('TIME_JOIN_REJECTED:NONINCREASING_FRAME_TIMESTAMP')
        previous = timestamp
        if timestamp <= archive_cutoff_ms:
            selected = (index, frame)
    if frames and archive_cutoff_ms > previous:
        raise PostGameInputRejected('TIME_JOIN_REJECTED:CUTOFF_AFTER_SOURCE_END')
    frame_index, frame = selected if selected is not None else (None, {})
    timestamp = frame.get('timestamp')
    participant_frames = frame.get('participantFrames', {})
    _object(participant_frames, '/timeline/info/frames/*/participantFrames')
    for key, row in participant_frames.items():
        if type(key) is not str or not re.fullmatch(r'[1-9][0-9]*', key):
            raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:FRAME_KEY')
        row = _object(row, '/timeline/info/frames/*/participantFrames/' + key)
        if not _int(row.get('participantId'), minimum=1) or row['participantId'] != int(key) or int(key) not in roster:
            raise PostGameInputRejected('PARTICIPANT_JOIN_REJECTED:FRAME_ID')
    own_frame = participant_frames.get(str(participant_id), {})
    missing = ('NO_FRAME_AT_OR_BEFORE_CUTOFF' if selected is None else
               'PARTICIPANT_FRAME_MISSING' if str(participant_id) not in participant_frames else None)
    prefix = '/info/frames/' + (str(frame_index) if selected else '*') + '/participantFrames/' + str(participant_id)
    specs = {
        'health': ('championStats', 'health'), 'health_max': ('championStats', 'healthMax'),
        'resource': ('championStats', 'power'), 'resource_max': ('championStats', 'powerMax'),
        'current_gold': ('currentGold',), 'level': ('level',),
        'lane_cs': ('minionsKilled',), 'jungle_cs': ('jungleMinionsKilled',),
        'position_x': ('position', 'x'), 'position_y': ('position', 'y'),
    }
    raw = [_fact(field, own_frame, path, pointer=prefix + '/' + '/'.join(path),
                 source='timeline', provenance=provenance, timestamp=timestamp,
                 participant_id=participant_id, missing_reason=missing)
           for field, path in specs.items()]
    match_index = match_info['participants'].index(roster[participant_id])
    for field, name, kind in (('champion_name', 'championName', 'text'),
                              ('role_label', 'teamPosition', 'text'), ('team_id', 'teamId', 'integer')):
        raw.append(_fact(field, roster[participant_id], (name,),
                         pointer='/info/participants/' + str(match_index) + '/' + name,
                         source='match', provenance=provenance, timestamp=None,
                         participant_id=participant_id, kind=kind))
    by = {row['field']: row for row in raw}
    derived = []
    for name, parents, formula, valid, compute in (
        ('health_fraction', ('health', 'health_max'), 'health / health_max',
         lambda a, b: b > 0 and a <= b, lambda a, b: a / b),
        ('cs', ('lane_cs', 'jungle_cs'), 'lane_cs + jungle_cs',
         lambda a, b: a + b <= _INT64_MAX, lambda a, b: a + b),
    ):
        source_rows = [by[parent] for parent in parents]
        values = [row['value'] for row in source_rows]
        present = all(row['state'] == 'PRESENT' for row in source_rows)
        valid_inputs = present and valid(*values)
        derived.append(dict(field=name, layer='L1', state='DERIVED_DIAGNOSTIC' if valid_inputs else 'UNKNOWN',
                            value=compute(*values) if valid_inputs else None,
                            missing_reason=None if valid_inputs else ('INPUT_MISSING_OR_INVALID' if not present else 'INVARIANT_VIOLATION'),
                            formula=formula, formula_version='r7.postgame.' + name + '.v1',
                            lineage=[dict(field=row['field'], pointer=row['pointer'],
                                          source_sha256=row['source_sha256'], frame_timestamp_ms=row['frame_timestamp_ms'])
                                     for row in source_rows],
                            source_sha256=provenance['timeline']['sha256'],
                            frame_timestamp_ms=timestamp, participant_id=participant_id,
                            scope='POST_GAME_DATASET', knowledge_scope='POST_GAME_ONLY',
                            player_known=False, decision_eligible=False, coaching_eligible=False))
    opponents = []
    own_team = by['team_id']['value']
    for pid, participant in sorted(roster.items()):
        if pid == participant_id or own_team is None or not _int(participant.get('teamId')) or participant['teamId'] == own_team:
            continue
        row = participant_frames.get(str(pid), {})
        position_prefix = '/info/frames/' + (str(frame_index) if selected else '*') + '/participantFrames/' + str(pid)
        opponents.append(dict(participant_id=pid, knowledge_scope='POST_GAME_ONLY',
                              visibility_at_archive_time='UNKNOWN', player_known=False,
                              coordinates=[_fact('position_' + axis, row, ('position', axis),
                                                 pointer=position_prefix + '/position/' + axis,
                                                 source='timeline', provenance=provenance, timestamp=timestamp,
                                                 participant_id=pid, missing_reason=missing if selected is None else None)
                                           for axis in ('x', 'y')]))
    return dict(schema_version='r7.postgame-archive-diagnostic.v1',
                source_schema=SOURCE_SCHEMA, source_schema_status='SUPPORTED_SOURCE_SCHEMA',
                scope='POST_GAME_DATASET',
                source_origin=provenance['match'].get('source_authenticity', provenance['match'].get('origin', 'DECLARED_SOURCE_ORIGIN_UNVERIFIED')),
                source_byte_binding='UNPINNED_SCHEMA_DIAGNOSTIC', provenance=provenance,
                match_id=metadata['matchId'], game_id=game_id, patch_version=patch_version,
                participant_id=participant_id,
                bson_numeric_decodings=[dict(source=kind, pointer='/info/gameId',
                                            encoding='BSON_EXTENDED_JSON_NUMBER_LONG',
                                            semantics='SIGNED_INT64_EXACT',
                                            original_literal=info['gameId']['$numberLong'],
                                            decoded_value=game_id,
                                            source_sha256=provenance[kind]['sha256'])
                                       for kind, info in (('match', match_info), ('timeline', timeline_info))],
                archive_cutoff_ms=archive_cutoff_ms, archive_clock_basis=clock_basis,
                frame_interval_ms=interval, selected_frame_index=frame_index,
                selected_frame_timestamp_ms=timestamp,
                archive_data_status=('MISSING_AT_ARCHIVE_CUTOFF' if selected is None else
                                     'MISSING_PARTICIPANT_FRAME' if missing else 'PRESENT'),
                raw=raw, derived=derived, opponent_archive_coordinates=opponents,
                player_information_state=None, ground_truth_state=None,
                verified_player_state_variables=0, strategic=[], engine_executed=False,
                coaching_enabled=False, coaching_validation_N=0, coaching_accuracy=None,
                decision_candidate=dict(facts=[], status='BLOCKED',
                                        blockers=['POST_GAME_ONLY_IS_NOT_PLAYER_INFORMATION', 'PLAYER_REFERENCE_MISSING', 'ENGINE_SYNTHETIC_ONLY']),
                excluded_source_categories=['ALL_TIMELINE_EVENTS', 'FUTURE_FRAMES',
                                            'MATCH_FINAL_STATS', 'MATCH_OUTCOME', 'MATCH_FINAL_TIME_FIELDS'],
                non_equivalences=['archive coordinates != player-visible coordinates',
                                  'role label != spatial position', 'CS != wave state',
                                  'health fraction != trade permission', 'resource value != cooldown readiness'])


def diagnose_postgame(match_raw, timeline_raw, *, expected_match_id, participant_id,
                      archive_cutoff_ms, clock_basis='ELAPSED_GAME_MS'):
    """Read the preserved exact byte pair as a post-game source diagnostic only.

    Cutoff is elapsed game milliseconds. Choose the latest archive frame at or
    before it; never interpolate or claim the chosen frame is current player data.
    Supported missing scalar fields become UNKNOWN, never substituted zeros.
    """
    records, provenance = {}, {}
    for kind, raw in (('match', match_raw), ('timeline', timeline_raw)):
        if type(raw) is not bytes:
            raise PostGameInputRejected('SOURCE_BYTES_REQUIRED:' + kind)
        pin = PINNED_SOURCES[kind]
        if len(raw) > pin['bytes']:
            raise PostGameInputRejected('SOURCE_HASH_MISMATCH:' + kind)
        record = strict_json(raw)
        if len(raw) != pin['bytes'] or sha(raw) != pin['sha256']:
            raise PostGameInputRejected('SOURCE_HASH_MISMATCH:' + kind)
        records[kind] = record
        provenance[kind] = dict(pin, revision=SOURCE_REVISION, response_status=206,
                                url='https://huggingface.co/datasets/AngryBacteria/league_of_legends/resolve/' + SOURCE_REVISION + '/' + pin['source_file'],
                                receipt_path='evidence/r7-continuation/source-range-receipts.json',
                                raw_original_object_no_serialization=True,
                                source_authenticity=SOURCE_ORIGIN, pinned_bytes_verified=True)
    result = _diagnose_records(records['match'], records['timeline'], expected_match_id=expected_match_id,
                               participant_id=participant_id, archive_cutoff_ms=archive_cutoff_ms,
                               clock_basis=clock_basis, provenance=provenance)
    result['source_byte_binding'] = 'PINNED_SOURCE_BYTES_VERIFIED'
    return result
