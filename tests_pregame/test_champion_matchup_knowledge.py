"""Source-scoped qualitative knowledge, independent of statistical tier filters."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/champion_matchup_references.json'
PUBLIC = ROOT / 'web_r4/champion-matchup-knowledge.json'


class ChampionMatchupKnowledgeTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.find_spec('coach_v1.champion_matchup_knowledge')
        self.assertIsNotNone(spec, 'qualitative matchup projector must exist')
        from coach_v1 import champion_matchup_knowledge as module
        self.module = module
        self.config = json.loads(CONFIG.read_text())
        self.catalog = json.loads((ROOT / 'web_r4/loading-data.json').read_text())
        self.existing = json.loads((ROOT / 'web_r4/loading-knowledge.json').read_text())

    def build(self, config=None):
        return self.module.build_knowledge(self.config if config is None else config, self.catalog, self.existing)

    def test_retained_counts_fewer_than_five_and_jungle_scope(self):
        index = self.build()
        expected = {'Caitlyn': ('BOTTOM', 4, 3), 'Ezreal': ('BOTTOM', 3, 2),
                    'Fiora': ('TOP', 5, 5), 'Graves': ('JUNGLE', 5, 5), 'Yunara': ('BOTTOM', 5, 2)}
        for champion, (position, difficult, easier) in expected.items():
            with self.subTest(champion=champion):
                result = self.module.select_knowledge(index, champion, position)
                self.assertEqual((len(result['difficult']), len(result['easier'])), (difficult, easier))
                self.assertTrue(all(r['assessment_scope'] == ('JUNGLE' if position == 'JUNGLE' else 'LANING')
                                    for r in result['difficult'] + result['easier']))
                self.assertEqual(result['coverage']['fewer_than_five'], difficult < 5 or easier < 5)
        self.assertEqual(self.module.select_knowledge(index, 'Kaisa', 'BOTTOM')['coverage']['status'], 'NO_RESEARCH')
        self.assertEqual(self.module.select_knowledge(index, 'Fiora', 'MID')['coverage']['status'], 'NO_RESEARCH')

    def test_whole_game_categories_do_not_become_easy_lane(self):
        result = self.module.select_knowledge(self.build(), 'Ezreal', 'BOTTOM')
        self.assertEqual({r['opponent'] for r in result['references']}, {'Kaisa', 'Caitlyn', 'Lucian', 'Aphelios'})
        self.assertFalse({'Caitlyn', 'Lucian'} & {r['opponent'] for r in result['easier']})
        self.assertTrue(all(r['qualitative_difficulty'] == 'UNKNOWN_FOR_SCOPE' for r in result['references']))
        self.assertEqual({r['id'] for r in result['conditional']},
                         {r['id'] for r in result['difficult'] + result['easier']})

    def test_no_statistical_tier_power_or_tactical_promotion(self):
        index = self.build()
        self.assertTrue(index['tier_independent'])
        self.assertFalse(index['derived_from_statistics'])
        self.assertFalse(index['coaching'])
        self.assertEqual(index['tactical_validation'], 'UNREVIEWED')
        for r in index['records']:
            self.assertEqual(r['tactical_validation'], 'UNREVIEWED')
            for f in ('reason', 'action', 'change_if'):
                self.assertTrue(r[f]['origin'].startswith(('AI_', 'SOURCE_')))
                self.assertTrue(r[f]['source_quote_refs'])
        bad = copy.deepcopy(self.config)
        bad['records'][0]['winrate'] = 0.9
        with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config)
        bad['records'][0]['tactical_validation'] = 'APPROVED'
        with self.assertRaises(ValueError): self.build(bad)

    def test_rejects_noncanonical_ids_duplicate_conflicting_buckets_and_wrong_phase(self):
        for mutate in [lambda r: r.update(opponent="Kai'Sa"), lambda r: r.update(champion='__proto__'),
                       lambda r: r.update(assessment_scope='JUNGLE'), lambda r: r.update(position='ADC'),
                       lambda r: r.update(publication_eligibility=True), lambda r: r.update(author_category=5),
                       lambda r: r.update(qualitative_difficulty='EASY'),
                       lambda r: r.update(qualitative_difficulty=[]), lambda r: r.update(source_refs=[{}])]:
            bad = copy.deepcopy(self.config); mutate(bad['records'][0])
            with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config)
        duplicate = copy.deepcopy(bad['records'][0]); duplicate['qualitative_difficulty'] = 'RELATIVELY_EASIER_CONDITIONAL'
        bad['records'].append(duplicate)
        with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['records'][0]['id'] = 'unstable-id'
        with self.assertRaises(ValueError): self.build(bad)

    def test_reference_only_cannot_claim_lane_difficulty_and_patch_mapping_is_explicit(self):
        bad = copy.deepcopy(self.config)
        record = next(r for r in bad['records'] if r['publication_eligibility'] == 'REFERENCE_ONLY')
        record['qualitative_difficulty'] = 'DIFFICULT'
        with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['records'][0]['patch_scope']['namespace_mapping'] = 'MATCH'
        with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['records'][0]['source_refs'] = ['missing']
        with self.assertRaises(ValueError): self.build(bad)

    def test_only_https_named_public_sources_with_reused_existing_source_ids(self):
        index = self.build()
        old = {s['url']: s['id'] for s in self.existing['sources']}
        for s in index['sources']:
            if s['url'] in old: self.assertEqual(s['id'], old[s['url']])
        for url in ['http://example.com/guide', 'https://user:password@example.com/g',
                    'https://127.0.0.1/private', 'https://example.com/a?token=secret',
                    'https://www.youtube.com/watch?v=abc']:
            bad = copy.deepcopy(self.config); bad['sources'][0]['url'] = url
            with self.subTest(url=url), self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['sources'][0]['access_status'] = 'AUTHENTICATED'
        with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['sources'][0]['html_sha256'] = 'bad'
        with self.assertRaises(ValueError): self.build(bad)

    def test_copyright_private_fields_and_unapproved_quote_corpus_rejected(self):
        for target, key, value in [('record', 'exact_quote', 'full source text'),
                                   ('record', 'raw_html', '<html>private corpus</html>'),
                                   ('source', 'local_snapshot', '/workspace/private.html'),
                                   ('source', 'token', 'secret')]:
            bad = copy.deepcopy(self.config)
            (bad['records'][0] if target == 'record' else bad['sources'][0])[key] = value
            with self.assertRaises(ValueError): self.build(bad)
        bad = copy.deepcopy(self.config); bad['records'][0]['evidence']['exact_quote'] = 'copied '*100
        with self.assertRaises(ValueError): self.build(bad)
        serialized = json.dumps(self.build(), ensure_ascii=False)
        for forbidden in ['local_snapshot', 'paragraph_snapshot_ref', 'exact_quote', 'raw_html', '/workspace/']:
            self.assertNotIn(forbidden, serialized)

    def test_source_severity_only_and_ties_are_deterministic_with_max_five(self):
        index = self.build()
        shuffled = copy.deepcopy(index); shuffled['records'].reverse()
        self.assertEqual(self.module.select_knowledge(index, 'Graves', 'JUNGLE'),
                         self.module.select_knowledge(shuffled, 'Graves', 'JUNGLE'))
        rows = self.module.select_knowledge(index, 'Graves', 'JUNGLE')['difficult']
        self.assertEqual([r['author_category'] for r in rows], ['Extreme'] * 3 + ['Major'] * 2)
        for rows in [self.module.select_knowledge(index, c, p)[k] for c, p in
                     [('Fiora', 'TOP'), ('Graves', 'JUNGLE')] for k in ('difficult', 'easier')]:
            self.assertLessEqual(len(rows), 5)
            self.assertTrue(all('rank' not in r and 'strength' not in r for r in rows))
        # An isolated synthetic sixth record tests the presentation cap, never saved as research.
        six = copy.deepcopy(index)
        extra = copy.deepcopy(next(r for r in six['records'] if r['champion'] == 'Fiora'
                                   and r['qualitative_difficulty'] == 'DIFFICULT'))
        extra.update(id='Fiora:TOP:Teemo', opponent='Teemo')
        six['records'].append(extra)
        self.assertEqual(len(self.module.select_knowledge(six, 'Fiora', 'TOP')['difficult']), 5)
        for c, p in [('Unknown', 'BOTTOM'), ('Caitlyn', 'ADC'), ('constructor', 'BOTTOM')]:
            with self.assertRaises(ValueError): self.module.select_knowledge(index, c, p)

    def test_public_artifact_is_reproducible_and_check_detects_drift(self):
        result = subprocess.run(['python', 'scripts/build_champion_matchup_knowledge.py', '--check'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(PUBLIC.read_text()), self.build())
        with tempfile.TemporaryDirectory() as temporary:
            stale = Path(temporary) / 'stale.json'; stale.write_text('{}\n')
            result = subprocess.run(['python', 'scripts/build_champion_matchup_knowledge.py',
                                     '--check', '--output', str(stale)], cwd=ROOT,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(stale.read_text(), '{}\n')
