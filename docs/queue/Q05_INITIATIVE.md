# Q05 initiative candidates for PRE_GAME v2

[initiative-v2.json](../../knowledge_candidates/initiative-v2.json) contains 13
supplemental COMMON PROFILE specs under new `Q05-I-*` IDs. The original 173
source profiles and 177 typed v1 specs retain their original bytes. Supplemental
empty legacy profile fields mean UNKNOWN and carry no replacement assertion.
The other 160 champions have no new initiative annotation in this delivery;
absence of an annotation does not assert that an ability or role is absent.

Every candidate is **EXPLORATORY**. No KnowledgeStore proposal, USER_WEB decision,
approval actor, applied tactical instruction, current game patch, or real-match
accuracy is claimed. The static source build is 16.20.1; all gameplay `patches`
remain empty. An independently supplied draft patch cannot make an empty rule
patch scope executable.

| Champion | Initiative interpretation | Archived mechanism and condition |
| --- | --- | --- |
| Ornn | INITIATOR | E terrain contact; R recast redirect and enemy contact |
| Sejuani | INITIATOR | Q/R contact; E maximum Frost stacks |
| Ahri | INITIATOR | E encountering an enemy for charm |
| Lux | INITIATOR, PROTECTOR | Q binding up to two units; W friendly contact for protection |
| Nautilus | INITIATOR | Q enemy collision; R opponent chase and eruption |
| Ashe | INITIATOR | R enemy champion collision for stun |
| LeeSin | INITIATOR, PROTECTOR | R target displacement/collision; W allied champion target for ally shield |
| Fiora | SELF_SUFFICIENT | Own Q/vital pressure tools; W stun depends on parrying immobilization |
| Zed | SELF_SUFFICIENT | Own shadow/mark tools; mark repetition depends on damage dealt while marked |
| Ezreal | SELF_SUFFICIENT | Own Q/E tools; Q reduction requires an enemy-unit hit |
| Caitlyn | SELF_SUFFICIENT | Own shot/trap/net tools; empowered Headshot and trap control are conditional |
| Yunara | SELF_SUFFICIENT | Own attack/movement tools; directional dash requires Transcendent State |
| Kaisa | FOLLOW_UP; needs ALLY_CC | Passive explicitly says allied immobilizing effects help stack Plasma |

These labels interpret a possible mechanic, not a champion's exclusive role or
successful player behavior. INITIATOR does not mean that an opening is safe,
available, unavoidable or optimal. PROTECTOR records direct allied protection
mechanics; it does not assert effective peel in an observed fight.
SELF_SUFFICIENT describes a tentative own-tool pressure capability, not proven
independence from allies, protection needs, or safe solo success. No relative
strength, matchup result, lane priority, phase strength or mandatory teammate
action is inferred from these descriptions.

Kai'Sa's `ALLY_CC` annotation records a conditional **benefit**, not inability to
act alone. Her own basic attacks also stack Plasma. The archived R excerpt says
only that she dashes near an enemy champion; it does not substantiate a
Plasma-mark requirement for the dash. No such requirement is encoded. Other
champions' `needs` remain empty because these selected source excerpts do not
establish mandatory allied initiation, CC or peel.

The 28 `necessary_conditions` are labelled strings of the form
`STATIC_SOURCE_16.20.1|exact.locator|exact archived description`. Each has a
corresponding HTTPS Data Dragon URL, original document SHA-256, locator and
static source version in the same spec. They describe static mechanisms and
conditional clauses; they are not runtime predicates or claims of observed
ability readiness, target contact, resources, enemy cooldowns or ally behavior.
Every spec also carries a concrete counterexample and the source/interpretation
limits. Full prose, including HTML tags, is preserved for source comparison.

The catalog does not add OPERATIONS rules, request templates, teammate play
instructions, pick recommendations or a champion-combination lookup. Those
outputs require separately source-bound REVIEWED templates and exact current
approval binding. Existing golden review order remains untouched; the ten
golden champions plus Yunara, Ashe and Kai'Sa are the source-audit priority.

Q18 stage roles remain UNKNOWN. These unchanged v2 payloads do not add an early,
middle or late-game role, validated movement pattern, role transition or
grouping instruction. A kit description does not establish such behavior; in
particular, Nocturne's vision reduction and dash text cannot substantiate a
late-game grouping role. Stage-specific claims require a separately versioned,
source-bound candidate and actual review.

Verification from the repository root:

```sh
PYTHONPATH=. python -m unittest tests_pregame.test_initiative_candidates -v
```

The tests verify exact archived bytes and descriptions, preserved baseline
hashes, 13 unique new IDs, strict v2 parsing and proposal digest prefixes,
unknown gameplay patch, absence of runtime observations/operations, and the
conditional Kai'Sa limit. Source receipts already live under
[q05/source-receipts.json](../../evidence/queue/q05/source-receipts.json);
the additive validation receipt is
[q05-initiative/validation.json](../../evidence/queue/q05-initiative/validation.json).
