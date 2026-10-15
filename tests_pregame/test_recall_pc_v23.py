"""New V6 integration boundaries; earlier v2.1 evidence is reused."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_pregame.test_pc_coach import draft


class RecallPCIntegrationTests(unittest.TestCase):
    def test_pc_power_snapshot_matches_original_view_and_isolates_output(self):
        from coach_v1.recall_pc import PCPowerSnapshot
        from coach_v1.power_stats import build_power_dataset,select_power_view
        from tests_pregame.test_power_stats import pair,source
        data=build_power_dataset([pair(0),pair(1)],source=source())
        snapshot=PCPowerSnapshot(data)
        for champion,opponent in [('Champion','Opponent'),('Champion',None),('Absent',None)]:
            expected=select_power_view(data,champion,'TOP','16.19','GOLD',opponent)
            actual=snapshot.view(champion,'TOP','16.19','GOLD',opponent)
            actual.pop('dataset_digest');actual.pop('schema_version')
            self.assertEqual(actual,expected)
        first=snapshot.view('Champion','TOP','16.19','GOLD',None)
        first['source']['tier']='IRON'
        data['source']['tier']='IRON'
        self.assertEqual(snapshot.view('Champion','TOP','16.19','GOLD',None)['source']['tier'],'GOLD')

    def test_real_sized_archive_loads_but_over_limit_archive_is_rejected(self):
        import json
        from coach_v1.recall_pc import load_datasets
        from coach_v1.recall_stats import build_dataset
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'data/recall/2026-10-15/challenger/recall-data.json'
            target.parent.mkdir(parents=True)
            payload=json.dumps(build_dataset([],population='CHALLENGER',retrieved_at='2026-10-15T00:00:00Z'))
            target.write_text(payload+' '*(12_000_001-len(payload)),encoding='utf-8')
            server=type('Server',(),{})()
            with patch('coach_v1.recall_pc.ROOT',root):
                self.assertEqual(load_datasets(server)['CHALLENGER'],'AVAILABLE')
                with target.open('r+b') as stream:stream.truncate(32_000_001)
                self.assertEqual(load_datasets(server)['CHALLENGER'],'INVALID_NEWEST_ARCHIVE')

    def test_validated_projection_is_cached_and_isolated_from_mutable_inputs_and_outputs(self):
        from coach_v1.recall_pc import reference_response
        from coach_v1.recall_stats import build_dataset,validate_dataset
        raw=build_dataset([],population='CHALLENGER',retrieved_at='2026-10-15T00:00:00Z')
        server=type('Server',(),{'recall_datasets':{'CHALLENGER':raw}})()
        body=dict(champion='Caitlyn',position='BOTTOM',patch='16.20',opponent_champion='Ezreal')
        with patch('coach_v1.recall_stats.validate_dataset',wraps=validate_dataset) as validate:
            first=reference_response(server,body)
            raw['population']='PRO_REFERENCE'
            first['own'][0]['measurement_policy']['coverage_guard']['version']='tampered'
            second=reference_response(server,body)
            self.assertEqual(validate.call_count,1)
        self.assertEqual(second['own'][0]['population'],'CHALLENGER')
        self.assertEqual(second['own'][0]['measurement_policy']['coverage_guard']['version'],'FRAME_ORIGIN_AND_CADENCE.v2')
        self.assertEqual(first['own'][0]['dataset_sha256'],second['own'][0]['dataset_sha256'])

    def test_missing_data_stays_unknown_with_reason_not_zero(self):
        from coach_v1.recall_pc import reference_response, cards_for_draft
        class Server:
            recall_datasets = {}
        response = reference_response(Server(), dict(champion='Caitlyn', position='BOTTOM', patch='16.20', opponent_champion='Ezreal'))
        self.assertTrue(all(v['status'] == 'UNKNOWN' for v in response['own']))
        self.assertTrue(all(v.get('reason') for v in response['own']))
        cards = cards_for_draft(Server(), draft())
        self.assertTrue(any(c['section'] == 'RECALL' and c['evidence_level'] == 'UNKNOWN' for c in cards))
        self.assertFalse(any(c['evidence_level'] == 'STATISTICS' for c in cards))

    def test_in_game_and_patch_unknown_never_expose_recall_cards(self):
        from coach_v1.recall_pc import cards_for_draft
        class Server:
            recall_datasets = {}
        self.assertEqual(cards_for_draft(Server(), draft(phase='UNKNOWN')), [])
        self.assertEqual(cards_for_draft(Server(), draft(patch=None)), [])

    def test_direct_http_projection_suppresses_aggregates_after_observed_game_start(self):
        from coach_v1.recall_pc import reference_response
        class Services:
            def snapshot(self):return {'phase':'InProgress'}
        class Server:
            pc_services=Services()
            recall_datasets={}
        result=reference_response(Server(),dict(champion='Caitlyn',position='BOTTOM',patch='16.20',opponent_champion='Ezreal'))
        self.assertTrue(result['suppressed'])
        self.assertEqual(result['own'],[])
        self.assertEqual(result['markers'],[])

    def test_bad_public_request_is_rejected_before_data_selection(self):
        from coach_v1.recall_pc import validate_request
        from coach_v1.storage import ServiceError
        for body in [None, {}, {'champion': 'Caitlyn', 'position': 'BOTTOM', 'patch': '16.20', 'opponent_champion': None, 'puuid': 'never-read'},
                     dict(champion='../x',position='BOTTOM',patch='16.20',opponent_champion=None)]:
            with self.assertRaises(ServiceError):
                validate_request(body)

    def test_full_official_version_request_normalizes_before_dataset_selection(self):
        from coach_v1.recall_pc import validate_request
        body=dict(champion='Caitlyn',position='BOTTOM',patch='16.20.1',opponent_champion=None)
        self.assertEqual(validate_request(body)['patch'],'16.20')

    def test_unsupported_existing_draft_patch_keeps_unknown_card_instead_of_failing_projection(self):
        from coach_v1.recall_pc import cards_for_draft
        class Server:
            recall_datasets={}
        for value in ('UNKNOWN','16.20.1234.5678','차후 패치'):
            cards=cards_for_draft(Server(),draft(patch=value))
            self.assertTrue(cards)
            self.assertTrue(all(c['evidence_level']=='UNKNOWN' for c in cards))
            self.assertTrue(all(c['patch_status']=='GAME_PATCH_UNKNOWN' for c in cards))

    def test_item_cost_never_uses_mismatching_patch_or_invents_components(self):
        from coach_v1.recall_pc import purchase_summary
        purchase = [{'item_ids': [3006], 'count': 7, 'matches': 7}]
        mismatch = dict(prices_usable=False, items=[], catalog_version='16.21.1')
        self.assertIsNone(purchase_summary(purchase, mismatch)['reference_gold'])
        matching = dict(prices_usable=True, items=[dict(id='3006',name='시험 장화',gold={'total':1100},**{'from':['1001']})])
        result = purchase_summary(purchase, matching)
        self.assertEqual(result['reference_gold'], 1100)
        self.assertIn('보유 부품', result['limitation'])
        self.assertFalse(result['exact_required_gold_known'])

    def test_no_request_fetches_official_items(self):
        from coach_v1.recall_pc import reference_response
        class Server:
            recall_datasets = {}
        with patch('coach_v1.official_items.refresh_if_due', side_effect=AssertionError('HTTP must be read-only')):
            response=reference_response(Server(),dict(champion='Caitlyn',position='BOTTOM',patch='16.20',opponent_champion=None))
        self.assertEqual(response['schema_version'],'recall-reference.v1')

    def test_observation_summaries_use_korean_and_do_not_turn_missing_into_zero(self):
        from coach_v1.recall_pc import outcome_lines
        result=outcome_lines({'outcomes':{'self_deaths':{'status':'UNKNOWN','n':0,'participant_n':0,'missing_n':2,'mean':None}}})
        self.assertIn('미확인',' '.join(result))
        self.assertIn('누락 2',' '.join(result))
        self.assertNotIn('self_deaths',' '.join(result))

    def test_resource_plot_explicitly_names_and_queries_its_champion(self):
        from coach_v1.recall_pc import _resource_graph
        value=draft('Ezreal')
        with patch('coach_v1.pregame_server.power_response',return_value={'view':{'points':[],'reasons':[]}}) as read:
            result=_resource_graph(object(),value,[],'CHALLENGER')
        self.assertEqual(read.call_args.args[1]['champion'],'Ezreal')
        self.assertIn('Ezreal',result['title'])

    def test_opponent_recall_card_queries_opponent_resource_curve(self):
        from coach_v1.recall_pc import cards_for_draft
        from coach_v1.recall_stats import extract_match,build_dataset
        from tests_pregame.test_recall_stats_v23 import fixture,event
        observations=[]
        for i in range(5):
            match,timeline=fixture(i)
            event(timeline,'ITEM_PURCHASED',200000,participantId=1,itemId=1001)
            event(timeline,'ITEM_PURCHASED',250000,participantId=6,itemId=1052)
            observations.append(extract_match(match,timeline,population='CHALLENGER'))
        class Server:
            recall_datasets={'CHALLENGER':build_dataset(observations,population='CHALLENGER',retrieved_at='2026-10-15T00:00:00Z')}
        value=draft('Ahri');value['my_position']='MID'
        next(s for s in value['slots'] if s['side']=='ENEMY' and s['position']=='MID')['champion']='Syndra'
        with patch('coach_v1.pregame_server.power_response',return_value={'view':{'points':[],'reasons':[]}}) as read:
            cards=cards_for_draft(Server(),value)
        self.assertEqual([call.args[1]['champion'] for call in read.call_args_list],['Ahri','Syndra'])
        opponent=next(c for c in cards if c['id']=='recall-CHALLENGER-opponent')
        self.assertIn('Syndra',opponent['graph']['title'])

    def test_private_signals_require_positive_observed_outcome(self):
        from coach_v1.recall_pc import private_context
        from tests_pregame.test_recall_stats_v23 import fixture,event
        match,timeline=fixture()
        event(timeline,'CHAMPION_KILL',250000,victimId=1,killerId=6,position={'x':7000,'y':7000})
        event(timeline,'ITEM_PURCHASED',260000,participantId=1,itemId=1001)
        result=private_context(match,timeline,1)
        self.assertEqual([s['type'] for s in result['signals']],['LOW_HEALTH_STAY_DEATH'])
        self.assertTrue(all(s['inference']=='OBSERVED_CONTEXT_NOT_MISTAKE' for s in result['signals']))
        self.assertNotIn('population',result)
        self.assertNotIn('puuid',str(result).lower())
        match,timeline=fixture()
        result=private_context(match,timeline,1)
        self.assertEqual(result['signals'],[])


if __name__ == '__main__':
    unittest.main()
