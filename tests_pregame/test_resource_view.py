"""Only the new measured-time PC projection, no old browser or provider calls."""
import unittest
from coach_v1 import resource_view as view
from coach_v1.resource_recovery import audit_private_cache
from tests_pregame.test_resource_recovery import envelope
from coach_v1.postgame_match import PostgameStore
from pathlib import Path
import tempfile

class ResourceViewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.store=PostgameStore(self.root/'private'/'matches')
        self.store.import_match(envelope())
        self.report=audit_private_cache(self.root)
        c=self.report['cohorts'][0]
        self.draft=dict(my_champion=c['champion'],my_position=c['position'],patch=c['patch'],slots=[dict(side='ENEMY',position=c['position'],champion=c['opponent_champion'])],phase='PRE_GAME')
        self.binding=dict(report_sha256='a'*64)
    def test_observed_bin_card_has_actual_time_n_missing_and_separate_exact(self):
        cards=view.render_cards(self.report,self.binding,self.draft)
        self.assertEqual(len(cards),1);c=cards[0]
        self.assertEqual(c['evidence_level'],'STATISTICS')
        self.assertEqual(len(c['lines']),3)
        self.assertIn('10분 구간',c['lines'][1])
        for value in ['실제 관측 시각','600120','경험치','유효 1','누락 0','정확히 10분','보간하지 않습니다','행동의 우열']:
            self.assertIn(value,c['details'])
        self.assertEqual(c['sources'][0]['sha256'],'a'*64)
    def test_no_role_pool_fallback_or_patch_substitution(self):
        for change in [dict(patch='16.99'),dict(my_champion='Ashe'),dict(slots=[dict(side='ENEMY',position='TOP',champion='Ashe')]),dict(phase='IN_GAME')]:
            self.assertEqual(view.render_cards(self.report,self.binding,dict(self.draft,**change)),[])
    def test_unknown_values_are_not_zero(self):
        b=envelope();b['timeline']['info']['frames']=[f for f in b['timeline']['info']['frames'] if f['timestamp']<600000]
        b['match']['info']['gameDuration']=590
        root=Path(self.temp.name)/'second'
        PostgameStore(root/'private'/'matches').import_match(b)
        r=audit_private_cache(root)
        c=view.render_cards(r,self.binding,self.draft)[0]
        self.assertEqual(c['evidence_level'],'UNKNOWN')
        self.assertIn('미확인',c['lines'][1]);self.assertNotIn('차이 0',c['details'])
    def test_missing_bound_report_does_not_break_existing_cards(self):
        self.assertEqual(view.cards_for_draft(self.draft,Path(self.temp.name)/'missing'),[])
