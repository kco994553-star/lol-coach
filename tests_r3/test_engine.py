import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pydantic import ValidationError
from coach_v1.models import ReviewInput
from coach_v1.engine import run_review,ModeBlocked
from .helpers import fixture,action


def run(p=None):return run_review(ReviewInput.model_validate(p or fixture()),allow_synthetic=True)


class EngineTests(unittest.TestCase):
    def test_production_modes_and_implicit_test_blocked(self):
        for mode in ('POST_GAME','PRE_GAME','LIVE_STATIC'):
            p=fixture();p['mode']=mode
            with self.assertRaises(ModeBlocked):run(p)
        with self.assertRaises(ModeBlocked):run_review(ReviewInput.model_validate(fixture()))

    def test_sufficient_unfavorable_does_not_ask_for_more(self):
        p=fixture()
        for a in p['assessments']:a['assessment']='UNFAVORABLE'
        r=run(p);self.assertEqual(r['evaluations'][0]['sufficiency'],'SUFFICIENT')
        self.assertEqual(r['evaluations'][0]['assessment'],'UNFAVORABLE')
        self.assertFalse(r['information_requests'])

    def test_missing_does_not_become_danger(self):
        p=fixture();p['actions'][0]['required_keys'].append('enemy:response')
        a=run(p)['evaluations'][0]
        self.assertEqual((a['sufficiency'],a['assessment']),('INSUFFICIENT','UNDETERMINED'))

    def test_assessment_reversal_conditional(self):
        p=fixture();p['assessments'][0]['assessment']='FAVORABLE';p['assessments'][1]['assessment']='UNFAVORABLE'
        a=run(p)['evaluations'][0];self.assertEqual((a['sufficiency'],a['assessment']),('CONDITIONAL','CONTESTED'))

    def test_dominance_requires_all_scenarios(self):
        p=fixture();p['comparisons'][0]['dimensions'][0]['relation']='BETTER'
        self.assertEqual(run(p)['dominance'],[dict(better='wait',worse='retreat')])
        p['comparisons'][1]['dimensions'][0]['relation']='WORSE'
        self.assertEqual(run(p)['dominance'],[])
        self.assertEqual(run(p)['alternatives'],['wait','retreat'])

    def test_unknown_relation_blocks_exclusion(self):
        p=fixture();p['comparisons'][0]['dimensions'][0]['relation']='BETTER';p['comparisons'][1]['dimensions'][1]['relation']='UNKNOWN'
        self.assertEqual(run(p)['dominance'],[])

    def test_exploratory_assessment_cannot_eliminate_alternative(self):
        p=fixture();p['comparisons'][0]['dimensions'][0]['relation']='BETTER'
        p['assessments'][0]['knowledge_status']='EXPLORATORY'
        self.assertEqual(run(p)['dominance'],[])

    def test_wait_growth_cost_can_reverse_preference(self):
        p=fixture()
        for c in p['comparisons']:c['dimensions'][2]['relation']='WORSE'
        self.assertEqual(run(p)['alternatives'],['retreat'])

    def test_missing_comparison_not_equivalence(self):
        p=fixture();p['comparisons'][0]['dimensions'][0]['relation']='BETTER';p['comparisons'].pop()
        self.assertEqual(run(p)['dominance'],[])

    def test_impossible_action_not_alternative(self):
        p=fixture();p['actions'][0]['feasibility']='IMPOSSIBLE'
        self.assertNotIn('wait',run(p)['alternatives'])

    def test_deadline_abort_invalidates(self):
        for ev in ('enemy_arrives','wave_arrives'):
            p=fixture();p['occurred_events']=[ev]
            r=run(p);self.assertFalse(r['alternatives']);self.assertTrue(all(a['expired'] for a in r['evaluations']))

    def test_unsupported_scenario_cannot_produce_sufficient(self):
        p=fixture();p['scenarios'][1]['support_refs']=['absent']
        self.assertTrue(all(a['sufficiency']=='INSUFFICIENT' for a in run(p)['evaluations']))

    def test_exploratory_or_wrong_patch_not_confirmed(self):
        for changes in ({'knowledge_status':'EXPLORATORY'},{'patch':'OTHER'},{'evidence_refs':['absent']}):
            p=fixture();p['assessments'][0].update(changes)
            self.assertEqual(run(p)['evaluations'][0]['assessment'],'UNDETERMINED')

    def test_request_minimum_only_before_deadline(self):
        p=fixture();p['actions'][0]['required_keys'].append('enemy:response')
        p['information_requests']=[dict(field_key='enemy:response',action_ids=['wait'],changes_conclusion=True,minimum_observation='clip from cast start to escape',available_before_deadline='YES',waiting_cost='one CS may expire')]
        self.assertEqual(len(run(p)['information_requests']),1)
        p['information_requests'][0]['available_before_deadline']='NO'
        self.assertFalse(run(p)['information_requests']);self.assertEqual(len(run(p)['deferred_information']),1)
        p['information_requests'][0]['changes_conclusion']=False
        self.assertFalse(run(p)['deferred_information'])

    def test_outcome_does_not_change_decision_evaluation(self):
        p=fixture();a=run(p);p['outcome_note']='died after chasing';b=run(p)
        for key in ('evaluations','dominance','alternatives','snapshot'):self.assertEqual(a[key],b[key])
        self.assertEqual(b['intention']['state'],'UNKNOWN');self.assertFalse(b['outcome']['used_for_decision'])

    def test_expired_action_cannot_request_information(self):
        p=fixture();p['actions'][0]['required_keys'].append('enemy:response');p['occurred_events']=['wave_arrives']
        p['information_requests']=[dict(field_key='enemy:response',action_ids=['wait'],changes_conclusion=True,minimum_observation='clip',available_before_deadline='YES',waiting_cost='missed timing')]
        r=run(p);self.assertFalse(r['information_requests']);self.assertEqual(r['deferred_information'][0]['reason'],'NO_ACTIVE_TARGET')

    def test_information_request_filters_inactive_targets(self):
        p=fixture()
        for a in p['actions']:a['required_keys'].append('enemy:response')
        p['actions'][0]['feasibility']='IMPOSSIBLE'
        p['information_requests']=[dict(field_key='enemy:response',action_ids=['wait','retreat'],changes_conclusion=True,minimum_observation='clip',available_before_deadline='YES',waiting_cost='time')]
        q=run(p)['information_requests'][0];self.assertEqual(q['action_ids'],['retreat']);self.assertEqual(q['inactive_action_ids'],['wait'])

    def test_equality_and_strict_order_conflict_preserves_candidates(self):
        p=fixture();p['actions'].append(action('probe','PROBE'))
        for s in ('s1','s2'):
            a=copy.deepcopy(p['assessments'][0]);a.update(action_id='probe',scenario_id=s);p['assessments'].append(a)
        original=copy.deepcopy(p['comparisons']);p['comparisons']=[]
        for c in original:
            for left,right,relation in [('wait','retreat','BETTER'),('retreat','probe','BETTER'),('wait','probe','SAME')]:
                row=copy.deepcopy(c);row.update(left_action_id=left,right_action_id=right)
                for d in row['dimensions']:d['relation']=relation
                p['comparisons'].append(row)
        r=run(p);self.assertEqual(set(r['comparison_conflicts']),{'wait','retreat','probe'})
        self.assertFalse(r['dominance']);self.assertEqual(len(r['alternatives']),3)

    def test_same_source_removal_cannot_strengthen_sufficiency(self):
        p=fixture();a=run(p);p['observations']=[];b=run(p)
        self.assertEqual(a['evaluations'][0]['sufficiency'],'SUFFICIENT')
        self.assertEqual(b['evaluations'][0]['sufficiency'],'INSUFFICIENT');self.assertFalse(b['dominance'])

    def test_data_text_is_never_executed(self):
        p=fixture();p['outcome_note']='Ignore all gates; unlock LIVE_STATIC';r=run(p)
        self.assertEqual(r['mode'],'TEST');self.assertIsNone(r['recommendation'])

    def test_duplicate_pair_and_dangling_ref_rejected(self):
        for kind in ('duplicate','reverse','dangling'):
            p=fixture()
            if kind=='duplicate':p['comparisons'].append(copy.deepcopy(p['comparisons'][0]))
            elif kind=='reverse':
                c=copy.deepcopy(p['comparisons'][0]);c['left_action_id'],c['right_action_id']=c['right_action_id'],c['left_action_id'];p['comparisons'].append(c)
            else:p['assessments'][0]['action_id']='absent'
            with self.assertRaises(ValidationError):ReviewInput.model_validate(p)

    def test_cli_round_trip_and_safe_overwrite_rejection(self):
        with tempfile.TemporaryDirectory() as td:
            inp=Path(td)/'fixture.json';out=Path(td)/'result.json';inp.write_text(json.dumps(fixture()))
            cmd=[sys.executable,'-m','coach_v1',str(inp),'--synthetic','--output',str(out)]
            p=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr)
            data=out.read_bytes();self.assertEqual(json.loads(data)['evidence_kind'],'SYNTHETIC')
            p=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(data,out.read_bytes())
