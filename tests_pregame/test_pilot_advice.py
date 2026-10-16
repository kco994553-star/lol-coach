"""Changed seven-version projection; no predecessor suite invocation."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tests_pregame.test_pc_coach import draft

ROOT=Path(__file__).resolve().parents[1]


class PilotAdviceTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.pilot_advice'),'pilot module missing')
        from coach_v1 import pilot_advice
        return pilot_advice

    def test_new_versions_never_inherit_approval_or_overwrite_originals(self):
        module=self.module();packet=module.load_packet()
        self.assertEqual(len(packet['rows']),7)
        for row in packet['rows']:
            self.assertEqual(row['evidence_level'],'HYPOTHESIS')
            self.assertEqual(row['review_state'],'HOLD')
            self.assertIs(row['approval_inherited'],False)
        invalid=copy.deepcopy(packet);invalid['rows'][0]['evidence_level']='AUTO_VERIFIED'
        with self.assertRaises(ValueError):module.validate_packet(invalid)
        invalid=copy.deepcopy(packet);invalid['rows'][0]['previous_advice']['할 것']='changed original'
        with self.assertRaises(ValueError):module.validate_packet(invalid)

    def test_source_fact_cannot_borrow_an_unrelated_quote(self):
        module=self.module();packet=module.load_packet();invalid=copy.deepcopy(packet)
        invalid['rows'][0]['source_facts'][0]['quote']='unsupported factual statement'
        with self.assertRaises(ValueError):module.validate_packet(invalid)

    def test_action_conditions_stops_and_uncertainty_alternative_are_required(self):
        module=self.module();packet=module.load_packet();invalid=copy.deepcopy(packet)
        invalid['rows'][0]['actions'][0]['uncertain_alternative']=[]
        with self.assertRaises(ValueError):module.validate_packet(invalid)

    def test_revision_scope_uses_original_static_draft_conditions_only(self):
        module=self.module();packet=module.load_packet()
        cards,replaced=module.cards_for_draft(draft(),packet=packet)
        self.assertIn('KR-008',replaced)
        self.assertTrue(all(c['evidence_level']=='HYPOTHESIS' for c in cards))
        self.assertTrue(all(c['topic']=='SKILL_INTERACTION' for c in cards))
        self.assertTrue(all(c['revision_of'] in replaced for c in cards))
        self.assertTrue(all('불확실할 때' in c['details'] and '중단 조건' in c['details'] for c in cards))

    def test_original_objection_or_rejection_cannot_be_bypassed_with_revision(self):
        module=self.module();packet=module.load_packet()
        for kwargs in ({'withdrawn':{'KR-008'}},{'rejected':{'KR-008'}}):
            cards,replaced=module.cards_for_draft(draft(),packet=packet,**kwargs)
            self.assertNotIn('KR-008',replaced)
            self.assertFalse(any(c['revision_of']=='KR-008' for c in cards))

    def test_in_game_patch_mismatch_and_unmatched_champion_hide_new_advice(self):
        module=self.module();packet=module.load_packet()
        for value in (draft(phase='UNKNOWN'),draft(patch='16.21')):
            self.assertEqual(module.cards_for_draft(value,packet=packet),([],set()))

    def test_pc_preview_replaces_only_matching_legacy_auto_display_with_hypothesis(self):
        import tempfile
        from scripts.launch_pc import create_server
        from coach_v1.pc_coach import preview
        with tempfile.TemporaryDirectory() as directory:
            server=create_server(Path(directory),port=0)
            try:
                cards=preview(server,{'input':draft()})['cards']
                revision=next((c for c in cards if c.get('revision_of')=='KR-008'),None)
                self.assertIsNotNone(revision)
                self.assertEqual(revision['evidence_level'],'HYPOTHESIS')
                self.assertFalse(any(c['id']=='advice-KR-008' for c in cards))
                self.assertTrue(any(c['id']=='advice-KR-009' for c in cards))
            finally:server.server_close()

    def test_receipt_mismatch_falls_back_without_hiding_legacy_advice(self):
        from unittest.mock import patch
        module=self.module()
        with patch.object(module,'review_receipts',side_effect=ValueError('receipt mismatch')):
            self.assertEqual(module.cards_for_draft(draft()),([],set()))


if __name__=='__main__':unittest.main()
