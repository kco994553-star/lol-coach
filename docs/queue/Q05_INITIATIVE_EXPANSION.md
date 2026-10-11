Main integration correction: independent review found Zac E archive describes movement only. The initiative source now binds `data.Zac.spells.3.description`, which explicitly describes enemy knockup/slow; old candidate bytes remain in commitc78c03d. RED→GREEN semantic regression retained. Final catalog SHA256: `96a99b9c3acf66eaaa079d3e0cb505c531c7c1522ab61e109f3e89e33d75559e`. Current default HTTP cap is1,000,000bytes (not1MiB); integration uses actual encoded payload and32KiB margin.

# Q05 initiative expansion: all remaining 160 champions

[initiative-expansion-v2.json](../../knowledge_candidates/initiative-expansion-v2.json)
adds 160 COMMON PROFILE candidates under unique `Q05-IX-*` IDs using the frozen
`pregame.rule.v2` contract. The previous 190 candidates, original 173 roster,
and the completed 13 initiative payloads retain their exact bytes. Main owns the
additive fourth-catalog loader; this delivery does not change shared code.

Every new record binds one or two exact official static descriptions from the
already verified [160 source receipts](../../evidence/queue/q05-expansion/source-receipts.json).
Their archived hashes all match. Coverage is 160 champions and 174 distinct
champion/locator excerpts; 106 records have at least one interpreted initiative
label and 54 keep `initiative=[]` with an explicit `INITIATIVE_UNKNOWN` limit.
There are 69 INITIATOR, 28 PROTECTOR, 22 SELF_SUFFICIENT, and one FOLLOW_UP labels;
some records carry two labels. The first concrete 12-champion audit batch is
included, followed by every remaining source-backed record, without duplicate
annotations for the earlier 13 champions.

All are **AI_EXPLORATORY** candidates. No USER_WEB decision, approval, applied
coaching instruction, runtime observation, or real-match accuracy is asserted.
Gameplay `patches=[]`; source patch16.20.1 is a static build, not the current or
match patch. Roles, legacy threats/protection, strength-by-phase, lane/jungle
styles, output change conditions, typed runtime predicates and cooldowns remain
empty UNKNOWN. `plan_guard=null` and output operations remain null.

## Interpretation boundary

Each label has a source locator recorded as `INITIATIVE_BASIS|TYPE|locator` in
its limitations. That locator resolves to an exact bound excerpt in the same
candidate. Existing semantic features were an index into source descriptions,
not reviewed evidence or permission to promote every control/class tag.
The enumerations are incomplete possible capabilities, not exclusive roles.

- INITIATOR interprets quoted active control or a source-described own setup
  that can deliver control contact. Every quoted form, stack, target, timing,
  terrain, arrival or contact condition remains intact. CC does not prove a
  guaranteed, available, safe, unavoidable or optimal opening. For example,
  Braum uses the active Glacial Fissure excerpt, not a mandatory allied attack
  requirement. Alistar uses Pulverize, and Leona uses the conditional Zenith
  Blade enemy-hit/dash description.
- PROTECTOR interprets explicitly quoted allied shielding, healing, damage
  blocking or defense benefits. Target/proximity/setup restrictions remain.
  This does not prove effective peel or independence from another ally. Nilah's
  benefit specifically shares/enhances nearby allied healing/shielding; it is
  not an independently granted shield.
- SELF_SUFFICIENT interprets an own maneuver-and-strike tool in one exact
  excerpt. It does not establish viable solo pressure, absence of protection
  needs, relative strength or success without allies. It includes such gated
  cases as Akali's marked-target recast and Vex's missile-mark/recast dash.
- Jhin's FOLLOW_UP interprets his explicit optional allied contribution to
  the W root condition. His own damage or traps also qualify, so it is not a
  mandatory ally dependency. No compatible mandatory ALLY_INITIATION, ALLY_CC
  or ALLY_PEEL claim is established; all 160 `needs` arrays stay empty UNKNOWN.
  Samira and Yasuo have no new FOLLOW_UP assertion inferred from control
  wording without an explicit allied contribution in the selected excerpt.

