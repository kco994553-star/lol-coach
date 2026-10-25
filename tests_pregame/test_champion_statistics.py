"""Exact-scope champion summaries from isolated synthetic ending outcomes."""
import copy
import importlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from coach_v1.outcome_stats import build_outcome_dataset
from tests_pregame.test_outcome_stats import pair
from tests_pregame.test_power_stats import source, pair as resource_pair
from coach_v1.power_stats import build_power_dataset

ROOT = Path(__file__).resolve().parents[1]


class ChampionStatisticsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('coach_v1.champion_stats'),
                             'exact champion statistics projection is missing')
        self.stats = importlib.import_module('coach_v1.champion_stats')

    def dataset(self, rows):
        return build_outcome_dataset(rows, source=source())

    def select(self, data, opponent=None, patch='16.19', tier='GOLD'):
        return self.stats.summarize_outcome(data, 'Champion', 'TOP', patch, tier,
                                            opponent_champion=opponent)

    def test_summary_weights_trials_and_recomputes_wilson(self):
        data = self.dataset([pair(0, duration=60, win=True)] +
                            [pair(i + 1, duration=360, win=False) for i in range(9)])
        summary = self.select(data)
        self.assertEqual((summary['n'], summary['wins'], summary['win_rate_pct']), (10, 1, 10))
        self.assertAlmostEqual(summary['ci_low_pct'], 1.787621309507291, places=10)
        self.assertAlmostEqual(summary['ci_high_pct'], 40.415002679526, places=10)
        self.assertEqual(summary['status'], 'INSUFFICIENT_DATA')

    def test_opponent_scope_and_absent_scope_never_fall_back(self):
        data = self.dataset([pair(0, opponent='EnemyA', win=True),
                             pair(1, opponent='EnemyB', win=False)])
        self.assertEqual((self.select(data, 'EnemyA')['n'], self.select(data, 'EnemyA')['wins']), (1, 1))
        for summary in (self.select(data, 'Absent'), self.select(data, patch='16.20'),
                        self.select(data, tier='GRANDMASTER')):
            self.assertEqual(summary, dict(status='NO_DATA', n=0, wins=0,
                win_rate_pct=None, ci_low_pct=None, ci_high_pct=None))

    def test_disjoint_five_minute_bins_and_tail_keep_empty_gaps(self):
        minutes = [0, 4, 5, 9, 10, 59, 60, 75]
        data = self.dataset([pair(i, duration=max(1, m * 60)) for i, m in enumerate(minutes)])
        bins = self.stats.duration_outcomes(data, 'Champion', 'TOP', '16.19', 'GOLD')
        self.assertEqual([(b['start_minute'], b['end_minute']) for b in bins],
                         [(m, m + 5 if m < 60 else None) for m in range(0, 61, 5)])
        self.assertEqual([b['n'] for b in bins], [2, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2])
        self.assertEqual(sum(b['n'] for b in bins), self.select(data)['n'])
        self.assertIsNone(bins[3]['win_rate_pct'])
        self.assertTrue(all(not b['drawable'] for b in bins))

    def test_drawable_boundary_99_and_100(self):
        data = self.dataset([pair(i, duration=60 if i < 99 else 360) for i in range(199)])
        bins = self.stats.duration_outcomes(data, 'Champion', 'TOP', '16.19', 'GOLD')
        self.assertEqual((bins[0]['n'], bins[0]['drawable']), (99, False))
        self.assertEqual((bins[1]['n'], bins[1]['drawable']), (100, True))
        self.assertEqual(self.select(data)['status'], 'READY')

    def test_projection_deduplicates_positions_and_does_not_mutate_or_leak(self):
        data = self.dataset([pair(0), pair(0), pair(1, duration=600, win=False)])
        before = copy.deepcopy(data)
        result = self.stats.build_champion_statistics(data)
        self.assertEqual(data, before)
        self.assertEqual(result['format'], 'lol-coach-champion-statistics-v1')
        self.assertEqual(result['draw_min_n'], 100)
        champion = result['champions']['Champion']
        self.assertEqual(champion['observed_positions'], [{'position': 'TOP', 'matches': 2}])
        position = champion['positions']['TOP']
        self.assertEqual(position['summary']['n'], 2)
        self.assertEqual(position['opponents']['Opponent']['summary']['n'], 2)
        self.assertEqual(result['unsupported_metrics'], ['pick_rate', 'ban_rate', 'runes', 'item_builds', 'skill_order'])
        self.assertEqual(result['position_source']['matches'], 2)
        text = json.dumps(result)
        for secret in data['samples']['hashed_match_ids']:
            self.assertNotIn(secret, text)
        for key in ('input_match_hashes', 'hashed_match_ids', 'puuid', 'participantId'):
            self.assertNotIn(key, text)
        self.assertEqual(result, self.stats.build_champion_statistics(data))

    def test_position_dataset_counts_union_hashes_across_minute_rows(self):
        outcomes = self.dataset([pair(0)])
        coverage = self.dataset([pair(0), pair(1, duration=900)])
        result = self.stats.build_champion_statistics(outcomes, position_dataset=coverage)
        self.assertEqual(result['champions']['Champion']['observed_positions'][0]['matches'], 2)
        self.assertEqual(result['champions']['Champion']['positions']['TOP']['summary']['n'], 1)
        self.assertNotEqual(result['source']['dataset_digest'], result['position_source']['dataset_digest'])

    def test_distinct_position_snapshot_rejects_different_patch_or_tier(self):
        outcomes = self.dataset([pair(0)])
        different_patch_source = source()
        different_patch_source['patch'] = '16.20'
        different_patch = build_outcome_dataset([pair(0, patch='16.20')], source=different_patch_source)
        different_tier_source = source()
        different_tier_source['tier'] = 'CHALLENGER'
        different_tier = build_outcome_dataset([pair(0)], source=different_tier_source)
        for coverage in (different_patch, different_tier):
            with self.assertRaises(ValueError):
                self.stats.build_champion_statistics(outcomes, position_dataset=coverage)

    def test_manifest_reader_rejects_each_hash_binding_before_projection(self):
        spec = importlib.util.spec_from_file_location('champion_builder', ROOT / 'scripts/build_champion_statistics.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        entry = json.loads((ROOT / 'data/riot/2026-10-11/manifest.json').read_text())['files']['outcome-data.json']
        bindings = [entry['gzip_sha256'], entry['sha256'], entry['dataset_digest']]
        for index in range(3):
            corrupted = bindings[:]
            corrupted[index] = '0' * 64
            with self.assertRaises(ValueError):
                builder._read_bound(builder.OUTCOME, *corrupted)

    def test_invalid_hashes_counts_rates_and_mixed_scope_fail_closed(self):
        data = self.dataset([pair(0)])
        mutations = [lambda d: d['cohorts'][0]['points'][0].update(n=2),
                     lambda d: d['cohorts'][0]['points'][0].update(win_rate=0.123),
                     lambda d: d['cohorts'][0].update(patch='16.20'),
                     lambda d: d['cohorts'][0]['points'][0]['input_match_hashes'].append('a' * 64)]
        for mutate in mutations:
            broken = copy.deepcopy(data)
            mutate(broken)
            with self.assertRaises(ValueError):
                self.stats.build_champion_statistics(broken)

    def test_growth_keeps_power_denominators_units_delta_ci_and_selected_minutes(self):
        outcomes = self.dataset([pair(0)])
        power = build_power_dataset([resource_pair(i, delta=100 * (i + 1), minutes=(3, 5, 10))
                                    for i in range(3)], source=source())
        before = copy.deepcopy(power)
        value = self.stats.build_champion_statistics(outcomes, growth_dataset=power)
        self.assertEqual(value['source']['matches'], 1)
        self.assertEqual(value['growth_source']['matches'], 3)
        self.assertNotEqual(value['source']['dataset_digest'], value['growth_source']['dataset_digest'])
        self.assertEqual(value['growth_source']['uncertainty_scope'], 'CHAMPION_MINUS_POOLED_ROLE_RATE_NOT_CHAMPION_MEAN_CI')
        growth = value['champions']['Champion']['positions']['TOP']['growth']
        self.assertEqual(growth['status'], 'AVAILABLE')
        self.assertEqual({p['minute'] for p in growth['points']}, {5, 10})
        projected = next(p for p in growth['points'] if p['minute'] == 5 and p['metric'] == 'gold_delta')
        original = next(c for c in power['cohorts'] if c['champion'] == 'Champion' and
                        c['position'] == 'TOP' and c['metric'] == 'gold_delta' and c['comparison'] == 'ROLE_POPULATION')
        point = next(p for p in original['points'] if p['minute'] == 5)
        for key in ('champion_mean', 'champion_n', 'reference_mean', 'reference_n', 'n', 'visible', 'omission_reason'):
            self.assertEqual(projected[key], point[key])
        self.assertEqual(projected['delta_ci95'], point['ci95'])
        self.assertEqual(projected['mean_delta'], point['mean'])
        self.assertEqual(projected['unit'], 'GOLD_PER_MINUTE')
        self.assertNotIn('ci95', projected)
        self.assertEqual(power, before)
        text = json.dumps(value)
        for hashed in power['samples']['hashed_match_ids']:
            self.assertNotIn(hashed, text)
        for private in ('input_match_hashes', 'hashed_match_ids', 'PRIVATE_SYNTHETIC', 'puuid', 'participantId'):
            self.assertNotIn(private, text)

    def test_growth_markers_deduplicate_metrics_and_keep_observation_uncertainty(self):
        outcomes = self.dataset([pair(0)])
        power = build_power_dataset([resource_pair(i) for i in range(3)], source=source(),
                                    complete_item_ids=(3001, 3002))
        value = self.stats.build_champion_statistics(outcomes, growth_dataset=power)
        markers = value['champions']['Champion']['positions']['TOP']['growth']['markers']
        self.assertEqual(len(markers), 5)  # three LEVEL observations, two ITEM candidates, not x3 metrics
        levels = [m for m in markers if m['kind'] == 'LEVEL']
        self.assertEqual([m['level'] for m in levels], [2, 3, 6])
        for m in levels:
            self.assertEqual(m['n'], 3)
            self.assertEqual(m['observation'], 'FIRST_OBSERVED_FRAME_INTERVAL_CENSORED')
            self.assertEqual(m['label'], 'DESCRIPTIVE_NON_CAUSAL')
            self.assertEqual((m['q1_minute'], m['median_minute'], m['q3_minute']), ({2: 1, 3: 2, 6: 3}[m['level']],) * 3)
        items = [m for m in markers if m['kind'] == 'ITEM']
        self.assertEqual([m['item_id'] for m in items], [3001, 3002])
        self.assertTrue(all(m['n'] == 3 and m['observation'] == 'OBSERVED_NONBOOT_NONCONSUMABLE_COMPLETE_ITEM_PURCHASE_CANDIDATE' for m in items))
        self.assertTrue(all('item_name' not in m for m in items))
        self.assertFalse(any(m['level'] in (11, 16) for m in markers))

    def test_growth_suppression_and_power_only_role_do_not_invent_outcome_coverage(self):
        outcomes = self.dataset([pair(0)])
        power_pair = resource_pair(0, minutes=(5,))
        power_pair['match']['info']['participants'][0]['championName'] = 'PowerOnly'
        power = build_power_dataset([power_pair], source=source())
        value = self.stats.build_champion_statistics(outcomes, growth_dataset=power)
        champion = value['champions']['PowerOnly']
        self.assertEqual(champion['observed_positions'], [])
        role = champion['positions']['TOP']
        self.assertEqual(role['summary']['n'], 0)
        self.assertTrue(all(not p['visible'] for p in role['growth']['points']))
        self.assertTrue(all(p['champion_n'] == 1 and p['n'] == 1 for p in role['growth']['points']))
        broken = copy.deepcopy(power)
        for cohort in broken['cohorts']:
            cohort['tier'] = 'CHALLENGER'
        broken['source']['tier'] = 'CHALLENGER'
        with self.assertRaises(ValueError):
            self.stats.build_champion_statistics(outcomes, growth_dataset=broken)

    def test_real_generation_manifest_binding_and_public_contract(self):
        script = ROOT / 'scripts/build_champion_statistics.py'
        self.assertTrue(script.exists(), 'deterministic generator missing')
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'champion-stats.json'
            subprocess.run([sys.executable, str(script), '--output', str(output)], check=True,
                           cwd=ROOT, capture_output=True, text=True)
            first = output.read_bytes()
            subprocess.run([sys.executable, str(script), '--output', str(output)], check=True,
                           cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first, output.read_bytes())
        value = json.loads(first)
        self.assertEqual(first.count(b'\n'), 1, 'public payload should be minified')
        self.assertEqual(value['growth_source']['matches'], 275)
        self.assertEqual(value['growth_source']['dataset_digest'], '449829de01ff657f3f73d8527a6bcc50ef413a55ca6135a04653b9109712bd63')
        self.assertEqual(value['source']['matches'], 50)
        self.assertEqual(value['position_source']['matches'], 50)
        self.assertEqual(value['position_source']['count_basis'], 'UNIQUE_OUTCOME_MATCH_HASH_UNION')
        self.assertEqual(value['source']['dataset_digest'],
                         '1f6f276d153bc11978670b0644ee31b16b28f260deb1be23196aabf0053d64fc')
        self.assertEqual(value['source']['sample_kind'], 'REAL')
        self.assertEqual(value['source']['tier_meaning'],
                         'CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS')
        self.assertEqual(first, (ROOT / 'web_r4/champion-stats.json').read_bytes())
        for champion in value['champions'].values():
            for role in champion['positions'].values():
                self.assertEqual(sum(b['n'] for b in role['duration']), role['summary']['n'])
                self.assertEqual(sum(p['summary']['n'] for p in role['opponents'].values()), role['summary']['n'])


if __name__ == '__main__':
    unittest.main()
