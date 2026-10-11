"""Validate Q03 spec parsing, exact source/text preservation and no live predicates."""
from pathlib import Path
import datetime
import hashlib
import json

from coach_v1.pregame_contract import parse_rule, proposal_rule
from coach_v1.state import digest

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / 'evidence/queue/q05-adapter'
path = ROOT / 'knowledge_candidates/executable-v1.json'
specs = json.loads(path.read_text())
manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
bindings = {b['rule_id']: b for b in manifest['bindings']}
original_profiles = json.loads((ROOT / 'knowledge_candidates/q05-roster-profiles.json').read_text())
original_rules = {r['candidate_id']: r for r in json.loads((ROOT / 'knowledge_candidates/q05-type-rules.json').read_text())['candidates']}
guide = {g['locator']: g['text'] for g in json.loads((ROOT / 'evidence/queue/q05/sources/official-guide-text.json').read_text())}
assert len(specs) == 17 and len({s['rule_id'] for s in specs}) == 17
assert len([s for s in specs if s['profile']]) == 13
assert manifest['review_state']=='EXPLORATORY' and manifest['approval_actor'] is None and manifest['coaching_enabled'] is False
assert manifest['catalog_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
source_count = 0
for spec in specs:
    parsed = parse_rule(spec)
    assert parsed.model_dump(mode='json') == spec
    assert spec['patches'] == [] and spec['cooldowns'] == []
    assert spec['counterconditions'] == [] and spec['stop_conditions'] == []
    assert proposal_rule(spec)['patch_range'] == 'UNKNOWN'  # pure binding only; no store/proposal call
    binding = bindings[spec['rule_id']]
    assert binding['spec_sha256'] == digest(spec)
    original = ROOT / binding['original_path']
    assert binding['original_file_sha256'] == hashlib.sha256(original.read_bytes()).hexdigest()
    assert len(binding['source_bindings']) == len(spec['sources'])
    if spec['profile']:
        p = next(p for p in original_profiles['profiles'] if p['champion_id'] == spec['profile']['champion'])
        assert spec['output']['text'] == p['counterexamples'][-1]
        assert spec['profile']['roles'] == [] and spec['profile']['strong_when'] == [] and spec['profile']['jungle_style'] == []
    else:
        original_rule = original_rules[spec['rule_id']]
        assert spec['output']['text'] == original_rule['claim']
        assert spec['output']['change_conditions'] == original_rule['counterexamples']
        assert spec['counterexamples'] == original_rule['counterexamples']
        assert spec['limitations'][:-1] == original_rule['limitations']
    for source, ref in zip(spec['sources'],binding['source_bindings']):
        archived = ROOT / ref['archive']
        assert source['url'] == ref['url'] and source['locator'] == ref['locator']
        assert source['sha256'] == ref['sha256'] == hashlib.sha256(archived.read_bytes()).hexdigest()
        assert source['patch'] == ('16.20.1' if source['kind']=='DATA_DRAGON' else None)
        if ref['locator'].startswith('__NEXT_DATA__:'):
            assert guide[ref['locator'].removeprefix('__NEXT_DATA__:')] == ref['excerpt']
        else:
            value = json.loads(archived.read_text())
            for key in ref['locator'].split('.'):
                value = value[int(key)] if isinstance(value,list) else value[key]
            assert value == ref['excerpt']
        source_count += 1
    if spec['profile'] is None:
        for predicate in spec['conditions']:
            assert not any(p['champion_id'] in str(predicate['value']) for p in original_profiles['profiles'])
for receipt in json.loads((EVIDENCE / 'source-receipts.json').read_text()):
    if receipt['curl_exit'] == 0:
        source_path = ROOT / receipt['file']
        assert source_path.stat().st_size == receipt['bytes']
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == receipt['sha256']
    else:
        assert receipt['curl_exit'] == 22 and receipt['result'].startswith('404 ')
report = dict(status='PASS', valid_specs=17, profile_specs=13, common_specs=2, position_specs=2,
              source_bindings_verified=source_count, exact_original_claims_preserved=True,
              all_patch_scopes_empty=True, cooldowns_empty_all=True, production_proposals=0,
              user_web_approvals=0, production_runs=0,
              verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(EVIDENCE / 'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS:17 strict RuleSpecs;{source_count} original source/excerpt bindings;all patches/cooldowns empty;0 proposals/approvals/runs.')
