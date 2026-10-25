"""Exact cohort unions and public, aggregate-only champion encounter insights."""
from collections import defaultdict
from copy import deepcopy

from .champion_stats import TIER_MEANING
from .matchup_results import merge_matchup_results
from .outcome_stats import _champion, _integer, _wilson, validate_outcome_dataset
from .power_stats import POSITIONS, TIERS
from .state import digest

FORMAT = 'lol-coach-champion-insights-v1'
RANKING_MIN_N = 20
SCOPES = TIERS + ('MASTER_PLUS', 'ALL')
LIMITATIONS = [
    'CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS',
    'A_RANK_AT_MATCH_UNKNOWN',
    'CONVENIENCE_SAMPLE_NOT_REPRESENTATIVE_OF_ALL_RANKED_GAMES',
    'A_TEAM_FINAL_GAME_RESULT_NOT_LANE_FIGHT_OR_CAUSAL_COUNTER',
    'ROLE_TABLES_OVERLAP_DO_NOT_SUM_ACROSS_ENEMY_POSITIONS',
    'MANY_COMPARISONS_CI_MAY_OVERLAP',
    'SMALL_N_IS_DESCRIPTIVE_NOT_TACTICAL_CERTAINTY',
    'UNKNOWN_ROLES_EXCLUDED_NOT_INFERRED',
    'MIRRORED_CHAMPION_ROLE_OWN_AND_ENEMY_ENDPOINTS_EXCLUDED',
    'EARLY_TERMINATION_OR_REMAKE_CLASSIFICATION_UNVERIFIED',
]


def tier_members(tier):
    if tier == 'MASTER_PLUS':
        return list(TIERS[-3:])
    if tier == 'ALL':
        return list(TIERS)
    if tier in TIERS:
        return [tier]
    raise ValueError('unsupported champion insight tier')


def _stats(n, wins, min_n):
    return dict(n=n, wins=wins, win_rate=wins / n if n else None,
        ci95=_wilson(wins, n) if n else None,
        status='READY' if n >= min_n else 'INSUFFICIENT_DATA' if n else 'NO_DATA')


def _record_trials(record):
    """Yield each nonmirrored observed own slot and its actual enemy slots."""
    roles = [{s['position']: s['champion'] for s in team if s['position']} for team in record['teams']]
    mirrored = {role for role in POSITIONS if role in roles[0] and roles[0].get(role) == roles[1].get(role)}
    for team_index, own in enumerate(record['teams']):
        enemies = record['teams'][1 - team_index]
        enemy_by_role = {s['position']: s['champion'] for s in enemies if s['position'] and s['position'] not in mirrored}
        for slot in own:
            role, champion = slot['position'], slot['champion']
            if role is None or role in mirrored:
                continue
            yield champion, role, team_index == record['winner'], enemy_by_role


def _legacy_sets(dataset):
    return set(dataset['samples']['hashed_match_ids'])


def _check_covered_legacy(dataset, records):
    """A fully retained legacy snapshot can be redundant only if results agree."""
    indexed = {}
    for sha, record in records.items():
        for champion, role, won, enemies in _record_trials(record):
            indexed[(sha, champion, role)] = (won, enemies)
    for cohort in dataset['cohorts']:
        for point in cohort['points']:
            wins = 0
            for sha in point['input_match_hashes']:
                value = indexed.get((sha, cohort['champion'], cohort['position']))
                if value is None or (cohort['comparison'] == 'MATCHUP' and value[1].get(cohort['position']) != cohort['opponent_champion']):
                    raise ValueError('legacy/result overlap cannot establish cohort agreement')
                wins += value[0]
            if wins != point['wins']:
                raise ValueError('legacy/result overlapping winner conflict')


