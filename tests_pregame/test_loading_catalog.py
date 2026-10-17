"""Offline loading catalog provenance and evidence-boundary checks."""
import hashlib
import html
from functools import lru_cache
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('threats', 'protection', 'strong_when', 'lane_style',
          'jungle_style', 'initiative', 'needs')


@lru_cache(maxsize=None)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=None)
def document_at(path):
    return json.loads(path.read_text())


def located(document, locator):
    for segment in locator.split('.'):
        document = document[int(segment)] if isinstance(document, list) else document[segment]
    return document


class LoadingCatalogTests(unittest.TestCase):
    def catalog(self):
        path = ROOT / 'web_r4/loading-data.json'
        self.assertTrue(path.is_file(), 'loading catalog has not been compiled')
        return json.loads(path.read_text())

    def test_complete_korean_roster_and_archived_english_search_aliases(self):
        catalog = self.catalog()
        korean = json.loads((ROOT / 'data/official_catalog/versions/16.20.1/champion.ko_KR.json').read_text())
        english = json.loads((ROOT / 'evidence/queue/q05/sources/champion-roster-16.20.1.json').read_text())
        self.assertEqual(catalog['source_patch'], korean['version'])
        self.assertEqual(len(catalog['champions']), 173)
        self.assertEqual(set(catalog['champions']), set(korean['data']))
        for champion, row in catalog['champions'].items():
            self.assertEqual(row['name'], korean['data'][champion]['name'])
            self.assertEqual(row['official_tags'], korean['data'][champion]['tags'])
            self.assertTrue({champion, row['name'], english['data'][champion]['name']} <= set(row['aliases']))
        for champion, alias in [('MonkeyKing', 'Wukong'), ('Nunu', 'Nunu & Willump'),
                                ('Kaisa', "Kai'Sa"), ('KSante', "K'Sante")]:
            self.assertIn(alias, catalog['champions'][champion]['aliases'])

    def test_all_passive_and_four_skill_facts_bind_exact_korean_source(self):
        for champion, row in self.catalog()['champions'].items():
            self.assertEqual([f['slot'] for f in row['facts']], list('PQWER'))
            for fact in row['facts']:
                source = ROOT / fact['local_source']
                document = document_at(source)
                self.assertEqual(document['version'], fact['patch'])
                self.assertEqual(fact['patch'], '16.20.1')
                self.assertEqual(fact['sha256'], digest(source))
                self.assertEqual(fact['raw_excerpt'], located(document, fact['locator']))
                self.assertEqual(fact['url'], f'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/ko_KR/champion/{champion}.json')
                self.assertEqual(fact['id'], f'official:{champion}:{fact["slot"]}')
                self.assertNotRegex(fact['text'], r'<[^>]+>')
                self.assertEqual(' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fact['raw_excerpt'])).split()), fact['text'])

    def test_portraits_use_unchanged_official_sheets_and_in_bounds_roster_rectangles(self):
        catalog = self.catalog()
        roster = json.loads((ROOT / 'data/official_catalog/versions/16.20.1/champion.ko_KR.json').read_text())['data']
        self.assertEqual(len(catalog['assets']), 6)
        for asset in catalog['assets']:
            raw = (ROOT / 'web_r4' / asset['path']).read_bytes()
            self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
            width, height = struct.unpack('>II', raw[16:24])
            self.assertEqual((asset['width'], asset['height']), (width, height))
            self.assertEqual(asset['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(asset['version'], catalog['source_patch'])
            self.assertEqual(asset['url'], f'https://ddragon.leagueoflegends.com/cdn/16.20.1/img/sprite/{Path(asset["path"]).name}')
        for champion, row in catalog['champions'].items():
            portrait = row['portrait']
            source = roster[champion]['image']
            self.assertEqual(portrait['sprite'], 'loading-assets/' + source['sprite'])
            self.assertEqual({key: portrait[key] for key in ('x', 'y', 'w', 'h')},
                             {key: source[key] for key in ('x', 'y', 'w', 'h')})
            self.assertLessEqual(portrait['x'] + portrait['w'], portrait['sheet_width'])
            self.assertLessEqual(portrait['y'] + portrait['h'], portrait['sheet_height'])

    def test_profile_labels_are_only_exact_existing_exploratory_candidates(self):
        for champion, row in self.catalog()['champions'].items():
            profile = row['profile']
            self.assertEqual(profile['review_state'], 'EXPLORATORY')
            self.assertIs(profile['classification_incomplete'], True)
            self.assertEqual(profile['unlisted_labels'], 'UNKNOWN')
            expected = {key: set() for key in FIELDS}
            self.assertTrue(profile['rule_refs'])
            for reference in profile['rule_refs']:
                path = ROOT / reference['local_source']
                self.assertEqual(reference['sha256'], digest(path))
                source = located(document_at(path), reference['locator'])
                self.assertEqual(source['rule_id'], reference['id'])
                self.assertEqual(source['version'], reference['version'])
                self.assertEqual(source['profile']['champion'], champion)
                for key in FIELDS:
                    self.assertEqual(reference['fields'][key], source['profile'].get(key, []))
                    expected[key].update(source['profile'].get(key, []))
                for source_ref in reference['source_refs']:
                    source_path = ROOT / source_ref['local_source']
                    self.assertEqual(source_ref['sha256'], digest(source_path))
                    self.assertEqual(source_ref['raw_excerpt'], located(document_at(source_path), source_ref['locator']))
            for key in FIELDS:
                self.assertEqual(set(profile[key]), expected[key])

    def test_direction_scenes_are_exact_snapshot_with_source_hash(self):
        catalog = self.catalog()
        path = ROOT / 'web_r4/directions-data.json'
        self.assertEqual(catalog['directions'], json.loads(path.read_text()))
        self.assertEqual(len(catalog['directions']['presets']), 6)
        binding = next(s for s in catalog['source_bindings'] if s['local_source'] == 'web_r4/directions-data.json')
        self.assertEqual(binding['sha256'], digest(path))

    def test_every_local_reused_input_has_exact_source_binding(self):
        catalog = self.catalog()
        bindings = {s['local_source']: s for s in catalog['source_bindings']}
        for binding in bindings.values():
            self.assertEqual(binding['sha256'], digest(ROOT / binding['local_source']))
        for row in catalog['champions'].values():
            for fact in row['facts']:
                self.assertEqual(bindings[fact['local_source']]['sha256'], fact['sha256'])
            for reference in row['profile']['rule_refs']:
                self.assertIn(reference['local_source'], bindings)
                for source in reference['source_refs']:
                    self.assertIn(source['local_source'], bindings)

    def test_recall_references_keep_original_descriptive_scope_and_missingness(self):
        catalog = self.catalog()
        self.assertEqual(len(catalog['statistics']), 353)
        counts = {'PRO_REFERENCE': 0, 'CHALLENGER': 0}
        for reference in catalog['statistics']:
            self.assertEqual(reference['kind'], 'FIRST_RECALL_REFERENCE')
            self.assertEqual(reference['scope'], 'CHAMPION_POSITION_NOT_MATCHUP')
            self.assertIsNone(reference['opponent'])
            self.assertIn(reference['champion'], catalog['champions'])
            source = ROOT / reference['source']['local_source']
            document = document_at(source)
            cohort = located(document, reference['source']['locator'])
            self.assertEqual(reference['source']['sha256'], digest(source))
            self.assertEqual(reference['population'], document['population'])
            self.assertEqual(reference.get('population_samples'), document['samples'])
            self.assertEqual(reference['source_champion'], cohort['champion'])
            self.assertIn(cohort['champion'].casefold(),
                          [alias.casefold() for alias in catalog['champions'][reference['champion']]['aliases']])
            for key in ('position', 'patch', 'matches', 'participant_observations'):
                self.assertEqual(reference[key], cohort[key])
            for key in ('timing', 'current_gold', 'purchases', 'exclusions'):
                self.assertEqual(reference['first_recall'][key], cohort['first_recall'][key])
            for metric in ('timing', 'current_gold'):
                self.assertEqual(reference['first_recall'][metric]['n'] + reference['first_recall'][metric]['missing_n'],
                                 reference['participant_observations'])
            self.assertIn('OPPONENT_CHAMPION_SCOPE_UNAVAILABLE_NOT_MATCHUP', reference['limitations'])
            validation = reference['validation']
            self.assertEqual(validation['sha256'], digest(ROOT / validation['local_source']))
            counts[reference['population']] += 1
        self.assertEqual(counts, {'PRO_REFERENCE': 72, 'CHALLENGER': 281})

    def test_statistics_and_lecture_queue_do_not_claim_matchup_or_approval(self):
        catalog = self.catalog()
        self.assertEqual(catalog['lectures'], [])
        scope = json.loads((ROOT / 'evidence/actual-evidence/loading/catalog-scope.json').read_text())
        self.assertEqual(scope['statistics']['status'], 'DESCRIPTIVE_CHAMPION_POSITION_ONLY')
        self.assertEqual(scope['statistics']['matchup_rows'], 0)
        self.assertIn('NO_OPPONENT_CHAMPION_SCOPE', scope['statistics']['matchup_exclusion_reasons'])
        self.assertEqual(scope['real_coaching_n'], 0)
        self.assertIsNone(scope['accuracy'])
        self.assertEqual(catalog['legacy']['decisions'], 'UNCHANGED_NO_USER_OR_AUTO_PROMOTION')
        self.assertEqual(catalog['legacy']['video_slots_today'], '3/3_NO_NEW_CALLS')
        self.assertTrue(all(q['status'] == 'REGISTERED_SOURCE_ONLY_NOT_ACCEPTED_COACHING'
                            for q in catalog['legacy']['source_queues']))

    def test_offline_compiler_checks_reproducible_artifacts(self):
        self.catalog()
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_loading_catalog.py'), '--check'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
