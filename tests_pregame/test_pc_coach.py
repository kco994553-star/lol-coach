import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from coach_v1.server import Limits
from coach_v1.pregame_server import PregameWorkbench


def draft(champion='Caitlyn',phase='PRE_GAME',patch='16.20'):
    source=dict(kind='MANUAL',reference='검증용 수동 입력',observed_at=None,verification='UNVERIFIED')
    teams={'ALLY':['Ornn','Sejuani','Ahri',champion,'Lux'],'ENEMY':['Fiora','LeeSin','Zed','Ezreal','Nautilus']}
    positions=['TOP','JUNGLE','MID','BOTTOM','SUPPORT']
    return dict(title='합성 예시',patch=patch,phase=phase,observed_at=None,my_position='BOTTOM',my_champion=champion,my_slot=4,
        slots=[dict(side=side,slot=i+1,champion=c,position=positions[i],position_candidates=[],uncertainty='합성',champion_source=source,position_source=source,runes=dict(status='UNKNOWN',values=[],source=source),summoners=dict(status='UNKNOWN',values=[],source=source)) for side,champions in teams.items() for i,c in enumerate(champions)],source=source,original_capture=None)


class PcCoachTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.server=PregameWorkbench(Path(self.tmp.name)/'app.sqlite','x'*32,Limits(2_000_000,100,100,100,100,4))
        self.addCleanup(self.server.server_close)

    def test_stage_and_badges_and_no_user_approval(self):
        from coach_v1.pc_coach import preview
        result=preview(self.server,dict(input=draft()))
        self.assertEqual(result['stage'],'COMPOSITION')
        self.assertTrue(any(c['evidence_level']=='OFFICIAL' for c in result['cards']))
        self.assertTrue(all(len(c['lines'])<=3 and c['evidence_label'] for c in result['cards']))
        self.assertEqual(self.server.research.list(),[])

    def test_patch_unknown_and_unknown_phase_do_not_expose_tactics(self):
        from coach_v1.pc_coach import preview
        for value in [draft(patch=None),draft(phase='UNKNOWN')]:
            result=preview(self.server,dict(input=value))
            self.assertFalse(any(c['evidence_level'] in ('AUTO_VERIFIED','HYPOTHESIS','USER') for c in result['cards']))

    def test_objection_removes_matching_candidate_immediately(self):
        from coach_v1.pc_coach import preview,objection
        result=preview(self.server,dict(input=draft()))
        candidate=next(c for c in result['cards'] if c.get('candidate_id'))
        objection(self.server,dict(candidate_id=candidate['candidate_id'],candidate_sha256=candidate['candidate_sha256'],reason='条件の見直し'))
        changed=preview(self.server,dict(input=draft()))
        self.assertFalse(any(c.get('candidate_id')==candidate['candidate_id'] for c in changed['cards']))
        self.assertEqual(self.server.research.list(),[])

    def test_wrong_ally_does_not_show_lux_specific_advice(self):
        from coach_v1.pc_coach import preview
        value=draft();value['slots'][4]['champion']='Morgana'
        result=preview(self.server,dict(input=value))
        self.assertNotIn('KR-007',[c.get('candidate_id') for c in result['cards']])

    def test_observed_game_start_overrides_stale_manual_phase(self):
        from coach_v1.pc_coach import preview
        class Services:
            def snapshot(self):return dict(phase='InProgress',status='MANUAL_FALLBACK')
        self.server.pc_services=Services()
        result=preview(self.server,dict(input=draft()))
        self.assertEqual(result['phase'],'UNKNOWN')
        self.assertFalse(any(c.get('candidate_id') for c in result['cards']))

    def test_source_backed_held_advice_is_explicit_hypothesis(self):
        from coach_v1.pc_coach import preview
        from coach_v1.auto_review import assess
        held=assess()
        for row in held['rows']:row.update(state='HOLD',reasons=['반론 검사가 아직 끝나지 않았습니다.'])
        held.update(passed=0,held=30)
        with patch('coach_v1.pc_coach.assess',return_value=held):result=preview(self.server,dict(input=draft()))
        hypotheses=[c for c in result['cards'] if c['evidence_level']=='HYPOTHESIS']
        self.assertTrue(hypotheses)
        self.assertTrue(all(c['evidence_label']=='미검토 가설(AI 작성, 근거 링크)' and c['sources'] for c in hypotheses))
        original=[c for c in hypotheses if not c.get('revision_of')]
        revised=[c for c in hypotheses if c.get('revision_of')]
        self.assertTrue(original)
        self.assertTrue(revised)
        self.assertTrue(all('검토 보류:' in c['details'] for c in original))
        self.assertTrue(all('보류 이유·필요한 자료:' in c['details'] for c in revised))

    def test_source_integrity_failure_is_not_even_shown_as_hypothesis(self):
        from coach_v1.pc_coach import preview
        with patch('coach_v1.pc_coach.machine_check',return_value=['SOURCE_INVALID']):result=preview(self.server,dict(input=draft()))
        self.assertFalse(any(c.get('candidate_id') for c in result['cards']))

    def test_unreadable_original_sources_also_hide_revised_hypotheses(self):
        from coach_v1.pc_coach import preview
        baseline=preview(self.server,dict(input=draft()))
        self.assertTrue(any(c.get('revision_of') for c in baseline['cards']))
        with patch('coach_v1.auto_review._source_material',side_effect=OSError('source unavailable')):
            result=preview(self.server,dict(input=draft()))
        self.assertFalse(any(c.get('candidate_id') for c in result['cards']))

