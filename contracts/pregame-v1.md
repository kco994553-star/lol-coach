# PRE_GAME executable contract v1

Authority USER_QUEUE_V1.1_2026-10-11; additive to Frozen and PR10.
Implementation: coach_v1/pregame_contract.py; strict Pydantic, extra fields rejected.
Canonical digest: existing coach_v1.state.digest / sorted compact UTF-8 JSON.

## Input
InputDraft: title:str; patch:str|null; phase:PRE_GAME; observed_at:ISO offset|null;
my_position:TOP|JUNGLE|MID|BOTTOM|SUPPORT|null; my_champion:str|null; my_slot:int1..5|null;
slots:list[Slot] exactly10 unique (side ALLY/ENEMY,slot1..5);
source:Provenance; original_capture:original immutable draft record|null.
Slot: side,slot,champion:str|null,position:Position|null,position_candidates:list[Position],
uncertainty:str; champion_source:Provenance; position_source:Provenance;
runes:Selection; summoners:Selection.
Provenance: kind MANUAL|AUTOMATIC|UNKNOWN; reference:str|null; observed_at:ISO offset|null;
verification UNVERIFIED|SOURCE_VERIFIED|UNKNOWN (MANUAL never SOURCE_VERIFIED).
Selection: status FULL|PARTIAL|UNKNOWN; values:list[str]; source:Provenance.
UNKNOWN values empty; PARTIAL values nonempty; FULL values nonempty; the declaration is not gameplay authentication.
Position candidates cannot be silently resolved. Definite position cannot coexist with candidates.
No duplicate definite position per side. A selected champion must match a definite allied selected position when both known.
my_position is independent of slot numbering. my_slot is explicit own allied slot, never inferred from the first row. Alias ADC is displayed as 원딜 but canonical enum is existing BOTTOM.
Legacy imports normalize all10 slots, preserve original_capture and null/missing values.
Input schema never accepts live enemy cooldown/status/timer values.

## RuleSpec
schema_version:pregame.rule.v1; rule_id:slug; version:nonempty string;
scope:COMMON|POSITION; positions:list[Position] (COMMON empty; POSITION nonempty);
patches:list[str] exact gameplay patches (empty = UNKNOWN, never wildcard);
sources:list[Source] nonempty; required_fields:list[FieldPath];
conditions:list[Predicate]; counterconditions:list[Predicate]; stop_conditions:list[Predicate];
counterexamples:list[str] nonempty; limitations:list[str] nonempty;
output:RuleOutput; profile:ChampionProfile|null; cooldowns:list[Cooldown].
Source: url:https; title:str; locator:str; patch:str|null; sha256:64hex|null;
kind OFFICIAL|DATA_DRAGON|PATCH_NOTES|REFERENCE|SYNTHETIC.
Source hashes are original document byte hashes when available, not a correctness endorsement.
RuleOutput: section PROFILE|MAP|JUNGLE|COMPOSITION|ROLE|LANE|FIGHT|CHANGES;
target GLOBAL|SELF|ALLY|ENEMY|Position; outlook FAVORABLE|UNFAVORABLE|CONTESTED|UNKNOWN|null;
text:str; alternatives:list[str]; change_conditions:list[str]. All text is approved original.
ChampionProfile: champion:str; roles:list[Position]; threats:list[str]; protection:list[str];
strong_when:list[str]; lane_style:list[str]; jungle_style:list[str]. Missing categories empty = UNKNOWN.
Enums: threats ASSASSINATION,DIVE,GRAB_PICK,POKE,NONE;
protection PEEL,FRONTLINE,NONE; strong_when EARLY,MID,LATE;
lane_style PRESSURE,SCALING,ROAM,SPLIT; jungle_style EARLY_GANK,SCALING.
PROFILE must be COMMON and target GLOBAL; a profile is attached only to its named champion.
Other rules use type predicates, not champion-combination lookup policies.

FieldPath whitelist: patch, my.position, my.champion;
ally|enemy.Position.champion|position|runes|summoners|threats|protection|strong_when|lane_style|jungle_style;
ally|enemy.threats|protection|lane_style|jungle_style.
Predicates: field:FieldPath; op EQ|HAS|INTERSECTS; value:str|list[str].
EQ exact string; HAS string membership; INTERSECTS set overlap. No prose interpretation, weights or numeric thresholds.
Rule conditions conjunction: any FALSE→FALSE; else any UNKNOWN→UNKNOWN; else TRUE.
Unknown/partial required fields do not become false. Counter/stop predicates are disjunction,
any TRUE excludes; unknown counter/stop conservatively holds output UNKNOWN.
Rule patch mismatch FALSE, unknown patch UNKNOWN. Scope mismatch FALSE.
Common rules cannot refer to my.* and cannot produce ROLE/LANE/FIGHT; POSITION rules cannot produce MAP/JUNGLE/COMPOSITION/PROFILE.
Conflicting applicable output outlooks for the same section/target become CONFLICTING; preserve all evidence and alternatives.
Conflicting profile claims withhold the conflicting profile fields; no confidence score.

