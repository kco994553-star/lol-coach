"""Read-only learning references: loss of uncertainty must fail these tests."""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
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


if __name__ == '__main__':
    unittest.main()
