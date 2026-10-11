"""Verify expanded source bindings and frozen initial profile/unknown boundaries."""
from pathlib import Path
import ast
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'evidence/queue/q05-expansion'
BASE = '9f9d9b9'
roster = json.loads((ROOT / 'knowledge_candidates/q05-roster-profiles.json').read_text())
baseline_manifest = json.loads((HERE / 'initial-source-manifest.json').read_text())
initial_bytes = (HERE / 'initial-roster.json').read_bytes()
assert hashlib.sha256(initial_bytes).hexdigest() == baseline_manifest['initial_roster_sha256']
baseline = json.loads(initial_bytes)
receipts = json.loads((HERE / 'source-receipts.json').read_text())
audit = json.loads((HERE / 'mechanic-audit.json').read_text())
official = json.loads((ROOT / 'evidence/queue/q05/sources/champion-roster-16.20.1.json').read_text())['data']
profiles = {p['champion_id']:p for p in roster['profiles']}
original = {p['champion_id']:p for p in baseline['profiles']}
assert len(roster['profiles']) == len(profiles) == len(official) == 173
assert set(profiles) == set(official)
assert len(receipts) == 160 and len({r['champion_id'] for r in receipts}) == 160
assert len(audit) == 160 and len({a['champion_id'] for a in audit}) == 160
assert set(profiles) - set(baseline['detailed_profile_ids']) == {r['champion_id'] for r in receipts}
assert all(profiles[cid] == original[cid] for cid in baseline['detailed_profile_ids'])
assert roster['repository_patch'] is None and roster['runtime_patch'] is None
assert roster['source_snapshot_version'] == '16.20.1'
assert roster['source_expansion_status'] == 'COMPLETE'
assert roster['remaining_profile_ids'] == []
assert len(roster['detailed_profile_ids']) == 173 and len(set(roster['detailed_profile_ids'])) == 173
assert len(roster['expanded_profile_ids']) == 160

# Dictionary mistakes must not silently override a manual audit exclusion.
tree = ast.parse((HERE / 'classify.py').read_text())
for node in ast.walk(tree):
    if isinstance(node,ast.Dict):
        keys = [k.value for k in node.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)]
        assert len(keys) == len(set(keys))

mechanic_refs = 0
candidate_claims = 0
for receipt in receipts:
    cid = receipt['champion_id']
    p = profiles[cid]
    assert receipt['status'] == 'SOURCE_VERIFIED' and receipt['semantic_error'] is None
    assert receipt['curl_exit'] == 0 and receipt['http_status_effective_url'].startswith('200 ')
    assert receipt['error'] is None
    assert receipt['url'] == f'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion/{cid}.json'
    timestamp = datetime.datetime.fromisoformat(receipt['retrieved_at_utc'])
    assert timestamp.utcoffset() is not None
    path = ROOT / receipt['archive']
    assert path.stat().st_size == receipt['bytes']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt['sha256']
    doc = json.loads(path.read_text())
    assert doc['version'] == '16.20.1' and set(doc['data']) == {cid}
    assert p['official_roles'] == official[cid]['tags'] == doc['data'][cid]['tags']
    assert p['position_candidate'] is None and p['position_basis'] is None
    assert p['lane_characteristics'] is None and p['jungle_characteristic'] is None
    assert all(value is None for value in p['strength_by_phase'].values())
    assert p['cooldowns'] is None and p['numeric_confidence'] is None and p['matchup_win_rate'] is None
    assert p['source_refs'][0] == original[cid]['source_refs'][0]
    new_refs = p['source_refs'][1:]
    assert len(new_refs) == 5
    assert {r['locator'] for r in new_refs} == {f'data.{cid}.passive.description', *[f'data.{cid}.spells.{i}.description' for i in range(4)]}
    for ref in new_refs:
        assert ref['url'] == receipt['url'] and ref['sha256'] == receipt['sha256']
        assert ref['retrieved_at_utc'] == receipt['retrieved_at_utc']
        assert ref['patch_range'] == 'SOURCE_SNAPSHOT_16.20.1_ONLY; GAME_PATCH_UNKNOWN'
        value = doc
        for key in ref['locator'].split('.'):
            value = value[int(key)] if isinstance(value,list) else value[key]
        assert ref['excerpt'] == value
        mechanic_refs += 1
    features = p['semantic_features']
    expected_threats = {f['candidate_label'] for f in features if f['candidate_field']=='threat_types'}
    expected_protection = {f['candidate_label'] for f in features if f['candidate_field']=='protection_types'}
    assert set(p['threat_types'] or []) == expected_threats
    assert set(p['protection_types'] or []) == expected_protection
    assert expected_threats <= {'assassination','dive','grab-pick','poke'}
    assert expected_protection <= {'protection','frontline'}
    if 'assassination' in expected_threats:assert 'Assassin' in p['official_roles'] and 'dive' in expected_threats
    if 'frontline' in expected_protection:assert 'Tank' in p['official_roles']
    for feature in features:
        ref = next(r for r in new_refs if r['locator']==feature['source_locator'])
        assert feature['source_excerpt']==ref['excerpt'] and feature['source_sha256']==ref['sha256']
        assert feature['source_url']==ref['url'] and feature['patch_range']==ref['patch_range']
        assert feature['limitations'] and feature['review_state']=='EXPLORATORY'
        candidate_claims += 1
for p in roster['profiles']:
    assert p['review_state']=='EXPLORATORY' and p['approval_actor'] is None and p['coaching_enabled'] is False
    assert p['counterexamples'] and p['limitations'] and p['patch_range']
    assert all(value is None for value in p['strength_by_phase'].values())
    assert p['jungle_characteristic'] is None and p['cooldowns'] is None
for unchanged in ['knowledge_candidates/executable-v1.json','knowledge_candidates/q05-type-rules.json',
                  'knowledge_candidates/q05-review-priority.json','evidence/queue/q05/build_candidates.py',
                  'evidence/queue/q05/validate_candidates.py','evidence/queue/q05/source-receipts.json']:
    assert hashlib.sha256((ROOT / unchanged).read_bytes()).hexdigest() == baseline_manifest['unchanged_source_sha256'][unchanged]
unknown_ids = [cid for cid in roster['expanded_profile_ids'] if profiles[cid]['threat_types'] is None and profiles[cid]['protection_types'] is None]
assert unknown_ids == roster['expanded_profiles_without_type_labels']
report = dict(status='PASS',baseline_commit=BASE,roster_rows=173,initial_profiles_unchanged=13,
              official_individual_documents_fetched=160,http_failures=[],remaining_fetch_ids=[],
              expanded_mechanic_refs_verified=mechanic_refs,exploratory_mechanic_label_claims=candidate_claims,
              expanded_profiles_with_label_candidates=160-len(unknown_ids),expanded_profiles_without_type_labels=unknown_ids,
              all_phase_strength_unknown=True,all_jungle_style_unknown=True,
              expanded_lane_style_and_positions_unknown=True,all_cooldown_arrays_unknown=True,
              executable_catalog_unchanged=True,production_proposals=0,user_web_approvals=0,
              gameplay_validation_count=0,coaching_accuracy=None,
              verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(HERE / 'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS:173 roster;13 initial profiles unchanged;160 verified documents;{mechanic_refs} mechanic refs;{candidate_claims} exploratory labels;{len(unknown_ids)} entirely unclassified expanded profiles;0 gameplay validations/approvals.')
