"""New V6 integration boundaries; earlier v2.1 evidence is reused."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_pregame.test_pc_coach import draft


class RecallPCIntegrationTests(unittest.TestCase):
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