def build_champion_insights(outcome_datasets=(), *, result_datasets=(), ranking_min_n=RANKING_MIN_N,
                            allow_synthetic=False):
    """Pure public projection. Legacy partial overlaps fail closed.

    Real UI builds reject synthetic sources. Passing allow_synthetic is solely
    for isolated fixtures; the public envelope marks its sample kind explicitly.
    """
    if not _integer(ranking_min_n, 1):
        raise ValueError('positive ranking minimum required')
    outcomes_by_digest = {}
    for dataset in outcome_datasets:
        d = validate_outcome_dataset(dataset)
        outcomes_by_digest[digest(d)] = d
    outcomes = [outcomes_by_digest[key] for key in sorted(outcomes_by_digest)]
    results = merge_matchup_results(*result_datasets)
    # Stable identity binds patch across the complete source set before any
    # scope is selected. Otherwise filtering first could hide contradictions
    # in separate patch buckets and publish both incompatible source claims.
    hash_patches = {}
    for d in outcomes:
        for sha in _legacy_sets(d):
            previous = hash_patches.setdefault(sha, d['source']['patch'])
            if previous != d['source']['patch']:
                raise ValueError('same anonymous match has conflicting source patches')
    for record in results['records']:
        previous = hash_patches.setdefault(record['hash'], record['patch'])
        if previous != record['patch']:
            raise ValueError('same anonymous match has conflicting source patches')
    kinds = {d['source']['sample_kind'] for d in outcomes} | {r['sample_kind'] for r in results['records']}
    if len(kinds) > 1 or ('SYNTHETIC' in kinds and not allow_synthetic):
        raise ValueError('public champion insights require unmixed REAL evidence')
    sample_kind = next(iter(kinds), 'REAL')
    patches = sorted({d['source']['patch'] for d in outcomes if d['source']['patch']} |
                     {r['patch'] for r in results['records']}, key=lambda p: tuple(map(int, p.split('.'))))
    sources = []
    for d in outcomes:
        s = d['source']
        sources.append(dict(kind='LEGACY_SAME_ROLE_OUTCOMES', dataset_digest=digest(d),
            patch=s['patch'], tier=s['tier'], sample_kind=s['sample_kind'],
            matches=len(_legacy_sets(d)), window_start=s['window_start'], window_end=s['window_end'],
            retrieved_at=s['retrieved_at'], division=None))
    # Public provenance is aggregate source metadata; never per-match rosters,
    # source member hashes, raw responses, or player identity fields.
    if results['records']:
        provenance = {}
        for r in results['records']:
            for p in r['provenance']:
                key = (r['patch'], digest(p))
                row = provenance.setdefault(key, dict(kind='ANONYMOUS_RESULT_COMPANION',
                    dataset_digest=digest(results), patch=r['patch'], tier=p['tier'],
                    sample_kind=r['sample_kind'], matches=0,
                    window_start=p.get('window_start'), window_end=p.get('window_end'),
                    retrieved_at=p.get('retrieved_at'), division=p.get('division')))
                row['matches'] += 1
        sources.extend(provenance[key] for key in sorted(provenance))
    scopes, summaries, matchups = [], [], []
    for patch in patches:
        patch_outcomes = [d for d in outcomes if d['source']['patch'] == patch and _legacy_sets(d)]
        patch_results = [r for r in results['records'] if r['patch'] == patch]
        for tier in SCOPES:
            requested = tier_members(tier)
            records = {r['hash']: r for r in patch_results if set(r['seed_tiers']) & set(requested)}
            legacy = [d for d in patch_outcomes if d['source']['tier'] in requested]
            available = {d['source']['tier'] for d in legacy} | {t for r in records.values() for t in r['seed_tiers'] if t in requested}
            cross_available = {t for r in records.values() for t in r['seed_tiers'] if t in requested}
            used = set(records)
            safe_legacy = []
            for d in legacy:
                hashes = _legacy_sets(d)
                overlap = hashes & used
                if overlap:
                    if hashes <= set(records):
                        _check_covered_legacy(d, records)
                        continue
                    raise ValueError('legacy overlap cannot recover per-match wins for exact union')
                used.update(hashes)
                safe_legacy.append(d)
            base = defaultdict(lambda: [0, 0])
            same = defaultdict(lambda: [0, 0])
            cross = defaultdict(lambda: [0, 0])
            for record in records.values():
                for champion, role, won, enemies in _record_trials(record):
                    base[(champion, role)][0] += 1
                    base[(champion, role)][1] += won
                    for enemy_role, enemy in enemies.items():
                        cross[(champion, role, enemy_role, enemy)][0] += 1
                        cross[(champion, role, enemy_role, enemy)][1] += won
                        if enemy_role == role:
                            same[(champion, role, enemy)][0] += 1
                            same[(champion, role, enemy)][1] += won
            for d in safe_legacy:
                for c in d['cohorts']:
                    values = base[(c['champion'], c['position'])] if c['comparison'] == 'CHAMPION_ROLE' else same[(c['champion'], c['position'], c['opponent_champion'])]
                    values[0] += sum(p['n'] for p in c['points'])
                    values[1] += sum(p['wins'] for p in c['points'])
            scopes.append(dict(patch=patch, tier=tier, requested_tiers=requested,
                available_tiers=[t for t in requested if t in available],
                missing_tiers=[t for t in requested if t not in available],
                coverage='COMPLETE' if len(available) == len(requested) else 'PARTIAL' if available else 'EMPTY',
                matches=len(used), cross_role_matches=len(records),
                cross_role_available_tiers=[t for t in requested if t in cross_available],
                cross_role_missing_tiers=[t for t in requested if t not in cross_available],
                cross_role_status='AVAILABLE' if records else 'NO_RETAINED_ROSTER_RESULTS',
                source_digests=sorted({s['dataset_digest'] for s in sources if s['patch'] == patch and s['tier'] in requested}),
                tier_meaning=TIER_MEANING, a_rank_at_match='UNKNOWN'))
            for (champion, role), (n, wins) in sorted(base.items()):
                summaries.append(dict(patch=patch, tier=tier, champion=champion, position=role,
                    **_stats(n, wins, ranking_min_n)))
            # Same-role encounter rows can use legacy results; cross-role ranked
            # rows are separately marked, and come exclusively from rosters.
            for (champion, role, enemy), (n, wins) in sorted(same.items()):
                matchups.append(dict(patch=patch, tier=tier, champion=champion, position=role,
                    enemy_position=role, enemy_champion=enemy, basis='SAME_ROLE_ENCOUNTERS',
                    **_stats(n, wins, ranking_min_n)))
            for (champion, role, enemy_role, enemy), (n, wins) in sorted(cross.items()):
                matchups.append(dict(patch=patch, tier=tier, champion=champion, position=role,
                    enemy_position=enemy_role, enemy_champion=enemy, basis='ENEMY_TEAM_ROSTER',
                    **_stats(n, wins, ranking_min_n)))
    result = dict(format=FORMAT, default_tier='MASTER_PLUS', default_patch=patches[-1] if patches else None,
        patches=patches, tiers=list(SCOPES), sample_kind=sample_kind, ranking_min_n=ranking_min_n,
        ranking_policy='MIN_N_20_PUBLICATION_RULE_NOT_VALIDATED_TACTICAL_THRESHOLD' if ranking_min_n == 20 else 'EXPLICIT_TEST_OR_PUBLICATION_MINIMUM',
        ranking_ties='RATE_THEN_N_DESC_THEN_CANONICAL_CHAMPION_ASC',
        ranking_overlap='INDEPENDENT_TOP5_BOTTOM5_OVERLAP_DISCLOSED_WHEN_FEW_ELIGIBLE',
        denominator_basis='UNIQUE_MATCH_UNION_PER_CHAMPION_OWN_ROLE_AND_ENEMY_ROLE_CHAMPION',
        limitations=list(LIMITATIONS), sources=sources, scopes=scopes, summaries=summaries,
        matchups=matchups, omissions=deepcopy(results['omissions']))
    return validate_champion_insights(result, allow_synthetic=allow_synthetic)


