"""HTTP mechanics only; fixtures never approve gameplay knowledge."""
import copy
import unittest
from tests_pregame import test_http
from tests_pregame.test_contract import golden, rule
from tests_pregame.test_v13 import v2_rule
from coach_v1.pregame_contract import proposal_rule


class V14HTTPTests(unittest.TestCase):
    setUp=test_http.HTTPTests.setUp
    cleanup=test_http.HTTPTests.cleanup
    call=test_http.HTTPTests.call

    def test_status_internal_mode_and_static_asset(self):
        status,body=self.call('/dev/v1/pregame/status')
        self.assertEqual(status,200);self.assertFalse(body['test_mode'])
        self.assertEqual(body['power_tiers'],[]);self.assertIsNone(body['current_patch'])
        self.assertEqual(self.call('/pregame_power.js')[0],200)
        self.assertEqual(self.call('/dev/v1/pregame/status','POST',{'test_mode':True})[0],404)

    def test_version_bound_sources_and_exploratory_only(self):
        for version in [1,2,3]:
            spec=rule() if version==1 else v2_rule()
            spec['schema_version']='pregame.rule.v'+str(version)
            spec['rule_id']='http-source-v'+str(version)
            if version==3:spec['output']['movement']=[]
            status,result=self.call('/dev/v1/pregame/candidates','POST',dict(spec=spec))
            self.assertEqual(status,201);self.assertEqual(result['proposal']['review_state'],'EXPLORATORY')
            rows=self.call('/dev/v1/pregame/knowledge')[1]
            self.assertEqual(next(r for r in rows if r['proposal']['rule_id']==result['proposal']['rule_id'])['spec'],spec)
            ref=result['proposal']['source_refs'][0]
            resource=self.server.research.get(ref['resource_id'])
            self.assertEqual(resource['report']['schema_version'],'pregame.rule-source.v'+str(version))

    def test_mismatched_wrapper_never_binds(self):
        s=v2_rule();s['rule_id']='wrapper-mismatch'
        source=self.server.research.add('RAW_DIAGNOSTIC','Mismatch',dict(schema_version='pregame.rule-source.v1',spec=s))
        n=self.server.research.put_note(source['id'],'overview',dict(known='Synthetic fixture',intention='',alternative='',outcome=''),0)
        self.server.research.propose(proposal_rule(s),dict(resource_id=source['id'],anchor='overview',note_revision=n['revision']),max_bytes=1000000)
        self.assertIsNone(self.call('/dev/v1/pregame/knowledge')[1][0]['spec'])

    def test_new_v3_and_versioned_historical_replay(self):
        from coach_v1.pregame_evaluator import evaluate_gameplan
        from coach_v1.pregame_v2 import evaluate_gameplan_v2
        created=self.call('/dev/v1/pregame/inputs','POST',dict(input=golden()),'v3-input')[1]
        sid=created['session_id']
        old=[]
        for version,evaluator in [(1,evaluate_gameplan),(2,evaluate_gameplan_v2)]:
            p=self.server.pregame.save_plan(sid,1,evaluator(golden(),[]),'historical-'+str(version))
            old.append(p)
            self.assertEqual(self.call('/dev/v1/pregame/plans/'+p['id'])[1]['validity'],'CURRENT')
        status,p=self.call('/dev/v1/pregame/inputs/'+sid+'/plans','POST',dict(expected_revision=1),'new-v3')
        self.assertEqual(status,201);self.assertEqual(p['schema_version'],'pregame.plan.v3')
        self.assertEqual(p['movement']['status'],'UNKNOWN');self.assertIsNone(p['movement_statistics_fingerprint'])
        archive=self.server.pregame.export_data()
        from coach_v1.pregame_store import PregameStore
        self.server.pregame=PregameStore(self.tmp.name+'/http-restored.sqlite')
        self.assertEqual(self.call('/dev/v1/pregame/restore','POST',dict(archive=archive))[0],200)
        self.assertEqual(self.call('/dev/v1/pregame/plans/'+p['id'])[1],p)
        archive=self.server.pregame.export_data()
        # Structural archives may be admissible data; replay never grants them authority.
        restored=PregameStore(self.tmp.name+'/restored.sqlite');restored.import_data(archive)
        from coach_v1.pregame_store import plan_fields
        forged={k:copy.deepcopy(p[k]) for k in plan_fields(p)};forged['movement']['texts']=['forged advice']
        forged=restored.save_plan(sid,1,forged,'forged')
        self.server.pregame=restored
        self.assertIn('PLAN_RESULT_MISMATCH',self.call('/dev/v1/pregame/plans/'+forged['id'])[1]['expiry_reasons'])

    def test_power_auth_exact_fields_and_no_zero_substitution(self):
        request=dict(champion='Caitlyn',position='BOTTOM',patch='16.19',tier=None,opponent_champion='Ezreal')
        path='/dev/v1/pregame/power-view'
        self.assertEqual(self.call(path,'POST',request,auth=False)[0],401)
        status,response=self.call(path,'POST',request)
        self.assertEqual(status,200);self.assertEqual(response['view']['status'],'UNKNOWN')
        self.assertEqual(response['view']['points'],[]);self.assertFalse(response['test_mode'])
        for mutation in [dict(request,test_mode=True),dict(request,position='ADC'),dict(request,champion={'raw':'private'}),dict(request,tier='ALL'),dict(request,patch=True),dict(request,champion='x'*101)]:
            self.assertEqual(self.call(path,'POST',mutation)[0],422)
        self.assertEqual(self.call(path,'GET')[0],404)

    def test_catalog_additive_supplement_preserves_ids_and_no_approval(self):
        status,rows=self.call('/dev/v1/pregame/candidates')
        self.assertEqual(status,200);self.assertEqual(len(rows),190)
        self.assertEqual(sum(r['schema_version']=='pregame.rule.v2' for r in rows),13)
        self.assertEqual(self.call('/dev/v1/pregame/knowledge')[1],[])


if __name__=='__main__':unittest.main()
