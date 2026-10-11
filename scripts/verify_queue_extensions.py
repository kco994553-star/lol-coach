"""Execute frozen adapter assertions and additive contract lineage assertions.

Historical source/manifest bytes are immutable. Their whole-module hash applies
to the frozen v1 source view; the documented amendment checks current semantics.
"""
from __future__ import annotations

import hashlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FROZEN_COMMIT = '708dc737ca4cd70eff86e6a4c6a2ceba039430f3'
CONTRACT = 'coach_v1/pregame_contract.py'
VALIDATOR = 'evidence/queue/q05-expanded-adapter/validate.py'
MANIFEST = 'evidence/queue/q05-expanded-adapter/manifest.json'
PINNED_HASHES = {
    CONTRACT: '23c9d0fd4a90f968c71d9e425bdd51ac56b8d0fdd9f7e7a9253aae4c1b9c9761',
    VALIDATOR: 'e13717b145254ca42026715459f03c47763fbd7b58358f19267c5353d0ca2660',
    MANIFEST: '03c69af2497c5fc2c435a4852da11c7b80b24207e06349ee0a512cf1f351fe63',
}


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen_bytes(path):
    result = subprocess.run(['git', 'show', FROZEN_COMMIT + ':' + path], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError('Frozen history unavailable; CI checkout requires fetch-depth: 0')
    raw = result.stdout
    if path in PINNED_HASHES and sha256(raw) != PINNED_HASHES[path]:
        raise ValueError('Frozen byte hash mismatch: ' + path)
    return raw


def module_from_bytes(name, raw, filename):
    module = types.ModuleType(name)
    module.__file__ = str(filename)
    module.__package__ = 'coach_v1'
    sys.modules[name] = module
    exec(compile(raw, str(filename), 'exec'), module.__dict__)
    return module


def frozen_contract():
    # The archived module imports canonical/digest from state; validate that
    # dependency too, rather than silently sharing a changed implementation.
    if (ROOT / 'coach_v1/state.py').read_bytes() != frozen_bytes('coach_v1/state.py'):
        raise ValueError('Frozen canonical/digest dependency changed')
    return module_from_bytes('coach_v1._queue_frozen_contract', frozen_bytes(CONTRACT), ROOT / CONTRACT)


def adapter_module(name, source_root, contract):
    for path in (VALIDATOR, MANIFEST):
        if (ROOT / path).read_bytes() != frozen_bytes(path):
            raise ValueError('Historical adapter file changed: ' + path)
    module = module_from_bytes(name, frozen_bytes(VALIDATOR), ROOT / VALIDATOR)
    module.ROOT = source_root
    module.CATALOG = source_root / 'knowledge_candidates/executable-expanded-v1.json'
    module.ORIGINAL = source_root / 'knowledge_candidates/executable-v1.json'
    module.ROSTER = source_root / 'knowledge_candidates/q05-roster-profiles.json'
    module.parse_rule = contract.parse_rule
    module.proposal_rule = contract.proposal_rule
    module.binding_matches = contract.binding_matches
    return module


def assert_v1_compatibility(test, frozen, current):
    """Execute byte, model, serialization, digest and binding invariants."""
    from coach_v1.state import canonical, digest
    manifest = json.loads((ROOT / MANIFEST).read_text())
    for path, expected in manifest['preserved_files_sha256'].items():
        raw = frozen_bytes(path) if path == CONTRACT else (ROOT / path).read_bytes()
        test.assertEqual(sha256(raw), expected, path)
    test.assertEqual((ROOT / VALIDATOR).read_bytes(), frozen_bytes(VALIDATOR))
    test.assertEqual((ROOT / MANIFEST).read_bytes(), frozen_bytes(MANIFEST))
    model_names = [name for name, value in vars(frozen).items()
                   if isinstance(value, type) and issubclass(value, frozen.Strict)]
    test.assertTrue(model_names)
    for name in model_names:
        test.assertEqual(getattr(current, name).model_json_schema(),
                         getattr(frozen, name).model_json_schema(), name)
    specs = json.loads((ROOT / 'knowledge_candidates/executable-v1.json').read_text())
    specs += json.loads((ROOT / 'knowledge_candidates/executable-expanded-v1.json').read_text())
    test.assertEqual(len(specs), 177)
    for raw in specs:
        old = frozen.parse_rule(raw).model_dump(mode='json')
        new = current.parse_rule(raw).model_dump(mode='json')
        test.assertEqual(old, raw)
        test.assertEqual(new, old, raw['rule_id'])
        test.assertEqual(canonical(new), canonical(old), raw['rule_id'])
        test.assertEqual(digest(new), digest(old), raw['rule_id'])
        test.assertEqual(current.proposal_rule(raw), frozen.proposal_rule(raw), raw['rule_id'])
        test.assertTrue(current.binding_matches(frozen.proposal_rule(raw), raw))
        altered = dict(frozen.proposal_rule(raw), claim='CHANGED CLAIM')
        test.assertFalse(current.binding_matches(altered, raw))
        test.assertFalse(frozen.binding_matches(altered, raw))
    from tests_pregame.test_contract import golden
    for position in ('TOP', 'JUNGLE', 'MID', 'BOTTOM', 'SUPPORT'):
        raw = golden(position)
        test.assertEqual(current.parse_input(raw).model_dump(mode='json'),
                         frozen.parse_input(raw).model_dump(mode='json'))
        changed = dict(raw, hidden_enemy_coordinates={'x': 0, 'y': 0})
        for contract in (frozen, current):
            with test.assertRaises(ValueError):
                contract.parse_input(changed)
    return dict(original_v1_models=model_names, original_specs_checked=len(specs),
                selected_positions_checked=5, exact_model_schemas=True,
                exact_spec_roundtrip=True, exact_canonical_and_digest=True,
                exact_proposal_payloads=True, changed_claim_binding_rejected=True,
                hidden_input_coordinates_rejected=True)


def amended_test_class(module, frozen, current):
    class AmendedExpandedAdapterTests(module.ExpandedAdapterTests):
        def test_original_catalog_and_source_rows_remain_unchanged(self):
            # Authorized amendment supersedes only whole-current-module equality.
            # The original six assertions also execute unmodified against frozen
            # source bytes in historical_frozen_v1; no old assertion is skipped.
            amendment = ROOT / 'docs/queue/CONTRACT_AMENDMENT_V3.md'
            self.assertTrue(amendment.is_file(), 'explicit contract amendment missing')
            text = amendment.read_text()
            self.assertIn('USER_QUEUE_V1.4_2026-10-11', text)
            self.assertIn(FROZEN_COMMIT, text)
            type(self).amendment_audit = assert_v1_compatibility(self, frozen, current)
    return AmendedExpandedAdapterTests


class VersionedExtensionTests(unittest.TestCase):
    def setUp(self):
        from coach_v1 import pregame_contract as current
        self.current = current
        raw = (ROOT / 'knowledge_candidates/initiative-v2.json').read_bytes()
        self.assertEqual(sha256(raw), '986c1740df77c3af4c0d1b81297bf2bc72a959579f4e4616b1b20785cccc4627')
        self.v2 = json.loads(raw)

    def test_v2_original_profiles_serialize_and_bind_exactly(self):
        for raw in self.v2:
            self.assertEqual(self.current.parse_rule(raw).model_dump(mode='json'), raw)
            proposal = self.current.proposal_rule(raw)
            self.assertTrue(proposal['required_fields'][0].startswith('EXECUTABLE_V2_SHA256:'))
            self.assertTrue(self.current.binding_matches(proposal, raw))
            self.assertEqual(proposal['patch_range'], 'UNKNOWN')
            changed = copy.deepcopy(raw)
            changed['profile']['live_enemy_cooldown'] = 0
            with self.assertRaises(ValueError):
                self.current.parse_rule(changed)

    def test_v3_profile_version_is_separate_and_extras_are_rejected(self):
        from coach_v1.state import digest
        for original in self.v2:
            raw = copy.deepcopy(original)
            raw['schema_version'] = 'pregame.rule.v3'
            raw['output']['movement'] = []
            parsed = self.current.parse_rule(raw)
            self.assertEqual(parsed.model_dump(mode='json'), raw)
            proposed = self.current.proposal_rule(parsed)
            self.assertEqual(proposed['required_fields'][0], 'EXECUTABLE_V3_SHA256:' + digest(raw))
            self.assertTrue(self.current.binding_matches(proposed, raw))
            self.assertFalse(self.current.binding_matches(self.current.proposal_rule(original), raw))
            with self.assertRaises(ValueError):
                self.current.parse_rule(dict(raw, opponent_tracker=True))


def run_suite(test_class, out, filename, expected):
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
    names = [test.id() for test in suite]
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (out / filename).write_text(stream.getvalue())
    return dict(tests_run=result.testsRun, expected=expected, test_ids=names,
                failures=[test.id() for test, _ in result.failures],
                errors=[test.id() for test, _ in result.errors],
                skipped=[dict(test=test.id(), reason=reason) for test, reason in result.skipped],
                passed=result.wasSuccessful() and result.testsRun == expected and not result.skipped)


def main():
    from coach_v1 import pregame_contract as current
    out = ROOT / 'evidence/queue' / ('adapter-v3-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    errors = []
    suites = {}
    audit = None
    try:
        frozen = frozen_contract()
        with tempfile.TemporaryDirectory(prefix='adapter-v1-source-view-') as temporary:
            view = Path(temporary)
            (view / 'coach_v1').mkdir()
            (view / CONTRACT).write_bytes(frozen_bytes(CONTRACT))
            # Catalog and source assertions operate on current preserved bytes.
            # Only the explicitly versioned contract module uses frozen bytes.
            (view / 'knowledge_candidates').symlink_to(ROOT / 'knowledge_candidates', target_is_directory=True)
            (view / 'evidence').symlink_to(ROOT / 'evidence', target_is_directory=True)
            original = adapter_module('coach_v1._queue_adapter_frozen', view, frozen)
            suites['historical_frozen_v1'] = run_suite(original.ExpandedAdapterTests, out, 'historical-frozen.log', 6)
        amended = adapter_module('coach_v1._queue_adapter_current', ROOT, current)
        amended_class = amended_test_class(amended, frozen, current)
        suites['current_additive_amendment'] = run_suite(amended_class, out, 'current-amendment.log', 6)
        audit = getattr(amended_class, 'amendment_audit', None)
        suites['versioned_extensions'] = run_suite(VersionedExtensionTests, out, 'versioned-extensions.log', 2)
    except Exception as error:
        errors.append(type(error).__name__ + ': ' + str(error))
    report = dict(schema_version='queue.adapter-v3-verification.v1',
                  passed=len(suites) == 3 and all(s['passed'] for s in suites.values()) and not errors,
                  frozen_commit=FROZEN_COMMIT, pinned_hashes=PINNED_HASHES,
                  amendment='docs/queue/CONTRACT_AMENDMENT_V3.md', amendment_audit=audit,
                  current_contract_sha256=sha256((ROOT / CONTRACT).read_bytes()),
                  source_sha256={path: sha256((ROOT / path).read_bytes()) for path in
                                 ('scripts/verify_queue_extensions.py',
                                  'docs/queue/CONTRACT_AMENDMENT_V3.md',
                                  'coach_v1/pregame_contract.py', 'coach_v1/pregame_v2.py',
                                  'coach_v1/pregame_v3.py', 'coach_v1/state.py',
                                  'contracts/pregame-v2.md', 'contracts/pregame-v3.md')
                                 if (ROOT / path).is_file()},
                  suites=suites, runner_errors=errors,
                  git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  github_binding={key: os.environ.get(key) for key in ['GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT']},
                  historical_source_files_unchanged=all(sha256((ROOT / path).read_bytes()) == PINNED_HASHES[path] for path in (VALIDATOR, MANIFEST)),
                  direct_current_historical_validator='NOT_CLAIMED_PASS; original whole-module byte pin applies to frozen v1 view only',
                  production_proposals=0, user_web_approvals=0,
                  coaching_accuracy=None, real_match_validation='NOT_EVALUATED')
    (out / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], evidence_directory=str(out), suites=suites, errors=errors)))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
