"""Offline, exact-scope ending-result summaries for the champion browser.

Only validated outcome cohorts carry the member hashes needed for disjoint
trials and exact role counts. Elapsed-minute resource data is never a result
fallback. Public projections contain counts and provenance, never member IDs.
"""
from collections import defaultdict
from datetime import datetime, timezone

from .outcome_stats import _wilson, validate_outcome_dataset
from .power_stats import POSITIONS, validate_power_dataset
from .state import digest

FORMAT = 'lol-coach-champion-statistics-v1'
DRAW_MIN_N = 100
UNSUPPORTED_METRICS = ('pick_rate', 'ban_rate', 'runes', 'item_builds', 'skill_order')
TIER_MEANING = 'CURRENT_LEAGUE_SEED_COHORT_NOT_ALL_PARTICIPANT_RANKS'
GROWTH_MINUTES = (5, 10, 15, 20, 25, 30)
RESOURCE_UNITS = {'gold_delta': 'GOLD_PER_MINUTE', 'xp_delta': 'XP_PER_MINUTE', 'cs_delta': 'CS_PER_MINUTE'}


def _validated(dataset):
    try:
        return validate_outcome_dataset(dataset)
    except (TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError('invalid outcome dataset') from None


def _summary(points):
    n = sum(point['n'] for point in points)
    wins = sum(point['wins'] for point in points)
    ci = _wilson(wins, n) if n else None
    return dict(status='READY' if n >= DRAW_MIN_N else 'INSUFFICIENT_DATA' if n else 'NO_DATA',
                n=n, wins=wins, win_rate_pct=100 * wins / n if n else None,
                ci_low_pct=100 * ci['low'] if ci else None,
                ci_high_pct=100 * ci['high'] if ci else None)


def _points(dataset, champion, position, patch, tier, opponent_champion):
    comparison = 'CHAMPION_ROLE' if opponent_champion is None else 'MATCHUP'
    for cohort in dataset['cohorts']:
        if (cohort['champion'], cohort['position'], cohort['patch'], cohort['tier'],
                cohort['comparison'], cohort['opponent_champion']) == (
                champion, position, patch, tier, comparison, opponent_champion):
            return cohort['points']
    return []


def _duration(points):
    bins = []
    for start in range(0, 61, 5):
        end = start + 5 if start < 60 else None
        selected = [point for point in points if point['minute'] >= start and
                    (end is None or point['minute'] < end)]
        summary = _summary(selected)
        bins.append(dict(start_minute=start, end_minute=end,
                         **{key: value for key, value in summary.items() if key != 'status'},
                         drawable=summary['n'] >= DRAW_MIN_N))
    return bins


def summarize_outcome(dataset, champion, position, patch, tier, opponent_champion=None):
    """Combine one exact cohort's disjoint ending bins; never average rates."""
    return _summary(_points(_validated(dataset), champion, position, patch, tier, opponent_champion))


def duration_outcomes(dataset, champion, position, patch, tier, opponent_champion=None):
    """Return all thirteen disjoint five-minute bins, preserving empty gaps."""
    return _duration(_points(_validated(dataset), champion, position, patch, tier, opponent_champion))


def _source(dataset):
    source = dataset['source']
    def iso(value):
        return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None
    return dict(patch=source['patch'], region=source['platform'], queue_id=source['queue_id'],
                tier=source['tier'], tier_meaning=TIER_MEANING,
                retrieved_at=source['retrieved_at'], period_start=iso(source['window_start']),
                period_end=iso(source['window_end']), dataset_digest=digest(dataset),
                matches=dataset['samples']['real_matches'] + dataset['samples']['synthetic_matches'],
                sample_kind=source['sample_kind'])


def _empty_role():
    return dict(summary=_summary([]), duration=_duration([]), opponents={},
                growth=dict(status='NO_DATA', points=[], markers=[]))


def _growth(cohorts):
    points = []
    markers = {}
    for cohort in cohorts:
        for point in cohort['points']:
            if point['minute'] in GROWTH_MINUTES:
                points.append(dict(metric=cohort['metric'], minute=point['minute'],
                    unit=RESOURCE_UNITS[cohort['metric']],
                    **{key: point[key] for key in ('champion_mean', 'champion_n', 'reference_mean',
                        'reference_n', 'n', 'visible', 'omission_reason')},
                    mean_delta=point['mean'], delta_ci95=dict(point['ci95'])))
        for marker in cohort['markers']:
            key = (marker['kind'], marker['level'], marker['item_id'], marker['item_order'])
            # Markers are repeated unchanged in all resource metrics. Summing
            # their n would triple the same observations. Conflicts fail closed.
            if key in markers and markers[key] != marker:
                raise ValueError('inconsistent duplicated growth marker')
            markers[key] = marker
    projected_markers = []
    for key in sorted(markers, key=lambda key: (key[0] == 'ITEM', key[1] or 0, key[3] or 0, key[2] or 0)):
        marker = markers[key]
        projected_markers.append(dict(marker, observation=(
            'FIRST_OBSERVED_FRAME_INTERVAL_CENSORED' if marker['kind'] == 'LEVEL' else
            'OBSERVED_NONBOOT_NONCONSUMABLE_COMPLETE_ITEM_PURCHASE_CANDIDATE')))
    return dict(status='AVAILABLE' if points or projected_markers else 'NO_DATA',
                points=sorted(points, key=lambda point: (point['minute'], point['metric'])),
                markers=projected_markers)


def build_champion_statistics(outcome, *, position_dataset=None, growth_dataset=None):
    """Build a deterministic allowlisted public projection without changing inputs.

    A separate validated outcome snapshot may provide coverage; its provenance
    remains distinct. Minute-row counts from power datasets are not accepted.
    """
    outcome = _validated(outcome)
    coverage = _validated(position_dataset) if position_dataset is not None else outcome
    for key in ('patch', 'platform', 'regional', 'queue_id', 'map_id', 'tier', 'sample_kind'):
        if coverage['source'][key] != outcome['source'][key]:
            raise ValueError('position snapshot scope mismatch: ' + key)
    growth = validate_power_dataset(growth_dataset) if growth_dataset is not None else None
    if growth is not None:
        for key in ('patch', 'platform', 'regional', 'queue_id', 'map_id', 'tier', 'sample_kind'):
            if growth['source'][key] != outcome['source'][key]:
                raise ValueError('growth snapshot scope mismatch: ' + key)
    observed = defaultdict(lambda: defaultdict(set))
    for cohort in coverage['cohorts']:
        if cohort['comparison'] == 'CHAMPION_ROLE':
            for point in cohort['points']:
                observed[cohort['champion']][cohort['position']].update(point['input_match_hashes'])
    champions = {}
    for champion in sorted(set(observed) | {c['champion'] for c in outcome['cohorts']}):
        champions[champion] = dict(observed_positions=[
            dict(position=position, matches=len(observed[champion][position]))
            for position in POSITIONS if observed[champion][position]], positions={})
    for cohort in sorted(outcome['cohorts'], key=lambda c: (
            c['champion'], POSITIONS.index(c['position']), c['comparison'], c['opponent_champion'] or '')):
        roles = champions[cohort['champion']]['positions']
        role = roles.setdefault(cohort['position'], _empty_role())
        projection = dict(summary=_summary(cohort['points']), duration=_duration(cohort['points']))
        if cohort['comparison'] == 'CHAMPION_ROLE':
            role.update(projection)
        else:
            role['opponents'][cohort['opponent_champion']] = projection
    growth_source = None
    if growth is not None:
        groups = defaultdict(list)
        for cohort in growth['cohorts']:
            if cohort['comparison'] == 'ROLE_POPULATION':
                groups[(cohort['champion'], cohort['position'])].append(cohort)
        for (champion, position), cohorts in sorted(groups.items()):
            row = champions.setdefault(champion, dict(observed_positions=[], positions={}))
            row['positions'].setdefault(position, _empty_role())['growth'] = _growth(cohorts)
        growth_source = dict(_source(growth),
            formula_version=growth['source']['formula_version'],
            population_formula_version=growth['source'].get('population_reference', {}).get('formula_version'),
            comparison='ROLE_POPULATION',
            uncertainty_scope='CHAMPION_MINUS_POOLED_ROLE_RATE_NOT_CHAMPION_MEAN_CI',
            rate_scope='OBSERVED_CUMULATIVE_RESOURCE_DIVIDED_BY_ACTUAL_ELAPSED_MINUTES',
            time_scope='ELAPSED_MINUTE_FLOOR_LATEST_RECEIVED_FRAME',
            marker_scope='FIRST_OBSERVED_LEVEL_OR_ITEM_PURCHASE_NOT_STRENGTH_OR_OPTIMAL_BUILD',
            limitations=list(growth['source']['limitations']))
    return dict(format=FORMAT, source=_source(outcome), growth_source=growth_source,
                position_source=dict(_source(coverage), count_basis='UNIQUE_OUTCOME_MATCH_HASH_UNION'),
                draw_min_n=DRAW_MIN_N, unsupported_metrics=list(UNSUPPORTED_METRICS),
                limitations=['ENDING_DURATION_CONDITIONAL_OUTCOME_NOT_STRENGTH',
                             'CONVENIENCE_SAMPLE_NOT_POPULATION_PICK_OR_BAN_RATES',
                             'NO_BOT_DUO_OR_SUPPORT_PAIR_STATISTICS',
                             'DESCRIPTIVE_NOT_CAUSAL_OR_COACHING_ACCURACY'],
                champions=dict(sorted(champions.items())))
