"""Source lineage and execution boundary for supplemental initiative candidates."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRIORITY = {'Ornn', 'Sejuani', 'Ahri', 'Caitlyn', 'Lux', 'Fiora', 'LeeSin',
            'Zed', 'Ezreal', 'Nautilus', 'Yunara', 'Ashe', 'Kaisa'}
BASELINE_HASHES = {
    'executable-v1.json': '01be0ca8047ad1dc555067c6a5edb7545e7b317a5e6291ee4fe9d637e8a0942c',
    'executable-expanded-v1.json': '5c5787c3d35805c8692d4367239ace7b1cbf19c12c27f3c86cf751e909877160',
}


class InitiativeCandidateTests(unittest.TestCase):
    def candidates(self):
        path = ROOT / 'knowledge_candidates/initiative-v2.json'
        self.assertTrue(path.is_file(), 'supplemental initiative catalog missing')
        return json.loads(path.read_text())

    def test_catalog_preserves_baseline_and_has_thirteen_distinct_profiles(self):
        rows = self.candidates()
        self.assertEqual(len(rows), 13)
        self.assertEqual({r['profile']['champion'] for r in rows}, PRIORITY)
        originals = []
        for name, expected in BASELINE_HASHES.items():
            raw = (ROOT / 'knowledge_candidates' / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
            originals.extend(json.loads(raw))
        self.assertEqual(len(originals), 177)
        self.assertEqual(len({r['profile']['champion'] for r in originals if r['profile']}), 173)
        self.assertEqual(len({r['rule_id'] for r in originals + rows}), 190)
        self.assertTrue(all(r['rule_id'].startswith('Q05-I-') for r in rows))

    def test_every_static_condition_binds_exact_official_source_bytes(self):
        for row in self.candidates():
            champion = row['profile']['champion']
            archive = ROOT / f'evidence/queue/q05/sources/{champion}-16.20.1.json'
            raw = archive.read_bytes()
            document = json.loads(raw)
            self.assertEqual(len(row['sources']), len(row['profile']['necessary_conditions']))
            for source, condition in zip(row['sources'], row['profile']['necessary_conditions']):
                self.assertEqual(source['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(source['url'], f'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion/{champion}.json')
                self.assertEqual(source['kind'], 'DATA_DRAGON')
                self.assertEqual(source['patch'], '16.20.1')
                value = document
                for segment in source['locator'].split('.'):
                    value = value[int(segment)] if isinstance(value, list) else value[segment]
                self.assertIsInstance(value, str)
                self.assertEqual(condition, f'STATIC_SOURCE_16.20.1|{source["locator"]}|{value}')

    def test_no_static_build_becomes_gameplay_patch_or_approval(self):
        from coach_v1.pregame_contract import parse_rule, proposal_rule
        for row in self.candidates():
            spec = parse_rule(row)
            self.assertEqual(spec.schema_version, 'pregame.rule.v2')
            self.assertEqual(spec.patches, [])
            self.assertIsNone(spec.plan_guard)
            self.assertIsNone(spec.output.operations)
            self.assertEqual(spec.cooldowns, [])
            self.assertEqual(spec.conditions + spec.counterconditions + spec.stop_conditions, [])
            proposed = proposal_rule(spec)
            self.assertEqual(proposed['patch_range'], 'UNKNOWN')
            self.assertEqual(proposed['author'], 'AI_EXPLORATORY')
            self.assertTrue(proposed['required_fields'][0].startswith('EXECUTABLE_V2_SHA256:'))
            self.assertTrue(any('EXPLORATORY' in text for text in spec.limitations))
            self.assertTrue(any('GAME_PATCH_UNKNOWN' in text for text in spec.limitations))
            self.assertTrue(spec.counterexamples)
            self.assertEqual(spec.profile.roles + spec.profile.strong_when + spec.profile.lane_style + spec.profile.jungle_style, [])

    def test_follower_claim_keeps_optional_ally_cc_limit_and_other_needs_unknown(self):
        rows = {r['profile']['champion']: r for r in self.candidates()}
        kaisa = rows['Kaisa']
        self.assertEqual(kaisa['profile']['initiative'], ['FOLLOW_UP'])
        self.assertEqual(kaisa['profile']['needs'], ['ALLY_CC'])
        self.assertIn('Allies\' immobilizing effects help stack Plasma.', kaisa['profile']['necessary_conditions'][0])
        self.assertTrue(any('optional benefit' in x for x in kaisa['limitations']))
        self.assertFalse(any('Killer Instinct' in x for x in kaisa['profile']['necessary_conditions']))
        for champion, row in rows.items():
            if champion != 'Kaisa':
                self.assertEqual(row['profile']['needs'], [])
        self.assertIn('PROTECTOR', rows['Lux']['profile']['initiative'])
        self.assertIn('PROTECTOR', rows['LeeSin']['profile']['initiative'])
        self.assertEqual(rows['Yunara']['profile']['initiative'], ['SELF_SUFFICIENT'])


if __name__ == '__main__':
    unittest.main()
