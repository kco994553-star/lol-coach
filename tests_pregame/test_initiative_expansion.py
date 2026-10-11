"""Complete static-source coverage without approving or executing candidates."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASELINES = {
    'executable-v1.json': '01be0ca8047ad1dc555067c6a5edb7545e7b317a5e6291ee4fe9d637e8a0942c',
    'executable-expanded-v1.json': '5c5787c3d35805c8692d4367239ace7b1cbf19c12c27f3c86cf751e909877160',
    'initiative-v2.json': '986c1740df77c3af4c0d1b81297bf2bc72a959579f4e4616b1b20785cccc4627',
    'q05-roster-profiles.json': '09246c1a70085da4d85328ebcee72a80f74ac6f96459c85d4658ebd2c337a3f0',
}


class InitiativeExpansionTests(unittest.TestCase):
    def rows(self):
        path = ROOT / 'knowledge_candidates/initiative-expansion-v2.json'
        self.assertTrue(path.is_file(), 'all-160 supplementary catalog is missing')
        return json.loads(path.read_text())

    def test_exact_remaining_roster_and_preserved_190_candidates(self):
        originals = []
        for name, sha in BASELINES.items():
            raw = (ROOT / 'knowledge_candidates' / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), sha)
            if name != 'q05-roster-profiles.json':
                originals.extend(json.loads(raw))
        rows = self.rows()
        roster = json.loads((ROOT / 'knowledge_candidates/q05-roster-profiles.json').read_text())
        previous = {r['profile']['champion'] for r in originals if r['schema_version'] == 'pregame.rule.v2'}
        expected = {p['champion_id'] for p in roster['profiles']} - previous
        self.assertEqual(len(originals), 190)
        self.assertEqual(len(rows), 160)
        self.assertEqual({r['profile']['champion'] for r in rows}, expected)
        self.assertEqual(len({r['rule_id'] for r in originals + rows}), 350)
        self.assertTrue(all(r['rule_id'].startswith('Q05-IX-') for r in rows))

    def test_every_claim_resolves_exact_archive_hash_locator_and_receipt(self):
        receipts = {r['champion_id']: r for r in json.loads(
            (ROOT / 'evidence/queue/q05-expansion/source-receipts.json').read_text())}
        for row in self.rows():
            champion = row['profile']['champion']
            receipt = receipts[champion]
            raw = (ROOT / receipt['archive']).read_bytes()
            doc = json.loads(raw)
            self.assertEqual(receipt['status'], 'SOURCE_VERIFIED')
            self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['sha256'])
            self.assertIn(len(row['sources']), (1, 2))
            self.assertEqual(len(row['sources']), len(row['profile']['necessary_conditions']))
            self.assertEqual(len({s['locator'] for s in row['sources']}), len(row['sources']))
            for source, condition in zip(row['sources'], row['profile']['necessary_conditions']):
                self.assertEqual(source['url'], receipt['url'])
                self.assertEqual(source['sha256'], receipt['sha256'])
                self.assertEqual(source['kind'], 'DATA_DRAGON')
                self.assertEqual(source['patch'], '16.20.1')
                value = doc
                for part in source['locator'].split('.'):
                    value = value[int(part)] if isinstance(value, list) else value[part]
                self.assertEqual(condition, f'STATIC_SOURCE_16.20.1|{source["locator"]}|{value}')
                self.assertTrue(any(source['locator'] in c for c in row['counterexamples']))
            for tag in row['profile']['initiative']:
                prefix = 'INITIATIVE_BASIS|' + tag + '|'
                bases = [s[len(prefix):] for s in row['limitations'] if s.startswith(prefix)]
                self.assertEqual(len(bases), 1)
                self.assertIn(bases[0], {s['locator'] for s in row['sources']})

    def test_unknown_fields_and_no_patch_approval_or_execution(self):
        from coach_v1.pregame_contract import parse_rule, proposal_rule
        for row in self.rows():
            spec = parse_rule(row)
            self.assertEqual(spec.model_dump(mode='json'), row)
            self.assertEqual(spec.schema_version, 'pregame.rule.v2')
            self.assertEqual(spec.patches + spec.positions + spec.cooldowns, [])
            self.assertIsNone(spec.plan_guard)
            self.assertIsNone(spec.output.operations)
            self.assertEqual(spec.conditions + spec.counterconditions + spec.stop_conditions, [])
            self.assertEqual(spec.profile.roles + spec.profile.strong_when + spec.profile.lane_style +
                spec.profile.jungle_style + spec.profile.threats + spec.profile.protection, [])
            self.assertEqual(spec.profile.needs, [])
            self.assertEqual(spec.output.change_conditions, [])
            proposal = proposal_rule(spec)
            self.assertEqual(proposal['author'], 'AI_EXPLORATORY')
            self.assertEqual(proposal['patch_range'], 'UNKNOWN')
            self.assertTrue(proposal['required_fields'][0].startswith('EXECUTABLE_V2_SHA256:'))
            self.assertTrue(any('GAME_PATCH_UNKNOWN' in s for s in spec.limitations))
            self.assertTrue(any('STAGE_ROLE_UNKNOWN' in s for s in spec.limitations))
            if not spec.profile.initiative:
                self.assertTrue(any('INITIATIVE_UNKNOWN' in s for s in spec.limitations))

    def test_conservative_partial_labels_and_source_specific_dependency_limits(self):
        rows = {r['profile']['champion']: r for r in self.rows()}
        for champion in ('Amumu', 'Malphite', 'Rakan', 'Braum', 'Alistar', 'Blitzcrank',
                'Leona', 'Rell', 'Shen', 'Nami'):
            self.assertIn('INITIATOR', rows[champion]['profile']['initiative'])
        for champion in ('Rakan', 'Braum', 'Shen', 'Soraka', 'Nami', 'Janna'):
            self.assertIn('PROTECTOR', rows[champion]['profile']['initiative'])
        for champion in ('Akali', 'Kassadin', 'Samira', 'Yasuo'):
            self.assertIn('SELF_SUFFICIENT', rows[champion]['profile']['initiative'])
        self.assertEqual(rows['Jhin']['profile']['initiative'], ['FOLLOW_UP'])
        self.assertTrue(any('optional allied contribution' in s for s in rows['Jhin']['limitations']))
        self.assertTrue(any('own damage or traps' in s for s in rows['Jhin']['limitations']))
        self.assertEqual(rows['Jhin']['profile']['needs'], [])
        for champion in ('Kalista', 'Kayle', 'Smolder', 'Taliyah', 'Teemo'):
            if champion == 'Kayle':
                self.assertEqual(rows[champion]['profile']['initiative'], ['PROTECTOR'])
            else:
                self.assertEqual(rows[champion]['profile']['initiative'], [])
        self.assertNotIn('FOLLOW_UP', rows['Yasuo']['profile']['initiative'])
        self.assertTrue(any('own maneuver and strike' in s for s in rows['Samira']['limitations']))

    def test_combined_candidate_wire_budget_stays_below_unchanged_one_mib(self):
        originals = []
        for name in ('executable-v1.json', 'executable-expanded-v1.json', 'initiative-v2.json'):
            originals.extend(json.loads((ROOT / 'knowledge_candidates' / name).read_text()))
        # Exact existing bounded_reply/reply encoding; no response-limit change.
        # The server returns a bare list. Retain a 32KiB safety margin.
        payload = json.dumps(originals + self.rows(), ensure_ascii=False, allow_nan=False).encode()
        self.assertLess(len(payload), 1024 * 1024 - 32 * 1024)


if __name__ == '__main__':
    unittest.main()