## Approval binding
Immutable Research report {schema_version:pregame.rule-source.v1,spec:RuleSpec} and overview note.
PR10 proposal required_fields exactly [EXECUTABLE_V1_SHA256:<digest(spec)>,...spec.required_fields].
claim exactly output.text; patch_range exactly comma-joined patches or UNKNOWN;
applicability exactly {champion:TYPE_BASED,role:ALL or comma-joined positions,
matchup:STRUCTURED_CONDITIONS,level:PRE_GAME_CONDITIONAL,context:PRE_GAME}.
Empty patches cannot be approved for execution. Free-string PR10 edits mismatching this binding are UNBOUND/UNKNOWN.
Current PR10 head REVIEWED is required. No fallback to old approvals after new proposal/rejection.
review_decision/source payload hashes and source_refs preserved by existing KnowledgeStore.
Import/propose endpoints never call decide. Only explicit trusted user button plus native confirmation sends PR10 decision request.

## Cooldown
Cooldown: name:str; side ALLY|ENEMY; position:Position; category NORMAL|CHARGE|RESET_REFUND|STACK|TRANSFORM|UNKNOWN; spell_kind ABILITY|SUMMONER;
base:BaseCooldown; conditional:HasteCondition; remaining:NOT_AVAILABLE; linked_condition:str.
BaseCooldown: status CONFIRMED|CONFLICTING|UNKNOWN; values:list[nonnegative number]; patch:str|null; sources:list[Source].
HasteCondition: haste:nonnegative number|null; source:Source|null; kind ABILITY|SUMMONER.
Spell and haste kind must match; summoner haste is not ability haste.
CONFIRMED requires nonempty values, patch, at least2 distinct source URLs and a non-DD source.
UNKNOWN category/CONFLICTING base/patch mismatch withhold values. Normal base is label “가속 0 기준 상한값”; CHARGE is “재충전 시간·가속 0 기준 상한값”.
RESET_REFUND/STACK/TRANSFORM display explicit category and conditional limit; never actual remaining cooldown.
conditional calculated base*100/(100+haste) only when haste and its source exist, labelled 계산/조건부 and provenance.
remaining is always NOT_AVAILABLE. Cooldown is displayed only within an applied REVIEWED rule's linked condition, pregame only.
Prioritize selected-role lane enemy / allied synergy / own spells, jungle target lanes and opposing jungle.
All other spell details stay in rule detail. No in-game clock, timer, remaining input, OCR or tracker.

## Evaluator result and plans
evaluate_gameplan(input:InputDraft,knowledge:list[dict])->dict. Each knowledge item:
{proposal:exact current KnowledgeStore report,spec:RuleSpec|null}. specs source-validated by server/store before evaluation.
Result keys: schema_version:pregame.plan.v1; mode:PRE_GAME; input:serialized InputDraft;
common:{map:list[5 cells],jungle:cell,composition:cell}; personal:{role:cell,lane:cell,fight:cell};
changes:cell; evaluations:list[trace]; knowledge_fingerprint:digest(current proposals + spec digests);
coaching_accuracy:null; real_match_validation:NOT_EVALUATED.
Cell: key,title,status KNOWN|UNKNOWN|CONFLICTING,texts:list[str],reasons:list[str],
rules:list[full applied proposal+spec traces],outlook enum|null,cooldowns:list[display items].
UNKNOWN texts empty; UI says 미확인 plus reasons, no filler tactical prose.
Evaluation trace: rule_id/version/spec_version/spec_sha256/review_state/condition TRUE|FALSE|UNKNOWN,
status APPLIED|EXCLUDED|UNKNOWN|CONFLICTING; reasons,missing_fields,sources,conditions,counterconditions,stop_conditions,output.
Knowledge fingerprint includes current unbound/rejected versions so any change expires old plans.
Stored plan adds id,session_id,revision,input_revision,input_sha256,created_at;
GET adds validity CURRENT|EXPIRED and expiry_reasons, without rewriting immutable stored payload.
Any input revision change or current knowledge/source fingerprint change expires old plan.
