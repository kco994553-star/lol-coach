# Caitlyn + Lux vs Kai’Sa + Nautilus: retained mechanism audit

This is a source audit for the existing six milestone rows. It does not author a lane plan, change the Loading MVP, validate a matchup advantage, or authorize collection. New tactical interpretations remain `DESIGN_HYPOTHESIS`; real coaching N=0, accuracy=null. All sources/history/grades and protected decisions are preserved. Network/provider/video/game calls, source refreshes, old test reruns and protected issue writes: 0.

The archived source build is16.20.1; actual game-patch applicability is unknown without observed match context. Exact machine quotes, locators and hashes are in `mechanism-audit.json`.

## Findings that constrain the six rows

- Nautilus Q: retained description and full tooltip describe enemy/terrain hits; neither explicitly defines minion collision, first-unit stopping, hitbox width, or behind-minion safety. A wave is not source-proven immunity.
- Lux Q binds at most two enemy units; full tooltip says the first two hit. A single minion is not a general projectile shield. Lux Q→Caitlyn W is an untested timing/contact hypothesis, not a guaranteed chain.
- Kai’Sa R: current `official:Kaisa:R` is abbreviated. The same retained full tooltip explicitly requires a Plasma-marked enemy champion and grants a shield. Any use of those details needs the tooltip locator, not attribution to the short description alone.
- Nautilus passive roots on basic-attack contact; Q tooltip adds a brief stun; R tracks an enemy champion and can knock up/stun other enemies hit. Q missing does not establish that every engage tool is gone.
- Lux W shields allies touched by the wand on outbound/return paths; E reveals its area per tooltip. Neither proves contact, survival, complete brush visibility, or hidden enemy positions.
- Caitlyn trap requires actual trigger; net recoil does not prove escape from CC. R can be intercepted by an enemy champion. Trap description and tooltip use different reveal/root duration wording; do not merge the1.5-second description with3-second true-sight tooltip into one duration.
- Item text supports stats/costs/effects, not an optimal first item, win threshold, relative power reversal, or Kai’Sa evolution at one completed item. QSS explicitly excludes airborne CC; World Atlas has an empty official description.

## Source inventory

| Source ID | Retained path | SHA256 |
| --- | --- | --- |
| `retained:champion:Caitlyn` | `data/official_catalog/versions/16.20.1/Caitlyn-16.20.1.ko_KR.json` | `d3215fc64246d7014dbd924cf1b76620756f84184c01191f0f6ffa65c3625029` |
| `retained:champion:Lux` | `data/official_catalog/versions/16.20.1/Lux-16.20.1.ko_KR.json` | `93a8e2062496941166b55bea23541f428ac6f1511c8c15c2eb2a8efcc5f93d9b` |
| `retained:champion:Kaisa` | `data/official_catalog/versions/16.20.1/Kaisa-16.20.1.ko_KR.json` | `98544004fbc81a31b38a8856c301b5434e7881bb05fd4ec708dabb0827214ed3` |
| `retained:champion:Nautilus` | `data/official_catalog/versions/16.20.1/Nautilus-16.20.1.ko_KR.json` | `87cf8bdca7e108fc7214c921715298e04a350bca1d619a8aa8c0ab0450e7ce32` |
| `retained:items` | `data/official_items/versions/16.20.1/item.ko_KR.json` | `8fd60c77bddc212fd1550850f0db01caa68c05c9f11e377d52df03a9627f8085` |
| `context:loading-data` | `web_r4/loading-data.json` | `923c57741d552d28e2be5b07329617c3b219ac9f4b79637ce3f22e2d735368b1` |
| `context:agents` | `AGENTS.md` | `8a3991710fc377a3d5d6b634635fdb513e248731045d2b2385c4dd356a268450` |
| `context:handoff` | `CURRENT_HANDOFF.md` | `9f798d0f8fe56a04d6a8abca130bee48636fc27aadd92164871c8946f9a96b62` |
| `context:contract` | `contracts/loading-strategy-v1.md` | `3c16cca8ca673c2307659ee6c63395b7530a8dea3a30b08828341ce8034f24ab` |
| `manifest:champions` | `data/official_catalog/versions/16.20.1/manifest.json` | `e61307d1acf1f8b27e66dd144b4136384dda35451a22e932a307e06c8885c406` |
| `manifest:items` | `data/official_items/versions/16.20.1/manifest.json` | `d7b89641deccbf91e076386a3bc60a4065e4edce35293fc65238d5686dd738ee` |
| `queue:expert-channels` | `config/expert_channels.json` | `d6d2ae9e5a27dbe07527d3f1d757fd1777836a018ecaa5e57d8ded74c6101af8` |
| `queue:pov-channels` | `config/pov_channels.json` | `7e937fce0a48ed3e772c9936e6eccbf6b7d178c7f60faccb6bc4249e365d1ecb` |
| `queue:pov-metadata` | `data/pov_metadata/2026-10-16/pov-metadata.json` | `9ece66abdb0b71613a68c0a98cffbe8de4c43c03b745ffa263158e76990e92b5` |
| `queue:pov-binding` | `data/pov_metadata/2026-10-16/metadata-binding.json` | `0a54e26f3dc4b4936dac026690c897574e6558052abc2cbe7b7cd38397145461` |
| `queue:pov-discovery` | `evidence/actual-evidence/pov-public-investigation.json` | `9acd6c2cbe783483f8c98acc75a0c3fa9bde4d7e1250bd6d00cf28eea3f5d868` |
| `queue:expert-readiness` | `evidence/actual-evidence/video-step-diagnostic/resume-20261017/expert-report-readiness.json` | `887796f7f65c634d95c9185807307bb8b575789086e8fcb9a426a48b8a2bc409` |
| `queue:items-summary` | `evidence/queue/v23/items-source-summary.json` | `89c62990ce4abac66012027519fb9dd65edb096859bb86e41868d141582a0cc6` |
| `queue:overview` | `docs/queue/QUEUE.md` | `e1233ea8a9f72fc9ca338e4a479a2a87ab9a58e758895e1b0465077a77d62130` |
| `queue:quality-import` | `data/coaching_quality/2026-10-16/import-receipt.json` | `38762dc30d526483a7a0fe4e9c981057b204e5a07da50d0aa50824adb38e02a2` |

