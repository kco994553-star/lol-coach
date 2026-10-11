"""Isolated synthetic reports exercise semantics; they are not real approvals."""
import copy
import importlib.util
import unittest

from coach_v1.pregame_contract import POSITIONS, parse_input, proposal_rule
from coach_v1.state import digest
from tests_pregame.test_contract import golden, rule


def approved(spec, state='REVIEWED', version='decision-1'):
    return dict(proposal=dict(proposal_rule(spec), schema_version='knowledge-decision.v1',
        rule_id=spec['rule_id'], version=version, review_state=state, supersedes=None,
        source_refs=[dict(resource_id='isolated-synthetic', anchor='fixture', note_revision=1,
                          source_payload_sha256='0'*64)],
        review_decision=dict(actor='USER_WEB', selected_version='synthetic-proposal',
                             selected_payload_sha256='0'*64), coaching_enabled=False), spec=copy.deepcopy(spec))


def profile(champion, field='threats', values=None, identifier='profile'):
    spec=rule('PROFILE');spec['rule_id']=identifier
    spec['profile']=dict(champion=champion,roles=[],threats=[],protection=[],strong_when=[],lane_style=[],jungle_style=[])
    spec['profile'][field]=values or ['POKE']
    return spec


def source(url, kind='REFERENCE', patch='SYNTHETIC-1'):
    return dict(url=url,title='isolated test reference',locator='fixture',patch=patch,sha256=None,kind=kind)


