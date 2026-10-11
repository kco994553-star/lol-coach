"""Conservative source-excerpt candidates; this is not a gameplay evaluator.

Text patterns only locate explicit mechanics for manual audit. They do not infer
timing, win rates, jungle strength, optimal positions, live readiness or outcomes.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'evidence/queue/q05-expansion'
ROSTER = ROOT / 'knowledge_candidates/q05-roster-profiles.json'
BASE = '9f9d9b9'
original = json.loads(subprocess.check_output(['git','show',BASE+':knowledge_candidates/q05-roster-profiles.json'],text=True))
receipts = json.loads((HERE / 'source-receipts.json').read_text())
lookup = {p['champion_id']: p for p in original['profiles']}
PIN = 'SOURCE_SNAPSHOT_16.20.1_ONLY; GAME_PATCH_UNKNOWN'
LIMITS = {
 'poke': '명시된 발사체/원거리 피해 동작에서 포킹 가능성을 해석한 후보다. 적중·실제 사거리·교환 우세·스킬 가용성은 미확인이다.',
 'grab-pick': '명시된 속박/기절/매혹/도발/끌기/제압/공중 제어/공포/수면에서 포획 가능성을 해석한 후보다. 발동·적중 조건과 가용성을 모르며 모든 제어가 그랩이라는 뜻은 아니다.',
 'dive': '명시된 적/대상 접근 또는 공격 이동 동작을 진입 가능성으로 해석한 후보다. 안전한 진입·포탑 다이브 성공·현재 가용성은 미확인이다.',
 'assassination': '공식 Assassin 태그와 적 접근 메커니즘을 함께 해석한 암살 가능성 후보다. 피해량·킬 성공·게임 단계별 강도는 미확인이다.',
 'protection': '아군에게 적용되는 회복/보호막/무적/피해 차단/방어 능력 강화 메커니즘에서 보호 가능성을 해석한 후보다. 현재 사용 가능성·조건 충족·보호 성공은 미확인이다.',
 'frontline': '공식 Tank 태그와 자가 방어/회복 메커니즘을 함께 해석한 전방 역할 후보다. 생존·현재 탱킹 능력·최적 위치는 미확인이다.'
}
FEATURES = {'poke':'projectile_damage_candidate','grab-pick':'catch_control_candidate','dive':'offensive_access_candidate',
            'assassination':'assassin_access_candidate','protection':'ally_defense_candidate','frontline':'tank_self_defense_candidate'}
MOVE = re.compile(r'\b(dash(?:es|ing)?|leap(?:s|ing)?|jump(?:s|ing)?|blink(?:s|ing)?|teleport(?:s|ing)?|lung(?:es|ing)|rush(?:es|ing))\b|\bcharg(?:es|ing) (?:toward|towards|forward|into)\b|\bcharg(?:es|ing) to (?:an? |the )?(?:enemy|target|location|point)\b|\blaunch(?:es|ing)? (?:himself|herself|itself)\b',re.I)
PROJECTILE = re.compile(r'\b(fires|firing|shoots?|shooting|throws?|hurls?|launches?|tosses?|missiles?|projectiles?|beams?|bolts?|orbs?|arrows?|shurikens?|boomerangs?|cannonballs?|rockets?|bullets?|spears?)\b|\bfire (?:a|an|the)\b',re.I)
CATCH = re.compile(r'\b(stuns?|stunned|stunning|roots?|rooted|rooting|charms?|charming|taunts?|taunting|pulls?|pulling|snares?|snaring|suppresses|suppressing|grabs?|grabbing|drags?|dragging|yanks?|yanked|hooks?|hooking|airborne)\b|\bknock(?:s|ing|ed)? (?:\w+ ){0,5}(?:up|into the air)\b',re.I)
ALLY = re.compile(r'\b(ally|allies|allied|friendly|teammates?)\b',re.I)
DEFENSE = re.compile(r'\b(shield|shields|shielding|heal|heals|healing|invulnerable|invulnerability|protects?|protection)\b',re.I)
SELF_DEFENSE = re.compile(r'\b(gains? (?:\w+ ){0,6}(?:shield|armor|armour|magic resist|health)|increas\w* (?:his |her |their )?(?:armor|magic resist|health regeneration)|heals? (?:himself|herself|itself)|damage reduction|(?:reduces?|reducing|negates?) (?:\w+ ){0,8}damage|takes? reduced damage|restor\w* (?:his |her )?(?:health|life)|recover\w* (?:his |her )?(?:health|life)|bonus health|maximum health (?:increases|increased))\b',re.I)

# Explicitly denied interpretations are populated after inspecting previews.
# A denied label does not erase its official mechanic source or declare NONE.
DENY = {
 'Akshan': [('passive.description','poke'),('spells.2.description','grab-pick')],
 'Alistar': [('passive.description','grab-pick')],
 'Braum': [('spells.1.description','dive')],
 'Briar': [('spells.2.description','dive'),('spells.2.description','assassination')],
 'Gnar': [('spells.3.description','poke')],
 'Graves': [('spells.2.description','dive')],
 'Hwei': [('spells.0.description','poke')],
 'Ivern': [('spells.0.description','dive')],
 'Jayce': [('spells.2.description','poke')],
 'Kalista': [('spells.3.description','dive'),('spells.2.description','poke')],
 'Kayle': [('spells.2.description','poke')],
 'Kindred': [('spells.2.description','poke')],
 'Lulu': [('spells.2.description','dive')],
 'Mel': [('passive.description','poke'),('spells.1.description','poke')],
 'Neeko': [('spells.3.description','dive')],
 'Qiyana': [('spells.1.description','dive'),('spells.1.description','assassination')],
 'Rammus': [('passive.description','frontline')],
 'Rumble': [('spells.1.description','grab-pick')],
 'Samira': [('spells.1.description','poke'),('passive.description','grab-pick')],
 'Sylas': [('spells.2.description','grab-pick')],
 'Teemo': [('spells.3.description','poke')],
 'Tristana': [('spells.1.description','poke'),('spells.2.description','poke')],
 'TwistedFate': [('spells.3.description','dive')],
 'Varus': [('spells.1.description','poke')],
 'Vayne': [('spells.1.description','poke')],
 'Yuumi': [('spells.1.description','dive')],
 'Zeri': [('spells.2.description','dive')],
 'Zyra': [('passive.description','grab-pick'),('spells.1.description','grab-pick')],
}
# Positive manual readings cover direct mechanics phrased outside the locator
# patterns; they add no strength/position predictions and preserve full excerpts.
ADD = {
 'Aatrox': [('spells.1.description','grab-pick')],
 'Akali': [('spells.2.description','dive'),('spells.2.description','assassination')],
 'Belveth': [('spells.0.description','dive')],
 'Braum': [('spells.1.description','protection')],
 'Darius': [('spells.0.description','frontline')],
 'Fiddlesticks': [('spells.0.description','grab-pick')],
 'Galio': [('spells.2.description','dive'),('spells.3.description','dive')],
 'Gnar': [('spells.2.description','dive')],
 'Hecarim': [('spells.3.description','grab-pick')],
 'Illaoi': [('passive.description','frontline')],
 'JarvanIV': [('spells.0.description','dive'),('spells.1.description','frontline')],
 'Lucian': [('spells.0.description','poke')],
 'Malphite': [('passive.description','frontline')],
 'Malzahar': [('spells.3.description','grab-pick')],
 'Maokai': [('passive.description','frontline')],
 'Morgana': [('spells.0.description','grab-pick'),('spells.2.description','protection')],
 'Nocturne': [('spells.2.description','grab-pick')],
 'Nunu': [('spells.0.description','frontline')],
 'Rammus': [('spells.1.description','frontline')],
 'Shen': [('passive.description','frontline'),('spells.1.description','protection'),('spells.2.description','dive')],
 'Sion': [('spells.3.description','dive')],
 'Skarner': [('spells.2.description','dive'),('spells.3.description','grab-pick')],
 'Taric': [('spells.1.description','frontline')],
 'TahmKench': [('spells.0.description','frontline')],
 'Thresh': [('spells.0.description','dive')],
 'Tristana': [('spells.1.description','dive'),('spells.1.description','assassination')],
 'Trundle': [('passive.description','frontline')],
 'Tryndamere': [('spells.2.description','dive'),('spells.2.description','assassination')],
 'Twitch': [('spells.3.description','poke')],
 'Udyr': [('spells.2.description','grab-pick')],
 'Urgot': [('spells.2.description','dive'),('spells.2.description','frontline'),('spells.2.description','grab-pick')],
 'Vi': [('spells.3.description','dive'),('spells.3.description','assassination')],
 'Viego': [('spells.3.description','dive'),('spells.3.description','assassination')],
 'Volibear': [('spells.2.description','frontline')],
 'Warwick': [('spells.3.description','dive')],
 'Zoe': [('spells.2.description','grab-pick')],
}
assert all(pair not in DENY.get(cid,[]) for cid,pairs in ADD.items() for pair in pairs)
proposals = []
for receipt in receipts:
    cid = receipt['champion_id']
    if receipt['status'] != 'SOURCE_VERIFIED':
        continue
    path = ROOT / receipt['archive']
    doc = json.loads(path.read_text())['data'][cid]
    mechanics = [('passive.description',doc['passive']['description'])] + [(f'spells.{i}.description',s['description']) for i,s in enumerate(doc['spells'])]
    facts = []
    for locator, excerpt in mechanics:
        text = html.unescape(re.sub(r'<[^>]+>',' ',excerpt))
        labels = []
        damage = bool(re.search(r'\bdamag\w*\b',text,re.I))
        if PROJECTILE.search(text) and damage and not re.search(r'\blaunch(?:es|ing) (?:himself|herself|itself)\b',text,re.I) and not (DEFENSE.search(text) and not re.search(r'\b(enemy|enemies|targets?)\b',text,re.I)):
            labels.append('poke')
        control_text = re.sub(r'\broots? (?:herself|himself|itself|themself|themselves)\b','',text,flags=re.I)
        if CATCH.search(control_text) and not re.search(r'\b(immune|immunity|tenacity)\b',text,re.I):
            labels.append('grab-pick')
        access = False
        for motion in MOVE.finditer(text):
            after = text[motion.start():motion.end()+160]
            if re.search(r'\b(dealing|damaging|deals|deal|damages|knock\w*)\b.{0,80}\b(damage|enemies|enemy|champions)\b|\b(?:to|through|toward|towards|at) (?:\w+ ){0,5}(?:enemy|enemies|target|unit)\b',after,re.I):
                access = True
        access = access and not re.search(r'\b(backward|backwards|away|retreats?|retreating)\b',text,re.I)
        if access:
            labels.append('dive')
            if 'Assassin' in doc['tags']:
                labels.append('assassination')
        if ALLY.search(text) and DEFENSE.search(text):
            labels.append('protection')
        if 'Tank' in doc['tags'] and SELF_DEFENSE.search(text):
            labels.append('frontline')
        labels = [x for x in labels if (locator,x) not in DENY.get(cid,[])]
        labels = sorted(set(labels) | {label for loc,label in ADD.get(cid,[]) if loc==locator})
        facts.append(dict(locator=locator,excerpt=excerpt,labels=labels))
    proposals.append(dict(champion_id=cid,tags=doc['tags'],facts=facts))

(HERE / 'mechanic-audit.json').write_text(json.dumps(proposals,ensure_ascii=False,indent=2)+'\n')
decisions = dict(review_state='EXPLORATORY',actor='AI_CONTENT_AUDIT_NOT_USER_WEB',approval_actor=None,
                 exclusion_count=sum(len(v) for v in DENY.values()),addition_count=sum(len(v) for v in ADD.values()),
                 exclusions=DENY,additions=ADD,
                 rationale='Patterns locate excerpts only. AI source reading excludes self/ally-only motion, self-control, energy/spell charging, enemy shield/projectile removal, names without asserted effects, and basic-attack/stack descriptions without clear poke. Explicit additional mechanics are source readings, not user approval or outcome validation.')
(HERE / 'audit-decisions.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n')
if '--apply' not in sys.argv:
    for p in proposals:
        labeled = [(f['locator'],f['labels'],re.sub('<[^>]+>',' ',f['excerpt'])) for f in p['facts'] if f['labels']]
        print(p['champion_id'],p['tags'])
        for loc,labels,text in labeled:print(' ',loc,','.join(labels),text.rstrip())
    raise SystemExit(0)

for proposal in proposals:
    cid = proposal['champion_id']
    p = lookup[cid]
    receipt = next(r for r in receipts if r['champion_id']==cid)
    all_labels = {label for fact in proposal['facts'] for label in fact['labels']}
    p['threat_types'] = [x for x in ['assassination','dive','grab-pick','poke'] if x in all_labels] or None
    p['protection_types'] = [x for x in ['protection','frontline'] if x in all_labels] or None
    p['classification_basis'] = 'EXPLORATORY_KIT_INTERPRETATION'
    p['source_expansion_status'] = 'SOURCE_VERIFIED_MECHANICS_WITH_NULL_UNSUPPORTED_LABELS'
    p['counterexamples'].append('정적 설명의 메커니즘을 유형 후보로 해석했다. 발동 조건·현재 가용성·방향·거리·상대 대응에 따라 실제 위협/보호가 달라질 수 있다.')
    p['limitations'].append('후보 라벨은 가능성의 비완전 목록이다. 미부여 라벨은 능력 부재나 NONE을 뜻하지 않으며 최적 위치·강도·실제 결과를 추정하지 않는다.')
    for fact in proposal['facts']:
        ref = dict(url=receipt['url'],archive=receipt['archive'],sha256=receipt['sha256'],
                   locator=f'data.{cid}.{fact["locator"]}',excerpt=fact['excerpt'],patch_range=PIN,
                   retrieved_at_utc=receipt['retrieved_at_utc'],evidence_kind='OFFICIAL_STATIC_MECHANIC')
        p['source_refs'].append(ref)
        for label in fact['labels']:
            p['semantic_features'].append(dict(feature=FEATURES[label],candidate_label=label,
                candidate_field='protection_types' if label in ('protection','frontline') else 'threat_types',
                review_state='EXPLORATORY',patch_range=PIN,source_locator=ref['locator'],source_url=ref['url'],
                source_sha256=ref['sha256'],source_excerpt=fact['excerpt'],limitations=[LIMITS[label]]))
    p['counterexamples'].extend(LIMITS[x] for x in ['assassination','dive','grab-pick','poke','protection','frontline'] if x in all_labels)

expanded = [r['champion_id'] for r in receipts if r['status']=='SOURCE_VERIFIED']
failed = [r['champion_id'] for r in receipts if r['status']!='SOURCE_VERIFIED']
original['initial_detailed_profile_ids'] = list(original['detailed_profile_ids'])
original['detailed_profile_ids'].extend(expanded)
original['expanded_profile_ids'] = expanded
original['remaining_profile_ids'] = failed
original['source_expansion_status'] = 'COMPLETE' if not failed else 'PARTIAL'
original['classification_expansion_status'] = 'EXPLORATORY_SPARSE_WITH_UNCONFIRMED_LABELS'
original['expanded_profiles_without_type_labels'] = [cid for cid in expanded if lookup[cid]['threat_types'] is None and lookup[cid]['protection_types'] is None]
original['expansion_baseline_commit'] = BASE
ROSTER.write_text(json.dumps(original,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(f'Applied {len(expanded)} source-verified expanded rows;remaining={failed}. Original13 profiles unchanged.')
