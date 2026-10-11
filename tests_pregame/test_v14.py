"""Synthetic version and immutable-history checks for Q18, no gameplay approvals."""
import copy
from pathlib import Path
import tempfile
import unittest
from tests_pregame.test_v13 import v2_rule,v2_input
from coach_v1.pregame_contract import parse_rule,proposal_rule
from coach_v1.state import digest


def stage_role(position='BOTTOM'):
    return dict(stage='LATE',layer='DEFAULT',subject='SELF',position=position,location='MAIN_GROUP',
        role='SYNTHETIC phase role',why='SYNTHETIC rationale',exceptions=['SYNTHETIC exception'],
        stage_conditions=[dict(field='LONG_RESPAWN_RISK',value=True)],overrides=[],statistics_ref=None)


def v3_rule(position='BOTTOM'):
    s=v2_rule('MOVEMENT',position);s['schema_version']='pregame.rule.v3'
    s['output']['movement']=[stage_role(position)]
    return s


class V14Tests(unittest.TestCase):
    def test_v3_exact_binding_and_v2_bytes_preserved(self):
        old=v2_rule();self.assertEqual(parse_rule(old).model_dump(mode='json'),old)
        s=v3_rule();self.assertEqual(parse_rule(s).model_dump(mode='json'),s)
        self.assertEqual(proposal_rule(s)['required_fields'][0],'EXECUTABLE_V3_SHA256:'+digest(s))

    def test_stage_state_conditions_strict_and_no_minute_classifier(self):
        for mutate in [lambda r:r.update(minute=25),lambda r:r.update(stage_conditions=[]),
                       lambda r:r['stage_conditions'].append(dict(field='LONG_RESPAWN_RISK',value=False)),
                       lambda r:r.update(stage='EARLY'),lambda r:r.update(stage_conditions=[dict(field='LONG_RESPAWN_RISK',value=False)]),lambda r:r.update(exceptions=[]),lambda r:r.update(why=' '),
                       lambda r:r.update(statistics_ref=dict(dataset_sha256='bad',cohort_id='x'))]:
            s=v3_rule();mutate(s['output']['movement'][0])
            with self.assertRaises(ValueError):parse_rule(s)

    def test_scope_and_section_isolation(self):
        s=v3_rule();s.update(scope='COMMON',positions=[])
        with self.assertRaises(ValueError):parse_rule(s)
        s=v3_rule();s['output']['section']='ROLE'
        with self.assertRaises(ValueError):parse_rule(s)

    def test_nine_card_unknown_without_movement_data_and_accuracy_null(self):
        from coach_v1.pregame_v3 import evaluate_gameplan_v3
        p=evaluate_gameplan_v3(v2_input(),[])
        self.assertEqual(p['schema_version'],'pregame.plan.v3')
        self.assertEqual(p['movement']['status'],'UNKNOWN')
        self.assertIsNone(p['movement_statistics_fingerprint'])
        self.assertIsNone(p['coaching_accuracy'])

    def test_unpicked_v3_profile_has_same_candidate_behavior_as_v2(self):
        from tests_pregame.test_v13 import v2_profile
        from tests_pregame.test_evaluator import approved
        from coach_v1.pregame_v3 import evaluate_gameplan_v3
        d=v2_input();d.update(my_pick_state='UNPICKED',my_champion=None,frequent_champions=['Ashe'])
        d['slots'][3]['champion']=None
        ops=v2_rule('OPERATIONS');ops['output']['operations']['win_condition_allies']=[]
        ops['output']['operations']['pick_candidates']=[dict(champion='Ashe',reason='SYNTHETIC recommendation')]
        profiles=[v2_profile(c,['PROTECTOR']) for c in ['Ornn','Sejuani','Ahri','Lux']]
        candidate=v2_profile('Ashe',['INITIATOR']);candidate['schema_version']='pregame.rule.v3';candidate['output']['movement']=[]
        p=evaluate_gameplan_v3(d,[approved(s) for s in [ops,candidate,*profiles]])
        self.assertEqual(p['pick_warnings'][0]['champion'],'Ashe')

    def test_v3_store_restart_restore_exact_and_unknown_support(self):
        from coach_v1.pregame_v3 import evaluate_gameplan_v3
        from coach_v1.pregame_store import PregameStore
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'sidecar';store=PregameStore(path)
            r=store.save(v2_input(),None,0,'input');result=evaluate_gameplan_v3(r['input'],[])
            p=store.save_plan(r['session_id'],1,result,'plan')
            self.assertEqual(store.replay_plan(r['session_id'],1,'plan'),p)
            archive=PregameStore(path).export_data();restored=PregameStore(Path(td)/'restored')
            restored.import_data(archive);self.assertEqual(restored.export_data(),archive)
            bad=copy.deepcopy(archive);bad['plans'][0]['movement_statistics_fingerprint']='forged'
            with self.assertRaises(Exception):PregameStore(Path(td)/'bad').import_data(bad)