def cooldown(category='NORMAL', position='BOTTOM', side='ENEMY'):
    return dict(name='Q',side=side,position=position,category=category,spell_kind='ABILITY',
        base=dict(status='CONFIRMED',values=[10.0,12.0],patch='SYNTHETIC-1',
                  sources=[source('https://example.org/a'),source('https://example.org/b','DATA_DRAGON')]),
        conditional=dict(haste=20.0,source=source('https://example.org/haste'),kind='ABILITY'),
        remaining='NOT_AVAILABLE',linked_condition='합성 조건일 때만 표시')


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pregame_evaluator'), 'pure evaluator missing')
        from coach_v1 import pregame_evaluator as evaluator
        self.e=evaluator

    def evaluate(self, specs=(), draft=None):
        return self.e.evaluate_gameplan(draft or golden(patch='SYNTHETIC-1'), [approved(s) for s in specs])

    def test_golden_unknown_patch_all_five_positions_and_common_invariance(self):
        common=[]
        for position in POSITIONS:
            result=self.evaluate([rule('MAP')],golden(position))
            self.assertEqual(result['schema_version'],'pregame.plan.v1')
            self.assertIsNone(result['coaching_accuracy'])
            self.assertEqual(result['real_match_validation'],'NOT_EVALUATED')
            self.assertEqual(len(result['common']['map']),5)
            for cell in [*result['common']['map'],result['common']['jungle'],result['common']['composition'],*result['personal'].values(),result['changes']]:
                self.assertEqual(cell['status'],'UNKNOWN');self.assertEqual(cell['texts'],[]);self.assertTrue(cell['reasons'])
            self.assertIn('PATCH_UNKNOWN',result['evaluations'][0]['reasons'])
            common.append(result['common'])
        self.assertTrue(all(value==common[0] for value in common))

    def test_original_text_and_five_role_scope(self):
        specs=[rule('MAP')]
        for position in POSITIONS:
            s=rule(position=position);s['rule_id']='role-'+position;s['output']['text']='원문 '+position;specs.append(s)
        results=[self.evaluate(specs,golden(p,patch='SYNTHETIC-1')) for p in POSITIONS]
        self.assertTrue(all(r['common']==results[0]['common'] for r in results))
        for p,r in zip(POSITIONS,results):self.assertEqual(r['personal']['role']['texts'],['원문 '+p])

    def test_patch_mismatch_empty_patch_and_missing_personal_scope(self):
        spec=rule();self.assertEqual(self.evaluate([spec],golden(patch='OTHER'))['evaluations'][0]['condition'],'FALSE')
        spec['patches']=[];r=self.evaluate([spec]);self.assertEqual(r['evaluations'][0]['condition'],'UNKNOWN')
        self.assertIn('RULE_PATCH_UNKNOWN',r['evaluations'][0]['reasons'])
        self.assertEqual(self.evaluate([rule()],golden(None,patch='SYNTHETIC-1'))['evaluations'][0]['condition'],'UNKNOWN')

    def test_binding_current_review_and_fingerprint(self):
        spec=rule();item=approved(spec);r=self.e.evaluate_gameplan(golden(patch='SYNTHETIC-1'),[item])
        self.assertEqual(r['evaluations'][0]['status'],'APPLIED')
        for mutate in [lambda p:p.update(claim='edited'),lambda p:p.update(review_state='EXPLORATORY'),lambda p:p.update(review_state='REJECTED'),lambda p:p.update(current=False)]:
            bad=copy.deepcopy(item);mutate(bad['proposal'])
            result=self.e.evaluate_gameplan(golden(patch='SYNTHETIC-1'),[bad])
            self.assertEqual(result['personal']['role']['texts'],[])
            self.assertNotEqual(r['knowledge_fingerprint'],result['knowledge_fingerprint'])
        unbound=dict(proposal=dict(rule_id='legacy',version='1',review_state='REVIEWED',claim='free prose'),spec=None)
        result=self.e.evaluate_gameplan(golden(),[unbound]);self.assertEqual(result['evaluations'][0]['status'],'UNKNOWN')
        self.assertEqual(result['evaluations'][0]['proposal'],unbound['proposal'])
        self.assertEqual(self.e.knowledge_fingerprint([item]),r['knowledge_fingerprint'])

    def test_new_head_rejection_never_falls_back_and_version_preserved(self):
        old=approved(rule(),version='old');new=approved(rule(),'REJECTED','new');new['proposal']['supersedes']='old'
        r=self.e.evaluate_gameplan(golden(patch='SYNTHETIC-1'),[old,new])
        self.assertEqual(r['personal']['role']['texts'],[])
        self.assertEqual([e['version'] for e in r['evaluations']],['old','new'])
        self.assertEqual(r['evaluations'][0]['proposal'],old['proposal'])
        changed=copy.deepcopy(new);changed['proposal']['version']='newer'
        self.assertNotEqual(self.e.knowledge_fingerprint([new]),self.e.knowledge_fingerprint([changed]))

    def test_partial_required_and_three_value_predicates(self):
        d=golden(patch='SYNTHETIC-1');d['slots'][8]['runes'].update(status='PARTIAL',values=['known'])
        s=rule();s['conditions']=[dict(field='enemy.BOTTOM.runes',op='HAS',value='known')]
        self.assertEqual(self.evaluate([s],d)['evaluations'][0]['condition'],'TRUE')
        s['required_fields']=['enemy.BOTTOM.runes'];trace=self.evaluate([s],d)['evaluations'][0]
        self.assertEqual(trace['condition'],'UNKNOWN');self.assertEqual(trace['missing_fields'],s['required_fields'])
        s['required_fields']=[];s['conditions'][0]['value']='absent'
        self.assertEqual(self.evaluate([s],d)['evaluations'][0]['condition'],'UNKNOWN')
        d['slots'][8]['runes']['status']='FULL'
        self.assertEqual(self.evaluate([s],d)['evaluations'][0]['condition'],'FALSE')

    def test_false_conditions_dominate_unknown_and_counter_stop_are_or(self):
        s=rule();s['conditions']=[dict(field='enemy.BOTTOM.runes',op='HAS',value='missing'),dict(field='enemy.BOTTOM.champion',op='EQ',value='Wrong')]
        self.assertEqual(self.evaluate([s])['evaluations'][0]['condition'],'FALSE')
        for field in ['counterconditions','stop_conditions']:
            s=rule();s[field]=[dict(field='enemy.BOTTOM.runes',op='HAS',value='missing')]
            self.assertEqual(self.evaluate([s])['evaluations'][0]['condition'],'UNKNOWN')
            s[field].append(dict(field='enemy.BOTTOM.champion',op='EQ',value='Ezreal'))
            self.assertEqual(self.evaluate([s])['evaluations'][0]['status'],'EXCLUDED')

    def test_types_only_from_applicable_reviewed_exact_champion_profiles(self):
        s=rule('COMPOSITION');s['conditions']=[dict(field='enemy.BOTTOM.threats',op='HAS',value='POKE')]
        self.assertEqual(self.evaluate([s])['evaluations'][0]['condition'],'UNKNOWN')
        p=profile('Ezreal');r=self.evaluate([s,p]);self.assertEqual(r['common']['composition']['texts'],[s['output']['text']])
        p['profile']['champion']='Caitlyn';self.assertEqual(self.evaluate([s,p])['evaluations'][0]['condition'],'UNKNOWN')
        p=profile('Ezreal');p['patches']=['OTHER'];self.assertEqual(self.evaluate([s,p])['evaluations'][0]['condition'],'UNKNOWN')
        items=[approved(s),approved(profile('Ezreal'),'EXPLORATORY')]
        self.assertEqual(self.e.evaluate_gameplan(golden(patch='SYNTHETIC-1'),items)['evaluations'][0]['condition'],'UNKNOWN')

    def test_profile_conflicts_withhold_only_disputed_fields_and_aggregate_is_conservative(self):
        p=profile('Ezreal',identifier='p1');p['profile']['protection']=['PEEL']
        q=profile('Ezreal',values=['DIVE'],identifier='p2');q['profile']['protection']=['PEEL']
        s=rule('COMPOSITION');s['conditions']=[dict(field='enemy.BOTTOM.threats',op='HAS',value='POKE')]
        r=self.evaluate([p,q,s]);self.assertEqual(r['evaluations'][2]['condition'],'UNKNOWN')
        self.assertIn('PROFILE_FIELD_CONFLICT:Ezreal.threats',r['evaluations'][0]['reasons'])
        s['conditions']=[dict(field='enemy.BOTTOM.protection',op='HAS',value='PEEL')]
        self.assertEqual(self.evaluate([p,q,s])['evaluations'][2]['status'],'APPLIED')
        s['conditions']=[dict(field='enemy.threats',op='HAS',value='ASSASSINATION')]
        self.assertEqual(self.evaluate([p,s])['evaluations'][1]['condition'],'UNKNOWN')

    def test_conflicting_outlook_preserves_both_full_approval_traces(self):
        a=rule('MAP');a['rule_id']='a';a['output']['outlook']='FAVORABLE'
        b=copy.deepcopy(a);b['rule_id']='b';b['output'].update(outlook='UNFAVORABLE',text='다른 원문',alternatives=['승인된 대안'])
        r=self.evaluate([a,b]);cell=r['common']['map'][0]
        self.assertEqual(cell['status'],'CONFLICTING');self.assertIsNone(cell['outlook']);self.assertEqual(len(cell['rules']),2)
        for t in cell['rules']:
            self.assertEqual(t['status'],'CONFLICTING');self.assertEqual(t['spec_sha256'],digest(t['spec']))
            self.assertEqual(t['sources'],t['spec']['sources']);self.assertIn('review_decision',t['proposal'])

    def test_cooldown_display_conditional_charge_and_priority(self):
        s=rule();s['cooldowns']=[cooldown(),cooldown('CHARGE','TOP')]
        r=self.evaluate([s]);trace=r['evaluations'][0]
        self.assertEqual(len(trace['cooldowns']),2);self.assertEqual(len(r['personal']['role']['cooldowns']),1)
        normal,charge=trace['cooldowns'];self.assertEqual(normal['label'],'가속 0 기준 상한값')
        self.assertEqual(normal['base_values'],[10.0,12.0]);self.assertEqual(normal['conditional_values'],[10*100/120,10.0])
        self.assertIn('재충전',charge['label']);self.assertEqual(normal['remaining'],'NOT_AVAILABLE')
        self.assertEqual(normal['linked_condition'],s['cooldowns'][0]['linked_condition'])
        self.assertFalse(charge['priority'])

    def test_cooldown_withholds_conflict_category_patch_source_and_haste_kind(self):
        mutations=[lambda c:c['base'].update(status='CONFLICTING'),lambda c:c.update(category='UNKNOWN'),
            lambda c:c['base'].update(patch='OTHER'),lambda c:c['base']['sources'][0].update(patch='OTHER')]
        for mutate in mutations:
            s=rule();c=cooldown();mutate(c);s['cooldowns']=[c]
            shown=self.evaluate([s])['evaluations'][0]['cooldowns'][0]
            self.assertEqual(shown['status'],'UNKNOWN');self.assertEqual(shown['base_values'],[]);self.assertEqual(shown['conditional_values'],[])
        for mutate in [lambda c:c['conditional'].update(kind='SUMMONER'),lambda c:c['conditional'].update(source=None),lambda c:c['conditional']['source'].update(patch='OTHER')]:
            s=rule();c=cooldown();mutate(c);s['cooldowns']=[c]
            shown=self.evaluate([s])['evaluations'][0]['cooldowns'][0]
            self.assertTrue(shown['base_values']);self.assertEqual(shown['conditional_values'],[])
        s=rule();s['cooldowns']=[cooldown()];item=approved(s,'REJECTED')
        r=self.e.evaluate_gameplan(parse_input(golden(patch='SYNTHETIC-1')),[item]);self.assertEqual(r['evaluations'][0]['cooldowns'],[])

    def test_common_cooldown_details_do_not_depend_on_personal_role(self):
        s=rule('MAP');s['cooldowns']=[cooldown()]
        results=[self.evaluate([s],golden(p,patch='SYNTHETIC-1')) for p in POSITIONS]
        self.assertTrue(all(r['common']==results[0]['common'] for r in results))
        self.assertEqual(results[0]['common']['map'][0]['cooldowns'],[])
        self.assertEqual(len(results[0]['common']['map'][0]['rules'][0]['cooldowns']),1)

    def test_disagreeing_applied_cooldown_reports_withhold_display_values(self):
        a=rule();a['rule_id']='a';a['cooldowns']=[cooldown()]
        b=copy.deepcopy(a);b['rule_id']='b';b['cooldowns'][0]['base']['values']=[99.0]
        r=self.evaluate([a,b])
        for t in r['evaluations']:
            shown=t['cooldowns'][0]
            self.assertEqual(shown['status'],'UNKNOWN');self.assertEqual(shown['base_values'],[])
            self.assertEqual(shown['conditional_values'],[]);self.assertIn('COOLDOWN_VALUE_CONFLICT',shown['reasons'])
            self.assertTrue(t['spec']['cooldowns'][0]['base']['values'])

    def test_unbound_rejected_trace_keeps_predicates_and_unknown_missing_fields(self):
        s=rule();s['conditions']=[dict(field='enemy.BOTTOM.runes',op='HAS',value='unknown')]
        r=self.evaluate([s]);trace=r['evaluations'][0]
        self.assertIn('enemy.BOTTOM.runes',trace['missing_fields'])
        item=approved(s,'REJECTED');trace=self.e.evaluate_gameplan(golden(),[item])['evaluations'][0]
        self.assertEqual(trace['conditions'][0]['predicate'],s['conditions'][0])
        self.assertEqual(trace['conditions'][0]['condition'],'UNKNOWN')

    def test_reset_stack_transform_and_jungle_cooldown_priority(self):
        for category in ['RESET_REFUND','STACK','TRANSFORM']:
            s=rule(position='JUNGLE');s['cooldowns']=[cooldown(category,'TOP')]
            shown=self.evaluate([s],golden('JUNGLE',patch='SYNTHETIC-1'))['personal']['role']['cooldowns'][0]
            self.assertIn(category,shown['label']);self.assertIn('조건부',shown['label'])
            self.assertEqual(shown['remaining'],'NOT_AVAILABLE')

    def test_applied_rule_prioritizes_allied_synergy_and_lane_enemy_only(self):
        s=rule(position='TOP');s['cooldowns']=[cooldown(position='JUNGLE',side='ALLY'),cooldown(position='TOP'),cooldown(position='MID')]
        result=self.evaluate([s],golden('TOP',patch='SYNTHETIC-1'))
        shown=result['personal']['role']['cooldowns']
        self.assertEqual([(c['side'],c['position']) for c in shown],[('ALLY','JUNGLE'),('ENEMY','TOP')])
        self.assertEqual(len(result['evaluations'][0]['cooldowns']),3)

    def test_fingerprint_order_independent_and_spec_sensitive(self):
        a=approved(rule());s=rule('MAP');s['rule_id']='other';b=approved(s)
        self.assertEqual(self.e.knowledge_fingerprint([a,b]),self.e.knowledge_fingerprint([b,a]))
        changed=copy.deepcopy(b);changed['spec']['version']='2'
        self.assertNotEqual(self.e.knowledge_fingerprint([b]),self.e.knowledge_fingerprint([changed]))

    def test_deterministic_input_and_knowledge_not_mutated(self):
        d=golden(patch='SYNTHETIC-1');items=[approved(rule())];original=copy.deepcopy((d,items))
        first=self.e.evaluate_gameplan(d,items);second=self.e.evaluate_gameplan(parse_input(d),items)
        self.assertEqual(first,second);self.assertEqual((d,items),original)

    def test_unknown_phase_never_applies_even_with_confirmed_patch(self):
        d=golden(patch='SYNTHETIC-1');d['phase']='UNKNOWN'
        s=rule();s['cooldowns']=[cooldown()]
        result=self.evaluate([s,profile('Ezreal')],d)
        for trace in result['evaluations']:
            self.assertEqual(trace['condition'],'UNKNOWN');self.assertEqual(trace['status'],'UNKNOWN')
            self.assertIn('PHASE_NOT_CONFIRMED',trace['reasons']);self.assertEqual(trace['cooldowns'],[])
        self.assertEqual(result['personal']['role']['texts'],[])


if __name__=='__main__':unittest.main()
