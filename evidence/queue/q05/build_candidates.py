"""Rebuild Q05 static, unapproved content from archived official source bytes.

This script is an evidence/content builder, not a product import or approval.
All strategic interpretations are candidates. It never invokes web decisions.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'knowledge_candidates'
SRC = ROOT / 'evidence/queue/q05/sources'
PIN = '16.20.1'
PATCH = 'SOURCE_SNAPSHOT_16.20.1_ONLY; GAME_PATCH_UNKNOWN'
URL = 'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion/'
GUIDE_URL = 'https://www.leagueoflegends.com/en-us/how-to-play/'
GOLDEN = ['Ornn', 'Sejuani', 'Ahri', 'Caitlyn', 'Lux', 'Fiora', 'LeeSin', 'Zed', 'Ezreal', 'Nautilus']
FREQUENT = ['Yunara', 'Ashe', 'Kaisa']


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def source(champion, field):
    file = SRC / f'{champion}-{PIN}.json'
    doc = json.loads(file.read_text())
    locator = f'data.{champion}.{field}'
    value = doc['data'][champion]
    for key in field.split('.'):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return dict(url=URL + champion + '.json', archive=str(file.relative_to(ROOT)),
                sha256=hashlib.sha256(file.read_bytes()).hexdigest(), locator=locator,
                excerpt=value, patch_range=PATCH, evidence_kind='OFFICIAL_STATIC_MECHANIC')


def guide(locator):
    extracts = json.loads((SRC / 'official-guide-text.json').read_text())
    value = next(x for x in extracts if x['locator'] == locator)
    file = SRC / 'official-how-to-play.html'
    return dict(url=GUIDE_URL, archive=str(file.relative_to(ROOT)),
                sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                locator='__NEXT_DATA__:' + locator, excerpt=value['text'],
                patch_range='UNVERSIONED_OFFICIAL_GUIDE; GAME_PATCH_UNKNOWN',
                evidence_kind='OFFICIAL_GENERAL_GUIDE')


def g(blade, group=None):
    return guide(f'$.props.pageProps.page.blades[{blade}].' + (
        'header.description.body' if group is None else f'groups[{group}].content.description.body'))


# Combat classes are official tags. Position is golden input context, not a
# claim about optimal/allowed lanes. Strategic labels remain kit interpretations.
# Missing fields are null: absence of a reviewed label never means "none".
PROFILES = {
 'Ornn': dict(position='TOP', threats=['dive'], protection=['frontline'], lane=['scaling'],
              facts=[('terrain_knockup','spells.2.description'),('team_item_upgrade','passive.description'),('ranged_reengage','spells.3.description')],
              limit='지형 충돌과 궁 재사용이 필요한 제어가 있다. 탱커 태그가 모든 상황의 생존이나 라인 우세를 보장하지 않는다.'),
 'Sejuani': dict(position='JUNGLE', threats=['dive','grab-pick'], protection=['frontline'], lane=None,
                 facts=[('dash_stops_on_champion','spells.0.description'),('conditional_stun','spells.2.description'),('ranged_first_champion_stun','spells.3.description'),('conditional_resistance','passive.description')],
                 limit='Q는 적 챔피언에 멈추며 E는 최대 Frost가 필요하다. 정적 설명으로 초반 갱킹 강도·청소 속도를 확정하지 않는다.'),
 'Ahri': dict(position='MID', threats=['assassination','grab-pick'], protection=None, lane=['roam'],
             facts=[('charm_stops_movement','spells.2.description'),('ultimate_mobility','spells.3.description')],
             limit='매혹은 적중해야 하며 이동 가능성은 실제 로밍 우선권·시야·궁 가용성을 증명하지 않는다.'),
 'Caitlyn': dict(position='BOT', threats=['poke','grab-pick'], protection=None, lane=['lane-pressure'],
                facts=[('ranged_attack','stats.attackrange'),('trap_root','spells.1.description'),('net_recoil','spells.2.description'),('interceptable_ultimate','spells.3.description')],
                limit='긴 기본 공격 사거리만으로 라인 승리·자동 푸시·다이브 안전을 확정하지 않는다. 덫은 밟아야 발동한다.'),
 'Lux': dict(position='SUPPORT', threats=['poke','grab-pick'], protection=['protection'], lane=['lane-pressure'],
             facts=[('two_target_root','spells.0.description'),('ally_shield','spells.1.description'),('area_slow_damage','spells.2.description')],
             limit='Q는 최대 두 유닛을 속박한다. 스킬 적중·마나·웨이브를 모르므로 라인 우세와 완전한 보호는 미확인이다.'),
 'Fiora': dict(position='TOP', threats=['dive'], protection=None, lane=None,
               facts=[('duelist_vitals','passive.description'),('dash_attack','spells.0.description'),('parry_counter_stun','spells.1.description'),('single_target_vitals','spells.3.description')],
               limit='응수는 짧은 창에 피해·제어를 막는다. 이 설명만으로 후반 우세·스플릿 속도·포탑 피해를 확정하지 않는다.'),
 'LeeSin': dict(position='JUNGLE', threats=['dive'], protection=['protection'], lane=None,
               facts=[('hit_gated_dash','spells.0.description'),('ally_dash_shield','spells.1.description'),('displacement','spells.3.description')],
               limit='Q 진입은 첫 적중과 재사용에 의존한다. 킷으로 초반 갱킹 우위·일정·실제 쿨타임을 확정하지 않는다.'),
 'Zed': dict(position='MID', threats=['assassination','dive','poke'], protection=None, lane=['roam'],
            facts=[('shadow_projectile','spells.0.description'),('shadow_swap','spells.1.description'),('target_access_delayed_mark','spells.3.description')],
            limit='암살자 태그와 대상 접근은 킬 보장이 아니다. 궁·그림자 가용성, 방어 수단, 체력, 웨이브를 별도로 확인해야 한다.'),
 'Ezreal': dict(position='BOT', threats=['poke'], protection=None, lane=None,
               facts=[('skillshot_poke','spells.0.description'),('teleport_escape','spells.2.description'),('objective_mark','spells.1.description')],
               limit='Q는 적 유닛에 맞는 투사체이며 E는 현재 가용성을 모른다. 이동기를 가진다고 항상 갱킹을 피하지 않는다.'),
 'Nautilus': dict(position='SUPPORT', threats=['grab-pick','dive'], protection=['frontline'], lane=None,
                 facts=[('pull_or_terrain_access','spells.0.description'),('first_attack_root','passive.description'),('self_shield','spells.1.description'),('targeted_tracking_cc','spells.3.description')],
                 limit='그랩은 충돌 대상과 지형에 따라 결과가 다르다. 탱커·자가 보호막은 아군 보호 성공을 보장하지 않는다.'),
 'Yunara': dict(position=None, threats=['poke'], protection=None, lane=None,
               facts=[('spread_attacks','spells.0.description'),('projectile_slow','spells.1.description'),('state_dependent_mobility','spells.2.description')],
               limit='평상시 E는 이동 속도와 Ghosted이며 변신 상태에서만 대시다. 항상 대시 가능한 원딜로 분류하면 안 된다.'),
 'Ashe': dict(position=None, threats=['poke','grab-pick'], protection=None, lane=None,
             facts=[('attack_slow','passive.description'),('scouting','spells.2.description'),('ranged_stun','spells.3.description')],
             limit='정찰 능력은 사용·정보 시점을 증명하지 않는다. 궁은 챔피언 충돌이 필요하며 적중을 보장하지 않는다.'),
 'Kaisa': dict(position=None, threats=['poke','dive'], protection=None, lane=['scaling'],
              facts=[('item_gated_upgrades','passive.description'),('long_range_projectile','spells.1.description'),('target_access','spells.3.description')],
              limit='아이템 구매에 따른 기본 스킬 강화는 직접 근거가 있지만 후반 우세는 미확인이다. 진입 가능성은 안전한 진입을 뜻하지 않는다.'),
}

roster_file = SRC / f'champion-roster-{PIN}.json'
roster_doc = json.loads(roster_file.read_text())
rows = []
for cid, champion in sorted(roster_doc['data'].items()):
    basis = dict(url=URL + '../champion.json', archive=str(roster_file.relative_to(ROOT)),
                 sha256=hashlib.sha256(roster_file.read_bytes()).hexdigest(),
                 locator=f'data.{cid}.tags', excerpt=champion['tags'], patch_range=PATCH,
                 evidence_kind='OFFICIAL_STATIC_IDENTITY_AND_TAGS')
    basis['url'] = 'https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion.json'
    row = dict(champion_id=cid, champion_key=champion['key'], name=champion['name'],
               review_state='EXPLORATORY', approval_actor=None, coaching_enabled=False,
               patch_range=PATCH, official_roles=champion['tags'], position_candidate=None,
               position_basis=None, threat_types=None, protection_types=None,
               strength_by_phase=dict(early=None, mid=None, late=None),
               lane_characteristics=None, jungle_characteristic=None,
               numeric_confidence=None, cooldowns=None, matchup_win_rate=None,
               semantic_features=[], source_refs=[basis],
               counterexamples=['공식 전투 클래스 태그는 라인 위치·승률·현재 게임 상태·전략 강도를 증명하지 않는다.'],
               limitations=['별도 킷 근거가 없는 전략 분류는 미확인(null)이다. null은 none이나 약함을 뜻하지 않는다.'])
    if cid in PROFILES:
        p = PROFILES[cid]
        row.update(position_candidate=p['position'],
                   position_basis='USER_GOLDEN_INPUT_CONTEXT' if p['position'] else None,
                   threat_types=p['threats'], protection_types=p['protection'],
                   lane_characteristics=p['lane'], classification_basis='EXPLORATORY_KIT_INTERPRETATION')
        for feature, field in p['facts']:
            ref = source(cid, field)
            row['source_refs'].append(ref)
            row['semantic_features'].append(dict(feature=feature, review_state='EXPLORATORY',
                                                  patch_range=PATCH, source_locator=ref['locator'],
                                                  source_url=ref['url'], limitations=[p['limit']]))
        row['counterexamples'].append(p['limit'])
        row['limitations'].append('키트 해석은 주요 위협의 후보이며 완전한 위협 목록·최적 역할·상대 우위를 의미하지 않는다.')
        if cid in ('Ahri','Zed'):
            row['limitations'].append('roam은 이동 기술에 기반한 가능성 후보이다. 실제 로밍 우선권은 미확인이다.')
        if cid in ('Caitlyn','Lux'):
            row['limitations'].append('lane-pressure는 사거리·원거리 피해에 기반한 가능성 후보이다. 실제 주도권은 미확인이다.')
    rows.append(row)

base = dict(format='q05-content-candidates.v1', review_state='EXPLORATORY', approval_actor=None,
            coaching_enabled=False, repository_patch=None, runtime_patch=None,
            source_snapshot_version=PIN,
            patch_policy='16.20.1 is a dated official static source snapshot; no repository or match patch is inferred.',
            provenance='Archived official HTTP responses; AI authored interpretations require real USER_WEB review.')
dump('q05-roster-profiles.json', dict(base, total_champions=len(rows), detailed_profile_ids=GOLDEN+FREQUENT,
                                    threat_vocabulary=['assassination','dive','grab-pick','poke','none'],
                                    protection_vocabulary=['protection','frontline','none'],
                                    lane_vocabulary=['lane-pressure','scaling','roam','split'],
                                    jungle_vocabulary=['early-gank','scaling'], profiles=rows))

candidates = []


def rule(cid, group, title, claim, mechanism, conditions, refs, counterexample,
         required, positions, golden_examples, priority=None, reason=None):
    # Type predicates are reviewable prose until Main supplies Q03 machine spec.
    # Champion names appear in examples only, never in rule applicability.
    item = dict(candidate_id=cid, group=group, title=title, review_state='EXPLORATORY',
                approval_actor=None, coaching_enabled=False, author='AI_Q05_EXPLORATORY',
                patch_range=PATCH, repository_patch=None, claim=claim, mechanism=mechanism,
                type_conditions=conditions, selected_positions=positions,
                required_fields=required, source_refs=refs,
                counterexamples=[counterexample],
                limitations=['정적 키트·일반 가이드에 기반한 전략 해석 후보이다. 실제 승패·현재 정보·쿨타임·행동 결과를 확정하지 않는다.',
                             '확정 경기 패치와 실제 웹 사용자 검토 없이 코칭에 활성화하지 않는다.'],
                numeric_confidence=None, success_probability=None, priority=priority,
                review_reason=reason, golden_examples=golden_examples,
                q03_structured_spec=None, evidence_kind='EXPLORATORY_TYPE_BASED_INFERENCE')
    candidates.append(item)


rule('Q05-C01','common-1','전방 제어와 지형 의존 진입',
     'frontline 유형의 지형 의존 knockup은 조합의 진입·보호 후보로 분류하되 지형·적중 조건을 함께 표시한다.',
     '공식 Tank 태그와 지형 충돌·궁 재사용 knockup 설명을 전략 타입으로 해석한다.',
     ['ally.protection_types contains frontline','ally.semantic_features contains terrain_knockup'],
     [source('Ornn','tags'),source('Ornn','spells.2.description'),source('Ornn','spells.3.description')],
     '평지에서 지형 충돌이 없거나 상대가 제어를 막으면 진입이 성립하지 않을 수 있다.',
     ['manual_patch','reviewed_profile_types','terrain_context','engage_readiness'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Ornn'],1,
     '골든 아군 전방 역할과 한타 진입 조건을 가장 먼저 확인한다.')
rule('Q05-C02','common-1','응수형 결투사',
     'duelist_vitals + parry_counter_stun 유형은 단일 대상 압박·제어 역전 위험 후보로 분류한다.',
     'Vitals·단일 대상 궁과 짧은 응수 창에서 immobilizing effect를 막으면 stun하는 설명이 근거다.',
     ['enemy.semantic_features contains duelist_vitals','enemy.semantic_features contains parry_counter_stun'],
     [source('Fiora','passive.description'),source('Fiora','spells.1.description'),source('Fiora','spells.3.description')],
     '응수가 가용하지 않거나 방향·타이밍이 맞지 않으면 제어 역전이 일어나지 않는다.',
     ['manual_patch','reviewed_profile_types','parry_readiness'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Fiora'],2,
     '골든 탑에서 핵심 제어를 무조건 성공으로 처리하는 오류를 막는다.')
rule('Q05-C03','common-1','대상 접근과 지연 폭발 암살',
     'assassination + target_access_delayed_mark 유형은 핵심 딜러 접근·지연 피해 위험 후보로 표시한다.',
     '대상에게 대시해 mark를 남기고 그동안 입힌 피해 일부를 후속 피해로 반복하는 설명에 근거한다.',
     ['enemy.threat_types contains assassination','enemy.semantic_features contains target_access_delayed_mark'],
     [source('Zed','tags'),source('Zed','spells.3.description')],
     '궁 가용성이 없거나 보호·방어 수단이 충분하면 실제 암살 위험이 달라진다.',
     ['manual_patch','reviewed_profile_types','enemy_access_readiness','carry_defensive_tools'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Zed'],3,
     '골든 미드와 원딜 보호 판단에 같은 위협 타입을 재사용한다.')
rule('Q05-L01','common-2','전방 제어 대 응수형 결투사 탑',
     'frontline 제어 대 parry_counter_stun 결투사 라인은 핵심 제어의 응수 가능성을 확인하는 조건부 아웃룩으로 제시한다.',
     'knockup과 immobilizing effect에 대한 응수 역전이 상호작용한다. 라인 승자를 선언하지 않는다.',
     ['lane is TOP','ally.protection_types contains frontline','enemy.semantic_features contains parry_counter_stun'],
     [source('Ornn','spells.2.description'),source('Fiora','spells.1.description')],
     '아이템·레벨·웨이브·응수 상태가 다르면 같은 타입에서도 교환 결과가 달라진다.',
     ['manual_patch','reviewed_profile_types','level_state','wave_state','parry_readiness'],['TOP'],['Ornn vs Fiora'],4,
     '첫 골든 탑 아웃룩을 타입 기반으로 연결한다.')
rule('Q05-L02','common-2','픽 제어 대 대상 접근 암살 미드',
     'charm_stops_movement 픽 유형 대 assassination 진입 유형은 제어 적중·방어 이동기 가용성에 따라 조건부 교환/로밍 아웃룩을 표시한다.',
     '매혹은 이동 기술을 멈출 수 있지만 암살 유형은 대상 접근·그림자 교환을 가진다.',
     ['lane is MID','ally.semantic_features contains charm_stops_movement','enemy.threat_types contains assassination'],
     [source('Ahri','spells.2.description'),source('Ahri','spells.3.description'),source('Zed','spells.1.description'),source('Zed','spells.3.description')],
     '픽 제어가 빗나가거나 궁을 쓸 수 없으면 해석이 달라진다. 이동 기술만으로 로밍 우선권을 확정하지 않는다.',
     ['manual_patch','reviewed_profile_types','cc_readiness','mobility_readiness','wave_state','vision_context'],['MID'],['Ahri vs Zed'],5,
     '골든 미드에 단정적 유불리 대신 확인할 메커니즘을 준다.')
rule('Q05-L03','common-2','포킹·속박 봇 대 그랩·이동 원딜',
     'poke + binding 봇 조합 대 grab-pick + mobile carry는 포킹 접근과 그랩 반격·원딜 이동 가용성을 함께 표시한다.',
     '사거리/원거리 피해·속박, 그랩/추적 제어, 이동 기술은 압박과 반격 양쪽 근거다.',
     ['lane is BOT','ally_bot.threat_types contains poke','ally_support.threat_types contains grab-pick','enemy_support.threat_types contains grab-pick','enemy_bot.semantic_features contains teleport_escape'],
     [source('Caitlyn','stats.attackrange'),source('Lux','spells.0.description'),source('Nautilus','spells.0.description'),source('Nautilus','spells.3.description'),source('Ezreal','spells.2.description')],
     '미니언 충돌·웨이브·시야·이동기 상태가 바뀌면 압박이 반격 노출로 바뀔 수 있다. 포킹 조합 승리를 보장하지 않는다.',
     ['manual_patch','reviewed_profile_types','wave_state','grab_readiness','carry_mobility_readiness','vision_context'],['BOT','SUPPORT'],['Caitlyn Lux vs Ezreal Nautilus'],6,
     '골든 봇 2대2를 사거리 수치만으로 자동 우세 처리하지 않는다.')
rule('Q05-J01','common-3','제어 정글 대 조건부 대시 정글',
     'CC engage jungler 대 hit_gated_dash/displacement jungler는 라인 제어 후속과 상대 진입·재진입 경로를 함께 검토한다.',
     '제어 정글의 Q는 챔피언에 멈추고 E/R은 각각 조건이 있다. 상대 Q 접근은 첫 적중이 필요하며 R은 변위를 만든다.',
     ['ally_jungle.semantic_features contains dash_stops_on_champion','enemy_jungle.semantic_features contains hit_gated_dash'],
     [source('Sejuani','spells.0.description'),source('Sejuani','spells.2.description'),source('Sejuani','spells.3.description'),source('LeeSin','spells.0.description'),source('LeeSin','spells.3.description')],
     '정글 위치·체력·웨이브가 없으면 특정 라인 갱킹 추천이나 초반 우위를 제시할 수 없다.',
     ['manual_patch','reviewed_profile_types','jungle_location','lane_wave','ally_cc_readiness','enemy_access_readiness'],['JUNGLE','TOP','MID','BOT','SUPPORT'],['Sejuani vs LeeSin'],7,
     '골든 정글 개입을 챔피언 파워 곡선의 추측 없이 설명한다.')
rule('Q05-J02','common-3','노출 라인 개입 전 확인',
     '그랩/제어 유형의 개입 후보는 라인 노출·실제 정글 위치·아군 후속 가능성이 확인될 때 검토한다.',
     '공식 가이드는 정글이 라인 사이를 다니며 방심한 상대와 중립 목표를 살핀다고 설명한다.',
     ['jungle_intervention_context is supplied','lane_control_type is known'],
     [g(8,1),source('Sejuani','spells.3.description'),source('LeeSin','spells.0.description')],
     '픽 조합만으로 적 정글 위치나 상대 방심을 추론할 수 없다.',
     ['manual_patch','reviewed_profile_types','jungle_location','lane_wave','ally_followup'],['JUNGLE','TOP','MID','BOT','SUPPORT'],['Golden all lanes'])
rule('Q05-W01','common-4','전방 진입·보호·원거리 후속 조합',
     'frontline + protection + ranged follow-up 조합의 승리 조건 후보는 제어 적중 뒤 원거리 딜러가 안전하게 후속하는 것이다.',
     '탱커 제어와 아군 보호막·원거리 공격이 함께 존재한다. 이를 조합 계획으로 해석한다.',
     ['ally_team.protection_types contains frontline','ally_team.protection_types contains protection','ally_team.official_roles contains Marksman'],
     [source('Ornn','spells.3.description'),source('Sejuani','spells.3.description'),source('Lux','spells.1.description'),source('Caitlyn','tags')],
     '진입과 보호를 동시에 쓸 수 없거나 원딜 후속 사거리가 닿지 않으면 제어 적중만으로 좋은 한타가 되지 않는다.',
     ['manual_patch','reviewed_profile_types','engage_readiness','carry_followup','protection_readiness'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Ornn Sejuani Ahri Caitlyn Lux'],8,
     '골든 아군 전체의 공동 승리 조건을 한 번에 검토한다.')
rule('Q05-W02','common-4','암살·그랩·진입에 대한 핵심 딜러 보호',
     'enemy assassination/dive/grab-pick가 함께 있을 때 핵심 딜러에게 접근하는 경로와 보호용 제어·보호막의 배분을 확인한다.',
     '대상 접근, 적중 조건 대시, 그랩/추적 제어가 원거리 딜러를 위협할 수 있다. 보호는 기계적 자동 성공이 아니다.',
     ['enemy_team.threat_types contains assassination','enemy_team.threat_types contains dive','enemy_team.threat_types contains grab-pick','ally_team.official_roles contains Marksman'],
     [source('Zed','spells.3.description'),source('LeeSin','spells.0.description'),source('Nautilus','spells.0.description'),source('Lux','spells.1.description')],
     '적 핵심 진입기가 이미 사용됐거나 다른 대상에 소모됐다면 전부를 현재 위협으로 취급하지 않는다.',
     ['manual_patch','reviewed_profile_types','enemy_access_readiness','carry_position_context','protection_readiness'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Golden enemy Zed LeeSin Nautilus'],9,
     '모든 선택 포지션이 공유할 골든 원딜 보호 조건이다.')
rule('Q05-O01','common-4','픽 이후 목표 전환은 목표 상태 확인 후',
     'pick/engage 성공 뒤 구조물·중립 목표 전환을 검토하되 웨이브·생존자·목표 가용성 정보를 요구한다.',
     '승리는 Nexus 파괴이며 구조물 경로를 열어야 한다. 공식 가이드는 중립 목표의 팀 버프와 미니언 앞세운 포탑 공격을 설명한다.',
     ['ally_team.threat_types contains grab-pick OR dive','objective_conversion_context is supplied'],
     [g(5),g(6),g(6,0),g(7)],
     '한 명을 잡았어도 남은 적·자원 부족·목표 미생성·밀리지 않은 웨이브 때문에 즉시 목표가 가능하지 않을 수 있다.',
     ['manual_patch','reviewed_profile_types','objective_availability','lane_wave','team_resources','remaining_enemies'],['TOP','JUNGLE','MID','BOT','SUPPORT'],['Golden pick/engage composition'],10,
     '골든 제어 조합이 킬 자체에서 끝나지 않도록 검토할 전환 후보이다.')

# Five role behavior candidates. These are type-conditioned, selected-role views.
role_rules = [
 ('TOP','Q05-R-TOP','전방 탑의 합류·라인 책임',
  'frontline 탑은 라인 손실과 합류 가능성을 확인한 뒤 핵심 딜러 보호/진입 역할을 선택한다.',
  ['selected_position is TOP','ally_profile.protection_types contains frontline'],[g(8,0),source('Ornn','spells.3.description')],
  '큰 웨이브나 상대 단일 대상 압박이 있으면 무조건 합류가 유리하지 않다.',
  ['manual_patch','reviewed_profile_types','lane_wave','join_path','team_engage_plan'],['Ornn']),
 ('JUNGLE','Q05-R-JUNGLE','제어 정글의 후속·목표 책임',
  'CC engage 정글은 라인 후속과 중립 목표 상태를 확인한 뒤 개입 후보를 고른다.',
  ['selected_position is JUNGLE','ally_profile.semantic_features contains ranged_first_champion_stun'],[g(8,1),source('Sejuani','spells.3.description')],
  '아군 후속이 없거나 목표가 불가능하면 제어 적중만으로 개입이 유리하지 않다.',
  ['manual_patch','reviewed_profile_types','jungle_location','ally_followup','objective_availability'],['Sejuani']),
 ('MID','Q05-R-MID','픽 미드의 이동·방어 균형',
  '픽/이동 미드는 웨이브와 시야가 허용할 때 합류를 검토하며 암살 접근에 대한 방어 이동기를 함께 고려한다.',
  ['selected_position is MID','ally_profile.semantic_features contains charm_stops_movement','enemy_team.threat_types contains assassination'],[g(8,2),source('Ahri','spells.2.description'),source('Ahri','spells.3.description')],
  '매혹/궁이 없거나 웨이브를 놓치면 같은 타입에서도 합류 판단이 바뀐다.',
  ['manual_patch','reviewed_profile_types','lane_wave','vision_context','mobility_readiness'],['Ahri']),
 ('BOT','Q05-R-BOT','포킹 원딜의 접근 안전',
  'poke 원딜은 골드·경험치 성장과 딜 후속을 목표로 하며 그랩/암살 접근 경로를 확인하고 압박한다.',
  ['selected_position is BOT','ally_profile.official_roles contains Marksman','enemy_team.threat_types contains grab-pick OR assassination'],[g(8,3),source('Caitlyn','stats.attackrange'),source('Nautilus','spells.0.description')],
  '긴 사거리도 대상 접근 궁이나 시야 밖 그랩에 대한 안전을 보장하지 않는다.',
  ['manual_patch','reviewed_profile_types','carry_position_context','enemy_access_readiness','farm_access'],['Caitlyn']),
 ('SUPPORT','Q05-R-SUPPORT','보호·속박 서포터의 스킬 배분',
  'protection + grab-pick 서포터는 픽 시도와 원딜 보호 중 현재 위험에 맞는 제어·보호막 배분을 검토한다.',
  ['selected_position is SUPPORT','ally_profile.protection_types contains protection','ally_profile.threat_types contains grab-pick'],[g(8,4),source('Lux','spells.0.description'),source('Lux','spells.1.description')],
  'Q/W를 전진 포킹에 쓴 직후에는 같은 수준의 보호가 남아 있다고 가정할 수 없다.',
  ['manual_patch','reviewed_profile_types','cc_readiness','protection_readiness','carry_position_context'],['Lux'])
]
for position,cid,title,claim,conditions,refs,counterexample,required,examples in role_rules:
    rule(cid,'role-behavior',title,claim,'공식 역할 가이드와 검증한 유형별 키트의 조합 해석이다.',
         conditions,refs,counterexample,required,[position],examples)

dump('q05-type-rules.json',dict(base,candidate_count=len(candidates),candidates=candidates))
dump('q05-review-priority.json',dict(base,recommended_review_order=[dict(
    candidate_id=c['candidate_id'],rank=c['priority'],reason=c['review_reason'],
    title=c['title'],source_urls=sorted({s['url'] for s in c['source_refs']}),
    patch_range=c['patch_range'],counterexamples=c['counterexamples'],review_state='EXPLORATORY')
    for c in candidates if c['priority'] is not None]))
print(f'Built {len(rows)} profile rows ({len(PROFILES)} detailed), {len(candidates)} type/role rules, 10 review priorities.')
