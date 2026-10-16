"""New isolated fixtures; their REAL provenance labels are fabricated for validation."""
import copy
import importlib
import importlib.util
import hashlib
import subprocess
import json
from pathlib import Path
import tempfile
import unittest

from coach_v1.postgame_match import PostgameStore


def envelope(selected=1, times=(0, 60020, 120040, 600120, 900180), match_number=800001):
    roles = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    names = ['Ornn', 'Sejuani', 'Ahri', 'Caitlyn', 'Lux', 'Fiora', 'Vi', 'Zed', 'Ezreal', 'Nami']
    people = [dict(participantId=i, puuid='PRIVATE_SENTINEL_'+str(i), championName=names[i-1],
                   teamPosition=roles[(i-1)%5], teamId=100 if i <= 5 else 200) for i in range(1, 11)]
    frames = [dict(timestamp=t, events=[], participantFrames={str(i): dict(participantId=i,
              totalGold=500+t//100+i, xp=t//200+i, level=min(18, 1+t//60000),
              position=dict(x=5000,y=5000)) for i in range(1, 11)}) for t in times]
    metadata = dict(matchId='KR_'+str(match_number), participants=[p['puuid'] for p in people])
    return dict(source='REAL', participant_id=selected,
                match=dict(metadata=copy.deepcopy(metadata), info=dict(gameVersion='16.20.1',
                    gameDuration=960, mapId=11, queueId=420, gameMode='CLASSIC', participants=people)),
                timeline=dict(metadata=copy.deepcopy(metadata), info=dict(frameInterval=60000,
                    participants=[dict(participantId=p['participantId'], puuid=p['puuid']) for p in people], frames=frames)))


def measurement(report, mode='OBSERVED_MINUTE_BIN', minute=10):
    return next(x for x in report['measurements'] if x['mode'] == mode and x['minute'] == minute)


class ResourceRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.resource_recovery'), 'new resource recovery module missing')
        self.api = importlib.import_module('coach_v1.resource_recovery')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = PostgameStore(self.root/'private'/'matches')

    def audit(self, body=None):
        self.store.import_match(body or envelope())
        return self.api.audit_private_cache(self.root)

    def test_offset_observation_recovers_gold_xp_level_without_claiming_exact(self):
        r = self.audit(); p = measurement(r)
        self.assertEqual(p['timestamp_ms']['median'], 600120)
        self.assertEqual(p['offset_ms']['median'], 120)
        self.assertEqual(p['metrics']['gold']['difference']['mean'], -5)
        self.assertEqual(p['metrics']['xp']['difference']['mean'], -5)
        self.assertEqual(p['metrics']['level']['difference']['mean'], 0)
        exact = measurement(r, 'EXACT_TIMESTAMP')['metrics']['gold']['difference']
        self.assertEqual(exact['n_valid'], 0)
        self.assertEqual(exact['missing_reasons']['EXACT_TIMESTAMP_ABSENT'], 1)
        self.assertIsNone(exact['mean'])
        self.assertEqual(r['inspection']['all_participant_frames']['xp']['n_valid'], 50)
        self.assertEqual(r['inspection']['transform_comparison']['mismatch_n'], 0)
        self.assertEqual(r['inspection']['transform_comparison']['checked_n'], 15)

    def test_exact_timestamp_and_latest_same_bin_are_separate_same_frame_pairs(self):
        b = envelope(times=(0, 600000, 600050, 900000))
        b['timeline']['info']['frames'][2]['participantFrames']['1']['totalGold'] = 9999
        r = self.audit(b)
        self.assertEqual(measurement(r, 'EXACT_TIMESTAMP')['timestamp_ms']['mean'], 600000)
        p = measurement(r)
        self.assertEqual(p['timestamp_ms']['mean'], 600050)
        self.assertEqual(p['frames_in_bin']['mean'], 2)
        self.assertEqual(p['metrics']['gold']['difference']['mean'], 9999-(500+600050//100+6))
        self.assertEqual(p['metrics']['gold']['difference']['n_valid'], 1)

    def test_does_not_borrow_previous_or_next_bin_or_interpolate_gap(self):
        b = envelope(times=(0, 599999, 660000, 900180))
        r = self.audit(b); p = measurement(r)
        self.assertEqual(p['timestamp_ms']['n_valid'], 0)
        self.assertEqual(p['metrics']['gold']['difference']['missing_reasons']['MINUTE_BIN_ABSENT'], 1)
        self.assertEqual(r['inspection']['timestamps']['internal_gap_over_65000_n'], 2)
        self.assertEqual(measurement(r, minute=15)['metrics']['gold']['difference']['n_valid'], 1)

    def test_point_observation_includes_final_received_frame_at_end(self):
        b = envelope(times=(0, 600000, 900000)); b['match']['info']['gameDuration'] = 900
        r = self.audit(b)
        self.assertEqual(measurement(r, minute=15)['metrics']['xp']['difference']['n_valid'], 1)
        self.assertEqual(measurement(r, minute=15)['selected_final_received_n'], 1)
        self.assertTrue(r['measurement_policy']['final_received_frame_allowed_if_not_after_reported_end'])

    def test_short_game_and_post_end_frame_have_distinct_diagnostics(self):
        b = envelope(times=(0, 600100, 900100)); b['match']['info']['gameDuration'] = 880
        r = self.audit(b)
        self.assertEqual(r['inspection']['timestamps']['frames_after_reported_end_n'], 1)
        p = measurement(r, minute=15)
        self.assertEqual(p['metrics']['gold']['difference']['missing_reasons']['TARGET_AFTER_REPORTED_END'], 1)
        self.assertEqual(p['timestamp_ms']['n_valid'], 0)

    def test_missing_own_xp_is_not_zero_or_inferred_from_level(self):
        b = envelope(); del b['timeline']['info']['frames'][3]['participantFrames']['1']['xp']
        b['timeline']['info']['frames'][3]['participantFrames']['6']['xp'] = 0
        r = self.audit(b); p = measurement(r)['metrics']['xp']
        self.assertEqual(p['own']['missing_reasons']['OWN_FIELD_MISSING'], 1)
        self.assertIsNone(p['own']['mean'])
        self.assertEqual(p['opponent']['mean'], 0)
        self.assertEqual(p['difference']['missing_reasons']['OWN_FIELD_MISSING'], 1)
        self.assertEqual(r['inspection']['all_participant_frames']['xp']['missing_n'], 1)
        self.assertEqual(measurement(r)['metrics']['level']['difference']['n_valid'], 1)

    def test_ambiguous_opponent_does_not_erase_own_observation(self):
        b = envelope(); b['match']['info']['participants'][6]['teamPosition'] = 'TOP'
        r = self.audit(b); p = measurement(r)['metrics']['gold']
        self.assertEqual(p['own']['n_valid'], 1)
        self.assertEqual(p['opponent']['missing_reasons']['OPPONENT_UNAVAILABLE'], 1)
        self.assertEqual(p['difference']['missing_reasons']['OPPONENT_UNAVAILABLE'], 1)
        self.assertIsNone(r['cohorts'][0]['opponent_champion'])

    def test_match_counts_deduplicate_distinct_selected_people(self):
        self.store.import_match(envelope(selected=1)); self.store.import_match(envelope(selected=4))
        r = self.api.audit_private_cache(self.root)
        self.assertEqual(r['source']['matches'], 1)
        self.assertEqual(r['source']['participant_observations'], 2)
        self.assertEqual(r['inspection']['all_participant_frames']['frames'], 50)
        self.assertEqual(r['inspection']['selected_participant_frames']['frames'], 10)
        self.assertEqual(measurement(r)['metrics']['gold']['difference']['match_n'], 1)
        self.assertEqual(measurement(r)['metrics']['gold']['difference']['n_valid'], 2)

    def test_conflicting_originals_for_same_match_fail_closed(self):
        self.store.import_match(envelope(selected=1))
        b = envelope(selected=4); b['timeline']['info']['frames'][3]['participantFrames']['1']['xp'] += 1
        self.store.import_match(b)
        with self.assertRaisesRegex(ValueError, 'CONFLICTING'):
            self.api.audit_private_cache(self.root)

    def test_quantiles_and_patches_do_not_pool_cohort_identity(self):
        for i, offset in enumerate((100,200,300,400)):
            b = envelope(times=(0,600000+offset,900000+offset),match_number=800010+i)
            if i == 3: b['match']['info']['gameVersion'] = '16.19.1'
            self.store.import_match(b)
        r = self.api.audit_private_cache(self.root)
        s = measurement(r)['offset_ms']
        self.assertEqual((s['minimum'],s['q1'],s['median'],s['q3'],s['maximum']), (100,175,250,325,400))
        self.assertEqual({x['patch']:x['participant_observations'] for x in r['patches']}, {'16.19':1,'16.20':3})
        self.assertEqual(len(r['cohorts']), 2)

    def test_strict_allowlist_rejects_identity_nonfinite_and_inconsistent_missing(self):
        r = self.audit()
        self.assertEqual(self.api.validate_report(r), r)
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(r)); self.assertNotIn('KR_800001', json.dumps(r))
        mutations = [lambda d: d.update(puuid='PRIVATE_SENTINEL'),
                     lambda d: d['cohorts'][0].update(champion='PRIVATE_SENTINEL'),
                     lambda d: measurement(d)['metrics']['xp']['own'].update(mean=float('nan')),
                     lambda d: measurement(d)['metrics']['xp']['own'].update(n_valid=True),
                     lambda d: measurement(d)['metrics']['xp']['own']['missing_reasons'].update(OWN_FIELD_MISSING=1),
                     lambda d: d['measurement_policy'].update(selection='NEAREST_FRAME')]
        for mutate in mutations:
            bad = copy.deepcopy(r); mutate(bad)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): self.api.validate_report(bad)

    def test_unbound_report_and_wrong_pinned_checkpoint_rejected(self):
        r = self.audit(); folder = self.root/'public'; folder.mkdir()
        (folder/'resources.json').write_text(json.dumps(r))
        with self.assertRaises(ValueError): self.api.load_bound_report(folder)
        (folder/'source-binding.json').write_text(json.dumps(dict(schema_version='resource-recovery.binding.v1', checkpoint=dict(run_id=1,artifact_id=2))))
        with self.assertRaises(ValueError): self.api.load_bound_report(folder)

    def test_binding_uses_real_git_ancestry_and_rejects_tampered_bytes_or_sources(self):
        # Fabricated 89/108 envelope counts exercise the scope gate, not real evidence.
        for i in range(89):
            self.store.import_match(envelope(match_number=810000+i))
            if i < 19:
                self.store.import_match(envelope(selected=4,match_number=810000+i))
        report = self.api.audit_private_cache(self.root)
        repo = self.root/'isolated-git'; repo.mkdir()
        original_source = Path(self.api.__file__).read_bytes()
        for name in self.api.SOURCE_FILES:
            path = repo/name; path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(original_source if name == 'coach_v1/resource_recovery.py' else b'isolated fixture source\n')
        for args in (['init','-q'], ['add','.'], ['-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','isolated fixture']):
            subprocess.run(['git',*args],cwd=repo,check=True,capture_output=True)
        commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        spec = importlib.util.spec_from_file_location('coach_v1._isolated_resource_binding',repo/'coach_v1/resource_recovery.py')
        isolated = importlib.util.module_from_spec(spec); spec.loader.exec_module(isolated)
        folder = repo/'public'; folder.mkdir()
        raw = json.dumps(report,sort_keys=True,allow_nan=False).encode()
        binding = dict(schema_version='resource-recovery.binding.v1',actual_commit=commit,
                       source_sha256={p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in self.api.SOURCE_FILES},
                       checkpoint=dict(run_id=38410710876,artifact_id=11822391323),
                       report_sha256=hashlib.sha256(raw).hexdigest(),source_samples=report['source'],
                       provider_requests=0,network_attempts=0,privacy='ANONYMOUS_ALLOWLIST_AGGREGATES_ONLY',coaching_accuracy=None)
        (folder/'resources.json').write_bytes(raw)
        (folder/'source-binding.json').write_text(json.dumps(binding))
        self.assertEqual(isolated.load_bound_report(folder), (report,binding))
        (folder/'resources.json').write_bytes(raw+b' ')
        with self.assertRaises(ValueError): isolated.load_bound_report(folder)
        (folder/'resources.json').write_bytes(raw)
        changed = repo/self.api.SOURCE_FILES[-1]; changed.write_bytes(b'altered source\n')
        with self.assertRaises(ValueError): isolated.load_bound_report(folder)
        changed.write_bytes(b'isolated fixture source\n')
        for key,value in [('actual_commit','0'*40),('provider_requests',True),('network_attempts',1),('checkpoint',dict(run_id=38410710876,artifact_id=1))]:
            bad = copy.deepcopy(binding); bad[key] = value
            (folder/'source-binding.json').write_text(json.dumps(bad))
            with self.subTest(key=key),self.assertRaises(ValueError): isolated.load_bound_report(folder)

    def test_summary_counts_and_means_reconcile_with_patch_and_cohort_partitions(self):
        self.store.import_match(envelope(match_number=820001))
        b = envelope(match_number=820002); b['timeline']['info']['frames'][3]['participantFrames']['1']['xp'] += 100
        self.store.import_match(b)
        r = self.api.audit_private_cache(self.root)
        bad = copy.deepcopy(r)
        measurement(bad['cohorts'][0])['metrics']['xp']['own']['mean'] += 1
        with self.assertRaises(ValueError): self.api.validate_report(bad)

    def test_diagnostic_original_frame_interval_and_origin_are_explicit(self):
        r = self.audit(envelope(times=(20,600020,900020)))
        t = r['inspection']['timestamps']
        self.assertIn('declared_interval_ms', t, 'original declared interval diagnostics absent')
        self.assertEqual(t['declared_interval_ms']['median'], 60000)
        self.assertEqual(t['first_received_nonzero_n'], 1)
        self.assertEqual(t['received_frames'], 3)
        self.assertEqual(t['first_received_ms']['median'], 20)
