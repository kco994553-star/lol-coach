"""Offline, anonymous resource diagnostics from the existing encrypted PRO cache.

Exact timestamps and observed floor-minute samples are separate measurements.
Only aggregate values leave this module; private identifiers remain in memory.
Point samples provide no interval coverage, player-known view or tactical verdict.
"""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess

from .postgame_match import PostgameStore

SOURCE_FILES = ['coach_v1/resource_recovery.py', 'coach_v1/postgame_match.py',
                'coach_v1/pro_checkpoint.py', 'coach_v1/private_pro_bundle.py',
                'scripts/recover_pro_cache.py', 'scripts/recover_resource_checkpoint.py', 'scripts/private_pro_bundle.py',
                '.github/workflows/resource-recovery-offline.yml', 'contracts/actual-evidence-v1.md']
MAX_ENTRIES = 2000
MAX_REPORT_BYTES = 16_000_000
ROLES = ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT', 'UNKNOWN')
ROLE_MAP = {**{x:x for x in ROLES[:-1]}, 'MIDDLE':'MID', 'UTILITY':'SUPPORT'}
CHAMPIONS = frozenset('''Aatrox Ahri Akali Akshan Alistar Ambessa Amumu Anivia Annie Aphelios Ashe AurelionSol Aurora Azir Bard Belveth Blitzcrank Brand Braum Briar Caitlyn Camille Cassiopeia Chogath Corki Darius Diana DrMundo Draven Ekko Elise Evelynn Ezreal Fiddlesticks Fiora Fizz Galio Gangplank Garen Gnar Gragas Graves Gwen Hecarim Heimerdinger Hwei Illaoi Irelia Ivern Janna JarvanIV Jax Jayce Jhin Jinx KSante Kaisa Kalista Karma Karthus Kassadin Katarina Kayle Kayn Kennen Khazix Kindred Kled KogMaw Leblanc LeeSin Leona Lillia Lissandra Locke Lucian Lulu Lux Malphite Malzahar Maokai MasterYi Mel Milio MissFortune MonkeyKing Mordekaiser Morgana Naafiri Nami Nasus Nautilus Neeko Nidalee Nilah Nocturne Nunu Olaf Orianna Ornn Pantheon Poppy Pyke Qiyana Quinn Rakan Rammus RekSai Rell Renata Renekton Rengar Riven Rumble Ryze Samira Sejuani Senna Seraphine Sett Shaco Shen Shyvana Singed Sion Sivir Skarner Smolder Sona Soraka Swain Sylas Syndra TahmKench Taliyah Talon Taric Teemo Thresh Tristana Trundle Tryndamere TwistedFate Twitch Udyr Urgot Varus Vayne Veigar Velkoz Vex Vi Viego Viktor Vladimir Volibear Warwick Xayah Xerath XinZhao Yasuo Yone Yorick Yunara Yuumi Zaahen Zac Zed Zeri Ziggs Zilean Zoe Zyra'''.split())
MODES = ('EXACT_TIMESTAMP', 'OBSERVED_MINUTE_BIN')
MINUTES = (10, 15)
FIELDS = {'gold':'totalGold', 'xp':'xp', 'level':'level'}
REASONS = ('TARGET_AFTER_REPORTED_END', 'EXACT_TIMESTAMP_ABSENT', 'MINUTE_BIN_ABSENT',
           'OPPONENT_UNAVAILABLE', 'OWN_FIELD_MISSING', 'OPPONENT_FIELD_MISSING',
           'OWN_FIELD_INVALID', 'OPPONENT_FIELD_INVALID')
