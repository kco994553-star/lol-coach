"""Tiny authored synthetic cues; no actual copyrighted transcript fixtures."""
import hashlib
import unittest
import unicodedata
from coach_intake.video import index_transcript

VIDEO_ID='SYNTHETIC01'

def parse(body,language='ko'):
    raw=('YouTube transcript\nVideo ID: '+VIDEO_ID+'\nLanguage: '+language+'\nCaptions: manual\n\n'+body).encode()
    return index_transcript(raw,VIDEO_ID),raw


class KoreanVideoIndexTests(unittest.TestCase):
    def test_requested_korean_topics_map_to_stable_candidate_keys(self):
        cues=('웨이브','라인','로밍','갱','정글','시야','와드','딜교','한타','운영','사이드','본대','오브젝트')
        expected=('WAVE','LANE','ROAM','JUNGLE','JUNGLE','VISION','VISION','TRADE','TEAMFIGHT','MACRO','SIDE','MAIN_BODY','OBJECTIVE')
        report,_=parse('\n'.join('[0:%02d] %s'%(i,term) for i,term in enumerate(cues)))
        self.assertEqual([c['topics'] for c in report['candidates']],[[t] for t in expected])
        self.assertEqual([c['cue_index'] for c in report['candidates']],list(range(1,14)))

    def test_attached_particles_and_exact_aliases_without_substring_guesses(self):
        report,_=parse('[0:01] 웨이브를 라인에서 로밍은 갱킹으로 시야가 와드도 딜교환을 한타에 운영의 사이드와 본대는 오브젝트까지\n'
                       '[0:02] 라인업 갱년기 운영체제 사이드바 본대학생 오브젝트화 딜교실\n')
        self.assertEqual(len(report['candidates']),1)
        self.assertEqual(report['candidates'][0]['topics'],['WAVE','ROAM','JUNGLE','VISION','TRADE','LANE','TEAMFIGHT','MACRO','SIDE','MAIN_BODY','OBJECTIVE'])

    def test_english_exact_word_behavior_and_mixed_topic_dedup_are_preserved(self):
        report,_=parse('[0:01] wave minion cs roam roaming roams jungle jungler gank ganked vision ward wards trade trades trading\n'
                       '[0:02] waveform roamingly jungleish wardsmith tradesman\n'
                       '[0:03] wave 웨이브를 trade 딜교환을 한타\n',language='en')
        self.assertEqual([c['topics'] for c in report['candidates']],
            [['WAVE','ROAM','JUNGLE','VISION','TRADE'],['WAVE','TRADE','TEAMFIGHT']])
        self.assertEqual([c['cue_index'] for c in report['candidates']],[1,3])

    def test_original_bytes_hash_and_unverified_candidate_shape_remain_exact(self):
        report,raw=parse('[0:01] '+unicodedata.normalize('NFD','웨이브')+'! 한타?\n')
        self.assertEqual(report['transcript_sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(report['format'],'lol-coach-video-index-v1')
        self.assertEqual(len(report['candidates']),1)
        self.assertEqual(report['candidates'][0],dict(cue_index=1,video_time_ms=1000,game_time_ms=None,
            topics=['WAVE','TEAMFIGHT'],kind='SPEECH_REVIEW_CANDIDATE',visual_verified=False,decision_eligible=False))
        self.assertFalse(report['coaching_enabled']);self.assertFalse(report['patch_verified'])
        self.assertNotIn('speech',report['candidates'][0]);self.assertNotIn('웨이브',str(report))

    def test_negation_is_only_topic_search_and_chinese_is_not_inferred(self):
        report,_=parse('[0:01] 한타는 하지 않는다\n[0:02] 兵线 视野 团战 运营\n')
        self.assertEqual([c['topics'] for c in report['candidates']],[['TEAMFIGHT']])
        self.assertFalse(report['candidates'][0]['decision_eligible'])


if __name__=='__main__':unittest.main()