## Official P/Q/W/E/R scope

The20existing Korean descriptions match the retained official bytes exactly. These are factual mechanism references; actual skill learned/rank, mana, cooldown, hit, relative positions and follow-up are not observed.

| Fact ID | Exact retained description | Supported limit |
| --- | --- | --- |
| `official:Caitlyn:P` | 케이틀린은 덫 또는 투망에 걸린 대상을 공격할 때나 일정 횟수 이상의 기본 공격을 했을 때 헤드샷을 발사하여 치명타 확률에 비례한 추가 피해를 입힙니다. 덫에 걸리거나 투망에 맞은 대상에게는 케이틀린의 헤드샷 공격 사거리가 두 배가 됩니다. | No guaranteed trap/net hit, Headshot readiness, damage amount, safe attack opportunity, or lane advantage. |
| `official:Caitlyn:Q` | 케이틀린이 소총을 1초 동안 조준한 후 관통하는 탄환을 발사하여 물리 피해를 입힙니다. (다음 명중하는 대상에게는 더 낮은 피해가 들어갑니다.) | No guaranteed waveclear/priority or hit; exact damage and animation interaction are not supplied by this description. |
| `official:Caitlyn:W` | 케이틀린이 함정을 설치합니다. 함정이 발동하면 함정에 걸린 적 챔피언은 1.5초간 모습이 드러나며 이동할 수 없게 되고, 케이틀린의 헤드샷이 강화됩니다. | A trap must trigger; placement does not guarantee contact or a Lux-to-trap chain. Description mentions1.5seconds for reveal/immobilize, while tooltip separately says3seconds true sight and leaves rootduration unresolved: do not conflate the two durations. |
| `official:Caitlyn:E` | 케이틀린이 무거운 그물을 발사하여 적을 느리게 합니다. 그 반동으로 케이틀린은 뒤로 밀려납니다. | No guarantee of escaping Nautilus Q/R, immunity to CC, wall traversal, or correct recoil direction in a concrete position. |
| `official:Caitlyn:R` | 케이틀린이 공을 들인 완벽한 사격을 하여 먼 거리에서 하나의 대상에게 큰 피해를 입힙니다. 적 챔피언이 자신의 아군을 위해 총알을 막아낼 수 있습니다. | No guaranteed kill or uninterrupted shot; Nautilus can be an interceptor only conditionally on actual position/contact, never from pick alone. |
| `official:Lux:P` | 럭스의 공격 스킬은 몇 초 동안 적을 빛의 에너지로 가득 채웁니다. 럭스의 기본 공격으로 이 에너지를 불태우면 적은 럭스의 레벨에 비례하는 추가 마법 피해를 받습니다. | No guaranteed passive proc: ability contact and Lux basic attack opportunity remain conditions. |
| `official:Lux:Q` | 럭스가 빛의 구를 발사하여 최대 2명의 적 유닛을 속박하며 피해를 입힙니다. | One intervening minion is not established as complete protection. This is not a general projectile-block rule and does not prove a guaranteed Caitlyn trap follow-up. |
| `official:Lux:W` | 럭스가 마법봉을 던져 아군 주변의 빛을 구부리며 적의 공격으로부터 보호해줍니다. | Ally proximity alone does not guarantee wand contact, shield timing, amount, survival, or CC removal. |
| `official:Lux:E` | 지정한 지역에 뒤틀린 빛의 구체를 띄워 주변 적의 속도를 늦춥니다. 럭스는 이 빛을 폭발시켜 피해를 입힐 수 있습니다. | No guaranteed target hit or full brush/hidden-position knowledge beyond the revealed area; no mandatory poke-versus-wave decision is proved. |
| `official:Lux:R` | 럭스가 에너지를 모아 빛 기둥을 발사하며 목표 지역에 있는 모든 대상에게 피해를 입힙니다. 또한 이는 럭스의 기본 지속 효과 스킬을 발동시키고 광채 효과의 지속시간을 갱신합니다. | No guaranteed kill, hit, full combo damage, or minion-blocking rule. |
| `official:Kaisa:P` | 카이사는 기본 공격으로 플라즈마 중첩을 쌓아 그에 따른 추가 마법 피해를 입힙니다. 아군의 이동 불가 효과가 적에게 적용됐을 때에도 플라즈마 중첩이 쌓입니다. 살아있는 무기 효과는 카이사가 구입하는 아이템에 따라 스킬을 강화시킵니다. | No guaranteed ally CC contact, Plasma detonation damage, evolution state, item threshold reached, or late-game superiority. |
| `official:Kaisa:Q` | 카이사가 근처 적들을 추격하는 미사일 세례를 퍼붓습니다. / 살아있는 무기: 이케시아 폭우가 발사하는 미사일 개수가 증가합니다. | No exact distribution/isolation damage, wave priority, or winning isolated trade follows from description; tooltip says repeated hits on the same champion/monster deal reduced damage and still has dynamic placeholders. |
| `official:Kaisa:W` | 카이사가 장거리 광선을 발사하며, 광선에 적중한 적에게 플라즈마 중첩이 쌓입니다. / 살아있는 무기: 공허추적자 적중 시 플라즈마 중첩이 추가로 쌓이며 챔피언에게 적중 시 재사용 대기시간이 감소합니다. | Hit and evolution are conditions; no guaranteed mark, follow-up, reset, or generic minion-blocking rule from description. |
| `official:Kaisa:E` | 카이사의 이동 속도가 잠시 동안 증가한 뒤 공격 속도가 증가합니다. / 살아있는 무기: 고속 충전을 사용하면 잠시 투명 상태가 됩니다. | Normal E does not imply invisibility; no guaranteed escape, chase success, or evolution at a fixed item count. |
| `official:Kaisa:R` | 카이사가 적 챔피언 근처로 돌진합니다. | Do not present R as an unconditional dash to any champion. Learned/ready, mana, actual mark, range, chosen destination, and safety are not observed. |
| `official:Nautilus:P` | 노틸러스가 대상에 대한 첫 기본 공격 시 추가 물리 피해를 입히고 잠시 속박합니다. | No contact or guaranteed CC chain; per-target reset duration is not specified in this description. |
| `official:Nautilus:Q` | 노틸러스가 전방으로 닻을 던집니다.  닻이 적을 맞히면 노틸러스와 대상이 가까이 당겨지며 대상에게 마법 피해를 입힙니다. 닻이 지형을 맞히면 노틸러스가 지형 쪽으로 끌려갑니다. | Neither retained description nor tooltip explicitly defines minion collision, first-unit stop, hook width, wall-edge priority, or behind-minion safety. No source-backed claim that a wave makes this lane safe. |
| `official:Nautilus:W` | 노틸러스가 잠시 보호막을 얻습니다. 보호막이 지속되는 동안 노틸러스의 기본 공격은 대상과 대상 주위의 적에게 지속 피해를 입힙니다. | No invulnerability, CC immunity, poke immunity, guaranteed all-in survival, or actual shield readiness. |
| `official:Nautilus:E` | 노틸러스가 주위에 세 번의 폭발을 일으킵니다. 폭발할 때마다 적에게 피해를 입히고 둔화시킵니다. | No guaranteed three hits, chase success, exact overlap damage, or waveclear timing. |
| `official:Nautilus:R` | 지면에 충격파를 발사하면 상대방을 추적해 갑니다. 충격파는 위의 지면을 찢으며 적들을 공중으로 띄웁니다. 충격파가 상대방에게 닿으면 폭발하여 대상을 공중으로 띄우고 기절시킵니다. | No source-backed minion-blocking safety, Q-miss removal of all engage tools, guaranteed interruptibility, target readiness, or successful follow-up. |