No label is filled merely from a Fighter/Mage/etc class tag or generic damage.
Factual-only records preserve their exact mechanics even when initiative
classification remains unknown. For example, Taliyah's selected minefield reacts
when enemies dash or are knocked through it; it does not establish an independent
opening. Kalista, Smolder and Teemo retain empty labels. Missing labels do not
assert a missing capability; the catalog is deliberately nonexhaustive.

`necessary_conditions` follow the exact form
`STATIC_SOURCE_16.20.1|locator|full archived description`. These are static
mechanic/condition excerpts, not observed predicates or a requirement that every
sentence occur simultaneously. Each excerpt has its official HTTPS URL, full
archived JSON SHA256, locator and static version in `sources`, and a named
mechanic counterexample/limit in the same record. No numerical trigger is
invented; numbers present in excerpts remain source literals.

## Phase and operating claims remain unsupported

No per-champion EARLY/MID/LATE role, movement plan, phase transition, ally request,
team composition recommendation or tactic is generated. A level/stack progression
clause, including Kayle/Smolder/Aurelion Sol mechanics elsewhere in the archives,
does not establish stage roles. Current-patch factual sources and independently
verified stage statistics remain absent. There is no Nocturne late-grouping claim,
minute threshold, approved template or synthetic actual coaching data.

## Validation and response budget

Five new tests first failed for the absent catalog. They verify all 160 unique
remaining champions, all 350 total candidate IDs, frozen original hashes, exact
receipts and source bytes/locators, strict v2 roundtrip and proposal digest prefix,
empty patch/phase/runtime/approval fields, conservative dependency interpretations,
and the unchanged response budget. The original four initiative tests also pass.
A full `tests_pregame` discovery run passed all 156 tests without skips at the
assigned baseline. Main's loader integration will separately check the live HTTP
350-candidate response; this isolated catalog delivery does not alter that loader.
A meaningful guard caught copied template change conditions; all such fields are
now explicitly empty for every new candidate.

The exact current server `json.dumps(..., ensure_ascii=False, allow_nan=False)`
encoding of all 350 candidate specs is **953,099 bytes**, under the unchanged
1,048,576-byte limit with 95,477 bytes of headroom. The test additionally
requires a 32KiB safety margin. Source clauses are restricted to one or two per
champion; repeated explanatory text is concise. The old payload bytes and server
encoding/response limit were not changed to obtain this result.

Verification from the repository root:

```sh
python -m unittest tests_pregame.test_initiative_expansion tests_pregame.test_initiative_candidates -v
python -m unittest discover -s tests_pregame -v
```

Catalog SHA256: `e6ef9587458362bdc35b4108633869aa4f9e228aa13cf1f09f674775346e3ade`.

## Per-champion excerpt and label index

The official document URL/hash for each row is carried in the catalog and existing
source receipt. Every locator below is under `data.<Champion>.` and ends with
`.description`. UNKNOWN is an absence of a supported annotation in this candidate,
not a claim that the champion has no such ability.

