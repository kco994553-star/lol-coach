"""Pure SYNTHETIC fixtures: no decisions, authority tokens, or provider calls."""
import copy
import importlib.util
import unittest

from coach_v1.pregame_contract import proposal_rule
from coach_v1.pregame_evaluator import knowledge_fingerprint
from coach_v1.pregame_v3 import evaluate_gameplan_v3
from coach_v1.power_stats import build_power_dataset
from coach_v1.state import digest
from tests_pregame.test_contract import golden, rule
from tests_pregame.test_movement import source
from tests_pregame.test_v20_postgame import body


class OpponentRightsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.opponent_rights'), 'opponent-right adapter missing')
        from coach_v1 import opponent_rights
        self.m = opponent_rights
        spec = rule(); spec['patches'] = ['16.19']
        spec['output']['text'] = 'SYNTHETIC explicit opponent may engage assertion under declared conditions.'
        spec['conditions'] = [dict(field='ally.BOTTOM.champion', op='EQ', value='Caitlyn')]
        proposal = dict(proposal_rule(spec), rule_id='1'*32, version='2'*32,
            review_state='REVIEWED', supersedes=None,
            source_refs=[dict(resource_id='a'*64, anchor='overview', note_revision=1,
                kind='RAW_DIAGNOSTIC', report_sha256='b'*64, note_sha256='c'*64)])
        self.knowledge = [dict(proposal=proposal, spec=spec)]
        self.plan = self.make_plan()
        pairs = []
        for i in (1, 2):
            pair = body(); pair['match']['info']['gameStartTimestamp'] = 100000
            pair['match']['metadata']['matchId'] = pair['timeline']['metadata']['matchId'] = 'KR_'+str(i)
            pairs.append(pair)
        src = source(); src['tier'] = 'CHALLENGER'
        self.data = build_power_dataset(pairs, source=src)
        self.cohort = next(c for c in self.data['cohorts'] if c['champion']=='Caitlyn' and c['position']=='BOTTOM' and c['metric']=='gold_delta' and c['comparison']=='ROLE_POPULATION')
        self.annotation = dict(card_key='ROLE', rule_id=proposal['rule_id'], selected_version=proposal['version'],
            spec_sha256=digest(spec), source_ref=copy.deepcopy(proposal['source_refs'][0]),
            assertion=dict(kind='MANUAL_REVIEWED_RIGHT_ASSERTION', right='opponent may engage',
                claim=proposal['claim'], classification='RISK_IF_OPPONENT_USES_RIGHT'),
            statistics=[dict(dataset_sha256=digest(self.data), cohort_sha256=digest(self.cohort), minute=1)])

    def make_plan(self, draft=None):
        plan = evaluate_gameplan_v3(draft or golden(patch='16.19'), self.knowledge)
        plan['validity'] = 'CURRENT'
        return plan

    def build(self, **overrides):
        args = dict(plan=self.plan, knowledge=self.knowledge, power_datasets=[self.data],
            annotations=[self.annotation], test_mode=True)
        args.update(overrides)
        return self.m.build_rights(**args)

    def card(self, result, key='ROLE'):
        return next(c for c in result['cards'] if c['key']==key)

    def test_no_approved_knowledge_leaves_all_five_position_nine_cards_unknown(self):
        for position in ('TOP','JUNGLE','MID','BOTTOM','SUPPORT'):
            plan=evaluate_gameplan_v3(golden(position,patch='16.19'),[]);plan['validity']='CURRENT'
            result=self.build(plan=plan,knowledge=[],annotations=[])
            self.assertEqual(len(result['cards']),9)
            self.assertTrue(all(c['status']=='UNKNOWN' and c['label']=='미확인' for c in result['cards']))
            self.assertIsNone(result['coaching_accuracy'])

    def test_statistics_and_ordinary_reviewed_claim_never_infer_rights(self):
        card=self.card(self.build(annotations=[]))
        self.assertEqual(card['status'],'UNKNOWN')
        self.assertIn('EXPLICIT_REVIEWED_RIGHT_ASSERTION_REQUIRED',card['reasons'])

    def test_exact_manual_reviewed_assertion_and_descriptive_point_enable_risk(self):
        try:self.m.validate_right_annotations([self.annotation])
        except ValueError:self.fail('actual immutable report/note source binding must be accepted')
        card=self.card(self.build())
        self.assertEqual(card['status'],'RISK_IF_OPPONENT_USES_RIGHT')
        self.assertEqual(card['label'],'상대가 권리를 쓰면 위험')
        self.assertEqual(card['evidence'][0]['claim'],self.annotation['assertion']['claim'])
        self.assertEqual(card['statistics'][0]['tier'],'CHALLENGER')
        self.assertEqual(card['statistics'][0]['inference'],'DESCRIPTIVE_NON_CAUSAL')

    def test_safe_classification_requires_same_explicit_manual_binding(self):
        annotation=copy.deepcopy(self.annotation)
        annotation['assertion']['classification']='SAFE_IF_OPPONENT_USES_RIGHT'
        card=self.card(self.build(annotations=[annotation]))
        self.assertEqual(card['status'],'SAFE_IF_OPPONENT_USES_RIGHT')
        self.assertEqual(card['label'],'상대가 권리를 써도 안전')

    def test_rejected_or_exploratory_rule_cannot_supply_classification(self):
        for state in ('REJECTED','EXPLORATORY'):
            knowledge=copy.deepcopy(self.knowledge);knowledge[0]['proposal']['review_state']=state
            plan=evaluate_gameplan_v3(golden(patch='16.19'),knowledge);plan['validity']='CURRENT'
            self.assertEqual(self.card(self.build(plan=plan,knowledge=knowledge))['status'],'UNKNOWN')

    def test_stale_rule_version_source_or_spec_binding_is_withheld(self):
        for field in ('selected_version','spec_sha256','source_ref'):
            a=copy.deepcopy(self.annotation)
            if field=='source_ref':a[field]['note_revision']=2
            else:a[field]='f'*len(a[field])
            self.assertEqual(self.card(self.build(annotations=[a]))['status'],'UNKNOWN')

    def test_unrelated_manual_right_or_rewritten_claim_is_not_an_assertion(self):
        for field,value in (('right','opponent uses unrelated hidden skill'),('claim','unreviewed rewrite')):
            a=copy.deepcopy(self.annotation);a['assertion'][field]=value
            self.assertEqual(self.card(self.build(annotations=[a]))['status'],'UNKNOWN')

    def test_expired_or_changed_knowledge_plan_is_unknown(self):
        p=copy.deepcopy(self.plan);p['validity']='EXPIRED'
        self.assertTrue(all(c['status']=='UNKNOWN' for c in self.build(plan=p)['cards']))
        k=copy.deepcopy(self.knowledge);k[0]['proposal']['version']='3'*32
        self.assertEqual(self.card(self.build(knowledge=k))['status'],'UNKNOWN')

    def test_missing_required_input_or_wrong_patch_is_unknown(self):
        p=self.make_plan(golden(patch='16.20'))
        self.assertEqual(self.card(self.build(plan=p))['status'],'UNKNOWN')
        k=copy.deepcopy(self.knowledge);k[0]['spec']['required_fields']=['enemy.BOTTOM.runes']
        k[0]['proposal']=dict(k[0]['proposal'],**proposal_rule(k[0]['spec']))
        p=evaluate_gameplan_v3(golden(patch='16.19'),k);p['validity']='CURRENT'
        self.assertEqual(self.card(self.build(plan=p,knowledge=k))['status'],'UNKNOWN')

    def test_missing_or_stale_statistics_cannot_turn_claim_into_tactical_truth(self):
        self.assertEqual(self.card(self.build(power_datasets=[]))['status'],'UNKNOWN')
        a=copy.deepcopy(self.annotation);a['statistics'][0]['dataset_sha256']='f'*64
        self.assertEqual(self.card(self.build(annotations=[a]))['status'],'UNKNOWN')
        a=copy.deepcopy(self.annotation);a['statistics'][0]['minute']=2
        self.assertEqual(self.card(self.build(annotations=[a]))['status'],'UNKNOWN')

    def test_production_ignores_synthetic_statistics(self):
        self.assertEqual(self.card(self.build(test_mode=False))['status'],'UNKNOWN')

    def test_conflicting_manual_assertions_stay_unknown(self):
        safe=copy.deepcopy(self.annotation);safe['assertion']['classification']='SAFE_IF_OPPONENT_USES_RIGHT'
        card=self.card(self.build(annotations=[self.annotation,safe]))
        self.assertEqual(card['status'],'UNKNOWN')
        self.assertIn('RIGHT_ASSERTION_CONFLICT',card['reasons'])

    def test_strict_annotation_schema_does_not_accept_approval_flags_or_unknown_kinds(self):
        for mutate in (lambda a:a.update(review_state='REVIEWED'),lambda a:a['assertion'].update(kind='AI_INFERRED')):
            a=copy.deepcopy(self.annotation);mutate(a)
            with self.assertRaises(ValueError):self.m.validate_right_annotations([a])

    def test_no_annotations_adapter_does_not_load_statistics(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        loader=Mock(side_effect=AssertionError('unnecessary full aggregate validation'))
        server=SimpleNamespace(research=object(),validated_power_datasets=loader,
            opponent_right_annotations=[],test_mode=True)
        with patch('coach_v1.pregame_server.current_knowledge',return_value=self.knowledge):
            result=self.m.opponent_rights_response(server,self.plan)
        loader.assert_not_called()
        self.assertTrue(all(c['status']=='UNKNOWN' for c in result['cards']))

    def test_read_only_adapter_preserves_every_input(self):
        values=copy.deepcopy((self.plan,self.knowledge,self.data,self.annotation))
        self.build()
        self.assertEqual((self.plan,self.knowledge,self.data,self.annotation),values)

    def test_map_aggregate_cannot_label_four_unreviewed_position_rows(self):
        spec=rule('MAP');spec['patches']=['16.19'];spec['output']['text']=self.annotation['assertion']['claim']
        proposal=dict(self.knowledge[0]['proposal'],**proposal_rule(spec))
        knowledge=[dict(proposal=proposal,spec=spec)]
        plan=evaluate_gameplan_v3(golden(patch='16.19'),knowledge);plan['validity']='CURRENT'
        annotation=copy.deepcopy(self.annotation);annotation.update(card_key='MAP',spec_sha256=digest(spec))
        self.assertEqual(self.card(self.build(plan=plan,knowledge=knowledge,annotations=[annotation]),'MAP')['status'],'UNKNOWN')
        spec['output']['target']='GLOBAL';proposal.update(proposal_rule(spec))
        plan=evaluate_gameplan_v3(golden(patch='16.19'),knowledge);plan['validity']='CURRENT'
        annotation['spec_sha256']=digest(spec)
        self.assertEqual(self.card(self.build(plan=plan,knowledge=knowledge,annotations=[annotation]),'MAP')['status'],'RISK_IF_OPPONENT_USES_RIGHT')

    def test_grandmaster_only_supports_exact_insufficient_primary_point(self):
        auxiliary=copy.deepcopy(self.data);auxiliary['source']['tier']='GRANDMASTER'
        for c in auxiliary['cohorts']:c['tier']='GRANDMASTER'
        cohort=next(c for c in auxiliary['cohorts'] if c['champion']=='Caitlyn' and c['position']=='BOTTOM' and c['metric']=='gold_delta' and c['comparison']=='ROLE_POPULATION')
        annotation=copy.deepcopy(self.annotation);annotation['statistics']=[dict(dataset_sha256=digest(auxiliary),cohort_sha256=digest(cohort),minute=1)]
        self.assertEqual(self.card(self.build(power_datasets=[self.data,auxiliary],annotations=[annotation]))['status'],'UNKNOWN')
        card=self.card(self.build(power_datasets=[auxiliary],annotations=[annotation]))
        self.assertEqual(card['status'],'RISK_IF_OPPONENT_USES_RIGHT')
        self.assertEqual(card['statistics'][0]['tier'],'GRANDMASTER')

    def test_other_tiers_cannot_support_manual_classification_under_new_decision(self):
        for tier in ('MASTER','GOLD'):
            data=copy.deepcopy(self.data);data['source']['tier']=tier
            for c in data['cohorts']:c['tier']=tier
            cohort=next(c for c in data['cohorts'] if c['champion']=='Caitlyn' and c['position']=='BOTTOM' and c['metric']=='gold_delta' and c['comparison']=='ROLE_POPULATION')
            annotation=copy.deepcopy(self.annotation);annotation['statistics']=[dict(dataset_sha256=digest(data),cohort_sha256=digest(cohort),minute=1)]
            self.assertEqual(self.card(self.build(power_datasets=[data],annotations=[annotation]))['status'],'UNKNOWN')

    def test_selected_pro_absolute_reference_is_separate_and_never_a_fake_tier(self):
        from coach_v1.pro_reference import build_pro_reference
        o=dict(match_sha256='a'*64,role='BOTTOM',champion='Caitlyn',patch='16.19',resources=[dict(minute=1,gold=1000,xp=200,cs=10)])
        other=copy.deepcopy(o);other['match_sha256']='b'*64
        data=build_pro_reference([o,other],roster_sha256='c'*64,retrieved_at='2026-10-13T00:00:00Z',sample_kind='SYNTHETIC')
        cohort=next(c for c in data['cohorts'] if c['metric']=='gold')
        annotation=copy.deepcopy(self.annotation);annotation['statistics']=[dict(dataset_sha256=digest(data),cohort_sha256=digest(cohort),minute=1)]
        card=self.card(self.build(power_datasets=[data],annotations=[annotation]))
        self.assertEqual(card['status'],'RISK_IF_OPPONENT_USES_RIGHT')
        self.assertEqual(card['statistics'][0]['comparison_group'],'PRO_ROSTER')
        self.assertEqual(card['statistics'][0]['tier'],'UNKNOWN')
        self.assertEqual(card['statistics'][0]['unit'],'gold total')

    def test_authenticated_server_adapter_cannot_create_approval_by_loading(self):
        import tempfile
        from pathlib import Path
        from coach_v1.pregame_server import PregameWorkbench,current_knowledge
        from coach_v1.server import Limits
        with tempfile.TemporaryDirectory() as tmp:
            server=PregameWorkbench(Path(tmp)/'work.sqlite','isolated-rights-token-at-least32characters',Limits(1000000,100,100,100,100,10))
            try:
                knowledge=current_knowledge(server.research)
                plan=evaluate_gameplan_v3(golden(patch='16.19'),knowledge);plan['validity']='CURRENT'
                before=server.research.list_proposals(1000000)
                result=self.m.opponent_rights_response(server,plan)
                self.assertTrue(all(c['status']=='UNKNOWN' for c in result['cards']))
                self.assertEqual(server.research.list_proposals(1000000),before)
                self.assertFalse(server.test_mode)
            finally:server.server_close()


if __name__=='__main__':unittest.main()