## Additive retained tooltip fields

These16tooltip fields are already in the same official source files; they are not separate facts in Loading at audit intake. Dynamic template values remain unresolved. Main owns any fact binding.

| Audit reference | Locator | Exact retained tooltip |
| --- | --- | --- |
| `audit:Caitlyn:Q:tooltip` | `data.Caitlyn.spells.0.tooltip` | 케이틀린이 조준한 후 적을 관통하는 총알을 발사하여 <physicalDamage>{{ initialdamage }}의 물리 피해</physicalDamage>를 입힙니다. 첫 번째 대상에게 적중한 후에는 탄도체 유효 범위가 넓어지며 <physicalDamage>{{ secondarydamage }}의 물리 피해</physicalDamage>를 입힙니다.<br /><br /><spellName>요들잡이 덫</spellName> 때문에 위치가 드러난 적은 항상 100%의 피해를 입습니다.{{ spellmodifierdescriptionappend }} |
| `audit:Caitlyn:W:tooltip` | `data.Caitlyn.spells.1.tooltip` | 케이틀린이 덫을 설치하여 처음 밟는 적을 {{ rootduration }}초 동안 <status>속박</status>하고 3초 동안 해당 적에 대한 <keywordStealth>절대 시야</keywordStealth>를 얻습니다. 덫은 {{ trapduration }}초 동안 지속되며 한 번에 {{ maximumtraps }}개까지 설치할 수 있습니다. 이 스킬은 {{ maximumcharges }}회까지 충전됩니다. ({{ ammorechargetime }}초마다 충전)<br /><br />이 스킬에 의해 속박된 대상은 <keywordMajor>헤드샷</keywordMajor>으로 <physicalDamage>{{ headshotbonusdamage }}의 물리 피해</physicalDamage>를 추가로 입습니다.{{ spellmodifierdescriptionappend }} |
| `audit:Caitlyn:E:tooltip` | `data.Caitlyn.spells.2.tooltip` | 케이틀린이 투망을 발사하여 처음으로 적중한 적을 {{ slowduration }}초 동안 {{ slowamount }}% <status>둔화</status>시키고 <magicDamage>{{ netdamage }}의 마법 피해</magicDamage>를 입힙니다. 케이틀린은 뒤로 밀려납니다.{{ spellmodifierdescriptionappend }} |
| `audit:Caitlyn:R:tooltip` | `data.Caitlyn.spells.3.tooltip` | 케이틀린이 잠시 정신을 집중하고 공을 들인 완벽한 사격을 하여 <physicalDamage>{{ rtotaldamage }}의 물리 피해</physicalDamage>를 입힙니다. 다른 적 챔피언이 총알을 대신 맞을 수도 있습니다. 정신을 집중하는 동안 대상에 대한 <keywordStealth>절대 시야</keywordStealth>를 얻습니다.<br /><br /><rules>피해량은 케이틀린의 치명타 확률 및 치명타 피해량에 비례합니다.</rules>{{ spellmodifierdescriptionappend }} |
| `audit:Lux:Q:tooltip` | `data.Lux.spells.0.tooltip` | 럭스가 빛의 구체를 발사하여 처음 적중한 적 둘을 {{ rootduration }}초 동안 <status>속박</status>하고 각각 <magicDamage>{{ totaldamagett }}의 마법 피해</magicDamage>를 입힙니다.{{ spellmodifierdescriptionappend }} |
| `audit:Lux:W:tooltip` | `data.Lux.spells.1.tooltip` | 럭스가 마법봉을 던져 봉에 닿은 모든 아군에게 {{ shieldduration }}초 동안 <shield>{{ totalshieldtt }}의 피해를 흡수하는 보호막</shield>을 씌웁니다. 마법봉은 돌아올 때도 똑같이 <shield>보호막</shield>을 부여합니다.{{ spellmodifierdescriptionappend }} |
| `audit:Lux:E:tooltip` | `data.Lux.spells.2.tooltip` | 럭스가 빛의 영역을 생성해 적들을 {{ slowpercent }}% <status>둔화</status>시키고 해당 지역을 드러냅니다. {{ slowzoneduration }}초가 지나거나 스킬을 <recast>재사용</recast>하면 폭발하며 <magicDamage>{{ totaldamagett }}의 마법 피해</magicDamage>를 입히고 추가로 {{ slowlingerduration }}초 동안 <status>둔화</status>시킵니다.{{ spellmodifierdescriptionappend }} |
| `audit:Lux:R:tooltip` | `data.Lux.spells.3.tooltip` | 럭스가 눈부신 광선을 발사하여 일직선상에 있는 모든 적에게 <magicDamage>{{ totaldamage }}의 마법 피해</magicDamage>를 입힙니다.{{ spellmodifierdescriptionappend }} |
| `audit:Kaisa:Q:tooltip` | `data.Kaisa.spells.0.tooltip` | 카이사가 근처 적들을 추격하는 미사일을 {{ e2 }}개 발사하며, 적중한 적에게 각각 <physicalDamage>{{ totalindividualmissiledamage }}의 물리 피해</physicalDamage>를 입힙니다. (최대 {{ maxdamagedisplay }}) 이미 미사일에 맞은 적 챔피언 또는 몬스터에게 추가 적중할 경우 {{ extrahitreduction*100 }}%의 피해를 입힙니다.<br /><br /><keywordMajor>진화 시</keywordMajor>: 미사일을 {{ e7 }}개 발사합니다.<br />현재: <physicalDamage>추가 공격력 {{ f11.1 }}/{{ e6 }}</physicalDamage>{{ spellmodifierdescriptionappend }} |
| `audit:Kaisa:W:tooltip` | `data.Kaisa.spells.1.tooltip` | 카이사가 공허 에너지 광선을 발사해 <magicDamage>{{ totaldamage }}의 마법 피해</magicDamage>를 입히고 <keywordMajor>플라즈마</keywordMajor> 중첩을 {{ e4 }}회 적용하며, {{ spell.kaisapassive:pduration }}초 동안 처음으로 적중한 적에 대한 <keywordStealth>절대 시야</keywordStealth>를 얻습니다.<br /><br /><keywordMajor>진화 시</keywordMajor>: <keywordMajor>플라즈마</keywordMajor> 중첩을 {{ e5 }}회 적용합니다. 챔피언 적중 시 재사용 대기시간이 {{ e3 }}% 감소합니다.<br />현재: <scaleAP>주문력 {{ f2.1 }}/{{ e2 }}</scaleAP>{{ spellmodifierdescriptionappend }} |
| `audit:Kaisa:E:tooltip` | `data.Kaisa.spells.2.tooltip` | 카이사가 공허 에너지를 고속 충전하여 <speed>이동 속도가 {{ totalmovespeed }}</speed> 증가하고 충전 중에는 유체화 상태가 되며, {{ e2 }}초 동안 <attackSpeed>공격 속도가 {{ e5 }}%</attackSpeed> 증가합니다.<br /><br />기본 공격 시 스킬의 재사용 대기시간이 {{ e4 }}초 감소합니다.<br /><br /><keywordMajor>진화 시</keywordMajor>: {{ e7 }}초 동안 <keywordStealth>투명</keywordStealth> 상태가 됩니다.<br />현재: <attackSpeed>추가 공격 속도 {{ f10.1 }}%/{{ e6 }}%</attackSpeed>{{ spellmodifierdescriptionappend }} |
| `audit:Kaisa:R:tooltip` | `data.Kaisa.spells.3.tooltip` | 카이사가 <keywordMajor>플라즈마</keywordMajor> 표식이 남은 적 챔피언 근처로 빠르게 돌진하며, {{ rshieldduration }}초 동안 <shield>{{ rcalculatedshieldvalue }}의 보호막</shield>을 얻습니다.{{ spellmodifierdescriptionappend }} |
| `audit:Nautilus:Q:tooltip` | `data.Nautilus.spells.0.tooltip` | 노틸러스가 전방으로 닻을 던집니다. 닻이 적을 맞히면 노틸러스와 대상이 가까이 당겨지며 대상에게 <magicDamage>{{ qdamagecalc }}의 마법 피해</magicDamage>를 입히고 잠시 <status>기절</status>시킵니다. 닻이 지형을 맞히면 노틸러스가 지형 쪽으로 끌려갑니다.{{ spellmodifierdescriptionappend }} |
| `audit:Nautilus:W:tooltip` | `data.Nautilus.spells.1.tooltip` | 노틸러스가 {{ shieldduration }}초 동안 <shield>{{ shieldcalc }}의 피해를 흡수하는 보호막</shield>을 얻습니다. <shield>보호막</shield>이 지속되는 동안 노틸러스의 기본 공격은 2초에 걸쳐 대상과 대상 주위의 모든 적에게 <magicDamage>{{ dotdamagecalc }}의 마법 피해</magicDamage>를 추가로 입힙니다.{{ spellmodifierdescriptionappend }} |
| `audit:Nautilus:E:tooltip` | `data.Nautilus.spells.2.tooltip` | 노틸러스가 주위에 세 번의 폭발을 일으킵니다. 폭발할 때마다 범위 내의 모든 적에게 <magicDamage>{{ damagecalc }}의 마법 피해</magicDamage>를 입히고 {{ slowduration }}초 동안 {{ slowpercent*100 }}% <status>둔화</status>시킵니다. 둔화 효과는 시간이 지나면 사라집니다.{{ spellmodifierdescriptionappend }} |
| `audit:Nautilus:R:tooltip` | `data.Nautilus.spells.3.tooltip` | 노틸러스가 적 챔피언을 추격하는 충격파를 발사해 <magicDamage>{{ primarytargetdamage }}의 마법 피해</magicDamage>를 입히며, {{ stunduration }}초 동안 <status>공중으로</status> <status>띄워 올리고</status> <status>기절</status>시킵니다. 충격파에 맞은 다른 적 또한 <status>공중에 뜨고</status> <status>기절</status>하며 <magicDamage>{{ secondarytargetdamage }}의 마법 피해</magicDamage>를 입습니다.{{ spellmodifierdescriptionappend }} |

