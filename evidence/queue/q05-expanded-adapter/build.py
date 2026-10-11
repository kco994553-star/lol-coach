"""Compile already-audited labels; never infer semantics from source prose."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import subprocess

from coach_v1.pregame_contract import parse_rule
from coach_v1.state import digest

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ROSTER=ROOT/'knowledge_candidates/q05-roster-profiles.json'
OUT=ROOT/'knowledge_candidates/executable-expanded-v1.json'
VERSION='q05-expanded-adapter-2026-10-11.v1'
TYPE_MAP={'poke':'POKE','dive':'DIVE','grab-pick':'GRAB_PICK',
          'assassination':'ASSASSINATION','protection':'PEEL','frontline':'FRONTLINE'}


def compile_profile(row):
    """Return an exact contract spec and its original, selected source records."""
    labels=set((row['threat_types'] or [])+(row['protection_types'] or []))
    locators={feature['source_locator'] for feature in row['semantic_features']}
    # Assassin/Tank tags are part of these existing candidate interpretations.
    # An unclassified profile retains identity evidence and makes no type claim.
    if not locators or labels & {'assassination','frontline'}:
        locators.add('data.'+row['champion_id']+'.tags')
    refs=[deepcopy(ref) for ref in row['source_refs'] if ref['locator'] in locators]
    assert len(refs)==len(locators)
    profile=dict(champion=row['champion_id'],roles=[],
        threats=[TYPE_MAP[label] for label in (row['threat_types'] or [])],
        protection=[TYPE_MAP[label] for label in (row['protection_types'] or [])],
        strong_when=[],lane_style=[],jungle_style=[])
    sources=[dict(url=ref['url'],title='Official Data Dragon static build16.20.1',
        locator=ref['locator'],patch='16.20.1',sha256=ref['sha256'],kind='DATA_DRAGON') for ref in refs]
    value=dict(schema_version='pregame.rule.v1',rule_id='Q05-P-'+row['champion_id'],version=VERSION,
        scope='COMMON',positions=[],patches=[],sources=sources,required_fields=['patch'],
        conditions=[],counterconditions=[],stop_conditions=[],counterexamples=deepcopy(row['counterexamples']),
        limitations=deepcopy(row['limitations']),
        output=dict(section='PROFILE',target='GLOBAL',outlook=None,text=row['counterexamples'][-1],
            alternatives=[],change_conditions=deepcopy(row['counterexamples'])),profile=profile,cooldowns=[])
    assert parse_rule(value).model_dump(mode='json')==value
    return value,refs


def compile_catalog(roster):
    rows={row['champion_id']:row for row in roster['profiles']}
    specs=[];bindings=[]
    for cid in roster['expanded_profile_ids']:
        row=rows[cid]
        spec,refs=compile_profile(row)
        specs.append(spec)
        bindings.append(dict(rule_id=spec['rule_id'],
            original_path='knowledge_candidates/q05-roster-profiles.json',
            original_locator='profiles[champion_id='+cid+']',spec_sha256=digest(spec),
            source_bindings=refs,semantic_features=deepcopy(row['semantic_features']),
            adaptation='Exact existing threat/protection candidate enums only. No semantic prose interpretation. Roles, phase strength, lane/jungle style, runtime patch and cooldowns remain unknown.'))
    return specs,bindings


if __name__=='__main__':
    roster=json.loads(ROSTER.read_text())
    specs,bindings=compile_catalog(roster)
    assert len(specs)==len({s['rule_id'] for s in specs})==160
    original_hash=hashlib.sha256(ROSTER.read_bytes()).hexdigest()
    for binding in bindings:binding['original_file_sha256']=original_hash
    OUT.write_text(json.dumps(specs,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    # Pin the actual committed input used, including source-audit corrections.
    roster_commit=subprocess.check_output(['git','log','-1','--format=%H','--','knowledge_candidates/q05-roster-profiles.json'],cwd=ROOT,text=True).strip()
    assert ROSTER.read_bytes()==subprocess.check_output(['git','show',roster_commit+':knowledge_candidates/q05-roster-profiles.json'],cwd=ROOT)
    preserved={name:hashlib.sha256(subprocess.check_output(['git','show','c8e2d2d:'+name],cwd=ROOT)).hexdigest()
               for name in ('knowledge_candidates/executable-v1.json','coach_v1/pregame_contract.py')}
    preserved['knowledge_candidates/q05-roster-profiles.json']=original_hash
    manifest=dict(schema_version='q05.expanded-adapter-evidence.v1',review_state='EXPLORATORY',
        approval_actor=None,coaching_enabled=False,input_roster_commit=roster_commit,
        preserved_files_sha256=preserved,
        original_catalog_base_commit='c8e2d2d',profile_count=160,combined_candidate_count=177,
        runtime_patch=None,source_snapshot_version='16.20.1',gameplay_patch_applicability='UNKNOWN_ALL_PATCHES_EMPTY',
        expanded_profiles_without_type_labels=roster['expanded_profiles_without_type_labels'],
        all_phase_strength_unknown=True,positions_lane_jungle_unknown=True,
        production_proposals=0,user_web_approvals=0,gameplay_validation_count=0,coaching_accuracy=None,
        catalog_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(),bindings=bindings)
    (HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print('Compiled160 exact COMMON PROFILE candidates; all game patches/cooldowns empty; no product writes.')
