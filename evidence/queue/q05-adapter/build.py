"""Adapt committed Q05 source content to Q03 without broadening its claims."""
from pathlib import Path
import hashlib
import json

from coach_v1.pregame_contract import parse_rule
from coach_v1.state import digest

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'knowledge_candidates/executable-v1.json'
EVIDENCE = ROOT / 'evidence/queue/q05-adapter'
PROFILES_PATH = ROOT / 'knowledge_candidates/q05-roster-profiles.json'
RULES_PATH = ROOT / 'knowledge_candidates/q05-type-rules.json'
PROFILES = json.loads(PROFILES_PATH.read_text())
RULES = {r['candidate_id']: r for r in json.loads(RULES_PATH.read_text())['candidates']}
VERSION = 'q05-adapter-2026-10-11.v1'
MAPPING_LIMIT = 'Data Dragon16.20.1 정적 빌드와 실제 경기 패치의 적용 관계는 미확인이다. patches=[]는 승인 가능한 패치 범위를 뜻하지 않는다.'
TYPE_MAP = {'assassination': 'ASSASSINATION', 'dive': 'DIVE', 'grab-pick': 'GRAB_PICK',
            'poke': 'POKE', 'none': 'NONE', 'protection': 'PEEL', 'frontline': 'FRONTLINE',
            'lane-pressure': 'PRESSURE', 'scaling': 'SCALING', 'roam': 'ROAM', 'split': 'SPLIT'}
bindings = []
specs = []


def source(ref):
    # Preserve the exact source's static revision, not an assumed game patch.
    # The RuleSpec patches list remains empty and Source.patch is not a runtime fact.
    dd = ref['url'].startswith('https://ddragon.leagueoflegends.com/')
    return dict(url=ref['url'], title='Official Data Dragon static build16.20.1' if dd else 'Official League of Legends how-to-play guide (unversioned)',
                locator=ref['locator'], patch='16.20.1' if dd else None,
                sha256=ref['sha256'], kind='DATA_DRAGON' if dd else 'OFFICIAL')


def add(rule_id, scope, positions, sources, required, conditions, counterexamples,
        limitations, section, target, text, change_conditions, profile, original_path,
        original_locator, adaptation):
    value = dict(schema_version='pregame.rule.v1', rule_id=rule_id, version=VERSION,
                 scope=scope, positions=positions, patches=[], sources=[source(s) for s in sources],
                 required_fields=required, conditions=conditions, counterconditions=[], stop_conditions=[],
                 counterexamples=counterexamples, limitations=limitations + [MAPPING_LIMIT],
                 output=dict(section=section, target=target,
                             outlook='UNKNOWN' if section in ('MAP','JUNGLE','COMPOSITION','LANE') else None,
                             text=text, alternatives=[], change_conditions=change_conditions),
                 profile=profile, cooldowns=[])
    parsed = parse_rule(value).model_dump(mode='json')
    assert parsed == value
    specs.append(value)
    bindings.append(dict(rule_id=rule_id, original_path=str(original_path.relative_to(ROOT)),
                         original_file_sha256=hashlib.sha256(original_path.read_bytes()).hexdigest(),
                         original_locator=original_locator, spec_sha256=digest(value),
                         source_bindings=sources, adaptation=adaptation))


for p in PROFILES['profiles']:
    if p['champion_id'] not in PROFILES['detailed_profile_ids']:
        continue
    # Official combat classes do not have a Position-enum equivalent. The golden
    # position candidate is declared input context, not an official role claim.
    profile = dict(champion=p['champion_id'], roles=[],
                   threats=[TYPE_MAP[x] for x in (p['threat_types'] or [])],
                   protection=[TYPE_MAP[x] for x in (p['protection_types'] or [])],
                   strong_when=[], lane_style=[TYPE_MAP[x] for x in (p['lane_characteristics'] or [])],
                   jungle_style=[])
    add('Q05-P-' + p['champion_id'], 'COMMON', [], p['source_refs'], ['patch'], [],
        p['counterexamples'], p['limitations'], 'PROFILE', 'GLOBAL',
        p['counterexamples'][-1], p['counterexamples'], profile, PROFILES_PATH,
        f'profiles[champion_id={p["champion_id"]}]',
        'Only existing threat/protection/lane candidate labels map to contract enums. Roles, timing strength and jungle curve remain unknown/empty. Original profile limit is displayed verbatim; exact mechanic excerpts/locators remain in source bindings.')


def predicate(field, op, value):
    return dict(field=field, op=op, value=value)