## Flat context fact candidates for Main

The JSON `context_fact_candidates` array has exact `local_source`, URL, patch, SHA256, locator, raw excerpt, normalized plain text, and source-supported limits for Kai’Sa P, Kai’Sa R tooltip, Lux W tooltip, Lux E tooltip and Nautilus P. Kai’Sa P/Nautilus P already exist among the865facts; only the three tooltip fields are additive candidates. The passive evidence for allied immobilization→Plasma and level1basic-attack root is preserved without duplicating or rewriting the original archive. Main owns bindings.

## Item reference boundaries

The existing Korean item archive SHA matches its retained manifest. At audit intake it is absent from Loading source bindings. The following16map11/purchasable examples illustrate factual fields relevant to comparing observed inventories; selection is not a build or first-purchase recommendation. Full total cost is not remaining purchase gold.

| Source reference | Archived item | Exact description | Limit |
| --- | --- | --- | --- |
| `audit:item:1001` | 장화 (1001), total300 | <mainText><stats>이동 속도 <attention>25</attention></stats><br><br></mainText> | Movement speed is not a guaranteed hook dodge or escape. |
| `audit:item:3006` | 광전사의 군화 (3006), total1100 | <mainText><stats>공격 속도 <attention>30%</attention><br>이동 속도 <attention>45</attention></stats><br><br></mainText> | Attack speed does not prove a Kai'Sa evolution without complete relevant stats and observed evolution state. |
| `audit:item:1036` | 롱소드 (1036), total350 | <mainText><stats>공격력 <attention>10</attention></stats><br><br></mainText> | A component does not prove an all-in threshold or remaining gold requirement. |
| `audit:item:1042` | 단검 (1042), total250 | <mainText><stats>공격 속도 <attention>10%</attention></stats><br><br></mainText> | No automatic evolution or trade advantage. |
| `audit:item:1018` | 민첩성의 망토 (1018), total600 | <mainText><stats>치명타 확률 <attention>15%</attention></stats><br><br></mainText> | Caitlyn passive crit scaling is supported; exact expected trade damage is not. |
| `audit:item:1038` | B.F. 대검 (1038), total1300 | <mainText><stats>공격력 <attention>40</attention></stats><br><br></mainText> | No first-back or first-core purchase recommendation is established. |
| `audit:item:1052` | 증폭의 고서 (1052), total400 | <mainText><stats>주문력 <attention>20</attention></stats><br><br></mainText> | AP is a static stat; relative burst/safety remains unknown. |
| `audit:item:3802` | 사라진 양피지 (3802), total1200 | <mainText><stats>주문력 <attention>40</attention><br>마나 <attention>300</attention><br>스킬 가속 <attention>10</attention></stats><br><br><passive>깨우치기</passive><br>레벨 업하면 3초 동안 <scaleMana>최대 마나의 20%</scaleMana>를 회복합니다.</mainText> | Not unconditional continuous mana restoration, guaranteed push, or a prescribed Lux item. |
| `audit:item:3145` | 마법공학 교류 발전기 (3145), total1100 | <mainText><stats>주문력 <attention>45</attention></stats><br><br><passive>자극</passive><br>챔피언에게 피해를 입히면 <magicDamage>추가 마법 피해</magicDamage>를 입힙니다.</mainText> | Dynamic bonus damage/cooldown and concrete kill range are not provided here. |
| `audit:item:3031` | 무한의 대검 (3031), total3500 | <mainText><stats>공격력 <attention>75</attention><br>치명타 확률 <attention>25%</attention><br>치명타 피해량 <attention>30%</attention></stats><br><br></mainText> | Does not prove optimal first core, stronger duo, or guaranteed kill. |
| `audit:item:6672` | 크라켄 학살자 (6672), total3000 | <mainText><stats>공격력 <attention>45</attention><br>공격 속도 <attention>40%</attention><br>이동 속도 <attention>4%</attention></stats><br><br><passive>벼락</passive><br>세 번째 기본 공격마다 <physicalDamage>추가 물리 피해</physicalDamage>(<OnHit>적중 시</OnHit> )를 입힙니다. 잃은 체력에 따라 피해량이 증가합니다.</mainText> | Not an assumed Kai'Sa purchase/evolution or fixed first-core superiority. |
| `audit:item:3124` | 구인수의 격노검 (3124), total3000 | <mainText><stats>공격력 <attention>30</attention><br>주문력 <attention>30</attention><br>공격 속도 <attention>25%</attention></stats><br><br><passive>분노</passive><br>공격 시 <magicDamage>30의 추가 마법 피해(<OnHit>적중 시</OnHit> )</magicDamage>를 입힙니다.<br><br><passive>들끓는 일격</passive><br>기본 공격 시 4초 동안 <attackSpeed>공격 속도가 8%</attackSpeed> 증가합니다. (4회 중첩) <br>최대 중첩 시 세 번째 기본 공격을 가할 때마다 <OnHit>적중 시</OnHit> 효과를 두 번씩 적용합니다.</mainText> | Specific Plasma/on-hit interactions, evolution thresholds met, optimal build, and matchup results are not established by item text alone. |
| `audit:item:3190` | 강철의 솔라리 펜던트 (3190), total2200 | <mainText><stats>체력 <attention>200</attention><br>방어력 <attention>30</attention><br>마법 저항력 <attention>30</attention><br>스킬 가속 <attention>10</attention></stats><br><br><active>헌신</active><br>주변 아군들에게 <shield>290~360의 피해를 흡수하는 보호막</shield>을 부여합니다. 보호막 피해 흡수량은 2.5초에 걸쳐 점차 감소합니다.</mainText> | Presence in inventory does not imply active ready, actual nearby ally shield, or survival. |
| `audit:item:3047` | 판금 장화 (3047), total1200 | <mainText><stats>방어력 <attention>25</attention><br>이동 속도 <attention>45</attention></stats><br><br><passive>장갑판</passive><br>기본 공격으로 받는 피해량이 10% 감소합니다.</mainText> | Not general10% damage reduction against spells or all Kai'Sa/Nautilus damage. |
| `audit:item:3140` | 수은 장식띠 (3140), total1300 | <mainText><stats>마법 저항력 <attention>30</attention></stats><br><br><active>수은</active><br>모든 군중 제어 효과(<keyword>공중에 뜸</keyword> 제외)를 제거합니다.</mainText> | Does not remove the airborne component of Nautilus R. No guaranteed escape or optimal purchase follows. |
| `audit:item:3865` | 세계 지도집 (3865), total400 | (official description is empty) | Do not invent support quest, charges, ward unlock timing, income, or evolution details from the empty description. |

