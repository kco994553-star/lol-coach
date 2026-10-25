"""Read-only learning references: loss of uncertainty must fail these tests."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LearningRoomTests(unittest.TestCase):
    def api(self):
        try:
            return importlib.import_module('coach_v1.learning_room')
        except ModuleNotFoundError:
            self.fail('learning-room read-only index API is missing')

    def test_taxonomy_search_round_trip_and_unclassified_video(self):
        api = self.api()
        index = api.build_index(ROOT)
        groups = index['taxonomy']['groups']
        self.assertEqual([g['label'] for g in groups], ['라인전', '교전', '운영', '한타'])
        self.assertEqual([len(g['topics']) for g in groups], [5, 5, 5, 5])
        leaves = [leaf for g in groups for t in g['topics'] for leaf in t['leaves']]
        self.assertEqual(len(leaves), 80)
        self.assertEqual(len({leaf['id'] for leaf in leaves}), 80)
        for leaf in leaves:
            result = api.search_index(index, topic_id=leaf['id'])
            self.assertTrue(all(l['primary_topic_id'] == leaf['id'] or leaf['id'] in l['secondary_topic_ids'] for l in result['lessons']))
        videos = api.search_index(index, topic_id='UNCLASSIFIED')['lessons']
        self.assertEqual(len(videos), 8)
        self.assertTrue(all(l['primary_topic_id'] is None for l in videos))

    def test_existing_claims_are_references_and_never_approve(self):
        api = self.api()
        index = api.build_index(ROOT)
        lesson = next(l for l in index['lessons'] if l['lesson_id'] == 'claim:A-WAVE')
        self.assertEqual(lesson['action'], {'claim_id': 'A-WAVE', 'field': 'text'})
        self.assertEqual(lesson['required_conditions'], {'claim_id': 'A-WAVE', 'field': 'conditions'})
        self.assertIsNone(lesson['waiting_cost'])
        self.assertIsNone(lesson['goal'])
        self.assertIsNone(lesson['alternative_or_recovery'])
        self.assertFalse(lesson['coaching_enabled'])
        self.assertNotIn('text', lesson)
        self.assertNotIn('approval', lesson)
        self.assertTrue(all(not x['coaching_enabled'] for x in index['lessons']))
        practice = next(p for p in index['practices'] if p['practice_id'] == lesson['practice_id'])
        self.assertEqual(practice['condition_ref'], {'claim_id': 'A-WAVE', 'field': 'conditions'})
        self.assertEqual(practice['question_origin'], 'APP_AUTHORED_REFLECTION_NOT_SOURCE_QUOTE')
        self.assertFalse(practice['auto_grade'])

    def test_link_only_has_unknown_video_facts_and_failure_reason(self):
        api = self.api()
        index = api.build_index(ROOT)
        video = next(v for v in index['videos'] if v['video_id'] == 'SA6o_QRPqL8')
        self.assertIsNone(video['title'])
        self.assertIsNone(video['source_patch'])
        self.assertEqual(video['transcript_state'], 'UNKNOWN')
        self.assertEqual(video['scene_state'], 'UNKNOWN')
        self.assertEqual(video['access_state'], 'UNKNOWN')
        self.assertEqual(video['acquisition']['reason'], 'WEB_TOOL_FETCH_THROTTLED')
        self.assertTrue(video['acquisition']['attempted'])
        untouched = next(v for v in index['videos'] if v['video_id'] == 'fBKnFxX-mpU')
        self.assertFalse(untouched['acquisition']['attempted'])
        self.assertEqual(index['segments'], [])
        self.assertEqual(index['provenance']['new_visual_review_n'], 0)

    def test_search_combines_filters_and_keeps_patch_uncertainty(self):
        api = self.api()
        index = api.build_index(ROOT)
        before = copy.deepcopy(index)
        result = api.search_index(index, '웨이브', role='BOTTOM', champion='caitlyn', opponent='Kaisa', evidence_state='SOURCE_REFERENCE')
        self.assertIn('claim:A-WAVE', [l['lesson_id'] for l in result['lessons']])
        self.assertEqual(api.search_index(index, champion='Darius', opponent='Kaisa')['total'], 0)
        self.assertEqual(api.search_index(index, patch='99.99')['total'], 0)
        self.assertGreater(api.search_index(index, patch='99.99')['patch_mismatch_count'], 0)
        self.assertGreater(api.search_index(index, patch='99.99')['unknown_patch_count'], 0)
        for l in api.search_index(index, patch='16.20.1')['lessons']:
            self.assertIn('16.20.1', l['source_patches'])
            self.assertIsNone(l['patch_compatible'])
        self.assertEqual(index, before)

    def test_projection_drops_private_identity_notes_and_transcript(self):
        api = self.api()
        knowledge = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())
        candidates = json.loads((ROOT / 'config/user_lesson_candidates.json').read_text())
        marker = 'PRIVATE_ACCOUNT_MATCH_NOTE_SENTINEL'
        knowledge['account_id'] = marker
        knowledge['matchups'][0]['private_notes'] = marker
        knowledge['matchups'][0]['claims'][0]['puuid'] = marker
        knowledge['sources'][0]['transcript'] = marker
        candidates['candidates'][0]['private_notes'] = marker
        index = api.build_index(ROOT, knowledge=knowledge, candidates=candidates)
        self.assertNotIn(marker, json.dumps(index))
        self.assertNotIn('excerpts', json.dumps(index))

    def test_bad_urls_and_duplicate_claim_ids_are_rejected(self):
        api = self.api()
        k = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())
        k['sources'][0]['url'] = 'javascript:alert(1)'
        with self.assertRaises(ValueError):
            api.build_index(ROOT, knowledge=k)
        k = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())
        k['matchups'][0]['claims'].append(copy.deepcopy(k['matchups'][0]['claims'][0]))
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            api.build_index(ROOT, knowledge=k)

    def segment(self):
        return dict(segment_id='segment:one', video_id='SA6o_QRPqL8', video_start_ms=10000,
                    video_end_ms=15000, game_clock_ms=90000, transcript_cue_ids=[],
                    scene_verified=False, viewer_perspective='UNKNOWN', source_hash=None,
                    evidence_kind='AI_INTERPRETATION', access_state='PERMITTED', license_or_access_state='PERMITTED')

    def test_video_clock_remains_distinct_from_game_clock(self):
        segment = self.api().validate_segment(self.segment())
        self.assertEqual(segment['video_start_ms'], 10000)
        self.assertEqual(segment['game_clock_ms'], 90000)
        self.assertFalse(segment['scene_verified'])

    def test_segment_projection_declares_validated_timestamps(self):
        self.assertEqual(self.api().validate_segment(self.segment())['timestamp_state'], 'VALIDATED')

    def test_query_resolves_existing_claim_prose_and_normalizes_term_and(self):
        api = self.api()
        index = api.build_index(ROOT)
        knowledge = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())
        result = api.search_index(index, '크래시 ＷＡＶＥ', champion='Caitlyn', knowledge=knowledge)
        self.assertIn('claim:A-WAVE', [l['lesson_id'] for l in result['lessons']])
        self.assertEqual(api.search_index(index, '크래시 없는문구', knowledge=knowledge)['total'], 0)
        self.assertEqual(api.search_index(index, patch_state='UNKNOWN', evidence_state='LINK_ONLY')['total'], 8)

    def test_invalid_intervals_and_unlicensed_evidence_rejected(self):
        api = self.api()
        for values in [dict(video_start_ms=-1), dict(video_end_ms=10000), dict(video_start_ms=True),
                       dict(video_end_ms=None), dict(game_clock_ms=-1), dict(license_or_access_state='UNKNOWN'),
                       dict(access_state='DENIED'), dict(evidence_kind='TRANSCRIPT', transcript_cue_ids=[]),
                       dict(evidence_kind='VISUAL', scene_verified=False)]:
            with self.subTest(values=values):
                segment = dict(self.segment(), **values)
                with self.assertRaises(ValueError):
                    api.validate_segment(segment)

    def test_separate_lessons_may_share_segment_but_ids_are_unique(self):
        api = self.api()
        index = api.build_index(ROOT)
        index['segments'] = [api.validate_segment(self.segment())]
        for lesson in index['lessons'][:2]:
            lesson['segment_ids'] = ['segment:one']
        api.validate_index(index)
        index['lessons'][1]['lesson_id'] = index['lessons'][0]['lesson_id']
        with self.assertRaisesRegex(ValueError, 'DUPLICATE'):
            api.validate_index(index)

    def test_public_index_rejects_coaching_promotion_and_invalid_video_binding(self):
        api = self.api()
        for change in ('root_coaching', 'lesson_coaching', 'practice_grading', 'video_url'):
            with self.subTest(change=change):
                index = api.build_index(ROOT)
                if change == 'root_coaching':
                    index['coaching_enabled'] = True
                elif change == 'lesson_coaching':
                    index['lessons'][0]['coaching_enabled'] = True
                elif change == 'practice_grading':
                    index['practices'][0]['auto_grade'] = True
                else:
                    index['videos'][0]['canonical_url'] = 'https://www.youtube.com/watch?v=AAAAAAAAAAA'
                with self.assertRaises(ValueError):
                    api.validate_index(index)

    def test_search_paging_copies_results_and_rejects_invalid_limits(self):
        api = self.api()
        index = api.build_index(ROOT)
        whole = api.search_index(index)
        page = api.search_index(index, offset=1, limit=2)
        self.assertEqual([l['lesson_id'] for l in page['lessons']], [l['lesson_id'] for l in whole['lessons'][1:3]])
        page['lessons'][0]['champions'].append('PRIVATE_MUTATION')
        self.assertNotIn('PRIVATE_MUTATION', json.dumps(index))
        for values in [dict(limit=0), dict(limit=True), dict(offset=-1), dict(limit=501)]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                api.search_index(index, **values)

    def test_deterministic_build_check_and_no_source_mutation(self):
        api = self.api()
        paths = [ROOT / 'web_r4/loading-knowledge.json', ROOT / 'config/user_lesson_candidates.json']
        before = [p.read_bytes() for p in paths]
        first = api.build_index(ROOT)
        self.assertEqual(first, api.build_index(ROOT))
        result = subprocess.run([sys.executable, 'scripts/build_learning_room.py', '--check'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def transcript(self, video_id='SA6o_QRPqL8'):
        return ('YouTube transcript\nVideo ID: ' + video_id + '\nLanguage: ko\nCaptions: manual\n'
                '[00:01] 웨이브를 확인합니다.\n[00:05] 정글 정보는 미확인입니다.\n[00:09] 끝.\n').encode()

    def append(self, raw=None, **changes):
        api = self.api()
        self.assertTrue(hasattr(api, 'append_transcript'), 'permitted offline transcript adapter is missing')
        raw = raw if raw is not None else self.transcript()
        args = dict(access_state='PERMITTED', license_or_access_state='PERMITTED',
                    source_provenance=dict(visibility='PUBLIC', transcript_sha256=hashlib.sha256(raw).hexdigest(), video_duration_ms=12000))
        args.update(changes)
        return api.append_transcript(api.build_index(ROOT), raw, 'SA6o_QRPqL8', **args)

    def test_offline_transcript_reuses_speech_candidates_without_text_or_visual_upgrade(self):
        index = self.append()
        speech = [l for l in index['lessons'] if l['evidence_state'] == 'SPEECH_REVIEW_CANDIDATE']
        self.assertEqual(len(speech), 2)
        self.assertEqual([(s['video_start_ms'], s['video_end_ms']) for s in index['segments']], [(1000, 5000), (5000, 9000)])
        self.assertTrue(all(not s['scene_verified'] and s['game_clock_ms'] is None for s in index['segments']))
        self.assertTrue(all(l['primary_topic_id'] is None and l['action'] is None and not l['coaching_enabled'] for l in speech))
        self.assertNotIn('웨이브를 확인합니다.', json.dumps(index, ensure_ascii=False))
        self.assertEqual(index['provenance']['new_visual_review_n'], 0)
        candidate = next(l for l in index['lessons'] if l['lesson_id'] == 'video:SA6o_QRPqL8')
        self.assertEqual(candidate['evidence_state'], 'LINK_ONLY')
        video = next(v for v in index['videos'] if v['video_id'] == 'SA6o_QRPqL8')
        self.assertEqual(video['acquisition']['reason'], 'WEB_TOOL_FETCH_THROTTLED')
        self.assertEqual(video['scene_state'], 'UNKNOWN')

    def test_transcript_id_hash_rights_privacy_and_clock_order_fail_closed(self):
        cases = [dict(raw=self.transcript('AAAAAAAAAAA')),
                 dict(access_state='UNKNOWN'), dict(license_or_access_state='DENIED'),
                 dict(source_provenance=dict(visibility='PRIVATE', transcript_sha256='0'*64, video_duration_ms=12000)),
                 dict(source_provenance=dict(visibility='PUBLIC', transcript_sha256='0'*64, video_duration_ms=12000)),
                 dict(raw=self.transcript().replace(b'[00:05]', b'[00:00]')),
                 dict(raw=self.transcript().replace(b'[00:05]', b'[00:65]')),
                 dict(source_provenance=dict(visibility='PUBLIC', transcript_sha256=hashlib.sha256(self.transcript()).hexdigest(), video_duration_ms=5000))]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                self.append(**case)

    def test_transcript_cue_assignments_keep_distinct_decisions_and_ingestion_idempotent(self):
        api = self.api()
        assignments = [dict(decision_id='first', cue_index=1, primary_topic_id='topic:1.1.1'),
                       dict(decision_id='second', cue_index=1, primary_topic_id='topic:1.3.1')]
        index = self.append(topic_assignments=assignments)
        speech = [l for l in index['lessons'] if l['evidence_state'] == 'SPEECH_REVIEW_CANDIDATE']
        self.assertEqual(len(speech), 2)
        self.assertNotEqual(speech[0]['lesson_id'], speech[1]['lesson_id'])
        self.assertEqual(speech[0]['segment_ids'], speech[1]['segment_ids'])
        again = api.append_transcript(index, self.transcript(), 'SA6o_QRPqL8', access_state='PERMITTED', license_or_access_state='PERMITTED',
                                     source_provenance=dict(visibility='PUBLIC', transcript_sha256=hashlib.sha256(self.transcript()).hexdigest(), video_duration_ms=12000),
                                     topic_assignments=assignments)
        self.assertEqual(index, again)
        self.assertNotEqual(index, api.build_index(ROOT))
        for invalid in [[dict(decision_id='bad', cue_index=99, primary_topic_id='topic:1.1.1')],
                        [dict(decision_id='bad', cue_index=1, primary_topic_id='topic:99')],
                        assignments + [assignments[0]]]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.append(topic_assignments=invalid)

    def test_operator_can_reference_valid_nonkeyword_cue_without_inventing_lexical_match(self):
        index = self.append(topic_assignments=[dict(decision_id='manual-cue', cue_index=3, primary_topic_id='topic:1.1.1')])
        speech = [l for l in index['lessons'] if l['evidence_state'] == 'SPEECH_REVIEW_CANDIDATE']
        self.assertEqual(len(speech), 1)
        self.assertEqual(index['segments'][0]['video_start_ms'], 9000)
        self.assertEqual(index['segments'][0]['video_end_ms'], 12000)
        self.assertEqual(index['transcript_indices'][0]['candidates'][0]['lexical_topic_hints'], [])

    def test_transcript_adapter_rejects_tampered_input_and_does_not_mutate_on_error(self):
        api = self.api()
        index = self.append()
        original = copy.deepcopy(index)
        index['coaching_enabled'] = True
        with self.assertRaises(ValueError):
            api.append_transcript(index, self.transcript(), 'SA6o_QRPqL8', access_state='PERMITTED', license_or_access_state='PERMITTED',
                source_provenance=dict(visibility='PUBLIC', transcript_sha256=hashlib.sha256(self.transcript()).hexdigest(), video_duration_ms=12000))
        index['coaching_enabled'] = False
        self.assertEqual(index, original)

    def test_offline_manifest_build_keeps_paths_notes_and_raw_out_of_public_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            raw = self.transcript()
            (path / 'PRIVATE_ACCOUNT_RAW.txt').write_bytes(raw)
            (path / 'accepted.json').write_text(json.dumps({'transcripts': [dict(path='PRIVATE_ACCOUNT_RAW.txt', video_id='SA6o_QRPqL8',
                access_state='PERMITTED', license_or_access_state='PERMITTED', source_provenance=dict(visibility='PUBLIC',
                    transcript_sha256=hashlib.sha256(raw).hexdigest(), video_duration_ms=12000, private_notes='PRIVATE_NOTE_SENTINEL'))]}))
            command = [sys.executable, 'scripts/build_learning_room.py', '--accepted-inputs', str(path / 'accepted.json'), '--output', str(path / 'index.json')]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            public = (path / 'index.json').read_text()
            self.assertNotIn('PRIVATE_ACCOUNT_RAW', public)
            self.assertNotIn('PRIVATE_NOTE_SENTINEL', public)
            self.assertNotIn('웨이브를 확인합니다.', public)
            self.assertEqual(len(json.loads(public)['segments']), 2)
            self.assertEqual((path / 'PRIVATE_ACCOUNT_RAW.txt').read_bytes(), raw)
            alias = path / 'raw-alias.txt'
            alias.hardlink_to(path / 'PRIVATE_ACCOUNT_RAW.txt')
            overwrite = command[:-1] + [str(alias)]
            rejected = subprocess.run(overwrite, cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual((path / 'PRIVATE_ACCOUNT_RAW.txt').read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