# Existing exact conditional prose remains in output/change_conditions. Live
# readiness, hp, wave, location and objective values are never executable fields.
MAPPINGS = [
    dict(cid='Q05-J02', scope='COMMON', positions=[], section='JUNGLE', target='JUNGLE',
         required=['patch','ally.threats','ally.JUNGLE.champion'],
         conditions=[predicate('ally.threats','HAS','GRAB_PICK')],
         reason='The original grab/control intervention candidate becomes an allied aggregate catch-type predicate. Declared allied jungle identity is required; live lane exposure/location/follow-up remain unachieved conditional prose.'),
    dict(cid='Q05-O01', scope='COMMON', positions=[], section='COMPOSITION', target='GLOBAL',
         required=['patch','ally.threats'],
         conditions=[predicate('ally.threats','INTERSECTS',['GRAB_PICK','DIVE'])],
         reason='Exact original OR catch/engage type guard maps to INTERSECTS. Objective conversion context is not observable in InputDraft and remains verbatim conditional prose.'),
    dict(cid='Q05-R-TOP', scope='POSITION', positions=['TOP'], section='ROLE', target='SELF',
         required=['patch','my.position','ally.TOP.protection'],
         conditions=[predicate('my.position','EQ','TOP'),predicate('ally.TOP.protection','HAS','FRONTLINE')],
         reason='Exact selected TOP and allied frontline conditions. No lane wave/join-path/engage-state input is fabricated.'),
    dict(cid='Q05-R-SUPPORT', scope='POSITION', positions=['SUPPORT'], section='ROLE', target='SELF',
         required=['patch','my.position','ally.SUPPORT.protection','ally.SUPPORT.threats'],
         conditions=[predicate('my.position','EQ','SUPPORT'),predicate('ally.SUPPORT.protection','HAS','PEEL'),
                     predicate('ally.SUPPORT.threats','HAS','GRAB_PICK')],
         reason='Exact selected SUPPORT, protection and catch-type conditions; protection enum maps to PEEL. Current cc/shield readiness and carry location remain conditional prose.')
]
for mapping in MAPPINGS:
    r = RULES[mapping['cid']]
    add(r['candidate_id'], mapping['scope'], mapping['positions'], r['source_refs'],
        mapping['required'], mapping['conditions'], r['counterexamples'], r['limitations'],
        mapping['section'], mapping['target'], r['claim'], r['counterexamples'], None,
        RULES_PATH, f'candidates[candidate_id={r["candidate_id"]}]', mapping['reason'])

omitted = {
    'Q05-C01': 'terrain_knockup mechanic feature is not an executable field; FRONTLINE alone does not establish terrain-dependent knockup.',
    'Q05-C02': 'duelist_vitals and parry_counter_stun features are not executable; DIVE does not establish a parry.',
    'Q05-C03': 'target_access_delayed_mark is not executable; ASSASSINATION alone does not establish a delayed mark.',
    'Q05-L01': 'parry_counter_stun is not executable; enemy DIVE cannot substitute for parry.',
    'Q05-L02': 'charm_stops_movement is not executable; GRAB_PICK cannot substitute for movement-stopping charm.',
    'Q05-L03': 'teleport_escape and binding features are not executable; POKE cannot substitute for a mobile carry.',
    'Q05-J01': 'dash_stops_on_champion and hit_gated_dash features are not executable; DIVE cannot establish these exact access mechanics.',
    'Q05-W01': 'official combat-class Marksman predicate is not executable. POKE or BOTTOM cannot certify that combat class; no guard is silently removed.',
    'Q05-W02': 'official combat-class Marksman predicate is not executable. BOTTOM assignment is not a combat-class assertion.',
    'Q05-R-JUNGLE': 'ranged_first_champion_stun feature is not executable; GRAB_PICK also includes roots/charm/pulls and cannot establish this exact feature.',
    'Q05-R-MID': 'charm_stops_movement feature is not executable; generic GRAB_PICK/ROAM would broaden the original predicate.',
    'Q05-R-BOT': 'official combat-class Marksman predicate is not executable; a BOTTOM position or POKE label cannot replace it.'
}
assert set(omitted) | {m['cid'] for m in MAPPINGS} == set(RULES)
assert not set(omitted) & {m['cid'] for m in MAPPINGS}
assert len(specs) == 17
OUT.write_text(json.dumps(specs, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
manifest = dict(schema_version='q05.adapter-evidence.v1', review_state='EXPLORATORY',
                approval_actor=None, coaching_enabled=False, original_content_commit='501255d9ac4aef689b6831adcdbdba93bb3bc4e9',
                q03_contract_origin_commit='627c77a', candidate_count=len(specs), profile_count=13,
                common_rule_count=2, position_rule_count=2, runtime_patch=None,
                executable_patch_applicability='UNKNOWN_ALL_PATCHES_EMPTY', source_snapshot_version='16.20.1',
                binding_count=len(bindings), bindings=bindings, omitted_candidates=omitted,
                unfilled_personal_sections=dict(ROLE=['JUNGLE','MID','BOTTOM'],LANE=['TOP','JUNGLE','MID','BOTTOM','SUPPORT'],
                                               FIGHT=['TOP','JUNGLE','MID','BOTTOM','SUPPORT']),
                catalog_sha256=hashlib.sha256(OUT.read_bytes()).hexdigest())
(EVIDENCE / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(f'Built {len(specs)} exact-contract candidates:13 profiles,2 common rules,2 role rules;12 incompatible source rules omitted.')
