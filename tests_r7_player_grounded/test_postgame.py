"""Archive schema negatives plus optional exact-byte preserved-source check.

The small records below are SYNTHETIC_SCHEMA_TEST_ONLY and exercise the private
schema helper. They never bypass the public pinned-byte entry or enter an engine.
"""
import copy
import json
import os
from pathlib import Path
import unittest

from coach_audit.extraction import extract
from coach_audit.postgame import (
    MATCH_ID, PINNED_SOURCES, PostGameInputRejected, UnsupportedSourceSchema,
    _diagnose_records, _number_long, diagnose_postgame,
)


def schema_fixture():
    """Explicit synthetic schema mechanics, not a real source/reference case."""
    match = {
        'metadata': {'matchId': 'TEST_42', 'participants': ['synthetic-own', 'synthetic-opponent']},
        'info': {'gameId': {'$numberLong': '42'}, 'gameVersion': 'SYNTHETIC_TEST_PATCH',
                 'participants': [
                     {'participantId': 1, 'puuid': 'synthetic-own', 'teamId': 100,
                      'championName': 'SYNTHETIC_OWN', 'teamPosition': 'TOP', 'kills': 999, 'win': True},
                     {'participantId': 2, 'puuid': 'synthetic-opponent', 'teamId': 200},
                 ], 'gameDuration': 999999, 'gameEndTimestamp': {'$numberLong': '999999999'},
                 'teams': [{'win': True}]},
    }
    def frame(timestamp, hp, x):
        return {'timestamp': timestamp, 'events': [{'type': 'CHAMPION_KILL', 'timestamp': timestamp + 5}],
                'participantFrames': {
                    '1': {'participantId': 1, 'championStats': {'health': hp, 'healthMax': 100,
                                                              'power': 0, 'powerMax': 0},
                          'currentGold': 3, 'level': 1, 'minionsKilled': 4, 'jungleMinionsKilled': 2,
                          'position': {'x': x, 'y': 5}},
                    '2': {'participantId': 2, 'position': {'x': x + 10, 'y': 20}},
                }}
    timeline = {'metadata': copy.deepcopy(match['metadata']),
                'info': {'gameId': {'$numberLong': '42'}, 'frameInterval': 100,
                         'participants': [{'participantId': 1, 'puuid': 'synthetic-own'},
                                          {'participantId': 2, 'puuid': 'synthetic-opponent'}],
                         'frames': [frame(100, 50, 10), frame(200, 1, 99999)]}}
    return match, timeline


def schema_diagnostic(match, timeline, *, expected_match_id='TEST_42', participant_id=1,
                      archive_cutoff_ms=150, clock_basis='ELAPSED_GAME_MS'):
    # This helper supplies honest synthetic provenance only to private mechanics.
    provenance = {kind: {'sha256': '0' * 64, 'origin': 'SYNTHETIC_SCHEMA_TEST_ONLY',
                         'pinned_bytes_verified': False} for kind in ('match', 'timeline')}
    return _diagnose_records(match, timeline, expected_match_id=expected_match_id,
                             participant_id=participant_id, archive_cutoff_ms=archive_cutoff_ms,
                             clock_basis=clock_basis, provenance=provenance)


