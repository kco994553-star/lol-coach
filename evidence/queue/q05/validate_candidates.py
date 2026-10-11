"""Check factual bindings and approval boundaries for Q05 content artifacts."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'knowledge_candidates'
SRC = ROOT / 'evidence/queue/q05/sources'
profiles = json.loads((OUT / 'q05-roster-profiles.json').read_text())
rules = json.loads((OUT / 'q05-type-rules.json').read_text())
priorities = json.loads((OUT / 'q05-review-priority.json').read_text())
official = json.loads((SRC / 'champion-roster-16.20.1.json').read_text())['data']
guide = {x['locator']: x['text'] for x in json.loads((SRC / 'official-guide-text.json').read_text())}

assert profiles['total_champions'] == len(profiles['profiles']) == len(official) == 173
assert {p['champion_id'] for p in profiles['profiles']} == set(official)
assert len({p['champion_id'] for p in profiles['profiles']}) == 173
assert rules['candidate_count'] == len(rules['candidates']) == 16
assert len({r['candidate_id'] for r in rules['candidates']}) == 16
assert sorted(p['rank'] for p in priorities['recommended_review_order']) == list(range(1, 11))
assert {r['selected_positions'][0] for r in rules['candidates'] if r['group'] == 'role-behavior'} == {
    'TOP', 'JUNGLE', 'MID', 'BOT', 'SUPPORT'}

refs_checked = 0
for envelope in [profiles, rules, priorities]:
    assert envelope['review_state'] == 'EXPLORATORY'
    assert envelope['coaching_enabled'] is False and envelope['approval_actor'] is None
    assert envelope['repository_patch'] is None and envelope['runtime_patch'] is None
for obj in profiles['profiles'] + rules['candidates']:
    assert obj['review_state'] == 'EXPLORATORY'
    assert obj['coaching_enabled'] is False and obj['approval_actor'] is None
    assert obj['counterexamples'] and obj['limitations'] and obj['patch_range'] and obj['source_refs']
    for ref in obj['source_refs']:
        path = ROOT / ref['archive']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == ref['sha256']
        assert ref['url'].startswith(('https://ddragon.leagueoflegends.com/', 'https://www.leagueoflegends.com/'))
        assert ref['patch_range']
        if ref['locator'].startswith('__NEXT_DATA__:'):
            assert guide[ref['locator'].removeprefix('__NEXT_DATA__:')] == ref['excerpt']
        else:
            value = json.loads(path.read_text())
            for key in ref['locator'].split('.'):
                value = value[int(key)] if isinstance(value, list) else value[key]
            assert value == ref['excerpt']
        refs_checked += 1

for p in profiles['profiles']:
    assert p['official_roles'] == official[p['champion_id']]['tags']
    assert p['champion_key'] == official[p['champion_id']]['key']
    assert p['cooldowns'] is None and p['numeric_confidence'] is None and p['matchup_win_rate'] is None
    assert all(value is None for value in p['strength_by_phase'].values())
    assert p['jungle_characteristic'] is None
unknown = [p for p in profiles['profiles'] if p['champion_id'] not in profiles['detailed_profile_ids']]
assert len(unknown) == 160
assert all(p['threat_types'] is None and p['protection_types'] is None and
           p['lane_characteristics'] is None and not p['semantic_features'] for p in unknown)
for r in rules['candidates']:
    assert r['q03_structured_spec'] is None
    assert r['numeric_confidence'] is None and r['success_probability'] is None
    assert not any(cid in condition for condition in r['type_conditions'] for cid in profiles['detailed_profile_ids'])
for receipt in json.loads((ROOT / 'evidence/queue/q05/source-receipts.json').read_text()):
    path = ROOT / receipt['file']
    assert receipt['curl_exit'] == 0 and receipt['error'] is None
    assert receipt['bytes'] == path.stat().st_size
    assert receipt['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()

report = dict(status='PASS', profile_rows=173, detailed_profiles=13, unknown_only_rows=160,
              type_rules=11, role_rules=5, review_priorities=10, source_refs_hash_and_excerpt_verified=refs_checked,
              all_exploratory=True, approval_actor=None, game_patch=None,
              strength_unknown_all=True, jungle_power_curve_unknown_all=True, cooldowns_unknown_all=True,
              verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(ROOT / 'evidence/queue/q05/content-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS:173 unique roster rows;13 detailed;16 rules;10 priorities;{refs_checked} source bindings;0 approvals.')