| Champion | Conditional interpretation | Exact archived locator suffixes |
| --- | --- | --- |
| Aatrox | UNKNOWN | spells.1.description |
| Akali | SELF_SUFFICIENT | spells.2.description |
| Akshan | SELF_SUFFICIENT | spells.2.description |
| Alistar | INITIATOR, PROTECTOR | spells.0.description, passive.description |
| Ambessa | UNKNOWN | spells.3.description |
| Amumu | INITIATOR | spells.0.description |
| Anivia | INITIATOR | spells.0.description |
| Annie | INITIATOR, PROTECTOR | passive.description, spells.2.description |
| Aphelios | UNKNOWN | spells.0.description |
| AurelionSol | UNKNOWN | spells.2.description |
| Aurora | SELF_SUFFICIENT | spells.3.description |
| Azir | SELF_SUFFICIENT | spells.2.description |
| Bard | PROTECTOR | spells.1.description |
| Belveth | SELF_SUFFICIENT | spells.0.description |
| Blitzcrank | INITIATOR | spells.0.description |
| Brand | UNKNOWN | spells.0.description |
| Braum | INITIATOR, PROTECTOR | spells.3.description, spells.1.description |
| Briar | SELF_SUFFICIENT | spells.0.description |
| Camille | INITIATOR | spells.2.description |
| Cassiopeia | UNKNOWN | spells.3.description |
| Chogath | UNKNOWN | passive.description |
| Corki | UNKNOWN | spells.0.description |
| Darius | INITIATOR | spells.2.description |
| Diana | INITIATOR | spells.3.description |
| DrMundo | UNKNOWN | passive.description |
| Draven | UNKNOWN | spells.2.description |
| Ekko | UNKNOWN | spells.0.description |
| Elise | INITIATOR | spells.2.description |
| Evelynn | INITIATOR | spells.1.description |
| Fiddlesticks | INITIATOR | spells.0.description |
| Fizz | INITIATOR | spells.3.description |
| Galio | INITIATOR, PROTECTOR | spells.1.description, spells.3.description |
| Gangplank | UNKNOWN | spells.0.description |
| Garen | UNKNOWN | spells.1.description |
| Gnar | INITIATOR | spells.1.description |
| Gragas | INITIATOR | spells.2.description |
| Graves | UNKNOWN | spells.1.description |
| Gwen | UNKNOWN | spells.3.description |
| Hecarim | INITIATOR | spells.3.description |
| Heimerdinger | UNKNOWN | spells.0.description |
| Hwei | UNKNOWN | spells.0.description |
| Illaoi | UNKNOWN | passive.description |
| Irelia | UNKNOWN | spells.0.description |
| Ivern | INITIATOR, PROTECTOR | spells.0.description, spells.2.description |
| Janna | PROTECTOR | spells.2.description |
| JarvanIV | INITIATOR | spells.0.description |
| Jax | INITIATOR | spells.2.description |
| Jayce | UNKNOWN | spells.0.description |
| Jhin | FOLLOW_UP | spells.1.description |
| Jinx | UNKNOWN | spells.0.description |
| KSante | PROTECTOR | spells.2.description |
| Kalista | UNKNOWN | spells.0.description |
| Karma | PROTECTOR | spells.2.description |
| Karthus | UNKNOWN | spells.0.description |
| Kassadin | SELF_SUFFICIENT | spells.3.description |
| Katarina | SELF_SUFFICIENT | spells.2.description |
| Kayle | PROTECTOR | spells.1.description |
| Kayn | SELF_SUFFICIENT | spells.0.description |
| Kennen | INITIATOR | passive.description |
| Khazix | SELF_SUFFICIENT | spells.2.description |
| Kindred | UNKNOWN | spells.0.description |
| Kled | INITIATOR | spells.0.description |
| KogMaw | UNKNOWN | spells.0.description |
| Leblanc | INITIATOR | spells.2.description |
| Leona | INITIATOR | spells.2.description |
| Lillia | UNKNOWN | spells.2.description |
| Lissandra | INITIATOR | spells.1.description |
| Locke | SELF_SUFFICIENT | spells.2.description |
| Lucian | UNKNOWN | spells.0.description |
| Lulu | PROTECTOR | spells.2.description |
| Malphite | INITIATOR | spells.3.description |
| Malzahar | INITIATOR | spells.3.description |
| Maokai | INITIATOR | spells.1.description |
| MasterYi | SELF_SUFFICIENT | spells.0.description |
| Mel | UNKNOWN | spells.0.description |
| Milio | PROTECTOR | spells.1.description |
| MissFortune | UNKNOWN | spells.0.description |
| MonkeyKing | INITIATOR | spells.3.description |
| Mordekaiser | UNKNOWN | spells.2.description |
| Morgana | INITIATOR, PROTECTOR | spells.0.description, spells.2.description |
| Naafiri | SELF_SUFFICIENT | spells.2.description |
| Nami | INITIATOR, PROTECTOR | spells.0.description, spells.1.description |
| Nasus | UNKNOWN | spells.3.description |
| Neeko | INITIATOR | spells.2.description |
| Nidalee | PROTECTOR | spells.2.description |
| Nilah | PROTECTOR | passive.description |
| Nocturne | INITIATOR | spells.2.description |
| Nunu | INITIATOR | spells.1.description |
| Olaf | UNKNOWN | spells.0.description |
| Orianna | PROTECTOR | spells.2.description |
| Pantheon | INITIATOR | spells.1.description |
| Poppy | INITIATOR | spells.2.description |
| Pyke | INITIATOR | spells.0.description |
| Qiyana | INITIATOR | spells.3.description |
| Quinn | UNKNOWN | spells.0.description |
| Rakan | INITIATOR, PROTECTOR | spells.1.description, spells.2.description |
| Rammus | INITIATOR | spells.2.description |
| RekSai | INITIATOR | spells.1.description |
| Rell | INITIATOR | spells.0.description |
| Renata | INITIATOR, PROTECTOR | spells.0.description, spells.2.description |
| Renekton | INITIATOR | spells.1.description |
| Rengar | INITIATOR | spells.2.description |
| Riven | INITIATOR | spells.1.description |
| Rumble | UNKNOWN | spells.2.description |
| Ryze | INITIATOR | spells.1.description |
| Samira | SELF_SUFFICIENT | spells.2.description |
| Senna | PROTECTOR | spells.0.description |
| Seraphine | PROTECTOR | spells.1.description |
| Sett | UNKNOWN | spells.1.description |
| Shaco | SELF_SUFFICIENT | spells.0.description |
| Shen | INITIATOR, PROTECTOR | spells.2.description, spells.1.description |
| Shyvana | UNKNOWN | spells.1.description |
| Singed | INITIATOR | spells.2.description |
| Sion | INITIATOR | spells.0.description |
| Sivir | UNKNOWN | spells.0.description |
| Skarner | INITIATOR | spells.2.description |
| Smolder | UNKNOWN | spells.0.description |
| Sona | INITIATOR, PROTECTOR | spells.3.description, spells.1.description |
| Soraka | PROTECTOR | spells.1.description |
| Swain | INITIATOR | spells.2.description |
| Sylas | SELF_SUFFICIENT | spells.1.description |
| Syndra | INITIATOR | spells.2.description |
| TahmKench | INITIATOR, PROTECTOR | spells.0.description, spells.3.description |
| Taliyah | UNKNOWN | spells.2.description |
| Talon | SELF_SUFFICIENT | spells.0.description |
| Taric | INITIATOR, PROTECTOR | spells.2.description, spells.0.description |
| Teemo | UNKNOWN | spells.0.description |
| Thresh | INITIATOR, PROTECTOR | spells.0.description, spells.1.description |
| Tristana | SELF_SUFFICIENT | spells.1.description |
| Trundle | UNKNOWN | passive.description |
| Tryndamere | SELF_SUFFICIENT | spells.2.description |
| TwistedFate | UNKNOWN | spells.0.description |
| Twitch | UNKNOWN | spells.3.description |
| Udyr | UNKNOWN | spells.1.description |
| Urgot | INITIATOR | spells.2.description |
| Varus | UNKNOWN | spells.0.description |
| Vayne | UNKNOWN | spells.2.description |
| Veigar | INITIATOR | spells.2.description |
| Velkoz | INITIATOR | spells.2.description |
| Vex | SELF_SUFFICIENT | spells.3.description |
| Vi | INITIATOR | spells.3.description |
| Viego | SELF_SUFFICIENT | spells.3.description |
| Viktor | UNKNOWN | spells.1.description |
| Vladimir | UNKNOWN | spells.0.description |
| Volibear | INITIATOR | spells.0.description |
| Warwick | INITIATOR | spells.3.description |
| Xayah | UNKNOWN | spells.0.description |
| Xerath | UNKNOWN | spells.0.description |
| XinZhao | INITIATOR | spells.0.description |
| Yasuo | SELF_SUFFICIENT | spells.2.description |
| Yone | INITIATOR | spells.0.description |
| Yorick | UNKNOWN | spells.0.description |
| Yuumi | PROTECTOR | spells.1.description |
| Zaahen | UNKNOWN | spells.0.description |
| Zac | INITIATOR | spells.2.description |
| Zeri | UNKNOWN | spells.0.description |
| Ziggs | UNKNOWN | spells.0.description |
| Zilean | INITIATOR | spells.0.description |
| Zoe | INITIATOR | spells.2.description |
| Zyra | INITIATOR | spells.2.description |
