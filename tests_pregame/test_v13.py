"""Synthetic contract mechanics, never gameplay knowledge or user approval."""
import copy
import tempfile
from pathlib import Path
import unittest
from tests_pregame.test_contract import golden,rule
from tests_pregame.test_evaluator import approved
from coach_v1.pregame_contract import parse_input,parse_rule,proposal_rule
from coach_v1.pregame_evaluator import evaluate_gameplan
from coach_v1.state import digest


def guard():
    return dict(preconditions=[dict(field='ALLY_MINIMAP',text='SYNTHETIC prerequisite')],
                invalidation_signals=[dict(field='GAME_TIME',text='SYNTHETIC invalidation')],alternative='SYNTHETIC alternative')


def v2_rule(section='ROLE',position='BOTTOM'):
    s=rule(section,position);s['schema_version']='pregame.rule.v2'
    s['plan_guard']=guard();s['output']['operations']=None
    if section=='OPERATIONS':
        s.update(scope='POSITION',positions=[position])
        s['output']['operations']=dict(opening_allies=['JUNGLE'],pressure_allies=['TOP'],win_condition_allies=['BOTTOM'],
            dependencies=[dict(position='JUNGLE',required_play='SYNTHETIC required play')],
            minimum_plays=[dict(position='JUNGLE',plays=['SYNTHETIC play'])],request_templates=['SYNTHETIC request'],
            solo_alternative='SYNTHETIC alternative',pick_candidates=[])
    return s


def v2_profile(champion,initiative,needs=None):
    s=v2_rule('PROFILE');s.update(rule_id='profile-'+champion,scope='COMMON',positions=[],plan_guard=None)
    s['output']['target']='GLOBAL'
    s['profile']=dict(champion=champion,roles=[],threats=[],protection=[],strong_when=[],lane_style=[],jungle_style=[],
                      initiative=initiative,needs=needs or [],necessary_conditions=['SYNTHETIC mechanic'])
    return s


def v2_input(position='BOTTOM',patch='SYNTHETIC-1'):
    return dict(golden(position,patch),schema_version='pregame.input-draft.v2',my_pick_state='PICKED',frequent_champions=['Ashe','Caitlyn'])


