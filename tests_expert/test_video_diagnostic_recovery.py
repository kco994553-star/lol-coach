"""Cancelled staged diagnostic quota snapshots; no Actions calls."""
import copy
from datetime import datetime,timezone
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from coach_v1.expert_collector import recover_ledger_snapshot
from scripts import collect_expert_claims as cli
from tests_expert.test_video_diagnostic import NOW,ledger


class RecoveryTests(unittest.TestCase):
    def snapshots(self):
        base=ledger()
        for i in range(3):
            base['reservations'].append(dict(video_id='freshvid001',seconds=900,reserved_at=NOW+i,
                reservation_id=str(i+1)*64))
            if i==0:baseline=copy.deepcopy(base)
            elif i==1:clipping=copy.deepcopy(base)
        return baseline,clipping,base

    def recover(self,states,*,artifacts=None):
        names=['expert-quota-reservation-44','expert-quota-reservation-44-CLIPPING',
            'expert-quota-reservation-44-RESPONSE_FORMAT','expert-quota-final-44']
        metadata=[dict(id=100+i,name=name,created_at=datetime.fromtimestamp(NOW+i,timezone.utc).isoformat(),expired=False)
                  for i,name in enumerate(names[:len(states)])] if artifacts is None else artifacts
        return recover_ledger_snapshot([dict(id=44,run_number=44,conclusion='cancelled')],current_run_id=45,
            list_artifacts=lambda run:metadata,download_artifact=lambda run,a:states[a['id']-100],now=NOW+10)

    def test_cancel_after_clipping_recovers_latest_durable_charge(self):
        base,clip,_=self.snapshots();actual,receipt=self.recover([base,clip])
        self.assertEqual(actual,clip);self.assertEqual(receipt['artifact_id'],101)

    def test_cancel_after_format_recovers_all_three_charges(self):
        base,clip,fmt=self.snapshots();actual,receipt=self.recover([base,clip,fmt])
        self.assertEqual(actual,fmt);self.assertEqual(receipt['artifact_id'],102)

    def test_final_that_refunds_intermediate_clipping_charge_is_unknown(self):
        base,clip,fmt=self.snapshots();actual,receipt=self.recover([base,clip,fmt,base])
        self.assertIsNone(actual);self.assertEqual(receipt['status'],'UNKNOWN')

    def test_reordered_reservations_are_not_prefix_preserving(self):
        base,clip,fmt=self.snapshots();bad=copy.deepcopy(fmt);bad['reservations'].reverse()
        actual,receipt=self.recover([base,clip,fmt,bad]);self.assertIsNone(actual)

    def test_duplicate_out_of_order_or_missing_middle_stage_is_unknown(self):
        base,clip,fmt=self.snapshots()
        base_meta=dict(id=100,name='expert-quota-reservation-44',created_at='2026-10-13T12:00:00Z',expired=False)
        clip_meta=dict(id=101,name='expert-quota-reservation-44-CLIPPING',created_at='2026-10-13T12:01:00Z',expired=False)
        format_meta=dict(id=102,name='expert-quota-reservation-44-RESPONSE_FORMAT',created_at='2026-10-13T12:02:00Z',expired=False)
        for artifacts in ([base_meta,clip_meta,dict(clip_meta,id=102)],
                          [base_meta,dict(clip_meta,created_at='2026-10-13T11:59:00Z')],
                          [base_meta,format_meta]):
            actual,receipt=self.recover([base,clip,fmt],artifacts=artifacts)
            self.assertIsNone(actual);self.assertEqual(receipt['status'],'UNKNOWN')

    def test_missing_artifact_after_successful_clipping_persistence_blocks_recovery(self):
        def gh(path):
            if '/workflows/' in path:return dict(workflow_runs=[dict(id=44,run_number=44)])
            if '/artifacts?' in path:return dict(total_count=0,artifacts=[])
            return dict(total_count=1,jobs=[dict(steps=[dict(name='Persist quota before any Gemini request',conclusion='skipped'),
                dict(name='Persist clipping diagnostic quota',conclusion='success')])])
        with tempfile.TemporaryDirectory() as temporary,patch.dict(cli.os.environ,{'GITHUB_REPOSITORY':'test/repo','GITHUB_RUN_ID':'45'},clear=True),\
             patch.object(cli,'gh_json',side_effect=gh),patch.object(cli.time,'time',return_value=NOW+10):
            receipt=cli.recovery(Path(temporary))
        self.assertEqual(receipt['status'],'UNKNOWN')


if __name__=='__main__':unittest.main()
