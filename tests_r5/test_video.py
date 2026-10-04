import json,unittest
from coach_intake.video import index_transcript
HEADER='YouTube transcript\nVideo ID: CejHqSces8Q\nLanguage: en\nCaptions: auto-generated\n\n'
def parse(body):return index_transcript((HEADER+body).encode(),'CejHqSces8Q')
class VideoTests(unittest.TestCase):
    def test_candidates_are_speech_not_events(self):
        r=parse('[0:01] I might roam.\n[0:04] big wave, no vision\n')
        self.assertEqual(r['cue_count'],2);self.assertEqual(len(r['candidates']),2)
        self.assertFalse(r['coaching_enabled']);self.assertEqual(r['visual_frames_reviewed'],0)
        self.assertFalse(r['game_clock_mapping_verified']);self.assertIsNone(r['candidates'][0]['game_time_ms'])
        self.assertNotIn('I might roam',json.dumps(r))
    def test_bad_timing_and_empty_rejected(self):
        for body in ('[0:60] wave','[0:04] wave\n[0:01] roam','','[0:01] wave\nuntimed line'):
            with self.assertRaises(ValueError):parse(body)
    def test_hour_timestamp_and_equal_times(self):
        r=parse('[1:02:03] ward\n[1:02:03] wave');self.assertEqual(r['last_cue_video_time_ms'],3723000)
    def test_id_mismatch_rejected(self):
        with self.assertRaises(ValueError):index_transcript((HEADER+'[0:01] wave').encode(),'abcdefghijk')
    def test_future_outcome_not_merged_into_prior(self):
        r=parse('[0:01] trade\n[0:20] trade was a mistake')
        self.assertEqual([x['video_time_ms'] for x in r['candidates']],[1000,20000]);self.assertTrue(all(not x['decision_eligible'] for x in r['candidates']))
