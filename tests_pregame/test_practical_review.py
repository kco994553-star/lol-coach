"""Isolated fictional comment fixtures; never actual user decisions."""
import copy
import importlib.util
import tempfile
from pathlib import Path
import unittest

from coach_v1.knowledge import KnowledgeStore
from coach_v1.pregame_server import candidate_specs, current_knowledge
from coach_v1.state import digest


class PracticalReviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.practical_review'), 'practical review workflow missing')
        from coach_v1 import practical_review
        self.p = practical_review
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = KnowledgeStore(Path(self.tmp.name)/'work.sqlite')
        self.rows = self.p.advice_catalog()
        self.manifest = {'repository':'fixture/fixture','user_login':'fixture-user','issues':[{'number':1,'candidate_versions':{r['id']:digest(r['spec']) for r in self.rows[:10]}}]}

    def comment(self, body, number=1):
        return dict(id=number,body=body,html_url=f'https://github.com/fixture/fixture/issues/1#issuecomment-{number}',created_at='2026-10-14T00:00:00Z',updated_at='2026-10-14T00:00:00Z',user={'login':'fixture-user'})

    def test_catalog_preserves_350_originals_and_binds_30_ko_advice_sources(self):
        originals = {s['rule_id']:s for s in candidate_specs()}
        self.assertEqual(len(originals),350)
        self.assertEqual(len(self.rows),30)
        self.assertEqual(len({r['id'] for r in self.rows}),30)
        for r in self.rows:
            self.assertIn(r['original_candidate_id'], originals)
            self.assertEqual(r['original_spec_sha256'],digest(originals[r['original_candidate_id']]))
            self.assertEqual(set(r['advice']),{'상황','할 것','하지 말 것','상대 권리','무효 조건','근거','패치'})
            self.assertNotRegex(' '.join(r['advice'].values()), r'EXPLORATORY|UNKNOWN|INITIATOR|SELF_SUFFICIENT|ROLE_POPULATION')
            self.assertTrue(all(s['sha256'] for s in r['spec']['sources']))
            from coach_v1.review_queue import _sources
            self.assertTrue(all(s['excerpt_status']=='ARCHIVED_VERIFIED' for s in _sources(r['spec'])))

    def test_explicit_approve_records_exact_comment_and_reopens_shared_store(self):
        r=self.rows[0];c=self.comment('승인 '+r['id'])
        result=self.p.import_comments(self.store,self.manifest,1,[c])
        self.assertEqual(result['applied'],1)
        saved=current_knowledge(KnowledgeStore(self.store.dbpath))[0]['proposal']
        self.assertEqual(saved['review_state'],'REVIEWED')
        self.assertEqual(saved['review_decision']['actor'],'USER_GITHUB')
        self.assertEqual(saved['review_decision']['github_comment']['body'],c['body'])
        self.assertEqual(saved['review_decision']['github_comment']['url'],c['html_url'])
        self.assertEqual(saved['review_decision']['github_comment']['created_at'],c['created_at'])
        self.assertFalse(saved['coaching_enabled'])

    def test_duplicate_import_is_idempotent_and_foreign_user_cannot_decide(self):
        c=self.comment('승인 '+self.rows[0]['id'])
        self.p.import_comments(self.store,self.manifest,1,[c])
        self.assertEqual(self.p.import_comments(self.store,self.manifest,1,[c])['applied'],0)
        c=self.comment('승인 '+self.rows[1]['id'],2);c['user']['login']='someone-else'
        self.assertEqual(self.p.import_comments(self.store,self.manifest,1,[c])['applied'],0)
        self.assertEqual(len(current_knowledge(self.store)),1)

    def test_reject_and_revision_never_implicitly_approve(self):
        a,b=self.rows[:2]
        self.p.import_comments(self.store,self.manifest,1,[self.comment(f'거절 {a["id"]}\n수정 {b["id"]}: 퇴로가 보일 때만 이동하세요.')])
        rows={r['spec']['rule_id']:r['proposal'] for r in current_knowledge(self.store)}
        self.assertEqual(rows[a['id']]['review_state'],'REJECTED')
        self.assertEqual(rows[b['id']]['review_state'],'EXPLORATORY')
        self.assertEqual(rows[b['id']]['claim'],'퇴로가 보일 때만 이동하세요.')
        self.assertTrue(any('issuecomment-' in t for t in rows[b['id']]['limitations']))

    def test_unknown_id_mixed_commands_and_wrong_batch_are_rejected_without_write(self):
        for body in ['승인 KR-999', '승인 '+self.rows[-1]['id'], '승인 '+self.rows[0]['id']+'\n거절 '+self.rows[0]['id'], '설명입니다. 승인 '+self.rows[0]['id']]:
            result=self.p.import_comments(self.store,self.manifest,1,[self.comment(body)])
            self.assertEqual(result['applied'],0,body)
        self.assertEqual(current_knowledge(self.store),[])

    def test_stale_web_revision_blocks_github_approval(self):
        r=self.rows[0];p=self.p.ensure_proposal(self.store,r)
        rule={k:p[k] for k in ('patch_range','applicability','required_fields','claim','mechanism','counterexamples','author','limitations')};rule['claim']='PC에서 수정한 다른 내용'
        source={k:p['source_refs'][0][k] for k in ('resource_id','anchor','note_revision')}
        self.store.propose(rule,source,p['rule_id'],p['version'],max_bytes=1000000)
        result=self.p.import_comments(self.store,self.manifest,1,[self.comment('승인 '+r['id'])])
        self.assertEqual(result['applied'],0)
        self.assertEqual(current_knowledge(self.store)[0]['proposal']['review_state'],'EXPLORATORY')

    def test_edited_comment_and_bad_provenance_do_not_decide(self):
        c=self.comment('승인 '+self.rows[0]['id']);c['updated_at']='2026-10-15T00:00:00Z'
        self.assertEqual(self.p.import_comments(self.store,self.manifest,1,[c])['applied'],0)
        c=self.comment('승인 '+self.rows[0]['id']);c['html_url']='https://github.com/fixture/other/issues/1#issuecomment-1'
        self.assertEqual(self.p.import_comments(self.store,self.manifest,1,[c])['applied'],0)
        self.assertEqual(current_knowledge(self.store),[])

    def test_default_pc_queue_shows_same_30_and_read_never_decides(self):
        from coach_v1.pregame_server import PregameWorkbench
        from coach_v1.server import Limits
        from coach_v1.review_queue import queue_response
        server=PregameWorkbench(Path(self.tmp.name)/'pc.sqlite','fictional-test-token-12345678901234567890',Limits(1000000,100,100,100,100,10))
        self.addCleanup(server.server_close)
        first=queue_response(server);second=queue_response(server,page=1)
        self.assertEqual(first['progress']['total'],30)
        self.assertEqual({c['spec']['rule_id'] for c in first['candidates']+second['candidates']},{r['id'] for r in self.rows})
        self.assertTrue(all(c.get('practical_advice') for c in first['candidates']))
        self.assertEqual(first['progress']['example_card_filled'],0)
        self.assertEqual(current_knowledge(server.research),[])

    def test_comment_batch_rolls_back_on_late_storage_failure(self):
        from unittest.mock import patch
        original=self.store.decide;count=0
        def fail_second(*args,**kwargs):
            nonlocal count
            count+=1
            if count==2:raise ValueError('fictional late failure')
            return original(*args,**kwargs)
        with patch.object(self.store,'decide',fail_second):
            result=self.p.import_comments(self.store,self.manifest,1,[self.comment('승인 KR-001 KR-002')])
        self.assertEqual(result['applied'],0)
        self.assertEqual(current_knowledge(self.store),[])
        self.assertEqual(self.store.list(),[])

    def test_issue_body_matches_immutable_claims_and_links(self):
        body=self.p.issue_body(self.rows[:10])
        for r in self.rows[:10]:
            self.assertIn(digest(r['spec']),body)
            for value in r['advice'].values():self.assertIn(value,body)
            for source in r['spec']['sources']:self.assertIn(source['url'],body)

    def test_github_sync_only_reads_registered_issues_and_reports_actual_zero(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        with patch('subprocess.run',return_value=SimpleNamespace(stdout='[]\n[]')) as run:
            result=self.p.sync_github(self.store,self.manifest)
        self.assertEqual(result['applied'],0)
        self.assertEqual(result['example_card_by_patch']['16.20'],0)
        args=run.call_args.args[0]
        self.assertEqual(args[:4],['gh','api','--method','GET'])
        self.assertIn('repos/fixture/fixture/issues/1/comments?per_page=100',args)
        self.assertEqual(current_knowledge(self.store),[])

    def test_invalid_origin_or_generic_call_cannot_forge_user_github(self):
        from coach_v1.storage import ServiceError
        p=self.p.ensure_proposal(self.store,self.rows[0])
        audit=self.p._audit(self.manifest,1,self.comment('승인 KR-001'))
        with self.assertRaises(ServiceError):
            self.store.decide(p['rule_id'],p['version'],p['version'],'REVIEWED',p['patch_range'],p['applicability'],max_bytes=1000000,github_comment=audit)
        self.assertEqual(current_knowledge(self.store)[0]['proposal']['review_state'],'EXPLORATORY')

    def test_revision_changed_after_preflight_is_not_approved(self):
        from unittest.mock import patch
        row=self.rows[0];first=self.p.ensure_proposal(self.store,row)
        original=self.p.ensure_proposal
        def changed_during_import(store,r):
            old=original(store,r)
            rule={k:old[k] for k in ('patch_range','applicability','required_fields','claim','mechanism','counterexamples','author','limitations')}
            rule['claim']='경쟁 저장으로 수정된 후보'
            source={k:old['source_refs'][0][k] for k in ('resource_id','anchor','note_revision')}
            return store.propose(rule,source,old['rule_id'],old['version'],max_bytes=1000000)
        with patch.object(self.p,'ensure_proposal',changed_during_import):
            result=self.p.import_comments(self.store,self.manifest,1,[self.comment('승인 '+row['id'])])
        self.assertEqual(result['applied'],0)
        self.assertEqual(result['decisions'],[])
        self.assertEqual(self.store.get_proposal(first['rule_id'],max_bytes=1000000),first)

    def test_import_report_counts_applied_cards_not_decision_count(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        c=self.comment('승인 KR-001')
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=__import__('json').dumps([c]))):
            result=self.p.sync_github(self.store,self.manifest)
        self.assertEqual(result['applied'],1)
        self.assertEqual(result['example_card_filled'],0)
        self.assertEqual(result['example_card_by_patch']['16.20'],1)

    def test_read_failure_in_later_issue_does_not_partially_import(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        import subprocess,json
        manifest=copy.deepcopy(self.manifest)
        manifest['issues'].append(dict(number=2,candidate_versions={r['id']:digest(r['spec']) for r in self.rows[10:20]}))
        responses=[SimpleNamespace(stdout=json.dumps([self.comment('승인 KR-001')])),subprocess.CalledProcessError(1,['gh'])]
        with patch('subprocess.run',side_effect=responses),self.assertRaises(Exception):
            self.p.sync_github(self.store,manifest)
        self.assertEqual(current_knowledge(self.store),[])

    def test_simultaneous_import_of_same_comment_applies_once(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        from unittest.mock import patch
        original=self.p._seen;barrier=threading.Barrier(2);local=threading.local()
        def concurrent_preflight(store,audit):
            value=original(store,audit)
            if not getattr(local,'checked',False):
                local.checked=True;barrier.wait(timeout=10)
            return value
        c=self.comment('승인 KR-001')
        with patch.object(self.p,'_seen',concurrent_preflight),ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(self.p.import_comments,self.store,self.manifest,1,[c]) for _ in range(2)]
            results=[f.result(timeout=20) for f in futures]
        self.assertEqual(sum(r['applied'] for r in results),1)
        self.assertEqual(len(self.store.list_proposals(1000000)),2)