def _validate_champion_insights(index, *, allow_synthetic=False):
    """Strict aggregate allowlist at the public serialization/import boundary."""
    from .outcome_stats import _hash
    import math
    expected = {'format', 'default_tier', 'default_patch', 'patches', 'tiers', 'sample_kind',
        'ranking_min_n', 'ranking_policy', 'ranking_ties', 'ranking_overlap', 'denominator_basis',
        'limitations', 'sources', 'scopes', 'summaries', 'matchups', 'omissions'}
    def require(ok):
        if not ok:
            raise ValueError('invalid public champion insights')
    require(isinstance(index, dict) and set(index) == expected)
    require(index['format'] == FORMAT and index['default_tier'] == 'MASTER_PLUS' and index['tiers'] == list(SCOPES))
    require(index['sample_kind'] == 'REAL' or allow_synthetic and index['sample_kind'] == 'SYNTHETIC')
    require(_integer(index['ranking_min_n'], 1) and index['limitations'] == LIMITATIONS)
    require(isinstance(index['patches'], list) and len(set(index['patches'])) == len(index['patches']))
    import re
    require(all(isinstance(p, str) and re.fullmatch(r'[0-9]+\.[0-9]+', p) for p in index['patches']))
    require(index['default_patch'] in index['patches'] or index['default_patch'] is None and not index['patches'])
    require(index['ranking_policy'] in ('MIN_N_20_PUBLICATION_RULE_NOT_VALIDATED_TACTICAL_THRESHOLD', 'EXPLICIT_TEST_OR_PUBLICATION_MINIMUM'))
    require(index['ranking_ties'] == 'RATE_THEN_N_DESC_THEN_CANONICAL_CHAMPION_ASC')
    require(index['ranking_overlap'] == 'INDEPENDENT_TOP5_BOTTOM5_OVERLAP_DISCLOSED_WHEN_FEW_ELIGIBLE')
    require(index['denominator_basis'] == 'UNIQUE_MATCH_UNION_PER_CHAMPION_OWN_ROLE_AND_ENEMY_ROLE_CHAMPION')
    require(isinstance(index['sources'], list))
    for s in index['sources']:
        require(isinstance(s, dict) and set(s) == {'kind', 'dataset_digest', 'patch', 'tier', 'sample_kind', 'matches', 'window_start', 'window_end', 'retrieved_at', 'division'})
        require(s['kind'] in ('LEGACY_SAME_ROLE_OUTCOMES', 'ANONYMOUS_RESULT_COMPANION') and _hash(s['dataset_digest']))
        require(s['patch'] in index['patches'] or s['patch'] is None)
        require(s['tier'] in TIERS and s['sample_kind'] == index['sample_kind'] and _integer(s['matches']))
        require(s['division'] is None or s['division'] in ('I', 'II', 'III', 'IV'))
        require(all(s[k] is None or _integer(s[k]) for k in ('window_start', 'window_end')))
        if s['retrieved_at'] is not None:
            from datetime import datetime
            require(isinstance(s['retrieved_at'], str) and len(s['retrieved_at']) <= 64)
            try:
                require(datetime.fromisoformat(s['retrieved_at'].replace('Z', '+00:00')).tzinfo is not None)
            except (TypeError, ValueError):
                raise ValueError('invalid public champion insights') from None
    require(isinstance(index['scopes'], list))
    keys = set()
    for s in index['scopes']:
        require(isinstance(s, dict) and set(s) == {'patch', 'tier', 'requested_tiers', 'available_tiers', 'missing_tiers', 'coverage', 'matches', 'cross_role_matches', 'cross_role_available_tiers', 'cross_role_missing_tiers', 'cross_role_status', 'source_digests', 'tier_meaning', 'a_rank_at_match'})
        require(s['patch'] in index['patches'] and s['tier'] in SCOPES and (s['patch'], s['tier']) not in keys)
        keys.add((s['patch'], s['tier']))
        require(s['requested_tiers'] == tier_members(s['tier']))
        for prefix in ('', 'cross_role_'):
            available, missing = s[prefix + 'available_tiers'], s[prefix + 'missing_tiers']
            require(isinstance(available, list) and isinstance(missing, list))
            require(available == [t for t in s['requested_tiers'] if t in available])
            require(missing == [t for t in s['requested_tiers'] if t not in available])
        require(s['coverage'] == ('COMPLETE' if not s['missing_tiers'] else 'PARTIAL' if s['available_tiers'] else 'EMPTY'))
        require(_integer(s['matches']) and _integer(s['cross_role_matches']) and s['cross_role_matches'] <= s['matches'])
        require(s['cross_role_status'] == ('AVAILABLE' if s['cross_role_matches'] else 'NO_RETAINED_ROSTER_RESULTS'))
        require(isinstance(s['source_digests'], list) and all(_hash(h) for h in s['source_digests']))
        require(s['tier_meaning'] == TIER_MEANING and s['a_rank_at_match'] == 'UNKNOWN')
    require(keys == {(p, t) for p in index['patches'] for t in SCOPES})
    for table in ('summaries', 'matchups'):
        require(isinstance(index[table], list))
        seen = set()
        for row in index[table]:
            fields = {'patch', 'tier', 'champion', 'position', 'n', 'wins', 'win_rate', 'ci95', 'status'}
            if table == 'matchups':
                fields |= {'enemy_position', 'enemy_champion', 'basis'}
            require(isinstance(row, dict) and set(row) == fields)
            require((row['patch'], row['tier']) in keys and _champion(row['champion']) and row['position'] in POSITIONS)
            if table == 'matchups':
                require(row['enemy_position'] in POSITIONS and _champion(row['enemy_champion']) and row['basis'] in ('SAME_ROLE_ENCOUNTERS', 'ENEMY_TEAM_ROSTER'))
                require(row['basis'] != 'SAME_ROLE_ENCOUNTERS' or row['position'] == row['enemy_position'])
            key = tuple(row[k] for k in ('patch', 'tier', 'champion', 'position') + (('enemy_position', 'enemy_champion', 'basis') if table == 'matchups' else ()))
            require(key not in seen)
            seen.add(key)
            require(_integer(row['n'], 1) and _integer(row['wins']) and row['wins'] <= row['n'])
            require(type(row['win_rate']) in (float, int) and math.isfinite(row['win_rate']))
            require(abs(row['win_rate'] - row['wins'] / row['n']) < 1e-12)
            ci = _wilson(row['wins'], row['n'])
            require(isinstance(row['ci95'], dict) and set(row['ci95']) == {'low', 'high'})
            require(all(type(row['ci95'][k]) in (int, float) and math.isfinite(row['ci95'][k]) and abs(row['ci95'][k] - ci[k]) < 1e-12 for k in ci))
            require(row['status'] == ('READY' if row['n'] >= index['ranking_min_n'] else 'INSUFFICIENT_DATA'))
    require(isinstance(index['omissions'], dict) and set(index['omissions']) <= {'INELIGIBLE_MATCH', 'TIMELINE_METADATA_MISMATCH'})
    require(all(_integer(n) for n in index['omissions'].values()))
    return deepcopy(index)


