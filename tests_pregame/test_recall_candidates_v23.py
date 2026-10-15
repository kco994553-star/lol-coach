"""New source-bound hypothesis projection cannot borrow previous approvals."""
import copy
import unittest
from tests_pregame.test_pc_coach import draft


class RecallCandidateTests(unittest.TestCase):
    def test_new_candidates_remain_held_without_both_bound_agent_reviews(self):
        from coach_v1.recall_candidates import assess_candidates
        result=assess_candidates(receipts=[])
        self.assertEqual(result['passed'],0)
        self.assertEqual(result['held'],20)
        self.assertEqual(result['user_decisions_created'],0)

    def test_changed_quote_is_rejected_not_projected_as_hypothesis(self):
        from coach_v1.recall_candidates import load_packet,check_sources
        packet=copy.deepcopy(load_packet())
        packet['rows'][0]['sources'][0]['excerpt']='원문에 없는 피해 9999'
        self.assertTrue(check_sources(packet['rows'][0]))

    def test_source_path_cannot_escape_or_rebind_another_champion(self):
        from coach_v1.recall_candidates import load_packet,check_sources
        row=copy.deepcopy(load_packet()['rows'][0])
        row['sources'][0]['path']='../outside.json'
        self.assertTrue(check_sources(row))
        row=copy.deepcopy(load_packet()['rows'][0])
        row['sources'][0]['url']=row['sources'][0]['url'].replace('Yunara','Ashe')
        self.assertTrue(check_sources(row))

    def test_matching_preferred_champion_has_label_sources_and_hold_reason(self):
        from coach_v1.recall_candidates import cards_for_draft
        class Server:
            pass
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as t:
            server=Server();server.pregame=type('Pregame',(),{'dbpath':str(Path(t)/'app.sqlite')})()
            cards=cards_for_draft(server,draft())
        self.assertEqual(len(cards),5)
        self.assertTrue(all(c['evidence_level'] in ('HYPOTHESIS','UNKNOWN') for c in cards))
        self.assertTrue(all(c['sources'] and '보류' in c['details'] for c in cards))
        self.assertEqual(cards_for_draft(server,draft(phase='UNKNOWN')),[])
        self.assertEqual(cards_for_draft(server,draft(patch='16.19')),[])

    def test_no_majority_or_author_declared_auto_state_can_promote(self):
        from coach_v1.recall_candidates import load_packet,assess_candidates
        packet=copy.deepcopy(load_packet())
        for row in packet['rows']:
            row['review_status']='AUTO_VERIFIED';row['status']='AUTO_VERIFIED'
        result=assess_candidates(packet,receipts=[])
        self.assertEqual(result['passed'],0)


if __name__=='__main__':unittest.main()
