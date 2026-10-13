"""Real isolated stores: queue never exercises user review authority."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from coach_v1.pregame_contract import parse_rule, proposal_rule
from coach_v1.pregame_server import PregameWorkbench
from coach_v1.server import Limits
from tests_pregame.test_contract import golden, rule


class ReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.review_queue'), 'review queue module missing')
        from coach_v1 import review_queue
        self.q = review_queue
        self.td = tempfile.TemporaryDirectory()
        self.server = PregameWorkbench(Path(self.td.name) / 'work.sqlite', 'test-review-token-at-least-32-characters', Limits(1_000_000,100,100,100,100,10))
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.td.cleanup)
        self.specs=[]
        self.catalog=patch('coach_v1.pregame_server.candidate_specs',lambda: copy.deepcopy(self.specs))
        self.catalog.start();self.addCleanup(self.catalog.stop)

    def spec(self, name, champion=None, section='ROLE'):
        s=rule(section);s['rule_id']=name
        if champion:
            s['conditions']=[dict(field='ally.BOTTOM.champion',op='EQ',value=champion)]
        self.specs.append(parse_rule(s).model_dump(mode='json'))
        return self.specs[-1]

    def proposal(self, spec):
        source=self.server.research.add('RAW_DIAGNOSTIC','SYNTHETIC fixture',dict(schema_version='pregame.rule-source.v1',spec=spec))
        note=self.server.research.put_note(source['id'],'overview',dict(known='fixture',intention='',alternative='',outcome=''),0)
        return self.server.research.propose(proposal_rule(spec),dict(resource_id=source['id'],anchor='overview',note_revision=note['revision']),max_bytes=1_000_000)

    def test_priority_golden_fulfillment_then_priority_picks_then_observed_frequency(self):
        self.spec('z-golden','Caitlyn');self.spec('a-ashe','Ashe');self.spec('b-jinx','Jinx');self.spec('c-other','Azir')
        self.server.pregame.save(golden(),None,0,'recent-input')
        result=self.q.queue_response(self.server)
        self.assertEqual([c['spec']['rule_id'] for c in result['candidates']],['z-golden','a-ashe','b-jinx','c-other'])
        self.assertEqual(result['candidates'][0]['priority']['tier'],0)
        self.assertGreater(result['candidates'][0]['priority']['observed_frequency'],0)
        self.assertEqual(result['progress']['example_card_total'],45)

    def test_priority_prefers_more_example_card_targets_before_candidate_id(self):
        self.spec('a-single','Caitlyn')
        self.spec('z-common',section='COMPOSITION')
        c=self.q.queue_response(self.server)['candidates']
        self.assertEqual(c[0]['spec']['rule_id'],'z-common')
        self.assertEqual(c[0]['priority']['conditional_card_targets'],5)
        self.assertEqual(c[1]['priority']['conditional_card_targets'],1)

    def test_later_persists_exact_revision_and_remains_revisitable(self):
        proposal=self.proposal(self.spec('one','Ashe'))
        first=self.q.queue_response(self.server)['candidates'][0]
        body={k:first[k] for k in ('candidate_id','selected_version')}
        result=self.q.defer_candidate(self.server,body)
        self.assertEqual(result['state'],'DEFERRED')
        q=self.q.queue_response(self.server)
        self.assertEqual(q['candidates'],[])
        self.assertEqual(q['deferred_candidates'][0]['candidate_id'],proposal['rule_id'])
        self.assertEqual(q['progress']['deferred'],1)
        next_rule=proposal_rule(self.specs[0]);next_rule['claim']='new revision'
        newer=self.server.research.propose(next_rule,{k:proposal['source_refs'][0][k] for k in ('resource_id','anchor','note_revision')},proposal['rule_id'],proposal['version'],max_bytes=1_000_000)
        self.assertEqual(self.q.queue_response(self.server)['candidates'][0]['selected_version'],newer['version'])
        with self.assertRaises(Exception) as stale:self.q.defer_candidate(self.server,body)
        self.assertEqual(stale.exception.code,'REVISION_CONFLICT')

    def test_queue_read_and_later_never_approve_and_preview_is_conditional(self):
        proposal=self.proposal(self.spec('one','Caitlyn'))
        before=self.server.research.list_proposals(1_000_000)
        c=self.q.queue_response(self.server)['candidates'][0]
        self.assertEqual(c['preview']['status'],'CONDITIONAL_PREVIEW')
        self.assertFalse(c['preview']['coaching_enabled'])
        self.assertIn('USER_REVIEW_REQUIRED',c['preview']['reasons'])
        self.q.defer_candidate(self.server,{k:c[k] for k in ('candidate_id','selected_version')})
        self.assertEqual(before,self.server.research.list_proposals(1_000_000))
        self.assertEqual(self.server.research.get_proposal(proposal['rule_id'],max_bytes=1_000_000)['review_state'],'EXPLORATORY')

    def test_export_top20_plain_text_excludes_credentials_private_urls_and_source_bindings(self):
        for i in range(25):self.spec('candidate-'+str(i))
        s=self.specs[0];s['sources'][0]['url']='https://example.org/synthetic?token=secret';s['sources'][0]['locator']='/private/match.json'
        result=self.q.queue_response(self.server)
        self.assertEqual(len(result['candidates']),20)
        exported=result['export_text']
        self.assertEqual(exported.count('주장: '),20)
        self.assertNotIn('127.0.0.1',exported);self.assertNotIn('secret',exported);self.assertNotIn('/private/',exported)
        self.assertNotIn('resource_id',exported);self.assertNotIn('selected_version',exported)
        self.assertLess(len(json.dumps(result).encode()),1_000_000)

    def test_source_excerpt_is_archived_verified_and_unknown_patch_stays_unknown(self):
        from coach_v1.pregame_server import ROOT
        data=json.loads((ROOT/'knowledge_candidates/initiative-v2.json').read_text())
        self.specs=[parse_rule(data[0]).model_dump(mode='json')]
        c=self.q.queue_response(self.server)['candidates'][0]
        self.assertEqual(c['patch_range'],'UNKNOWN')
        self.assertTrue(any(s['excerpt_status']=='ARCHIVED_VERIFIED' and s['excerpt'] for s in c['sources']))
        self.assertEqual(c['statistics']['status'],'UNKNOWN')
        self.assertEqual(c['preview']['status'],'CONDITIONAL_PREVIEW')

    def test_statistics_keep_original_units_and_sample_ci_without_causal_claim(self):
        from coach_v1.power_stats import build_power_dataset
        from tests_pregame.test_power_stats import pair,source
        self.spec('stats','Champion')
        self.server.test_mode=True
        self.server.power_data=build_power_dataset([pair(0),pair(1)],source=source())
        c=self.q.queue_response(self.server)['candidates'][0]
        self.assertEqual(c['statistics']['status'],'DESCRIPTIVE_ONLY')
        point=c['statistics']['comparisons'][0]['points'][0]
        self.assertEqual(point['minute'],1)
        self.assertEqual(point['n'],2)
        self.assertIn('unit',c['statistics']['comparisons'][0])
        self.assertEqual(c['priority']['tier'],2)

    def test_imported_power_datasets_supply_stats_when_legacy_single_dataset_empty(self):
        from coach_v1.power_stats import build_power_dataset
        from tests_pregame.test_power_stats import pair,source
        self.spec('stats','Champion');self.server.test_mode=True
        first=build_power_dataset([pair(0),pair(1)],source=source())
        second=copy.deepcopy(first);second['source']['tier']='SILVER'
        for cohort in second['cohorts']:cohort['tier']='SILVER'
        self.server.power_datasets={('16.19','GOLD'):first,('16.19','SILVER'):second}
        self.assertIsNone(self.server.power_data)
        c=self.q.queue_response(self.server)['candidates'][0]
        self.assertEqual(c['statistics']['status'],'DESCRIPTIVE_ONLY')
        self.assertEqual({r['tier'] for r in c['statistics']['comparisons']},{'GOLD','SILVER'})
        self.assertEqual(c['priority']['observed_frequency'],2)

    def test_second_deferred_page_can_revisit_twenty_first_candidate_without_approval(self):
        from coach_v1.state import digest
        import inspect
        self.assertIn('later_page',inspect.signature(self.q.queue_response).parameters,'deferred pagination missing')
        for i in range(21):self.spec('page-'+str(i).zfill(2),'Ashe')
        for spec in self.specs:self.q.defer_candidate(self.server,dict(candidate_id=spec['rule_id'],selected_version=digest(spec)))
        first=self.q.queue_response(self.server);second=self.q.queue_response(self.server,later_page=1)
        self.assertEqual(len(first['deferred_candidates']),20)
        self.assertEqual(len(second['deferred_candidates']),1)
        self.assertEqual(second['deferred_candidates'][0]['candidate_id'],'page-20')
        self.assertEqual(second['pagination']['later_pages'],2)
        self.assertEqual(self.server.research.list_proposals(1_000_000),[])
        with self.assertRaises(Exception):self.q.queue_response(self.server,page=True)

    def test_unbound_expert_summary_keeps_link_and_labels_paraphrase_not_quote(self):
        from coach_v1.expert_bridge import import_expert_artifact
        from tests_expert.test_bridge import artifact
        a=artifact();a['claims'][0]['champion']='Yunara'
        import_expert_artifact(self.server.research,a,max_bytes=1_000_000)
        c=self.q.queue_response(self.server)['candidates'][0]
        self.assertEqual(c['priority']['tier'],1)
        self.assertEqual(c['sources'][0]['excerpt_status'],'SOURCE_PARAPHRASE_UNVERIFIED')
        self.assertIn('?v=TESTVideo01',c['sources'][0]['url'])
        self.assertIn('t=60',c['sources'][0]['url'])
        self.assertEqual(c['sources'][0]['excerpt'],a['claims'][0]['paraphrase'])
        self.assertEqual(c['conditions']['source_conditions'],['TEST 상황'])
        self.assertIn('UNBOUND_SPEC',c['preview']['reasons'])

    def test_defer_validation_has_no_side_effect_and_coverage_no_false_approved_cards(self):
        self.spec('one','Caitlyn')
        for body in ({},{'candidate_id':'one','selected_version':'missing','extra':True}):
            with self.assertRaises(Exception):self.q.defer_candidate(self.server,body)
        result=self.q.queue_response(self.server)
        self.assertEqual(result['progress']['example_card_filled'],0)
        self.assertEqual(result['progress']['example_card_status'],'UNKNOWN_PATCH_CONDITIONAL')
        self.assertEqual(result['progress']['deferred'],0)


if __name__=='__main__':unittest.main()
