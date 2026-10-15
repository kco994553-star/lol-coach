"""Synthetic private-cache and fake-transport acquisition checks; no providers."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests_pregame.test_riot_collector import Clock, Responses, TEST_KEY, okay
from tests_pregame.test_power_stats import pair


class RecallCollectionTests(unittest.TestCase):
    def test_offline_reuses_private_envelopes_and_only_selected_participant(self):
        from coach_v1.recall_collection import reuse_private_cache
        from coach_v1.postgame_match import PostgameStore
        from tests_pregame.test_v20_postgame import body
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';store=PostgameStore(root/'private/matches',test_mode=True)
            envelope=body();envelope['source']='REAL';store.import_match(envelope)
            selected=[]
            def extract(match,timeline,**kwargs):
                selected.append(kwargs);return dict(population='PRO_REFERENCE',patch='16.19',cluster_key='a'*64,exclusions=[],participants=[{'observation':'anonymous'}])
            with patch('coach_v1.recall_collection.extract_match',side_effect=extract):
                observations,receipt=reuse_private_cache(root)
            self.assertEqual(len(observations),1);self.assertEqual(observations[0]['participants'],[{'observation':'anonymous'}])
            self.assertEqual(selected,[dict(population='PRO_REFERENCE',participant_ids=[envelope['participant_id']])])
            self.assertEqual(receipt['request_count'],0)
            self.assertEqual(receipt['reused_private_records'],1)
            self.assertNotIn('puuid',json.dumps(receipt).lower())

    def test_missing_or_unsafe_cache_fails_closed(self):
        from coach_v1.recall_collection import reuse_private_cache
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):reuse_private_cache(Path(tmp)/'missing')
            root=Path(tmp)/'private';(root/'private/matches').mkdir(parents=True)
            outside=Path(tmp)/'outside';outside.write_text('{}')
            (root/'private/matches'/('a'*64+'.json')).symlink_to(outside)
            with self.assertRaises(ValueError):reuse_private_cache(root)

    def test_challenger_consumes_original_raw_pair_once_no_extra_requests(self):
        from coach_v1.recall_collection import RecallCollector
        raw=pair(101);raw['match']['metadata']['matchId']='KR_101';raw['timeline']['metadata']['matchId']='KR_101';clock=Clock()
        transport=Responses([okay({'entries':[{'puuid':'PRIVATE_SEED'}]}),okay(['KR_101']),
                             okay(raw['match']),okay(raw['timeline'])])
        with patch('coach_v1.recall_collection.extract_match',return_value={'anonymous':True}) as extract:
            collector=RecallCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep,max_matches=1)
            observations,receipt=collector.collect_recall(patch='16.19')
        self.assertEqual(observations,[{'anonymous':True}]);self.assertEqual(len(transport.urls),4)
        self.assertEqual(extract.call_count,1);self.assertEqual(extract.call_args.kwargs,dict(population='CHALLENGER'))
        self.assertEqual(receipt['request_count'],4)
        self.assertNotIn('PRIVATE_SEED',json.dumps(receipt))

    def test_actual_challenger_extraction_filters_exact_patch_and_exports_safe_dataset(self):
        from coach_v1.recall_collection import RecallCollector,export_recall
        from tests_pregame.test_v20_postgame import body
        envelope=body();raw=envelope
        old=copy.deepcopy(raw['match']);old['info']['gameVersion']='16.18.1';old['metadata']['matchId']='KR_111'
        clock=Clock();transport=Responses([okay({'entries':[{'puuid':'PRIVATE_SEED'}]}),
            okay(['KR_111','KR_123456']),okay(old),okay(raw['match']),okay(raw['timeline'])])
        collector=RecallCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep,max_matches=1)
        observations,receipt=collector.collect_recall(patch='16.19')
        self.assertEqual(len(observations),1);self.assertEqual(observations[0]['patch'],'16.19')
        self.assertEqual(len(observations[0]['participants']),10);self.assertEqual(collector.requests,5)
        self.assertFalse(any('/KR_111/timeline' in url for url in transport.urls))
        with tempfile.TemporaryDirectory() as tmp:
            safe=export_recall(Path(tmp)/'public',Path(tmp)/'private',observations,receipt,
                               retrieved_at='2026-10-15T00:00:00Z')
            data=json.loads((Path(tmp)/'public/recall-data.json').read_text())
            self.assertEqual(data['population'],'CHALLENGER');self.assertEqual(safe['dataset_samples']['matches'],1)
            self.assertNotIn('PRIVATE',json.dumps(data)+json.dumps(safe))

    def test_authentication_stop_has_no_retries_or_raw_receipt(self):
        from coach_v1.recall_collection import RecallCollector
        for status in (401,403):
            clock=Clock();transport=Responses([(status,{},b'PRIVATE_ERROR')])
            collector=RecallCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep)
            observations,receipt=collector.collect_recall(patch='16.20')
            self.assertEqual(observations,[]);self.assertEqual(collector.requests,1)
            self.assertEqual(receipt['status'],'BLOCKED_EXTERNAL');self.assertEqual(receipt['observed_http_status'],status)
            self.assertNotIn('PRIVATE',json.dumps(receipt))

    def test_actual_cache_extract_export_merges_selected_players_and_keeps_health_unknown(self):
        from coach_v1.recall_collection import reuse_private_cache, export_recall
        from coach_v1.postgame_match import PostgameStore
        from coach_v1.recall_stats import validate_dataset
        from tests_pregame.test_v20_postgame import body
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';store=PostgameStore(root/'private/matches')
            envelope=body();envelope['source']='REAL';store.import_match(envelope)
            other=copy.deepcopy(envelope);other['participant_id']=9;store.import_match(other)
            observations,receipt=reuse_private_cache(root)
            self.assertEqual(len(observations),1);self.assertEqual(len(observations[0]['participants']),2)
            safe=export_recall(Path(tmp)/'public',root,observations,receipt,retrieved_at='2026-10-15T00:00:00Z')
            data=validate_dataset(json.loads((Path(tmp)/'public/recall-data.json').read_text()))
            self.assertEqual(data['samples'],dict(matches=1,participant_observations=2))
            self.assertEqual(safe['reused_private_records'],2);self.assertEqual(safe['reused_unique_matches'],1)
            self.assertTrue(all(p['low_health']['status']=='EXCLUDED' for p in observations[0]['participants']))
            serialized=json.dumps(data)+json.dumps(safe)
            for forbidden in ('PRIVATE_PUUID','KR_123456','cluster_key','participant_id'):
                self.assertNotIn(forbidden,serialized)

    def test_runtime_rejects_synthetic_envelopes_without_relabeling(self):
        from coach_v1.recall_collection import reuse_private_cache
        from coach_v1.postgame_match import PostgameStore
        from tests_pregame.test_v20_postgame import body
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';store=PostgameStore(root/'private/matches',test_mode=True)
            store.import_match(body())
            with self.assertRaises(ValueError):reuse_private_cache(root)

    def test_cli_is_offline_by_default_and_has_no_unsafe_fallback_on_bad_cache(self):
        from scripts.collect_recall_stats import main
        from coach_v1.postgame_match import PostgameStore
        from tests_pregame.test_v20_postgame import body
        from contextlib import redirect_stdout
        from io import StringIO
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'private';store=PostgameStore(root/'private/matches')
            envelope=body();envelope['source']='REAL';store.import_match(envelope)
            output=Path(tmp)/'public';args=['--private-directory',str(root),'--output-directory',str(output)]
            with patch('coach_v1.riot_collector._transport',side_effect=AssertionError('no provider calls')),redirect_stdout(StringIO()) as stdout:
                self.assertEqual(main(args),0)
            self.assertEqual(json.loads(stdout.getvalue())['request_count'],0)
            # A later broken cache clears stale public success before failing.
            next((root/'private/matches').glob('*.json')).write_text('{"private":"BROKEN_RAW"}')
            with patch('coach_v1.riot_collector._transport',side_effect=AssertionError('no provider calls')),redirect_stdout(StringIO()) as stdout:
                self.assertEqual(main(args),2)
            self.assertFalse((output/'recall-data.json').exists())
            self.assertNotIn('BROKEN_RAW',stdout.getvalue())

    def test_challenger_hard_caps_and_request_budget(self):
        from coach_v1.recall_collection import RecallCollector
        with self.assertRaises(ValueError):RecallCollector(TEST_KEY,max_matches=301)
        with self.assertRaises(ValueError):RecallCollector(TEST_KEY,max_requests=651)
        clock=Clock();transport=Responses([okay({'entries':[{'puuid':'PRIVATE_SEED'}]})])
        collector=RecallCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep,max_requests=1)
        observations,receipt=collector.collect_recall(patch='16.20')
        self.assertEqual(observations,[]);self.assertEqual(receipt['request_count'],1)
        self.assertEqual(receipt['reason'],'REQUEST_BUDGET_EXHAUSTED')
        with self.assertRaises(ValueError):collector.collect_recall(patch=None)

    def test_workflow_trust_serialization_and_safe_allowlist(self):
        text=Path('.github/workflows/recall-reference-collection.yml').read_text()
        for value in ("github.ref == 'refs/heads/main'",'inputs.key_renewed == true','github.run_attempt == 1',
                      'group: riot-power-collection-main','time.sleep(60)','time.sleep(1)',
                      'scripts/recover_pro_cache.py','scripts/private_pro_bundle.py decrypt',
                      'PRO_REFERENCE_ENCRYPTION_SEED: ${{ secrets.YOUTUBE_API_KEY }}',
                      'recall-data.json','source-binding.json'):
            self.assertIn(value,text)
        self.assertNotIn('pull_request:',text)
        self.assertNotIn('private/matches/',text)
        self.assertNotIn('encrypt --directory',text)
        import re
        for line in text.splitlines():
            if 'uses:' in line:self.assertRegex(line,r'@[0-9a-f]{40}(?:\s|$)')