STAT_VALUES = ('mean', 'minimum', 'q1', 'median', 'q3', 'maximum')
POLICY = dict(selection='LATEST_RECEIVED_ELIGIBLE_FRAME_PER_ELAPSED_MINUTE_FLOOR_BIN',
              exact='ORIGINAL_TIMESTAMP_EQUALS_TARGET_MS', bin_width_ms=60000,
              minutes=[10,15], paired='OWN_MINUS_UNAMBIGUOUS_OPPOSITE_ROLE_SAME_FRAME',
              eligibility='ORIGINAL_TIMESTAMP_NOT_AFTER_REPORTED_GAME_END',
              final_received_frame_allowed_if_not_after_reported_end=True,
              no_interpolation=True, no_bin_borrowing=True,
              cadence='DIAGNOSTIC_ONLY_POINT_SAMPLES_DO_NOT_ESTABLISH_WINDOW_COVERAGE',
              diagnostic_max_internal_gap_ms=65000,
              quantiles='LINEAR_INTERPOLATION_OF_SORTED_OBSERVED_VALUES',
              aggregation='SELECTED_PARTICIPANT_OBSERVATION_MEANS_WITH_DISTINCT_MATCH_COUNTS')
LIMITATIONS = ['RECORDED_PRO_REFERENCE_NOT_ALL_PARTICIPANTS_OR_VERIFIED_PRO_STATUS',
               'OBSERVED_MINUTE_BIN_IS_NOT_EXACT_10_OR_15_MINUTE_STATE',
               'TIMESTAMP_SUMMARIES_ARE_MARGINALS_NOT_INDIVIDUAL_TIMELINES',
               'NO_INTERPOLATION_ZERO_IMPUTATION_OR_ADJACENT_BIN_SUBSTITUTION',
               'FINAL_RECEIVED_POINT_POLICY_DIFFERS_FROM_RECALL_WINDOW_COVERAGE',
               'PARTICIPANTS_WITHIN_MATCH_NOT_INDEPENDENT',
               'XP_TOTAL_NOT_CHAMPION_LEVEL_UP_EVENT',
               'NO_PLAYER_KNOWN_VIEW_WAVE_INTENT_COOLDOWN_OR_SCENE_RECONSTRUCTION',
               'DESCRIPTIVE_NOT_TACTICAL_VALIDATION_OR_COACHING_ACCURACY']
EVALUATION = dict(evaluable_scenes=0, accuracy=None, approval='NOT_ASSESSED')


def _require(ok, message='INVALID_RESOURCE_RECOVERY_REPORT'):
    if not ok:
        raise ValueError(message)


def _integer(value, low=0, high=1_000_000_000_000):
    return type(value) is int and low <= value <= high


def _number(value):
    return type(value) in (int,float) and math.isfinite(value) and abs(value) <= 1_000_000_000_000


def _keys(value, names):
    _require(type(value) is dict and set(value) == set(names))


def _quantile(values, proportion):
    index = (len(values)-1)*proportion
    low, high = math.floor(index), math.ceil(index)
    return values[low]+(values[high]-values[low])*(index-low)


def _stat(items):
    """Items are (value, private match cluster, missing reason); never exported."""
    valid = sorted(v for v, _, _ in items if v is not None)
    result = dict(n_valid=len(valid), missing_n=len(items)-len(valid),
                  match_n=len({c for v,c,_ in items if v is not None}),
                  missing_reasons={reason:sum(v is None and why == reason for v,_,why in items) for reason in REASONS})
    result.update({key:None for key in STAT_VALUES})
    if valid:
        result.update(mean=statistics.mean(valid), minimum=valid[0], q1=_quantile(valid,.25),
                      median=_quantile(valid,.5), q3=_quantile(valid,.75), maximum=valid[-1])
    return result


def _valid_field(value, metric):
    return _integer(value, 1, 18) if metric == 'level' else _integer(value)


def _coverage(entries):
    entries = list(entries)
    result = dict(frames=len(entries))
    for metric, field in FIELDS.items():
        valid = sum(_valid_field(e.get(field),metric) for e in entries)
        result[metric] = dict(n_valid=valid, missing_n=len(entries)-valid)
    valid = sum(type(e.get('position')) is dict and
                all(_number(e['position'].get(k)) and 0 <= e['position'][k] <= 16000 for k in ('x','y'))
                for e in entries)
    result['position'] = dict(n_valid=valid, missing_n=len(entries)-valid)
    return result


def _value(entry, metric, side):
    field = FIELDS[metric]
    if field not in entry:
        return None, side+'_FIELD_MISSING'
    return (entry[field], None) if _valid_field(entry[field],metric) else (None,side+'_FIELD_INVALID')


