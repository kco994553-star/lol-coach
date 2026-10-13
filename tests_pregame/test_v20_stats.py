"""Queue v2 statistical tests: synthetic private inputs, never provider calls."""
import copy
import gzip
import importlib
import json
import math
from pathlib import Path
import tempfile
import unittest
import os
import subprocess
import sys

from coach_v1.power_stats import build_power_dataset, student_t_critical
from tests_pregame.test_power_stats import pair, source
from tests_pregame.test_riot_collector import Clock, Responses, TEST_KEY, okay


class AccumulationTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.find_spec('coach_v1.power_accumulator')
        self.assertIsNotNone(spec, 'anonymous exact accumulation module required')
        return importlib.import_module('coach_v1.power_accumulator')

    def test_overlapping_runs_equal_one_build_including_cluster_ci_and_markers(self):
        module = self.module()
        batches = [pair(i, delta=100+i*30) for i in range(5)]
        accumulator = module.PowerAccumulator()
        accumulator.add_pairs(batches[:3], source=source(), complete_item_ids=(3001,3002))
        actual = accumulator.add_pairs(batches[2:], source=source(), complete_item_ids=(3001,3002))
        expected = build_power_dataset(batches, source=source(), complete_item_ids=(3001,3002))
        self.assertEqual(actual, expected)
        self.assertEqual(accumulator.add_pairs(batches, source=source(), complete_item_ids=(3001,3002)), expected)
        serialized = json.dumps(accumulator.to_dict())
        for forbidden in ('PRIVATE_SYNTHETIC', 'puuid', 'summonerName', 'matchId', 'participantFrames', 'KR_SYNTHETIC'):
            self.assertNotIn(forbidden, serialized)

    def test_restore_patch_and_tier_buckets_do_not_mix(self):
        module = self.module(); accumulator = module.PowerAccumulator()
        old = accumulator.add_pairs([pair(1)], source=source())
        newer_source = source(); newer_source['patch']='16.20'
        newer = accumulator.add_pairs([pair(2,patch='16.20')], source=newer_source)
        self.assertEqual(newer['samples']['synthetic_matches'],1)
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'state.json.gz';accumulator.save(path)
            restored=module.PowerAccumulator.load(path)
            self.assertEqual(restored.dataset('16.19','GOLD'),old)
            self.assertEqual(restored.dataset('16.20','GOLD'),newer)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            raw=json.loads(gzip.decompress(path.read_bytes()))
            raw['buckets'][0]['records'][0]['puuid']='PRIVATE'
            with self.assertRaises(ValueError):module.PowerAccumulator(raw)

    def test_publish_only_restores_exact_state_without_any_riot_key(self):
        module=self.module();accumulator=module.PowerAccumulator()
        accumulator.add_pairs([pair(i,delta=100*i) for i in range(3)],source=source())
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);state=directory/'state.json.gz';accumulator.save(state)
            result=subprocess.run([sys.executable,'scripts/collect_power_stats.py','--publish-only',
                '--accumulator',str(state),'--aggregate-directory',str(directory/'published'),'--output',str(directory/'latest.json')],
                env={k:v for k,v in os.environ.items() if k!='RIOT_API_KEY'},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            public=directory/'published/power-16.19-GOLD.json';receipt=directory/'published/progress-16.19-GOLD.json'
            self.assertTrue(public.exists());self.assertTrue(receipt.exists())
            self.assertTrue((directory/'latest.json').exists(),'restored state needs an honest workflow summary')
            self.assertEqual(json.loads(public.read_text())['samples']['synthetic_matches'],3)
            self.assertEqual(json.loads(receipt.read_text())['roles'][0]['role_baseline']['status'],'ESTIMATED')

    def test_workflow_no_auth_preflight_and_restores_before_renewal_gate(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/riot-power-collection.yml').read_text()
        self.assertNotIn('python scripts/diagnose_riot_front.py',workflow,
                         'routine front diagnosis calls Python even after a first curl401/403')
        self.assertLess(workflow.index('--publish-only'),workflow.index('if: inputs.key_renewed'))
        self.assertIn('retention-days: 90',workflow)

    def test_conflicting_duplicate_fails_and_legacy_seed_cannot_be_blindly_merged(self):
        module = self.module(); accumulator = module.PowerAccumulator()
        accumulator.add_pairs([pair(1)],source=source())
        with self.assertRaises(ValueError):accumulator.add_pairs([pair(1,delta=999)],source=source())
        retained=Path(__file__).resolve().parents[1]/'data/riot/2026-10-11/power-data.json.gz'
        legacy=json.loads(gzip.decompress(retained.read_bytes()))
        seed=module.PowerAccumulator();seed.seed_legacy(legacy)
        self.assertEqual(seed.dataset(legacy['source']['patch'],legacy['source']['tier']),legacy)
        real_source=source('REAL');real_source['patch']=legacy['source']['patch'];real_source['tier']=legacy['source']['tier']
        p=pair(90,patch=real_source['patch']);p['match']['metadata']['matchId']='KR_999999999'
        p['timeline']['metadata']['matchId']='KR_999999999'
        current=seed.add_pairs([p],source=real_source)
        self.assertEqual(current['samples']['real_matches'],1)
        self.assertEqual(seed.to_dict()['legacy'][0]['samples']['real_matches'],50)


class ProgressTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.collection_progress'),'progress estimation module required')
        return importlib.import_module('coach_v1.collection_progress')

    def test_target_solves_existing_student_t_width_policy(self):
        module=self.module()
        expected=next(n for n in range(2,100) if 2*student_t_critical(n-1)/math.sqrt(n)<=1)
        self.assertEqual(module.estimated_target(7,2,None),expected)
        self.assertEqual(module.estimated_target(7,2,1),next(n for n in range(2,200) if 4*student_t_critical(n-1)/math.sqrt(n)<=1))
        self.assertIsNone(module.estimated_target(1,None,None))
        self.assertEqual(module.estimated_target(2,0,None),2)

    def test_progress_preserves_unknown_baseline_and_champion_support(self):
        module=self.module(); data=build_power_dataset([pair(1)],source=source())
        response=module.progress_response(data)
        self.assertEqual(len(response['roles']),5)
        self.assertTrue(all(row['role_baseline']['estimated_remaining_matches'] is None for row in response['roles']))
        self.assertTrue(all(row['role_baseline']['status']=='UNKNOWN' for row in response['roles']))
        self.assertIsNone(response['completion_percentage'])
        self.assertTrue(any(c['status']=='UNKNOWN' for row in response['roles'] for c in row['champion_graphs']))
        retained=Path(__file__).resolve().parents[1]/'data/riot/2026-10-11/power-data.json.gz'
        real=module.progress_response(json.loads(gzip.decompress(retained.read_bytes())))
        self.assertEqual(real['real_matches'],50)
        self.assertEqual(len(real['roles']),5)
        self.assertTrue(any(c['point_count'] for row in real['roles'] for c in row['champion_graphs']))
        self.assertLess(len(json.dumps(real).encode()),1024*1024)

    def test_none_is_unknown_and_records_make_exact_clustered_role_baseline(self):
        module=self.module()
        self.assertEqual(module.progress_response(None)['status'],'UNKNOWN')
        from coach_v1.power_accumulator import PowerAccumulator
        accumulator=PowerAccumulator()
        accumulator.add_pairs([pair(i,delta=100+30*i) for i in range(3)],source=source())
        response=accumulator.progress('16.19','GOLD',include_points=True)
        for role in response['roles']:
            baseline=role['role_baseline']
            self.assertEqual(baseline['status'],'ESTIMATED')
            self.assertEqual(baseline['estimated_remaining_matches'],15)
            gold=next(c for c in baseline['curves'] if c['metric']=='gold_delta')['points'][0]
            self.assertEqual(gold['mean'],665)
            self.assertAlmostEqual(gold['empirical_sd'],15)
            self.assertEqual(gold['match_count'],3)
        self.assertEqual(response['roles'][0]['champion_graph_summary']['estimated_remaining_matches'],15)

    def test_progress_receipt_digest_binding_and_strict_baseline_validation(self):
        module=self.module()
        self.assertTrue(hasattr(module,'validate_progress'),'published baseline sidecars require strict digest binding')
        from coach_v1.power_accumulator import PowerAccumulator
        accumulator=PowerAccumulator();dataset=accumulator.add_pairs([pair(i,delta=i*100) for i in range(3)],source=source())
        receipt=accumulator.progress('16.19','GOLD')
        self.assertEqual(module.validate_progress(receipt,dataset),receipt)
        wrong=copy.deepcopy(receipt);wrong['power_dataset_sha256']='0'*64
        with self.assertRaises(ValueError):module.validate_progress(wrong,dataset)

    def test_diverse_valid_dataset_has_bounded_progress_and_explicit_omissions(self):
        module=self.module();pairs=[]
        for i in range(90):
            p=pair(i,delta=i*30,minutes=(1,))
            for index,person in enumerate(p['match']['info']['participants']):person['championName']='Champion'+str(i*10+index)
            pairs.append(p)
        dataset=build_power_dataset(pairs,source=source())
        receipt=module.progress_response(dataset)
        self.assertLess(len(json.dumps(receipt).encode()),1024*1024)
        for row in receipt['roles']:
            self.assertLessEqual(len(row['champion_graphs']),60)
            self.assertGreater(row['champion_graphs_omitted'],0)
        self.assertEqual(module.validate_progress(receipt,dataset),receipt)
        wrong=copy.deepcopy(receipt);wrong['roles'][0]['role_baseline']['puuid']='PRIVATE'
        with self.assertRaises(ValueError):module.validate_progress(wrong,dataset)
        wrong=copy.deepcopy(receipt);wrong['roles'][0]['champion_graphs'][0]['estimated_remaining_matches']=0
        with self.assertRaises(ValueError):module.validate_progress(wrong,dataset)


class RateTests(unittest.TestCase):
    def test_local_rate_windows_apply_when_riot_headers_are_absent(self):
        from coach_v1.riot_collector import RiotCollector
        clock=Clock();transport=Responses([okay({})]*101)
        collector=RiotCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep,max_requests=200,deadline_seconds=300)
        collector._normalized_api_key=TEST_KEY
        for _ in range(101):collector._get('https://asia.api.riotgames.com/lol/match/v5/matches/KR_1','MATCH_V5_MATCH')
        self.assertGreaterEqual(clock.time,120,'missing headers must not permit >100 requests/120s')
        self.assertGreaterEqual(clock.waits[0],1,'missing headers must not permit >20 requests/s')

    def test_collect_retains_only_anonymous_sufficient_records_and_rotates(self):
        import coach_v1.riot_collector as module
        self.assertTrue(hasattr(module,'collection_tier'),'configured tier rotation required')
        RiotCollector=module.RiotCollector;collection_tier=module.collection_tier
        self.assertEqual([collection_tier(i) for i in range(3)],['CHALLENGER','GRANDMASTER','MASTER'])
        self.assertEqual(collection_tier(99,'SILVER'),'SILVER')
        p=pair(1);p['match']['metadata']['matchId']='KR_101';p['timeline']['metadata']['matchId']='KR_101'
        clock=Clock();transport=Responses([okay([{'puuid':'PRIVATE'}]),okay(['KR_101']),okay(p['match']),okay(p['timeline'])])
        collector=RiotCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep)
        data=collector.collect(tier='GOLD',patch='16.19',collect_items=False)
        self.assertEqual(len(collector.sufficient_records),1)
        self.assertEqual(collector.sufficient_records[0]['hash'],data['samples']['hashed_match_ids'][0])
        self.assertNotIn('PRIVATE',json.dumps(collector.sufficient_records))

    def test_known_hashes_skip_match_and_timeline_without_api_spend(self):
        import hashlib
        from coach_v1.riot_collector import RiotCollector
        clock=Clock();transport=Responses([okay([{'puuid':'PRIVATE'}]),okay(['KR_101'])])
        collector=RiotCollector(TEST_KEY,transport=transport,clock=clock.now,sleeper=clock.sleep)
        self.assertIn('known_match_hashes',__import__('inspect').signature(collector.collect).parameters,
                      'resume should avoid spending requests on retained matches')
        data=collector.collect(tier='GOLD',patch='16.19',collect_items=False,
            known_match_hashes=[hashlib.sha256(b'KR_101').hexdigest()])
        self.assertEqual(data['source']['collection']['request_count'],2)
        self.assertEqual(data['samples']['real_matches'],0)


if __name__=='__main__':unittest.main()