## Conditional questions and missing evidence by milestone

These are audit questions and constraints for Main, not player instructions or a new strategy.

| Milestone | Questions | Risk to avoid |
| --- | --- | --- |
| `LEVEL1` | 실제로 배운 각 챔피언의 첫 스킬과 현재 사용 가능 여부는 무엇인가? / 미니언·지형·상대 위치와 체력/마나를 관측했는가? | Base range and ranged spells do not establish automatic push/priority or a safe trade. Starting ability is unknown; Nautilus minion-collision protection is unestablished. |
| `LEVEL2` | 우리와 상대의 실제 레벨 상승 시점·경험치 차이·배운 스킬은 확인됐는가? / 이동 불가 효과 적중과 카이사의 후속 기본 공격/플라즈마를 관측했는가? | No source establishes who reaches2first, exact minion count, standard unlock order, guaranteed CC chain, or required all-in. |
| `LEVEL3_5` | 럭스 속박/둔화와 케이틀린 덫·투망의 실제 적중, 충전량, 사거리·마나·재사용 대기를 확인했는가? / 노틸러스가 Q를 빗나간 뒤에도 기본 공격 속박·E·보호막 또는 접근 수단이 남아 있는가? | Lux Q to Caitlyn W is a potential mechanism sequence, not evidence of guaranteed contact/chain. A missed Q does not establish a harmless Nautilus; missing cooldown alone does not prove safety from enemy jungle/other tools. |
| `LEVEL6` | 궁극기를 실제로 배웠고 재사용 대기·마나·사거리가 충족되는가? / 카이사의 돌진 대상에게 플라즈마가 실제로 남아 있으며, 케이틀린 R 경로에 대신 맞을 적 챔피언이 있는가? | R availability is not implied by row label. Kaisa requires Plasma mark; Nautilus R tracks a champion and affects others in path; Caitlyn R can be intercepted. No automatic minion safety or superior level6duo. |
| `FIRST_PURCHASE` | 각 챔피언이 실제로 산 아이템·남은 구성품·인벤토리·적용 게임 패치가 확인됐는가? / 해당 구매가 바꾼 것은 공격력/주문력/공격속도/마나/이속/방어 중 무엇이며 능동 효과가 사용 가능한가? | Catalog total cost is full item total, not remaining purchase gold or recall timing. Inventory/patch/active readiness unknown; boots do not guarantee dodge; QSS excludes airborne. |
| `FIRST_CORE` | 완성템의 정확한 이름·효과와 상대 구매를 확인했는가? / 카이사의 해당 스킬 진화와 케이틀린의 실제 치명타 조건·후속 공격 기회를 확인했는가? | One completed item does not prove a Kai'Sa evolution, relative power reversal, optimal build, stronger duo, or safe combat. Runes/levels/complete inventories/ability contact and readiness remain unknown. |

