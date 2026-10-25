"""Synthetic union, privacy and opponent-association counterexamples."""
from copy import deepcopy
import json
import unittest

from coach_v1.champion_insights import build_champion_insights, select_insights, validate_champion_insights
from coach_v1.matchup_results import (build_matchup_results, empty_matchup_results,
    merge_matchup_results, normalize_match, validate_matchup_results)
from coach_v1.outcome_stats import build_outcome_dataset
from tests_pregame.test_outcome_stats import pair
from tests_pregame.test_power_stats import source


def companion(numbers, tier='MASTER', wins=None):
    s = source()
    s['tier'] = tier
    return build_matchup_results([pair(i, win=(wins or {}).get(i, True)) for i in numbers], source=s)


def index(results=(), outcomes=(), **kwargs):
    return build_champion_insights(outcomes, result_datasets=results, allow_synthetic=True, **kwargs)


class ChampionInsightTests(unittest.TestCase):
    def test_extreme_win_rates_remain_inside_strict_wilson_interval(self):
        from coach_v1.outcome_stats import _wilson, validate_outcome_dataset
        for n in (1, 2, 3, 5, 10, 20, 100, 1000):
            for wins in (0, n):
                with self.subTest(n=n, wins=wins):
                    bounds = _wilson(wins, n)
                    self.assertLessEqual(bounds['low'], wins / n)
                    self.assertGreaterEqual(bounds['high'], wins / n)
        for won in (True, False):
            data = build_outcome_dataset([pair(i, win=won) for i in range(20)], source=source())
            self.assertEqual(validate_outcome_dataset(data), data)

    def test_unique_seed_union_not_sum_and_unrelated_tier_no_fallback(self):
        data = index([companion([1, 2], wins={2: False}), companion([2, 3], 'GRANDMASTER', {2: False}),
                      companion([3, 4], 'CHALLENGER'), companion([2, 5], 'GOLD', {2: False})])
        pooled = select_insights(data, 'Champion', 'TOP')
        self.assertEqual((pooled['summary']['n'], pooled['summary']['wins']), (4, 3))
        self.assertEqual(pooled['scope']['coverage'], 'COMPLETE')
        self.assertEqual(select_insights(data, 'Champion', 'TOP', 'ALL')['summary']['n'], 5)
        self.assertEqual(select_insights(data, 'Champion', 'TOP', 'IRON')['status'], 'NO_DATA')
        self.assertEqual(select_insights(data, 'Champion', 'TOP', patch='16.18')['status'], 'NO_DATA')
        self.assertEqual(select_insights(data, 'Champion', 'MID')['status'], 'NO_DATA')
        self.assertEqual(pooled['scope']['a_rank_at_match'], 'UNKNOWN')

    def test_nonuniform_rates_and_independent_wilson_recomputation(self):
        d = index([companion([1]), companion(range(2, 11), 'GRANDMASTER', {i: False for i in range(2, 11)})])
        row = select_insights(d, 'Champion', 'TOP')['summary']
        self.assertAlmostEqual(row['win_rate'], .1)
        self.assertAlmostEqual(row['ci95']['low'], .017876213095072896)
        self.assertAlmostEqual(row['ci95']['high'], .4041500267952385)

    def test_conflicts_fail_closed_patch_roster_winner_and_duplicate_dedup(self):
        a = companion([1])
        self.assertEqual(len(merge_matchup_results(a, deepcopy(a))['records']), 1)
        for mutate in (lambda r: r.update(winner=1), lambda r: r.update(patch='16.20'),
                       lambda r: r['teams'][1][1].update(champion='OtherJungler')):
            b = deepcopy(a)
            mutate(b['records'][0])
            with self.assertRaises(ValueError):
                merge_matchup_results(a, b)

    def test_enemy_cross_role_not_ally_or_same_role_and_reverse_complement(self):
        d = index([companion([1, 2], wins={2: False})], ranking_min_n=1)
        rows = [r for r in d['matchups'] if r['tier'] == 'MASTER' and r['champion'] == 'Champion' and r['basis'] == 'ENEMY_TEAM_ROSTER']
        self.assertEqual(len(rows), 5)
        jungle = next(r for r in rows if r['enemy_position'] == 'JUNGLE')
        self.assertEqual((jungle['enemy_champion'], jungle['n'], jungle['wins']), ('Opponent2', 2, 1))
        reverse = next(r for r in d['matchups'] if r['tier'] == 'MASTER' and r['champion'] == 'Opponent2' and r['position'] == 'JUNGLE' and r['enemy_champion'] == 'Champion' and r['enemy_position'] == 'TOP')
        self.assertEqual(jungle['wins'] + reverse['wins'], jungle['n'])
        self.assertFalse(any(r['enemy_champion'] == 'Champion2' for r in rows))

    def test_same_legacy_results_two_different_cross_role_worlds(self):
        first = [pair(1), pair(2, win=False)]
        second = deepcopy(first)
        for p in second:
            people = p['match']['info']['participants']
            people[1]['championName'], people[6]['championName'] = people[6]['championName'], people[1]['championName']
        self.assertEqual(build_outcome_dataset(first, source=source()), build_outcome_dataset(second, source=source()))
        def roster(pairs):
            return index([build_matchup_results(pairs, source=source())])
        one, two = roster(first), roster(second)
        def enemy(d):
            return next(r['enemy_champion'] for r in d['matchups'] if r['champion'] == 'Champion' and r['tier'] == 'GOLD' and r['enemy_position'] == 'JUNGLE')
        self.assertNotEqual(enemy(one), enemy(two))

    def test_unknown_roles_excluded_never_inferred_and_slot_order_stable(self):
        raw = pair()['match']
        raw['info']['participants'][6]['teamPosition'] = 'UNKNOWN'
        r = normalize_match(raw, 'MASTER', sample_kind='SYNTHETIC')
        self.assertIsNone(next(s['position'] for s in r['teams'][1] if s['champion'] == 'Opponent2'))
        raw['info']['participants'].reverse()
        self.assertEqual(r, normalize_match(raw, 'MASTER', sample_kind='SYNTHETIC'))
        companion_data = empty_matchup_results()
        companion_data['records'] = [r]
        d = index([companion_data])
        self.assertFalse(any(row['champion'] == 'Champion' and row['enemy_position'] == 'JUNGLE' for row in d['matchups']))
        self.assertTrue(any(row['champion'] == 'Champion' and row['enemy_position'] == 'MID' for row in d['matchups']))

    def test_mirrored_roles_exclude_symmetric_endpoints_preserve_other_roles(self):
        s = source()
        d = index([build_matchup_results([pair(opponent='Champion')], source=s)])
        self.assertFalse(any(r['champion'] == 'Champion' for r in d['summaries']))
        self.assertFalse(any(r['enemy_champion'] == 'Champion' for r in d['matchups']))
        self.assertTrue(any(r['champion'] == 'Champion2' for r in d['summaries']))

    def test_legacy_own_role_ranking_eligible_other_roles_unavailable(self):
        s = source()
        legacy = build_outcome_dataset([pair(i, win=i % 2 == 0) for i in range(20)], source=s)
        d = index(outcomes=[legacy])
        view = select_insights(d, 'Champion', 'TOP', 'GOLD')
        self.assertEqual(view['by_enemy_position']['TOP']['best'][0]['basis'], 'SAME_ROLE_ENCOUNTERS')
        self.assertEqual(view['by_enemy_position']['TOP']['best'][0]['n'], 20)
        self.assertEqual(view['by_enemy_position']['JUNGLE']['best'], [])
        self.assertEqual(view['scope']['cross_role_matches'], 0)

    def test_invalid_empty_source_and_malformed_private_records_reject(self):
        for tier in ('ALL', 'MASTER_PLUS', 'UNKNOWN'):
            s = source()
            s['tier'] = tier
            with self.assertRaises(ValueError):
                build_matchup_results([], source=s)
        wrong_provider = source()
        wrong_provider['provider'] = 'RIOT_API'
        with self.assertRaises(ValueError):
            build_matchup_results([], source=wrong_provider)
        valid = companion([1])
        mutations = [lambda r: r.update(seed_tiers=[{}]),
                     lambda r: r.update(provenance=[None]),
                     lambda r: r['teams'][0][0].update(position=[]),
                     lambda r: r.update(winner=True)]
        for mutate in mutations:
            d = deepcopy(valid)
            mutate(d['records'][0])
            with self.assertRaises(ValueError):
                validate_matchup_results(d)

    def test_invalid_wins_raw_fields_and_private_to_public_boundary(self):
        for mutation in (lambda i: i['participants'][0].pop('win'),
                         lambda i: i['teams'][0].update(win=1),
                         lambda i: i['participants'][0].update(win=False),
                         lambda i: i.update(gameDuration=True),
                         lambda i: i.update(gameEndTimestamp=0)):
            raw = pair()['match']
            mutation(raw['info'])
            self.assertIsNone(normalize_match(raw, 'MASTER', sample_kind='SYNTHETIC'))
        private = companion([1])
        public = index([private])
        serialized = json.dumps(public)
        for forbidden in ('PRIVATE_SYNTHETIC', 'KR_SYNTHETIC', 'puuid', 'participantId', 'teams', 'records', private['records'][0]['hash']):
            self.assertNotIn(forbidden, serialized)
        raw = deepcopy(private)
        raw['records'][0]['puuid'] = 'PRIVATE_SENTINEL'
        with self.assertRaises(ValueError):
            validate_matchup_results(raw)
        with self.assertRaises(ValueError):
            normalize_match(pair()['match'], 'MASTER', sample_kind='SYNTHETIC', provenance={'puuid': 'PRIVATE'})
        public['raw'] = 'PRIVATE'
        with self.assertRaises(ValueError):
            validate_champion_insights(public, allow_synthetic=True)
        with self.assertRaises(ValueError):
            build_champion_insights(result_datasets=[private])

    def test_legacy_partial_overlap_rejected_disjoint_and_repeated_snapshots_safe(self):
        def legacy(numbers, tier):
            s = source()
            s['tier'] = tier
            return build_outcome_dataset([pair(i) for i in numbers], source=s)
        a, b = legacy([1, 2], 'MASTER'), legacy([2, 3], 'GRANDMASTER')
        with self.assertRaises(ValueError):
            index(outcomes=[a, b])
        d = index(outcomes=[a, deepcopy(a), legacy([3], 'GRANDMASTER')])
        self.assertEqual(select_insights(d, 'Champion', 'TOP')['summary']['n'], 3)
        # A completely retained legacy source is verified and redundant.
        mixed = index([companion([1, 2])], [a])
        self.assertEqual(select_insights(mixed, 'Champion', 'TOP')['summary']['n'], 2)
        bad = companion([1, 2], wins={1: False})
        with self.assertRaises(ValueError):
            index([bad], [a])

    def test_same_hash_different_patch_legacy_and_mixed_sources_fail_closed(self):
        s = source()
        old = build_outcome_dataset([pair(741, patch='16.19')], source=s)
        s['patch'] = '16.20'
        newer = build_outcome_dataset([pair(741, patch='16.20')], source=s)
        with self.assertRaises(ValueError):
            index(outcomes=[old, newer])
        with self.assertRaises(ValueError):
            index([build_matchup_results([pair(741, patch='16.20')], source=s)], [old])

    def test_current_real_snapshot_partial_master_plus_no_cross_role_invention(self):
        from scripts.build_champion_insights import project
        d = project()
        scope = next(s for s in d['scopes'] if s['tier'] == 'MASTER_PLUS')
        self.assertEqual(scope['available_tiers'], ['CHALLENGER'])
        self.assertEqual(scope['missing_tiers'], ['MASTER', 'GRANDMASTER'])
        self.assertEqual((scope['coverage'], scope['matches'], scope['cross_role_matches']), ('PARTIAL', 50, 0))
        self.assertFalse(any(r['basis'] == 'ENEMY_TEAM_ROSTER' for r in d['matchups']))
        self.assertEqual(d['default_patch'], '16.20')
        self.assertEqual(select_insights(d, 'Qiyana', 'JUNGLE', 'IRON')['status'], 'NO_DATA')
        frequent = select_insights(d, 'Qiyana', 'JUNGLE')['frequent_opponents']
        self.assertEqual((frequent[0]['enemy_champion'], frequent[0]['n'], frequent[0]['wins']), ('LeeSin', 6, 4))

    def test_ranking_minimum_excludes_one_win_independent_lists_and_explicit_ties(self):
        batches = []
        for enemy_index in range(12):
            n = 1 if enemy_index == 11 else 20
            pairs = []
            for k in range(n):
                p = pair(enemy_index * 100 + k, win=(k < enemy_index))
                p['match']['info']['participants'][6]['championName'] = 'Enemy' + str(enemy_index)
                pairs.append(p)
            batches.append(build_matchup_results(pairs, source=source()))
        d = index(batches)
        view = select_insights(d, 'Champion', 'TOP', 'GOLD')
        ranking = view['by_enemy_position']['JUNGLE']
        self.assertEqual((len(ranking['best']), len(ranking['worst']), ranking['eligible_count']), (5, 5, 11))
        self.assertFalse({r['enemy_champion'] for r in ranking['best']} & {r['enemy_champion'] for r in ranking['worst']})
        self.assertFalse(any(r['enemy_champion'] == 'Enemy11' for r in ranking['best']))
        sparse = select_insights(index([companion(range(20))]), 'Champion', 'TOP')
        self.assertEqual(len(sparse['by_enemy_position']['JUNGLE']['best']), 1)
        self.assertEqual(len(sparse['by_enemy_position']['JUNGLE']['worst']), 1)
        self.assertEqual(sparse['by_enemy_position']['JUNGLE']['overlap_count'], 1)
        self.assertTrue(sparse['by_enemy_position']['JUNGLE']['all_tied'])

    def test_equal_rates_display_n_name_ties_without_strength_claim(self):
        pairs = []
        for k in range(40):
            p = pair(k, win=k % 2 == 0)
            p['match']['info']['participants'][6]['championName'] = 'EnemyA' if k < 20 else 'EnemyB'
            pairs.append(p)
        view = select_insights(index([build_matchup_results(pairs, source=source())]), 'Champion', 'TOP', 'GOLD')
        ranks = view['by_enemy_position']['JUNGLE']
        self.assertTrue(ranks['all_tied'])
        self.assertTrue(ranks['rate_ties'])
        self.assertEqual(ranks['overlap_count'], 2)
        self.assertEqual([r['enemy_champion'] for r in ranks['best']], ['EnemyA', 'EnemyB'])
        self.assertEqual([r['enemy_champion'] for r in ranks['worst']], ['EnemyA', 'EnemyB'])


if __name__ == '__main__':
    unittest.main()