class PostGameSchemaTests(unittest.TestCase):
    def setUp(self):
        self.match, self.timeline = schema_fixture()

    def by(self, result, field, section='raw'):
        return next(row for row in result[section] if row['field'] == field)

    def test_archive_cutoff_and_lineage_do_not_generate_player_information(self):
        result = schema_diagnostic(self.match, self.timeline)
        self.assertEqual(result['source_schema_status'], 'SUPPORTED_SOURCE_SCHEMA')
        self.assertEqual(result['source_origin'], 'SYNTHETIC_SCHEMA_TEST_ONLY')
        self.assertEqual(result['source_byte_binding'], 'UNPINNED_SCHEMA_DIAGNOSTIC')
        self.assertEqual(result['selected_frame_timestamp_ms'], 100)
        self.assertEqual(self.by(result, 'health_fraction', 'derived')['value'], 0.5)
        cs = self.by(result, 'cs', 'derived')
        self.assertEqual(cs['value'], 6)
        self.assertEqual(cs['formula'], 'lane_cs + jungle_cs')
        self.assertEqual([r['frame_timestamp_ms'] for r in cs['lineage']], [100, 100])
        self.assertTrue(all(r['scope'] == 'POST_GAME_DATASET' and not r['decision_eligible']
                            and not r['player_known'] for r in result['raw'] + result['derived']))
        self.assertIsNone(result['player_information_state'])
        self.assertIsNone(result['ground_truth_state'])
        self.assertEqual(result['decision_candidate']['facts'], [])
        self.assertEqual(result['verified_player_state_variables'], 0)
        self.assertFalse(result['engine_executed'])
        self.assertFalse(result['coaching_enabled'])
        self.assertEqual(result['coaching_validation_N'], 0)
        self.assertIsNone(result['coaching_accuracy'])

    def test_future_events_final_stats_and_outcome_cannot_change_candidate(self):
        baseline = schema_diagnostic(self.match, self.timeline)
        self.match['info']['participants'][0].update(kills=0, win=False, level=99, totalMinionsKilled=999)
        self.match['info'].update(gameDuration=1, gameEndTimestamp={'unexpected': True}, teams=[])
        self.timeline['info']['frames'][0]['events'] = [{'type': 'GAME_END', 'winningTeam': 200}]
        self.timeline['info']['frames'][1]['events'].append({'type': 'CHAMPION_KILL', 'killerId': 2})
        self.timeline['info']['frames'][1]['participantFrames']['1']['championStats']['health'] = 100
        self.timeline['info']['frames'][1]['participantFrames']['2']['position']['x'] = 44444
        self.assertEqual(schema_diagnostic(self.match, self.timeline), baseline)
        self.assertNotIn('win', {r['field'] for r in baseline['raw']})

    def test_opponent_coordinates_are_post_game_only_and_visibility_unknown(self):
        result = schema_diagnostic(self.match, self.timeline)
        opponent = result['opponent_archive_coordinates'][0]
        self.assertEqual(opponent['knowledge_scope'], 'POST_GAME_ONLY')
        self.assertEqual(opponent['visibility_at_archive_time'], 'UNKNOWN')
        self.assertFalse(opponent['player_known'])
        self.assertEqual([r['value'] for r in opponent['coordinates']], [20, 20])
        self.assertTrue(all(not r['decision_eligible'] and r['frame_timestamp_ms'] == 100
                            for r in opponent['coordinates']))

    def test_wrong_match_and_game_id_joins_rejected(self):
        for mutate in (
            lambda m, t: t['metadata'].update(matchId='TEST_43'),
            lambda m, t: t['info'].update(gameId={'$numberLong': '43'}),
            lambda m, t: (m['metadata'].update(matchId='TEST_43'), t['metadata'].update(matchId='TEST_43')),
        ):
            with self.subTest(mutate=mutate):
                match, timeline = schema_fixture()
                mutate(match, timeline)
                with self.assertRaisesRegex(PostGameInputRejected, 'MATCH_JOIN_REJECTED'):
                    schema_diagnostic(match, timeline)
        with self.assertRaisesRegex(PostGameInputRejected, 'REQUESTED_MATCH_ID'):
            schema_diagnostic(self.match, self.timeline, expected_match_id='TEST_43')

    def test_wrong_participant_identities_and_frame_joins_rejected(self):
        def frame_id(m, t):
            t['info']['frames'][0]['participantFrames']['1']['participantId'] = 2
        mutations = [
            lambda m, t: t['metadata']['participants'].reverse(),
            lambda m, t: t['info']['participants'][0].update(puuid='wrong'),
            lambda m, t: m['info']['participants'][0].update(participantId=True),
            lambda m, t: t['info']['participants'].append(copy.deepcopy(t['info']['participants'][0])),
            frame_id,
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                match, timeline = schema_fixture()
                mutate(match, timeline)
                with self.assertRaisesRegex(PostGameInputRejected, 'PARTICIPANT_JOIN_REJECTED'):
                    schema_diagnostic(match, timeline)
        for participant in (True, 0, 3, '1'):
            with self.subTest(participant=participant):
                with self.assertRaisesRegex(PostGameInputRejected, 'PARTICIPANT_JOIN_REJECTED'):
                    schema_diagnostic(self.match, self.timeline, participant_id=participant)

    def test_wrong_clock_scalar_future_cutoff_and_nonmonotonic_times_rejected(self):
        for cutoff in (True, -1, 150.0, '150', 201):
            with self.subTest(cutoff=cutoff):
                with self.assertRaisesRegex(PostGameInputRejected, 'TIME_JOIN_REJECTED'):
                    schema_diagnostic(self.match, self.timeline, archive_cutoff_ms=cutoff)
        with self.assertRaisesRegex(PostGameInputRejected, 'TIME_JOIN_REJECTED'):
            schema_diagnostic(self.match, self.timeline, clock_basis='UNIX_MS')
        self.timeline['info']['frames'][1]['timestamp'] = 100
        with self.assertRaisesRegex(PostGameInputRejected, 'NONINCREASING'):
            schema_diagnostic(self.match, self.timeline)
        self.timeline['info']['frames'][1]['timestamp'] = True
        with self.assertRaises(UnsupportedSourceSchema):
            schema_diagnostic(self.match, self.timeline)

    def test_supported_absent_scalar_is_unknown_never_zero(self):
        own = self.timeline['info']['frames'][0]['participantFrames']['1']
        del own['minionsKilled']
        own['championStats']['health'] = None
        result = schema_diagnostic(self.match, self.timeline)
        self.assertEqual(self.by(result, 'lane_cs')['missing_reason'], 'MISSING')
        self.assertEqual(self.by(result, 'health')['missing_reason'], 'NULL')
        for name in ('health_fraction', 'cs'):
            self.assertEqual(self.by(result, name, 'derived')['state'], 'UNKNOWN')
            self.assertIsNone(self.by(result, name, 'derived')['value'])
        del self.timeline['info']['frames'][0]['participantFrames']['1']
        result = schema_diagnostic(self.match, self.timeline)
        self.assertEqual(self.by(result, 'health')['missing_reason'], 'PARTICIPANT_FRAME_MISSING')

    def test_no_eligible_frame_keeps_supported_schema_separate_from_missing_data(self):
        result = schema_diagnostic(self.match, self.timeline, archive_cutoff_ms=99)
        self.assertEqual(result['source_schema_status'], 'SUPPORTED_SOURCE_SCHEMA')
        self.assertEqual(result['archive_data_status'], 'MISSING_AT_ARCHIVE_CUTOFF')
        self.assertIsNone(result['selected_frame_timestamp_ms'])
        self.assertEqual(self.by(result, 'health')['missing_reason'], 'NO_FRAME_AT_OR_BEFORE_CUTOFF')
        self.assertIsNone(self.by(result, 'health_fraction', 'derived')['value'])

    def test_invalid_health_scalars_and_pair_invariants_cannot_derive(self):
        for hp, maximum in ((True, 100), (50.0, 100), ('50', 100), (-1, 100), (101, 100),
                            (0, 0), (None, 100), (50, True), (50, -1), (50, 1 << 63)):
            with self.subTest(hp=hp, maximum=maximum):
                self.timeline['info']['frames'][0]['participantFrames']['1']['championStats'].update(health=hp, healthMax=maximum)
                ratio = self.by(schema_diagnostic(self.match, self.timeline), 'health_fraction', 'derived')
                self.assertEqual(ratio['state'], 'UNKNOWN')
                self.assertIsNone(ratio['value'])
        self.timeline['info']['frames'][0]['participantFrames']['1']['championStats'].update(health=0, healthMax=100)
        self.assertEqual(self.by(schema_diagnostic(self.match, self.timeline), 'health_fraction', 'derived')['value'], 0)

    def test_cs_requires_both_valid_parents_without_numeric_coercion(self):
        for value in (True, 2.0, '2', -1, None, 1 << 63):
            with self.subTest(value=value):
                self.timeline['info']['frames'][0]['participantFrames']['1']['jungleMinionsKilled'] = value
                self.assertIsNone(self.by(schema_diagnostic(self.match, self.timeline), 'cs', 'derived')['value'])

    def test_bson_exact_signed_int64_only_at_game_id_known_locations(self):
        self.assertEqual(_number_long({'$numberLong': '9007199254740993'}, '/info/gameId'), 9007199254740993)
        for wrapper in ({'$numberLong': 42}, {'$numberLong': '4.2'}, {'$numberLong': '042'},
                        {'$numberLong': '42', 'extra': 1}, {'$numberLong': str(1 << 63)},
                        {'$numberLong': str(-(1 << 63) - 1)}, {'$numberInt': '42'}, 42):
            with self.subTest(wrapper=wrapper):
                with self.assertRaises(UnsupportedSourceSchema):
                    _number_long(wrapper, '/info/gameId')
        for value in ({'$numberLong': '50'}, {'$numberDouble': '50'}):
            self.timeline['info']['frames'][0]['participantFrames']['1']['championStats']['health'] = value
            with self.assertRaisesRegex(UnsupportedSourceSchema, 'UNSUPPORTED_SOURCE_SCHEMA'):
                schema_diagnostic(self.match, self.timeline)
        self.timeline['info']['frames'][0]['participantFrames']['1']['championStats'] = {'$numberLong': '50'}
        with self.assertRaises(UnsupportedSourceSchema):
            schema_diagnostic(self.match, self.timeline)

    def test_other_schema_is_unsupported_not_missing_data(self):
        with self.assertRaisesRegex(UnsupportedSourceSchema, 'UNSUPPORTED_SOURCE_SCHEMA'):
            schema_diagnostic({'activePlayer': {}}, self.timeline)

    def test_public_entry_requires_exact_bytes_and_rejects_strict_json_failures(self):
        match = json.dumps(self.match).encode()
        timeline = json.dumps(self.timeline).encode()
        for raw, reason in ((b'{"a":1,"a":2}', 'DUPLICATE_KEY'),
                            (b'{"a":NaN}', 'NONFINITE_NUMBER'),
                            (b'{"a":1e999}', 'NONFINITE_NUMBER'),
                            (match, 'SOURCE_HASH_MISMATCH')):
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    diagnose_postgame(raw, timeline, expected_match_id='TEST_42', participant_id=1, archive_cutoff_ms=150)
        with self.assertRaisesRegex(PostGameInputRejected, 'SOURCE_BYTES_REQUIRED'):
            diagnose_postgame(self.match, timeline, expected_match_id='TEST_42', participant_id=1, archive_cutoff_ms=150)


class PinnedPostGameSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        location = os.environ.get('R7_POSTGAME_RAW_DIR')
        if not location:
            raise unittest.SkipTest('R7_POSTGAME_RAW_DIR required for preserved exact-byte source integration')
        cls.match_raw = (Path(location) / 'match.json').read_bytes()
        cls.timeline_raw = (Path(location) / 'timeline.json').read_bytes()

    def test_preserved_actual_frame_matches_existing_source_reference(self):
        result = diagnose_postgame(self.match_raw, self.timeline_raw, expected_match_id=MATCH_ID,
                                   participant_id=1, archive_cutoff_ms=300153)
        by = {row['field']: row for row in result['raw'] + result['derived']}
        for field, value in {'health': 261, 'health_max': 1177, 'current_gold': 424,
                             'level': 5, 'lane_cs': 24, 'jungle_cs': 0, 'resource': 0,
                             'resource_max': 0, 'position_x': 5597, 'position_y': 13531,
                             'champion_name': 'Aatrox', 'role_label': 'TOP', 'cs': 24,
                             'health_fraction': 261 / 1177}.items():
            self.assertEqual(by[field]['value'], value)
        self.assertEqual(result['selected_frame_timestamp_ms'], 300153)
        self.assertEqual(result['patch_version'], '14.17.613.973')
        self.assertEqual(result['scope'], 'POST_GAME_DATASET')
        self.assertEqual(result['source_byte_binding'], 'PINNED_SOURCE_BYTES_VERIFIED')
        self.assertTrue(all(r['pinned_bytes_verified'] for r in result['provenance'].values()))
        self.assertEqual([r['source_sha256'] for r in by['cs']['lineage']],
                         [PINNED_SOURCES['timeline']['sha256']] * 2)
        self.assertEqual(len(result['opponent_archive_coordinates']), 5)
        self.assertEqual(result['verified_player_state_variables'], 0)
        self.assertEqual(result['decision_candidate']['facts'], [])
        self.assertFalse(result['coaching_enabled'])

    def test_actual_frame_cutoff_excludes_next_frame(self):
        result = diagnose_postgame(self.match_raw, self.timeline_raw, expected_match_id=MATCH_ID,
                                   participant_id=1, archive_cutoff_ms=300152)
        self.assertEqual(result['selected_frame_index'], 4)
        self.assertLess(result['selected_frame_timestamp_ms'], 300153)
        self.assertTrue(all(r['frame_timestamp_ms'] <= 300152 for r in result['raw']
                            if r['frame_timestamp_ms'] is not None))

    def test_actual_byte_mutation_and_wrong_requested_match_rejected(self):
        with self.assertRaisesRegex(PostGameInputRejected, 'SOURCE_HASH_MISMATCH'):
            diagnose_postgame(self.match_raw + b' ', self.timeline_raw, expected_match_id=MATCH_ID,
                               participant_id=1, archive_cutoff_ms=300153)
        with self.assertRaisesRegex(PostGameInputRejected, 'REQUESTED_MATCH_ID'):
            diagnose_postgame(self.match_raw, self.timeline_raw, expected_match_id='EUW1_0',
                               participant_id=1, archive_cutoff_ms=300153)

    def test_existing_liveclient_extractor_is_unchanged_and_still_unsupported_for_pair(self):
        for raw in (self.match_raw, self.timeline_raw):
            result = extract(raw)
            self.assertEqual(sum(r['state'] == 'PRESENT' for r in result['raw']), 0)
            self.assertIsNone(result['player_information_state'])
            self.assertFalse(result['coaching_enabled'])


if __name__ == '__main__':
    unittest.main()
