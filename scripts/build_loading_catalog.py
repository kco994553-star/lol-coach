"""Compile the public loading catalog from preserved evidence; offline by default.

The optional --fetch-sprites flag allows only the six official roster-referenced
PNG sprite sheets. It never refreshes rosters, skills, matches, or videos.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import struct
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PROFILE_FIELDS = ('threats', 'protection', 'strong_when', 'lane_style',
                  'jungle_style', 'initiative', 'needs')
RULE_FILES = ('executable-v1.json', 'executable-expanded-v1.json',
              'initiative-v2.json', 'initiative-expansion-v2.json')
CATALOG_PATH = 'web_r4/loading-data.json'
SCOPE_PATH = 'evidence/actual-evidence/loading/catalog-scope.json'
SCOPE_MD_PATH = 'evidence/actual-evidence/loading/catalog-scope.md'
SPRITE_RECEIPTS = 'web_r4/loading-assets/sprite-receipts.json'


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def located(document, locator):
    for segment in locator.split('.'):
        document = document[int(segment)] if isinstance(document, list) else document[segment]
    return document


def plain_text(raw):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', raw)).split())


def png_dimensions(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR':
        raise ValueError('Expected an unchanged PNG sprite sheet')
    return struct.unpack('>II', raw[16:24])


def fetch_sprites(root=ROOT):
    """One bounded, explicitly requested official-static fetch; no other APIs."""
    receipt_path = root / SPRITE_RECEIPTS
    if receipt_path.exists():
        return 0
    current = json.loads((root / 'data/official_catalog/current.json').read_text())
    patch = current['source_patch']
    if not re.fullmatch(r'\d+\.\d+\.\d+', patch):
        raise ValueError('Invalid official source patch')
    roster = json.loads((root / f'data/official_catalog/versions/{patch}/champion.ko_KR.json').read_text())
    sprites = sorted({row['image']['sprite'] for row in roster['data'].values()})
    if len(sprites) != 6 or any(not re.fullmatch(r'champion[0-5]\.png', name) for name in sprites):
        raise ValueError('Sprite request exceeds the six-sheet loading contract')
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    def fetch(name):
        path = receipt_path.parent / name
        if path.exists():
            raise ValueError(f'Unreceipted sprite already exists: {name}')
        url = f'https://ddragon.leagueoflegends.com/cdn/{patch}/img/sprite/{name}'
        with urllib.request.urlopen(url, timeout=25) as response:
            if response.status != 200 or response.geturl() != url:
                raise ValueError('Unexpected sprite response')
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Sprite exceeds bounded download size')
        width, height = png_dimensions(raw)
        path.write_bytes(raw)
        return {'path': f'loading-assets/{name}', 'url': url, 'version': patch,
                'sha256': sha256(raw), 'bytes': len(raw), 'width': width, 'height': height,
                'http_status': 200, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
                'kind': 'OFFICIAL_DATA_DRAGON_SPRITE_UNMODIFIED'}

    with ThreadPoolExecutor(max_workers=3) as pool:
        receipts = list(pool.map(fetch, sprites))
    receipt_path.write_text(encode({'format': 'loading-sprite-receipts-v1', 'requests': receipts}))
    return len(receipts)


class Compiler:
    def __init__(self, root=ROOT):
        self.root = root
        self.bindings = {}
        self.documents = {}

    def read(self, local_source, kind, url=None, expected=None):
        if local_source not in self.documents:
            raw = (self.root / local_source).read_bytes()
            self.documents[local_source] = json.loads(raw)
            self.bindings[local_source] = {'local_source': local_source, 'sha256': sha256(raw),
                                           'bytes': len(raw), 'kind': kind}
        binding = self.bindings[local_source]
        if expected is not None and binding['sha256'] != expected:
            raise ValueError(f'Source hash mismatch: {local_source}')
        if url:
            binding['url'] = url
        return self.documents[local_source]

    def english_source(self, source, patch):
        url = source['url']
        prefix = f'https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/'
        if url == prefix + 'champion.json':
            path = f'evidence/queue/q05/sources/champion-roster-{patch}.json'
        else:
            match = re.fullmatch(re.escape(prefix) + r'champion/([A-Za-z0-9]+)\.json', url)
            if not match:
                raise ValueError('Unexpected existing candidate source URL')
            name = f'{match.group(1)}-{patch}.json'
            paths = [f'evidence/queue/{queue}/sources/{name}' for queue in ('q05', 'q05-expansion')]
            path = next((p for p in paths if (self.root / p).is_file()), None)
            if path is None:
                raise ValueError(f'Archived candidate source is missing: {name}')
        document = self.read(path, 'ARCHIVED_OFFICIAL_ENGLISH', url, source['sha256'])
        if document['version'] != patch or source['patch'] != patch:
            raise ValueError(f'Candidate source version mismatch: {path}')
        return {**source, 'local_source': path,
                'raw_excerpt': located(document, source['locator'])}

    def profiles(self, patch):
        profiles = {}
        for filename in RULE_FILES:
            path = 'knowledge_candidates/' + filename
            rows = self.read(path, 'EXISTING_EXPLORATORY_RULES')
            for index, rule in enumerate(rows):
                candidate = rule.get('profile')
                if not candidate:
                    continue
                champion = candidate['champion']
                profile = profiles.setdefault(champion, {**{key: [] for key in PROFILE_FIELDS},
                    'review_state': 'EXPLORATORY', 'classification_incomplete': True,
                    'unlisted_labels': 'UNKNOWN', 'rule_refs': [],
                    'necessary_conditions': [], 'limitations': []})
                for key in (*PROFILE_FIELDS, 'necessary_conditions'):
                    for value in candidate.get(key, []):
                        if value not in profile[key]:
                            profile[key].append(value)
                for value in rule.get('limitations', []):
                    if value not in profile['limitations']:
                        profile['limitations'].append(value)
                profile['rule_refs'].append({'id': rule['rule_id'], 'version': rule['version'],
                    'local_source': path, 'sha256': self.bindings[path]['sha256'], 'locator': str(index),
                    'review_state': 'EXPLORATORY',
                    'fields': {key: candidate.get(key, []) for key in PROFILE_FIELDS},
                    'source_refs': [self.english_source(source, patch) for source in rule['sources']],
                    'necessary_conditions': candidate.get('necessary_conditions', []),
                    'limitations': rule.get('limitations', []),
                    'counterexamples': rule.get('counterexamples', [])})
        return profiles

    def recall_references(self, champions):
        champion_aliases = {alias.casefold(): champion for champion, row in champions.items()
                            for alias in row['aliases']}
        validation_path = 'data/recall/2026-10-15/source-binding.json'
        validation = self.read(validation_path, 'EXISTING_ANONYMOUS_DATASET_VALIDATION')
        rows, datasets, excluded = [], [], []
        for directory in ('pro', 'challenger'):
            path = f'data/recall/2026-10-15/{directory}/recall-data.json'
            validated = validation['validated_datasets'][directory]
            document = self.read(path, 'EXISTING_ANONYMOUS_RECALL_PROJECTION', expected=validated['sha256'])
            if document['samples'] != validated['samples']:
                raise ValueError(f'Recall sample binding mismatch: {path}')
            population = document['population']
            dataset_rows = 0
            for index, cohort in enumerate(document['cohorts']):
                reason = None
                if cohort['champion'] is None:
                    reason = 'ROLE_FALLBACK_NOT_CHAMPION_REFERENCE'
                elif cohort['champion'].casefold() not in champion_aliases:
                    reason = 'CHAMPION_NOT_IN_OFFICIAL_CATALOG'
                elif (not re.fullmatch(r'\d+\.\d+', cohort['patch']) or
                      cohort['position'] not in ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT')):
                    reason = 'INVALID_PATCH_OR_POSITION_SCOPE'
                else:
                    counts = [cohort[key] for key in ('matches', 'participant_observations')]
                    if any(type(value) is not int or value <= 0 for value in counts):
                        reason = 'INVALID_COHORT_DENOMINATOR'
                    for key in ('timing', 'current_gold'):
                        metric = cohort['first_recall'][key]
                        if (any(type(metric[count]) is not int or metric[count] < 0
                                for count in ('n', 'missing_n', 'match_n')) or
                            metric['n'] + metric['missing_n'] != cohort['participant_observations'] or
                            metric['match_n'] > cohort['matches'] or metric['match_n'] > metric['n'] or
                            metric['status'] not in ('AVAILABLE', 'UNKNOWN')):
                            reason = 'INVALID_METRIC_DENOMINATOR_OR_STATUS'
                if reason:
                    excluded.append({'local_source': path, 'locator': f'cohorts.{index}', 'reason': reason})
                    continue
                champion = champion_aliases[cohort['champion'].casefold()]
                fields = {key: cohort[key] for key in ('patch', 'position', 'matches', 'participant_observations')}
                rows.append({'id': f'recall:{population}:{cohort["patch"]}:{champion}:{cohort["position"]}',
                    'kind': 'FIRST_RECALL_REFERENCE', 'scope': 'CHAMPION_POSITION_NOT_MATCHUP',
                    'population': population, 'population_samples': document['samples'],
                    **fields, 'champion': champion,
                    'source_champion': cohort['champion'], 'opponent': None,
                    'first_recall': {key: cohort['first_recall'][key]
                                     for key in ('timing', 'current_gold', 'purchases', 'exclusions')},
                    'limitations': document['limitations'] + ['OPPONENT_CHAMPION_SCOPE_UNAVAILABLE_NOT_MATCHUP',
                        'UNKNOWN_METRICS_STAY_UNKNOWN_NOT_OPTIMAL_PURCHASE_OR_ADVANTAGE',
                        'MATCH_ONLY_CHAMPION_POSITION_PATCH_POPULATION_NO_ROLE_FALLBACK'],
                    'source': {'local_source': path, 'sha256': self.bindings[path]['sha256'],
                               'locator': f'cohorts.{index}'},
                    'validation': {'local_source': validation_path,
                                   'sha256': self.bindings[validation_path]['sha256'],
                                   'locator': f'validated_datasets.{directory}'}})
                dataset_rows += 1
            datasets.append({'population': population, 'local_source': path,
                'sha256': self.bindings[path]['sha256'], 'samples': document['samples'],
                'cohorts': len(document['cohorts']), 'projected_champion_position_rows': dataset_rows,
                'metric_status': dict(Counter(r['first_recall']['timing']['status']
                                             for r in rows if r['population'] == population))})
        return rows, {'status': 'DESCRIPTIVE_CHAMPION_POSITION_ONLY', 'datasets': datasets,
            'projected_rows': len(rows), 'matchup_rows': 0,
            'matchup_exclusion_reasons': ['NO_OPPONENT_CHAMPION_SCOPE'], 'excluded_cohorts': excluded,
            'available_fields': ['patch', 'population', 'champion', 'position', 'matches',
                'participant_observations', 'first_recall.timing', 'first_recall.current_gold',
                'first_recall.purchases', 'first_recall.exclusions', 'limitations'],
            'omitted_fields': ['first_recall.priority_gap', 'low_health', 'sensitivity'],
            'note': 'Existing descriptive purchase proxy only; no optimal gold, matchup advantage, causality or coaching accuracy.'}

    def build(self):
        current_path = 'data/official_catalog/current.json'
        current = self.read(current_path, 'OFFICIAL_CATALOG_POINTER')
        patch = current['source_patch']
        archive = f'data/official_catalog/versions/{patch}'
        manifest_path = archive + '/manifest.json'
        manifest = self.read(manifest_path, 'OFFICIAL_KOREAN_ARCHIVE_MANIFEST', expected=current['manifest_sha256'])
        roster_path = archive + '/' + manifest['roster']['file']
        roster = self.read(roster_path, 'OFFICIAL_KOREAN_ROSTER', manifest['roster']['url'], manifest['roster']['sha256'])
        english_path = f'evidence/queue/q05/sources/champion-roster-{patch}.json'
        english = self.read(english_path, 'ARCHIVED_OFFICIAL_ENGLISH',
                            f'https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json')
        if roster['version'] != patch or english['version'] != patch:
            raise ValueError('Roster source version mismatch')
        receipts = self.read(SPRITE_RECEIPTS, 'OFFICIAL_SPRITE_RETRIEVAL_RECEIPTS')['requests']
        assets = {}
        for receipt in receipts:
            raw = (self.root / 'web_r4' / receipt['path']).read_bytes()
            if sha256(raw) != receipt['sha256'] or png_dimensions(raw) != (receipt['width'], receipt['height']):
                raise ValueError('Sprite bytes or dimensions no longer match receipt')
            name = Path(receipt['path']).name
            if (receipt['url'] != f'https://ddragon.leagueoflegends.com/cdn/{patch}/img/sprite/{name}' or
                receipt['version'] != patch):
                raise ValueError('Sprite URL or source version mismatch')
            assets[name] = receipt
        profiles = self.profiles(patch)
        source_rows = {source['champion']: source for source in manifest['sources']}
        champions = {}
        for champion, entry in sorted(roster['data'].items()):
            source = source_rows[champion]
            path = archive + '/' + source['file']
            detail = self.read(path, 'OFFICIAL_KOREAN_SKILLS', source['url'], source['sha256'])
            if detail['version'] != patch:
                raise ValueError('Skill version mismatch')
            detail = detail['data'][champion]
            facts = []
            for slot, ability, locator in [('P', detail['passive'], f'data.{champion}.passive.description')] + [
                (slot, ability, f'data.{champion}.spells.{index}.description')
                for index, (slot, ability) in enumerate(zip('QWER', detail['spells']))]:
                raw = ability['description']
                facts.append({'id': f'official:{champion}:{slot}', 'slot': slot, 'name': ability['name'],
                    'text': plain_text(raw), 'raw_excerpt': raw, 'url': source['url'],
                    'patch': patch, 'sha256': source['sha256'], 'local_source': path, 'locator': locator})
            image = entry['image']
            sheet = assets[image['sprite']]
            champions[champion] = {'id': champion, 'name': entry['name'],
                'aliases': list(dict.fromkeys([champion, entry['name'], english['data'][champion]['name']])),
                'key': entry['key'], 'official_tags': entry['tags'],
                'portrait': {'sprite': sheet['path'], **{key: image[key] for key in ('x', 'y', 'w', 'h')},
                             'sheet_width': sheet['width'], 'sheet_height': sheet['height']},
                'facts': facts, 'profile': profiles[champion]}
        directions = self.read('web_r4/directions-data.json', 'UNCHANGED_SIX_SCENE_SNAPSHOT')
        statistics, statistics_scope = self.recall_references(champions)
        queues = []
        for path, category in [('config/expert_channels.json', 'EXPERT_STATEMENT_CANDIDATES'),
                               ('config/pov_channels.json', 'POV_OBSERVATION_CANDIDATES')]:
            document = self.read(path, 'UNCHANGED_SOURCE_QUEUE_REGISTRY')
            queues.append({'category': category, 'local_source': path,
                'sha256': self.bindings[path]['sha256'],
                'status': 'REGISTERED_SOURCE_ONLY_NOT_ACCEPTED_COACHING',
                'channels': document['channels']})
        diagnostic_path = 'config/video_api_diagnostic.json'
        diagnostic = self.read(diagnostic_path, 'UNCHANGED_VIDEO_DIAGNOSTIC_BOUNDARY')
        content_review = []
        for review in diagnostic['content_reviews']:
            document = self.read(review['path'], 'DIAGNOSTIC_ONLY_NOT_SOURCE_FACT_REVIEW', expected=review['sha256'])
            content_review.append({'local_source': review['path'], 'sha256': review['sha256'],
                'decision': document['decision'], 'source_fact_review': document['source_fact_review'],
                'coaching_use': 'EXCLUDED_DIAGNOSTIC_ONLY'})
        catalog = {'format': 'lol-coach-loading-v1', 'source_patch': patch,
            'strategy_level': 'DESIGN_HYPOTHESIS', 'champions': champions,
            'statistics': statistics, 'lectures': [], 'directions': directions,
            'assets': [assets[key] for key in sorted(assets)],
            'source_bindings': [self.bindings[key] for key in sorted(self.bindings)],
            'legacy': {'directions': 'PRESERVED_EXACT_SIX_SCENE_SNAPSHOT',
                'decisions': 'UNCHANGED_NO_USER_OR_AUTO_PROMOTION',
                'knowledge': 'EXPLORATORY_INCOMPLETE_ABSENT_LABELS_UNKNOWN',
                'source_queues': queues, 'video_diagnostics': content_review,
                'video_slots_today': '3/3_NO_NEW_CALLS',
                'new_game_video_paid_provider_calls': 0,
                'official_static_sprite_gets': len(receipts),
                'facts_are_user_approval': False, 'real_coaching_n': 0, 'accuracy': None}}
        empty = [champion for champion, row in champions.items()
                 if not any(row['profile'][field] for field in PROFILE_FIELDS)]
        scope = {'format': 'loading-catalog-scope-v1', 'source_patch': patch,
            'champion_count': len(champions), 'official_fact_count': sum(len(c['facts']) for c in champions.values()),
            'candidate_rule_count': sum(len(c['profile']['rule_refs']) for c in champions.values()),
            'classification_incomplete': True, 'empty_classification_champions': empty,
            'empty_classification_meaning': 'UNKNOWN_NOT_ABSENCE_OR_WEAKNESS',
            'statistics': statistics_scope, 'lectures': {'accepted': 0, 'status': 'NO_ACCEPTED_COACHING_LECTURES'},
            'assets': catalog['assets'], 'source_queues': queues, 'video_diagnostics': content_review,
            'new_game_video_paid_provider_calls': 0, 'new_static_sprite_gets': len(receipts),
            'real_coaching_n': 0, 'accuracy': None,
            'source_bindings': catalog['source_bindings']}
        return catalog, scope


def encode(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def scope_markdown(scope):
    statistics = scope['statistics']
    datasets = '\n'.join(f'- {d["population"]}: {d["samples"]["matches"]} matches / '
        f'{d["samples"]["participant_observations"]} participant observations; '
        f'{d["projected_champion_position_rows"]} champion/position cohorts. '
        f'Timing status: {d["metric_status"]}.' for d in statistics['datasets'])
    return (f'# Loading catalog evidence scope\n\nSource snapshot: {scope["source_patch"]}. '
        f'{scope["champion_count"]} Korean champions, {scope["official_fact_count"]} exact P/Q/W/E/R facts, '
        f'{scope["candidate_rule_count"]} existing candidate profile references.\n\n'
        'Official facts retain URL, patch, source hash, exact raw excerpt and locator. English names come '
        'from the existing English archive. Interpretations remain EXPLORATORY and incomplete; unlisted '
        'labels mean UNKNOWN. No USER/AUTO promotion, new tactical rule or coaching accuracy claim.\n\n'
        f'Entirely unclassified champions ({len(scope["empty_classification_champions"])}): '
        + (', '.join(scope['empty_classification_champions']) or 'none') + '.\n\n'
        '## Existing descriptive purchase references\n\n' + datasets + '\n\n'
        f'{statistics["projected_rows"]} champion/position references retain original timing, preceding-frame '
        'gold, purchase bundles, missing counts and exclusions. UNKNOWN values remain UNKNOWN. All rows are '
        'CHAMPION_POSITION_NOT_MATCHUP; opponent champion scope is unavailable. No optimal gold, matchup '
        'advantage or causal recommendation follows. Role fallback cohorts remain excluded. Priority-gap, '
        'low-health and sensitivity aggregates are omitted. The preserved recall source-binding hashes '
        'validate these public anonymous files; no private cache is scanned or decrypted.\n\n'
        '## Preserved scenes, assets and source queues\n\n'
        'The six directions scenes are the exact existing directions-data.json snapshot. Existing map and '
        'three portraits remain untouched. Six official champion sprite sheets provide all roster portraits '
        'through the original rectangles; images are not cropped or edited. Each receipt records URL, '
        'version, SHA-256, dimensions, byte count and retrieval time. The compiler is offline unless '
        '--fetch-sprites is explicitly selected; an existing receipt prevents repeat downloads.\n\n'
        'Expert channel and POV registries remain read-only source queues. Registration, enabled status and '
        'content grades do not establish accepted coaching statements. Diagnostic content reviews explicitly '
        'retain source_fact_review=NOT_COMPLETED and remain excluded from coaching. Accepted lectures: 0. '
        'VIDEO quota already 3/3; no video, Gemini, Riot game API, new-match or paid calls were made.\n\n'
        'Real coaching sample n=0; accuracy is null. Existing actual match datasets retain their original '
        'sample counts and are distinct from coaching evaluation.\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='compare deterministic output without writing or network')
    parser.add_argument('--fetch-sprites', action='store_true', help='download only missing six official sprite sheets once')
    args = parser.parse_args()
    if args.check and args.fetch_sprites:
        parser.error('--check cannot download assets')
    fetched = fetch_sprites() if args.fetch_sprites else 0
    catalog, scope = Compiler().build()
    outputs = {CATALOG_PATH: encode(catalog), SCOPE_PATH: encode(scope), SCOPE_MD_PATH: scope_markdown(scope)}
    stale = []
    for path, content in outputs.items():
        destination = ROOT / path
        if args.check:
            if not destination.is_file() or destination.read_text() != content:
                stale.append(path)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content)
    print(json.dumps({'status': 'STALE' if stale else 'OK', 'champions': len(catalog['champions']),
                      'facts': scope['official_fact_count'], 'statistics': len(catalog['statistics']),
                      'sprite_gets_this_run': fetched, 'stale': stale}))
    return 1 if stale else 0


if __name__ == '__main__':
    raise SystemExit(main())