def _sample(body, own, other, mode, minute):
    frames = body['timeline']['info']['frames']; target = minute*60000
    end = body['match']['info']['gameDuration']*1000
    eligible = [f for f in frames if f['timestamp'] <= end]
    in_bin = [f for f in eligible if f['timestamp']//60000 == minute]
    chosen = next((f for f in eligible if f['timestamp'] == target), None) if mode == 'EXACT_TIMESTAMP' else (in_bin[-1] if in_bin else None)
    reason = ('TARGET_AFTER_REPORTED_END' if target > end else
              'EXACT_TIMESTAMP_ABSENT' if mode == 'EXACT_TIMESTAMP' else 'MINUTE_BIN_ABSENT') if chosen is None else None
    result = dict(timestamp_ms=chosen['timestamp'] if chosen else None,
                  offset_ms=chosen['timestamp']-target if chosen else None,
                  frames_in_bin=len(in_bin) if chosen else None,
                  final=chosen is frames[-1], reason=reason, metrics={})
    for metric in FIELDS:
        if chosen is None:
            a = b = diff = None; ar = br = dr = reason
        else:
            pf = chosen['participantFrames']
            a, ar = _value(pf.get(str(own['participantId']),{}),metric,'OWN')
            b, br = _value(pf.get(str(other['participantId']),{}),metric,'OPPONENT') if other else (None,'OPPONENT_UNAVAILABLE')
            diff = a-b if a is not None and b is not None else None
            dr = ar or br
        result['metrics'][metric] = dict(own=(a,ar), opponent=(b,br), difference=(diff,dr))
    return result


def _measurements(rows):
    output = []
    for mode in MODES:
        for minute in MINUTES:
            samples = [(r['samples'][(mode,minute)],r['cluster']) for r in rows]
            point = dict(mode=mode, minute=minute, target_timestamp_ms=minute*60000,
                         bin_start_ms=minute*60000, bin_end_exclusive_ms=(minute+1)*60000,
                         participant_observations=len(rows), matches=len({r['cluster'] for r in rows}),
                         selected_final_received_n=sum(s['final'] for s,_ in samples), metrics={})
            for key in ('timestamp_ms','offset_ms','frames_in_bin'):
                point[key] = _stat([(s[key],c,s['reason']) for s,c in samples])
            for metric in FIELDS:
                point['metrics'][metric] = {side:_stat([(s['metrics'][metric][side][0],c,s['metrics'][metric][side][1])
                                                       for s,c in samples]) for side in ('own','opponent','difference')}
            output.append(point)
    return output


def _group(rows, **identity):
    return dict(identity, matches=len({r['cluster'] for r in rows}), participant_observations=len(rows),
                opponent_missing_n=sum(r['opponent_champion'] is None for r in rows), measurements=_measurements(rows))


def audit_private_cache(private_directory):
    """Inspect one restored cache, returning only a strict anonymous aggregate report."""
    root = Path(private_directory).absolute(); directory = root/'private'/'matches'
    _require('..' not in root.parts and not any(p.is_symlink() for p in (directory,*directory.parents)))
    _require(directory.is_dir(), 'PRIVATE_RESOURCE_CACHE_REQUIRED')
    paths = sorted(directory.glob('*.json')); _require(0 < len(paths) <= MAX_ENTRIES)
    store = PostgameStore(directory)
    rows = []; seen = set(); duplicates = 0; originals = {}; all_entries = []; selected_entries = []
    first = []; last = []; gaps = []; intervals_declared = []; after_end = gap_n = checked = mismatches = 0
    received_frames = first_nonzero = 0
    for path in paths:
        body, own, cluster = store._load(path.stem)
        _require(body['source'] == 'REAL')
        # Compare complete originals before dedup: different selected envelopes must agree.
        original = json.dumps([body['match'],body['timeline']], sort_keys=True,allow_nan=False,separators=(',',':'))
        fingerprint = hashlib.sha256(original.encode()).digest()
        if cluster in originals:
            _require(originals[cluster] == fingerprint, 'CONFLICTING_PRIVATE_MATCH_ORIGINALS')
        else:
            originals[cluster] = fingerprint
            frames = body['timeline']['info']['frames']; end = body['match']['info']['gameDuration']*1000
            received_frames += len(frames); first_nonzero += frames[0]['timestamp'] != 0
            declared = body['timeline']['info']['frameInterval']
            _require(type(declared) is int and declared == 60000, 'INVALID_ORIGINAL_FRAME_INTERVAL')
            intervals_declared.append((declared,cluster,None))
            all_entries.extend(p for f in frames for p in f['participantFrames'].values())
            first.append((frames[0]['timestamp'],cluster,None)); last.append((frames[-1]['timestamp'],cluster,None))
            intervals = [b['timestamp']-a['timestamp'] for a,b in zip(frames,frames[1:])]
            gaps.extend((t,cluster,None) for t in intervals)
            gap_n += sum(t > 65000 for t in intervals)
            after_end += sum(f['timestamp'] > end for f in frames)
        identity = (cluster,body['participant_id'])
        if identity in seen:
            duplicates += 1; continue
        seen.add(identity)
        frames = body['timeline']['info']['frames']
        selected_entries.extend(f['participantFrames'].get(str(body['participant_id']),{}) for f in frames)
        people = body['match']['info']['participants']; role = ROLE_MAP.get(own.get('teamPosition'),'UNKNOWN')
        if role != 'UNKNOWN' and sum(p['teamId'] == own['teamId'] and ROLE_MAP.get(p.get('teamPosition')) == role for p in people) != 1:
            role = 'UNKNOWN'
        opponents = [p for p in people if p['teamId'] != own['teamId'] and ROLE_MAP.get(p.get('teamPosition')) == role]
        other = opponents[0] if role != 'UNKNOWN' and len(opponents) == 1 else None
        _require(own['championName'] in CHAMPIONS and (other is None or other['championName'] in CHAMPIONS))
        row = dict(cluster=cluster, patch='.'.join(body['match']['info']['gameVersion'].split('.')[:2]),
                   champion=own['championName'], position=role,
                   opponent_champion=other['championName'] if other else None,
                   samples={(mode,minute):_sample(body,own,other,mode,minute) for mode in MODES for minute in MINUTES})
        rows.append(row)
        # Compare the existing real transformation against source values; no raw output.
        detail = store.get_match(path.stem)
        bins = {f['timestamp']//60000:f for f in frames if f['timestamp'] <= body['match']['info']['gameDuration']*1000}
        transformed = {p['minute']:p for p in detail['resources']}
        _require(set(bins) == set(transformed), 'RESOURCE_TRANSFORM_BIN_MISMATCH')
        for minute,frame in bins.items():
            pf = frame['participantFrames'].get(str(body['participant_id']),{})
            for metric,field in FIELDS.items():
                checked += 1
                mismatches += transformed[minute].get(metric) != pf.get(field) or transformed[minute].get('timestamp_ms') != frame['timestamp']
    cohorts = defaultdict(list); patches = defaultdict(list)
    for row in rows:
        cohorts[tuple(row[k] for k in ('patch','champion','position','opponent_champion'))].append(row)
        patches[row['patch']].append(row)
    report = dict(schema_version='resource-recovery.v1', population='RECORDED_PRO_REFERENCE',
                  source=dict(kind='REAL', cache_entries=len(paths), matches=len(originals),
                              participant_observations=len(rows), duplicate_participant_entries=duplicates),
                  measurement_policy=deepcopy(POLICY), limitations=list(LIMITATIONS), evaluation=deepcopy(EVALUATION),
                  inspection=dict(all_participant_frames=_coverage(all_entries),selected_participant_frames=_coverage(selected_entries),
                      timestamps=dict(first_received_ms=_stat(first),last_received_ms=_stat(last),received_gap_ms=_stat(gaps),
                                      declared_interval_ms=_stat(intervals_declared),received_frames=received_frames,first_received_nonzero_n=first_nonzero,
                                      internal_gap_over_65000_n=gap_n,frames_after_reported_end_n=after_end),
                      transform_comparison=dict(checked_n=checked,mismatch_n=mismatches)),
                  measurements=_measurements(rows),
                  patches=[_group(rs,patch=p) for p,rs in sorted(patches.items())],
                  cohorts=[_group(rs,**dict(zip(('patch','champion','position','opponent_champion'),key)))
                           for key,rs in sorted(cohorts.items(),key=lambda p:tuple(v or '' for v in p[0]))])
    return validate_report(report)


def _validate_stat(value, total, matches):
    _keys(value, ('n_valid','missing_n','match_n','missing_reasons',*STAT_VALUES))
    _require(all(_integer(value[k]) for k in ('n_valid','missing_n','match_n')))
    _require(value['n_valid']+value['missing_n'] == total and value['match_n'] <= min(matches,value['n_valid']))
    _keys(value['missing_reasons'], REASONS)
    _require(all(_integer(v) for v in value['missing_reasons'].values()) and sum(value['missing_reasons'].values()) == value['missing_n'])
    data = [value[k] for k in ('minimum','q1','median','q3','maximum')]
    if value['n_valid']:
        _require(value['match_n'] >= 1 and all(_number(v) for v in data) and data == sorted(data))
        _require(_number(value['mean']) and data[0] <= value['mean'] <= data[-1])
    else:
        _require(value['match_n'] == 0 and all(value[k] is None for k in STAT_VALUES))


def _validate_measurements(values, total, matches):
    _require(type(values) is list and len(values) == 4)
    for point,(mode,minute) in zip(values, ((a,b) for a in MODES for b in MINUTES)):
        _keys(point,('mode','minute','target_timestamp_ms','bin_start_ms','bin_end_exclusive_ms',
                     'participant_observations','matches','selected_final_received_n','metrics','timestamp_ms','offset_ms','frames_in_bin'))
        _require(point['mode'] == mode and type(point['minute']) is int and point['minute'] == minute)
        for key,expected in (('target_timestamp_ms',minute*60000),('bin_start_ms',minute*60000),('bin_end_exclusive_ms',(minute+1)*60000),
                             ('participant_observations',total),('matches',matches)):
            _require(type(point[key]) is int and point[key] == expected)
        for key in ('timestamp_ms','offset_ms','frames_in_bin'):
            _validate_stat(point[key],total,matches)
        times,offsets,bins = (point[k] for k in ('timestamp_ms','offset_ms','frames_in_bin'))
        _require(times['n_valid'] == offsets['n_valid'] == bins['n_valid'])
        _require(_integer(point['selected_final_received_n'],0,times['n_valid']))
        if times['n_valid']:
            for key in STAT_VALUES:
                _require(abs(times[key]-(offsets[key]+minute*60000)) < 1e-6)
            _require(offsets['minimum'] >= 0 and offsets['maximum'] < 60000 and bins['minimum'] >= 1)
            if mode == 'EXACT_TIMESTAMP': _require(offsets['maximum'] == 0)
        _keys(point['metrics'],FIELDS)
        for metric, sides in point['metrics'].items():
            _keys(sides,('own','opponent','difference'))
            for stat in sides.values(): _validate_stat(stat,total,matches)
            _require(sides['difference']['n_valid'] <= min(sides['own']['n_valid'],sides['opponent']['n_valid']))
            for side in ('own','opponent'):
                s = sides[side]
                _require(s['n_valid'] <= times['n_valid'])
                if s['n_valid']:
                    _require(s['minimum'] >= (1 if metric == 'level' else 0))
                    if metric == 'level': _require(s['maximum'] <= 18)


def validate_report(report):
    """Fail closed on unknown fields, identities, invalid counts or nonfinite values."""
    try:
        _keys(report,('schema_version','population','source','measurement_policy','limitations','evaluation','inspection','measurements','patches','cohorts'))
        _require(report['schema_version'] == 'resource-recovery.v1' and report['population'] == 'RECORDED_PRO_REFERENCE')
        # Serialized equality also rejects bool-vs-int substitutions in constant policies.
        _require(json.dumps(report['measurement_policy'],sort_keys=True,allow_nan=False) == json.dumps(POLICY,sort_keys=True))
        _require(report['limitations'] == LIMITATIONS and report['evaluation'] == EVALUATION and type(report['evaluation']['evaluable_scenes']) is int)
        source = report['source']; _keys(source,('kind','cache_entries','matches','participant_observations','duplicate_participant_entries'))
        _require(source['kind'] == 'REAL' and all(_integer(v,0,MAX_ENTRIES) for k,v in source.items() if k != 'kind'))
        total,matches = source['participant_observations'],source['matches']
        _require(1 <= matches <= total <= 10*matches and source['cache_entries'] == total+source['duplicate_participant_entries'])
        inspection = report['inspection']; _keys(inspection,('all_participant_frames','selected_participant_frames','timestamps','transform_comparison'))
        for key in ('all_participant_frames','selected_participant_frames'):
            coverage = inspection[key]; _keys(coverage,('frames',*FIELDS,'position'))
            _require(_integer(coverage['frames'],0,245*MAX_ENTRIES*10))
            for field in (*FIELDS,'position'):
                _keys(coverage[field],('n_valid','missing_n'))
                _require(all(_integer(v) for v in coverage[field].values()) and sum(coverage[field].values()) == coverage['frames'])
        _require(inspection['selected_participant_frames']['frames'] <= 245*total)
        stamps = inspection['timestamps']; _keys(stamps,('first_received_ms','last_received_ms','received_gap_ms','declared_interval_ms','received_frames','first_received_nonzero_n','internal_gap_over_65000_n','frames_after_reported_end_n'))
        for key in ('first_received_ms','last_received_ms','declared_interval_ms'):
            _validate_stat(stamps[key],matches,matches)
            _require(stamps[key]['n_valid'] == matches and stamps[key]['minimum'] >= 0)
        _require(stamps['declared_interval_ms']['minimum'] == stamps['declared_interval_ms']['maximum'] == 60000)
        _require(_integer(stamps['received_frames'],matches,245*matches) and _integer(stamps['first_received_nonzero_n'],0,matches))
        _require(inspection['all_participant_frames']['frames'] <= 10*stamps['received_frames'])
        gap_count = stamps['received_gap_ms']['n_valid']+stamps['received_gap_ms']['missing_n']
        _validate_stat(stamps['received_gap_ms'],gap_count,matches)
        _require(stamps['received_gap_ms']['missing_n'] == 0 and gap_count == stamps['received_frames']-matches)
        if gap_count: _require(stamps['received_gap_ms']['minimum'] > 0)
        _require(_integer(stamps['internal_gap_over_65000_n'],0,gap_count))
        _require(_integer(stamps['frames_after_reported_end_n'],0,245*matches))
        comparison = inspection['transform_comparison']; _keys(comparison,('checked_n','mismatch_n'))
        _require(_integer(comparison['checked_n'],0,245*total*3) and _integer(comparison['mismatch_n'],0,comparison['checked_n']))
        _validate_measurements(report['measurements'],total,matches)
        for group_key in ('patches','cohorts'):
            _require(type(report[group_key]) is list and 1 <= len(report[group_key]) <= total)
            seen = set(); n = 0; patch_counts = defaultdict(int)
            for group in report[group_key]:
                identity = ('patch',) if group_key == 'patches' else ('patch','champion','position','opponent_champion')
                _keys(group,(*identity,'matches','participant_observations','opponent_missing_n','measurements'))
                _require(type(group['patch']) is str and re.fullmatch(r'[0-9]{1,3}\.[0-9]{1,3}',group['patch']))
                key = tuple(group[k] for k in identity); _require(key not in seen); seen.add(key)
                if group_key == 'cohorts':
                    _require(group['champion'] in CHAMPIONS and group['position'] in ROLES and (group['opponent_champion'] is None or group['opponent_champion'] in CHAMPIONS))
                count,m = group['participant_observations'],group['matches']
                _require(_integer(count,1,total) and _integer(m,1,min(matches,count)) and count <= 10*m)
                _require(_integer(group['opponent_missing_n'],0,count))
                if group_key == 'cohorts': _require(group['opponent_missing_n'] == (count if group['opponent_champion'] is None else 0))
                _validate_measurements(group['measurements'],count,m)
                n += count; patch_counts[group['patch']] += count
            _require(n == total)
            if group_key == 'patches':
                expected_patch_counts = dict(patch_counts)
                _require(sum(g['matches'] for g in report['patches']) == matches)
            else: _require(dict(patch_counts) == expected_patch_counts)
        # Every disjoint participant partition must reconcile counts and means.
        for group_key in ('patches','cohorts'):
            for index, point in enumerate(report['measurements']):
                for path in [('timestamp_ms',),('offset_ms',),('frames_in_bin',)]+[
                        ('metrics',metric,side) for metric in FIELDS for side in ('own','opponent','difference')]:
                    def at(value):
                        for part in path: value = value[part]
                        return value
                    total_stat = at(point)
                    parts = [at(group['measurements'][index]) for group in report[group_key]]
                    for key in ('n_valid','missing_n'):
                        _require(total_stat[key] == sum(part[key] for part in parts))
                    for reason in REASONS:
                        _require(total_stat['missing_reasons'][reason] == sum(part['missing_reasons'][reason] for part in parts))
                    if total_stat['n_valid']:
                        mean = sum(part['mean']*part['n_valid'] for part in parts if part['n_valid'])/total_stat['n_valid']
                        _require(math.isclose(total_stat['mean'],mean,rel_tol=1e-12,abs_tol=1e-8))
                _require(point['selected_final_received_n'] == sum(group['measurements'][index]['selected_final_received_n'] for group in report[group_key]))
        _require(len(json.dumps(report,allow_nan=False).encode()) <= MAX_REPORT_BYTES)
        return deepcopy(report)
    except (KeyError,TypeError,ValueError,OverflowError,RecursionError):
        raise ValueError('INVALID_RESOURCE_RECOVERY_REPORT') from None


def load_bound_report(directory):
    """Load resources.json only with pinned actual scope and exact source lineage."""
    try:
        folder = Path(directory).absolute(); root = Path(__file__).resolve().parents[1]
        report_path,binding_path = folder/'resources.json',folder/'source-binding.json'
        _require(not any(p.is_symlink() for p in (report_path,binding_path,folder,*folder.parents)))
        _require(report_path.stat().st_size <= MAX_REPORT_BYTES and binding_path.stat().st_size <= 100_000)
        raw = report_path.read_bytes(); report = validate_report(json.loads(raw)); binding = json.loads(binding_path.read_text())
        _keys(binding,('schema_version','actual_commit','source_sha256','checkpoint','report_sha256','source_samples',
                       'provider_requests','network_attempts','privacy','coaching_accuracy'))
        _require(binding['schema_version'] == 'resource-recovery.binding.v1')
        _require(binding['checkpoint'] == dict(run_id=38410710876,artifact_id=11822391323))
        _require(binding['report_sha256'] == hashlib.sha256(raw).hexdigest() and binding['source_samples'] == report['source'])
        _require(report['source']['matches'] == 89 and report['source']['participant_observations'] == 108)
        _require(all(type(binding[k]) is int and binding[k] == 0 for k in ('provider_requests','network_attempts')))
        _require(binding['privacy'] == 'ANONYMOUS_ALLOWLIST_AGGREGATES_ONLY' and binding['coaching_accuracy'] is None)
        commit = binding['actual_commit']; _require(type(commit) is str and re.fullmatch(r'[a-f0-9]{40}',commit))
        _keys(binding['source_sha256'],SOURCE_FILES)
        subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for name,expected in binding['source_sha256'].items():
            _require(type(expected) is str and re.fullmatch(r'[a-f0-9]{64}',expected))
            archived = subprocess.check_output(['git','show',commit+':'+name],cwd=root,stderr=subprocess.DEVNULL)
            _require(hashlib.sha256(archived).hexdigest() == expected == hashlib.sha256((root/name).read_bytes()).hexdigest())
        return report,deepcopy(binding)
    except (OSError,ValueError,TypeError,KeyError,subprocess.CalledProcessError):
        raise ValueError('INVALID_OR_UNBOUND_RESOURCE_RECOVERY_REPORT') from None