## Existing source queues

Relevant registered BOTTOM/SUPPORT expert candidates remain discovery sources with unchanged grades and unverified speakers: 정뚱땡 (UCbRAQlJtEMooC9td9lr4tQg, L), 땅우양 (UC9vI-9WYQLXKI6n9XdXXo3g, L), 프레이 (UCSzHok6X5qXEO7cjvVnE62g, C), 데스티니 (UC6NXJtCn3p-actkvBUlHwDA, L), 희성 (UCy-0ERPBCzs_p_E_Ag9C-Jw, L), 울프 (UCYJ0Ucu9jPX5kn6SeDcNaIQ, C), 이브 (UCerhqgFd8dnypewC3yjAlbg, UNKNOWN). Registration is not a relevant direct statement or coaching adoption.

POV sources remain separate from expert statements: Proview Lol (`UC60AsIDujUw3zd4k4Hz_4vA`) and LPL LCK Pros (`UCck3GtfaB356euYQPXvMPhw`). The later retained canonical API metadata verifies channel identity/handles; earlier public-search uncertainty remains historical. Actual footage, player view, continuity, matchup and game link remain unknown.

An existing discovery-only row names “Ruler proview2026/10/02 caitlyn kaisa” at https://www.youtube.com/watch?v=ng7bEhcTmQU in `evidence/actual-evidence/pov-public-investigation.json`. Champion tokens are search keys; this does not establish champion ownership, Lux/Nautilus presence, actual date/patch, same-game identity or sufficient predecision view. The later six-video metadata sample does not verify or refute this older candidate.

