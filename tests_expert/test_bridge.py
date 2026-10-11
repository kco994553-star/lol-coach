"""Authored manual statements: import plumbing, not expert or coaching evidence."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from coach_v1.knowledge import KnowledgeStore
from coach_v1.storage import ServiceError
from coach_v1.expert_bridge import import_expert_artifact, list_expert_claims


def artifact(video_id='TESTVideo01', text='TEST 의역: 조건을 확인한다'):
    return dict(schema_version='expert.claims.v1',video=dict(id=video_id,
        url='https://www.youtube.com/watch?v='+video_id,title='TEST authored manual fixture',
        channel_id=None,channel_name='TEST channel',speaker='UNKNOWN',speaker_verified=False,
        published_at=None,upload_date=None,duration_seconds=600,language='ko'),
        processing=dict(method='MANUAL_SUMMARY',model='UNKNOWN',processed_at='2026-10-11T00:00:00Z',input_sha256='a'*64),
        claims=[dict(timestamp='01:00',timestamp_seconds=60,paraphrase=text,champion='Nocturne',
            position='JUNGLE',stage='LATE',conditions=['TEST 상황'],context='EXPLANATION',measurable=True,
            patch_range='UNKNOWN',counterexamples=['TEST 반례 미확인'],limitations=['TEST 수치 기준 없음'],
            measurement=None,independent_group_id='YOUTUBE:'+video_id)],rejections=[],visual_verified=False,coaching_accuracy=None)


class ExpertBridgeTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.path=Path(self.directory.name)/'research.sqlite'
        self.store=KnowledgeStore(self.path);self.limit=1_000_000
    def tearDown(self):self.directory.cleanup()
    def import_(self,a=None):return import_expert_artifact(self.store,a or artifact(),max_bytes=self.limit)
    def rows(self):return list_expert_claims(self.store,max_bytes=self.limit)['claims']
    def test_source_bound_single_exploratory_and_idempotent_restart(self):
        result=self.import_();self.assertEqual(result['new_candidates'],1)
        row=self.rows()[0];p=row['proposal']
        self.assertEqual(p['review_state'],'EXPLORATORY');self.assertFalse(p['coaching_enabled'])
        self.assertEqual(p['source_refs'][0]['note_revision'],1)
        self.assertEqual(row['comparison']['status'],'UNMEASURABLE')
        self.assertTrue(row['artifact']['video']['url'].endswith('TESTVideo01'))
        self.store=KnowledgeStore(self.path)
        self.assertEqual(self.import_()['new_candidates'],0);self.assertEqual(len(self.rows()),1)
        with self.store._db() as db:
            values=[json.loads(r[0]) for r in db.execute('SELECT payload FROM knowledge_rules')]
        self.assertTrue(all('review_decision' not in v for v in values));self.assertEqual(len(values),1)
    def test_invalid_artifact_writes_nothing(self):
        bad=artifact();bad['claims'][0]['timestamp_seconds']=601
        with self.assertRaises(ValueError):self.import_(bad)
        self.assertEqual(self.store.list(),[]);self.assertEqual(self.store.list_proposals(self.limit),[])
    def test_partial_failure_resumes_exact_original_note(self):
        with patch.object(self.store,'propose',side_effect=RuntimeError('TEST failure')):
            with self.assertRaises(RuntimeError):self.import_()
        self.assertEqual(len(self.store.list()),1)
        self.assertEqual(self.import_()['new_candidates'],1)
        self.assertEqual(self.import_()['new_candidates'],0)
        row=self.rows()[0];self.assertEqual(self.store.get_note(row['resource_id'],row['anchor'])['revision'],1)
    def test_manual_note_edit_does_not_change_bound_revision(self):
        self.import_();row=self.rows()[0]
        self.store.put_note(row['resource_id'],row['anchor'],dict(known='MANUAL later',intention='',alternative='',outcome=''),1)
        self.assertEqual(self.import_()['new_candidates'],0)
        self.assertEqual(self.rows()[0]['proposal']['source_refs'][0]['note_revision'],1)
    def test_user_deleted_proposal_not_resurrected(self):
        self.import_();row=self.rows()[0];p=row['proposal']
        self.store.delete_proposal(p['rule_id'],p['version'],self.limit)
        self.assertEqual(self.import_()['new_candidates'],0);self.assertEqual(self.rows(),[])
    def test_user_deleted_resource_not_resurrected(self):
        self.import_();row=self.rows()[0];self.store.delete(row['resource_id'])
        self.assertEqual(self.import_()['new_candidates'],0);self.assertEqual(self.store.list(),[])
    def test_new_artifact_revision_preserves_original_version(self):
        self.import_();old=self.rows()[0];a=artifact(text='TEST 새로운 의역')
        self.assertEqual(self.import_(a)['new_candidates'],1)
        self.assertEqual(len(self.rows()),2)
        self.assertEqual(self.store.get_proposal(old['proposal']['rule_id'],max_bytes=self.limit),old['proposal'])
    def test_video_groups_counts_do_not_count_multiple_ai_summaries(self):
        self.import_();a=artifact();a['processing']['input_sha256']='b'*64;self.import_(a)
        self.assertTrue(all(r['independent_sources']==dict(videos=1,verified_speakers=0) for r in self.rows()))
        self.import_(artifact('TESTVideo02'))
        self.assertTrue(all(r['independent_sources']==dict(videos=2,verified_speakers=0) for r in self.rows()))
    def test_http_budget_preflight_no_writes(self):
        with self.assertRaises(ServiceError):import_expert_artifact(self.store,artifact(),max_bytes=100)
        self.assertEqual(self.store.list(),[])

if __name__=='__main__':unittest.main()