class V13Tests(unittest.TestCase):
    def evaluate(self,d=None,knowledge=None):
        from coach_v1.pregame_v2 import evaluate_gameplan_v2
        return evaluate_gameplan_v2(d or golden(patch='SYNTHETIC-1'),knowledge or [])

    def test_v1_raw_and_binding_digest_remain_exact(self):
        s=rule();self.assertEqual(parse_rule(s).model_dump(mode='json'),s)
        self.assertEqual(parse_input(golden()).model_dump(mode='json'),golden())
        self.assertEqual(proposal_rule(s)['required_fields'][0],'EXECUTABLE_V1_SHA256:'+digest(s))

    def test_typed_guard_whitelist_and_v2_binding(self):
        s=v2_rule();self.assertEqual(parse_rule(s).model_dump(mode='json'),s)
        self.assertEqual(proposal_rule(s)['required_fields'][0],'EXECUTABLE_V2_SHA256:'+digest(s))
        for field in ['ENEMY_POSITION','ALLY_COOLDOWN','ENEMY_JUNGLE_LAST_SEEN']:
            bad=copy.deepcopy(s);bad['plan_guard']['invalidation_signals'][0]['field']=field
            with self.assertRaises(ValueError):parse_rule(bad)
        for g in [None,dict(guard(),preconditions=[]),dict(guard(),alternative=' ')]:
            bad=copy.deepcopy(s);bad['plan_guard']=g
            with self.assertRaises(ValueError):parse_rule(bad)

    def test_explicit_unpicked_and_preferences_not_inferred(self):
        d=v2_input();self.assertEqual(parse_input(d).model_dump(mode='json'),d)
        d['my_pick_state']='UNPICKED'
        with self.assertRaises(ValueError):parse_input(d)
        d['my_champion']=None
        with self.assertRaises(ValueError):parse_input(d)
        d['slots'][3]['champion']=None
        self.assertEqual(parse_input(d).my_pick_state,'UNPICKED')
        d['my_pick_state']='PICKED'
        with self.assertRaises(ValueError):parse_input(d)

    def test_v2_operating_cell_only_from_current_reviewed_exact_binding(self):
        s=v2_rule('OPERATIONS')
        p=self.evaluate(knowledge=[approved(s)])
        self.assertEqual(p['schema_version'],'pregame.plan.v2')
        self.assertEqual(p['operations']['status'],'KNOWN')
        self.assertEqual(p['operations']['rules'][0]['spec']['plan_guard'],guard())
        for state in ['EXPLORATORY','REJECTED']:
            q=self.evaluate(knowledge=[approved(s,state)])
            self.assertEqual(q['operations']['status'],'UNKNOWN');self.assertEqual(q['operations']['texts'],[])
        item=approved(s);item['spec']['plan_guard']['alternative']='changed after approval'
        self.assertEqual(self.evaluate(knowledge=[item])['operations']['status'],'UNKNOWN')

    def test_linked_unknown_role_holds_operating_template(self):
        d=golden(patch='SYNTHETIC-1');d['slots'][1].update(position=None,position_candidates=['JUNGLE','MID'])
        p=self.evaluate(d,[approved(v2_rule('OPERATIONS'))])
        self.assertEqual(p['operations']['status'],'UNKNOWN')
        self.assertIn('OPERATING_ALLY_UNKNOWN',p['operations']['reasons'])

    def test_missing_initiative_not_counted_as_zero(self):
        p=self.evaluate(knowledge=[approved(v2_profile('Caitlyn',['FOLLOW_UP'],['ALLY_INITIATION']))])
        self.assertEqual(p['team_dependencies']['status'],'UNKNOWN')
        self.assertIsNone(p['team_dependencies']['initiator_count'])
        self.assertIsNone(p['team_dependencies']['dependency_risk'])

    def test_reviewed_complete_allies_followup_zero_or_single_risk(self):
        champs=['Ornn','Sejuani','Ahri','Caitlyn','Lux']
        specs=[v2_profile(c,['FOLLOW_UP'] if c=='Caitlyn' else ['PROTECTOR']) for c in champs]
        p=self.evaluate(knowledge=[approved(s) for s in specs])
        self.assertEqual(p['team_dependencies']['dependency_risk'],'NO_INITIATOR')
        specs[1]['profile']['initiative']=['INITIATOR']
        p=self.evaluate(knowledge=[approved(s) for s in specs])
        self.assertEqual(p['team_dependencies']['initiator_count'],1)
        self.assertEqual(p['team_dependencies']['dependency_risk'],'SINGLE_INITIATOR')
        specs[0]['profile']['initiative']=['INITIATOR']
        self.assertEqual(self.evaluate(knowledge=[approved(s) for s in specs])['team_dependencies']['dependency_risk'],'NONE')

    def test_conflicting_profile_and_outputs_keep_evidence_withhold_risk(self):
        a=v2_profile('Caitlyn',['FOLLOW_UP']);b=copy.deepcopy(a);b['rule_id']='other-caitlyn';b['profile']['initiative']=['INITIATOR']
        p=self.evaluate(knowledge=[approved(a),approved(b)])
        self.assertIsNone(p['team_dependencies']['dependency_risk'])
        a=v2_rule('OPERATIONS');a['output']['outlook']='FAVORABLE'
        b=copy.deepcopy(a);b['rule_id']='different';b['output']['outlook']='UNFAVORABLE'
        p=self.evaluate(knowledge=[approved(a),approved(b)])
        self.assertEqual(p['operations']['status'],'CONFLICTING')
        self.assertEqual(len(p['operations']['rules']),2)
        self.assertEqual(p['pick_warnings'],[])

    def test_v2_common_invariance_and_personal_eight_card_routing(self):
        specs=[]
        for role in ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']:
            s=v2_rule('OPERATIONS',role);s['rule_id']='ops-'+role;s['output']['text']='SYNTHETIC operating '+role;specs.append(s)
        plans=[self.evaluate(golden(r,'SYNTHETIC-1'),[approved(s) for s in specs]) for r in ['TOP','JUNGLE','MID','BOTTOM','SUPPORT']]
        self.assertTrue(all(p['common']==plans[0]['common'] for p in plans))
        self.assertEqual(len({p['operations']['texts'][0] for p in plans}),5)

    def test_pick_warnings_require_explicit_unpicked_preferences_and_reviewed_candidate(self):
        ops=v2_rule('OPERATIONS');ops['output']['operations']['pick_candidates']=[dict(champion='Ashe',reason='SYNTHETIC recommendation')]
        candidate=v2_profile('Ashe',['INITIATOR'])
        ops['output']['operations']['win_condition_allies']=[]
        d=golden(patch='SYNTHETIC-1');d['my_champion']=None;d['slots'][3]['champion']=None
        self.assertEqual(self.evaluate(d,[approved(ops),approved(candidate)])['pick_warnings'],[])
        d=dict(d,schema_version='pregame.input-draft.v2',my_pick_state='UNPICKED',frequent_champions=['Ashe'])
        self.assertEqual(self.evaluate(d,[approved(ops)])['pick_warnings'],[])
        profiles=[v2_profile(c,['PROTECTOR']) for c in ['Ornn','Sejuani','Ahri','Lux']]
        k=[approved(s) for s in [ops,candidate,*profiles]]
        self.assertEqual(self.evaluate(d,[approved(ops),approved(candidate)])['pick_warnings'],[])
        self.assertEqual(self.evaluate(d,k)['pick_warnings'][0]['champion'],'Ashe')
        profiles[0]['profile']['initiative']=['INITIATOR'];profiles[1]['profile']['initiative']=['INITIATOR']
        self.assertEqual(self.evaluate(d,[approved(s) for s in [ops,candidate,*profiles]])['pick_warnings'],[])
        d['my_pick_state']='UNKNOWN'
        self.assertEqual(self.evaluate(d,[approved(ops),approved(candidate)])['pick_warnings'],[])

    def test_v2_store_restart_export_restore_and_replay_preserve_guards(self):
        from coach_v1.pregame_store import PregameStore
        from coach_v1.pregame_evaluator import knowledge_fingerprint
        k=[approved(v2_rule('OPERATIONS'))]
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'sidecar';store=PregameStore(path)
            r=store.save(v2_input(),None,0,'input')
            p=store.save_plan(r['session_id'],1,self.evaluate(r['input'],k),'plan')
            reopened=PregameStore(path)
            self.assertEqual(reopened.get_plan(p['id'],knowledge_fingerprint(k))['operations'],p['operations'])
            archive=reopened.export_data();restored=PregameStore(Path(td)/'restored');restored.import_data(archive)
            self.assertEqual(restored.export_data(),archive)
            restored.save(v2_input('TOP'),r['session_id'],1,'newrole')
            replay=restored.replay_plan(r['session_id'],1,'plan')
            self.assertEqual(replay,p)
            self.assertEqual(restored.get_plan(p['id'],knowledge_fingerprint(k))['validity'],'EXPIRED')

    def test_prohibited_blame_templates_rejected(self):
        s=v2_rule('OPERATIONS');
        for phrase in ['정글 차이 때문에 졌다','jungle diff','support diff','정글\t차이 때문에 졌다','jungle\ndiff']:
            s['output']['operations']['request_templates']=[phrase]
            with self.assertRaises(ValueError):parse_rule(s)

if __name__=='__main__':unittest.main()