def validate_champion_insights(index, *, allow_synthetic=False):
    try:
        return _validate_champion_insights(index, allow_synthetic=allow_synthetic)
    except (KeyError, TypeError, AttributeError, OverflowError):
        raise ValueError('invalid public champion insights') from None


def select_insights(index, champion, position, tier='MASTER_PLUS', patch=None):
    """Select exact query scope, with no tier, role, or patch fallback."""
    tier_members(tier)
    if not _champion(champion) or position not in POSITIONS:
        raise ValueError('invalid champion insight selection')
    patch = index['default_patch'] if patch is None else patch
    requested = tier_members(tier)
    scope = next((deepcopy(s) for s in index['scopes'] if s['tier'] == tier and s['patch'] == patch), None)
    if scope is None:
        scope = dict(patch=patch, tier=tier, requested_tiers=requested, available_tiers=[], missing_tiers=requested,
            coverage='EMPTY', matches=0, cross_role_matches=0, cross_role_available_tiers=[],
            cross_role_missing_tiers=requested, cross_role_status='NO_RETAINED_ROSTER_RESULTS',
            source_digests=[], tier_meaning=TIER_MEANING, a_rank_at_match='UNKNOWN')
    def matching(row):
        return (row['champion'], row['position'], row['tier'], row['patch']) == (champion, position, tier, patch)
    summary = next((deepcopy(r) for r in index['summaries'] if matching(r)), _stats(0, 0, index['ranking_min_n']))
    frequent = sorted((deepcopy(r) for r in index['matchups'] if matching(r) and r['basis'] == 'SAME_ROLE_ENCOUNTERS'), key=lambda r: (-r['n'], r['enemy_champion']))
    by_enemy = {}
    for role in POSITIONS:
        basis = 'SAME_ROLE_ENCOUNTERS' if role == position else 'ENEMY_TEAM_ROSTER'
        rows = [deepcopy(r) for r in index['matchups'] if matching(r) and r['basis'] == basis and r['enemy_position'] == role and r['n'] >= index['ranking_min_n']]
        best = sorted(rows, key=lambda r: (-r['win_rate'], -r['n'], r['enemy_champion']))[:5]
        best_champions = {r['enemy_champion'] for r in best}
        worst = sorted(rows, key=lambda r: (r['win_rate'], -r['n'], r['enemy_champion']))[:5]
        by_enemy[role] = dict(best=best, worst=worst, eligible_count=len(rows),
            status='AVAILABLE' if rows else 'NO_ELIGIBLE_ROWS', overlap_policy=index['ranking_overlap'],
            overlap_count=len(best_champions & {r['enemy_champion'] for r in worst}),
            all_tied=bool(rows) and len({r['win_rate'] for r in rows}) == 1,
            rate_ties=len({r['win_rate'] for r in rows}) < len(rows))
    return dict(status=summary['status'], scope=scope, summary=summary, frequent_opponents=frequent,
        by_enemy_position=by_enemy, ranking_min_n=index['ranking_min_n'], limitations=deepcopy(index['limitations']))