Existing paths: `config/expert_channels.json`, `config/pov_channels.json`, `data/pov_metadata/2026-10-16/pov-metadata.json`, `data/pov_metadata/2026-10-16/metadata-binding.json`, `evidence/actual-evidence/pov-public-investigation.json`, `evidence/actual-evidence/video-step-diagnostic/resume-20261017/expert-report-readiness.json`, `evidence/actual-evidence/video-step-diagnostic/resume-20261017/stage3-source-plan.json`, `evidence/actual-evidence/video-step-diagnostic/resume-20261017/stage4-source-plan.json`, `docs/queue/QUEUE.md`.

Future expert use requires an exact utterance interval, paraphrase, speaker status, supported conditions and independent review. Future POV evaluation requires reliable same-game anchors, observed continuous player-known context before the decision, and exclusion of later information from generation input. Existing diagnostic stages are not tactical evidence. PRO89/108remain separate and cannot supply scenes by a name/title/date join.

No collection, schedule mutation or queue promotion occurred. Existing VIDEO3/3history and the Oct18stage3→separate review/gated publication→stage4sequence remain intact.

## Offline verification performed

Recomputed four champion source hashes and the item source hash against retained manifests; matched20Loading descriptions exactly; read16retained tooltips and4base attackrange fields; checked16item sample map11/purchasable fields. Parsed the new JSON. No old tests, gameplay/POV review, damage simulation, or efficacy evaluation were run.
