# Q05 — source-backed exploratory knowledge candidates

These files are review inputs. Every row/rule remains `EXPLORATORY`, with
`approval_actor: null` and `coaching_enabled: false`. No real USER_WEB decision,
reviewed Knowledge version, product import, engine activation, or live-game
verification has been created. Main owns integration after the Q03 contract.

The golden draft is Ornn / Sejuani / Ahri / Caitlyn / Lux against Fiora / Lee Sin /
Zed / Ezreal / Nautilus, in TOP / JUNGLE / MID / BOT / SUPPORT order. The same
type rules provide selected-position views for all five positions. Yunara, Ashe,
and Kai'Sa are additional frequent-pick profile candidates, not scope limits.

## Patch and source boundaries

The repository does **not** establish a current gameplay patch. `coach_v1/draft.py`
stores the operator's declaration. Synthetic tests use `26.20`, while historical
structured match evidence uses `14.17.613.973`; neither establishes the prospective
golden draft's patch. [Patch audit](../../evidence/queue/q05/patch-pin-audit.json)
records audited paths, hashes and intake commit.

An official Data Dragon **16.20.1 static source snapshot** was explicitly selected
after inspecting the official version list. It is not silently adopted as the
repository, manual draft, or actual-game patch. `repository_patch` and
`runtime_patch` remain null. Candidate `patch_range` explicitly says
`SOURCE_SNAPSHOT_16.20.1_ONLY; GAME_PATCH_UNKNOWN`. A real reviewer must select a
bounded game applicability patch before any candidate becomes coaching knowledge.

Official Data Dragon supplied identity, combat-class tags and ability descriptions.
The [official how-to-play guide](https://www.leagueoflegends.com/en-us/how-to-play/)
supplied general lane duties, structure progression and objective context. That
guide is unversioned: references say so, and its general descriptions are not
patch-specific timers, objective counts, or current jungle rules. No guide claim
about the exact number of drakes is promoted to a candidate.

Source responses are archived under `evidence/queue/q05/sources`. The
[HTTP receipts](../../evidence/queue/q05/source-receipts.json) preserve requested /
effective URLs, exit status, byte counts, SHA-256 and captured retrieval times.
For the initial versions request the exact timestamp/status was not recorded;
the receipt says that explicitly. Each candidate reference has an exact source
locator and excerpt, so the hash verifies the bytes and the locator verifies the
claim's content. Extraction of the guide's `__NEXT_DATA__` retains tab text that
was not initially rendered in the page body. No credentials or private input
were acquired.

## Content files

| File | Contents |
| --- | --- |
| [q05-roster-profiles.json](../../knowledge_candidates/q05-roster-profiles.json) | One row per all 173 champions; original 13 profiles preserved plus 160 source-audited mechanic profiles with sparse type candidates |
| [q05-type-rules.json](../../knowledge_candidates/q05-type-rules.json) | 11 common①–④ rules plus five selected-position behavior candidates |
| [q05-review-priority.json](../../knowledge_candidates/q05-review-priority.json) | Ten recommended review candidates with reasons, source URLs and limitations |

The common groups are ① champion classification, ② type-based lane outlook,
③ jungle intervention, and ④ composition win conditions/objective conversion.
The position views do not select only BOT: TOP/JUNGLE/MID/BOT/SUPPORT each has
a separate candidate.

## Common classification and unknowns

`official_roles` are Data Dragon combat classes (Tank, Fighter, Mage, Assassin,
Marksman, Support), **not** optimal lane positions. Golden `position_candidate`
comes from declared review context, with `position_basis: USER_GOLDEN_INPUT_CONTEXT`.
No official lane-position distribution is invented. Frequent picks' positions
remain unassigned in these source-only profiles.

Threat vocabulary: assassination / dive / grab-pick / poke / none.
Protection vocabulary: protection / frontline / none.
Lane vocabulary: lane-pressure / scaling / roam / split.
Jungle vocabulary: early-gank / scaling.

The original 13 profile labels are exploratory interpretations of their archived
kits. Expansion labels below follow the same possibility/unknown boundary.
`grab-pick` covers catch tools such as pull, root, charm, stun, knockup, fear or sleep;
`dive` describes access tools, not a successful tower dive. `frontline` is a Tank /
control interpretation and does not guarantee durability. The original `protection`
candidates have ally shield mechanics as evidence; expansion also preserves
explicit ally recovery, invulnerability, damage blocking and defensive-stat buffs.
Labels are possibilities rather than an
exhaustive ranking. In particular, absence of a label does not mean absence of
the capability.

| Champion | Threat candidates | Protection candidates | Lane candidates |
| --- | --- | --- | --- |
| Ornn | dive | frontline | scaling (team item upgrade capability, no timing curve) |
| Sejuani | dive, grab-pick | frontline | unknown |
| Ahri | assassination, grab-pick | unknown | roam possibility |
| Caitlyn | poke, grab-pick | unknown | lane-pressure possibility |
| Lux | poke, grab-pick | protection | lane-pressure possibility |
| Fiora | dive | unknown | unknown; split rate/strength not verified |
| Lee Sin | dive | protection | unknown |
| Zed | assassination, dive, poke | unknown | roam possibility |
| Ezreal | poke | unknown | unknown |
| Nautilus | grab-pick, dive | frontline | unknown |
| Yunara | poke | unknown | unknown; dash depends on Transcendent State |
| Ashe | poke, grab-pick | unknown | unknown |
| Kai'Sa | poke, dive | unknown | scaling (item-gated ability upgrades, no timing curve) |

Every early/mid/late strength value and every jungle early-gank/scaling value
is null across the roster. Win rates, success probabilities, confidence scores,
and cooldown arrays are also null. Official descriptions alone do not establish
matchup strengths, clear speeds, intervention schedules or a phase power curve.
Ability cooldown arrays are not promoted from one source. Numeric attack range
can appear only as an exact official source excerpt, not a fabricated comparison.

The original delivery kept the other 160 roster rows at official identity/classes
only. The subsequent source expansion below adds archived mechanic excerpts and
sparse threat/protection candidates. Every unsupported strategic field stays null.
`null` means **미확인 / unknown**, never `none`, weak,
not applicable, or a wildcard. The `none` vocabulary exists for a future explicit
review; this collection does not infer it by missing evidence.

## Ten recommended first reviews

| Order | Candidate | Golden value |
| --- | --- | --- |
| 1 | Q05-C01: terrain-dependent frontline control | Establish Ornn's engage and protection conditions |
| 2 | Q05-C02: parry duelist | Check Fiora's control reversal limit |
| 3 | Q05-C03: delayed-mark assassination access | Shared Zed threat for mid and carry protection |
| 4 | Q05-L01: frontline vs parry duelist TOP | Conditional Ornn/Fiora outlook without invented winner |
| 5 | Q05-L02: pick control vs assassination MID | Conditional Ahri/Zed control, movement and wave questions |
| 6 | Q05-L03: poke/binding vs grab/mobile carry BOT | Caitlyn/Lux vs Ezreal/Nautilus pressure and counteraccess |
| 7 | Q05-J01: control vs hit-gated dash JUNGLE | Sejuani/Lee Sin intervention prerequisites |
| 8 | Q05-W01: frontline/protection/ranged follow-up | Ally composition's shared engage/follow-up candidate |
| 9 | Q05-W02: carry protection vs assassination/dive/grab | All five position views share enemy access constraints |
| 10 | Q05-O01: convert a pick into an objective | Verify waves, survivors/resources and objective availability |

Each priority is a review recommendation, not an approval or certainty ranking.
All claims have at least one counterexample/limit. The JSON files preserve the
exact source URLs, excerpts, type predicates and required observations.

## Q03 integration advice

The strategic rule predicates reference **types/features**, not named matchups.
Champion names are source exemplars and `golden_examples` only. The displayed
types/features must themselves be reviewed for the confirmed patch; official
combat tags must not auto-fill unreviewed threat/protection/timing fields.

`q03_structured_spec` deliberately remains null until Main's contract is supplied.
These JSON envelopes are content files, not proposed replacements for common
schemas. Main can archive the immutable final spec and these receipts inside a
Research RAW_DIAGNOSTIC source report, bind an exact PR10 Knowledge proposal to
the saved note, and let the real browser user review that exact version. The
evaluator must validate the immutable spec hash and current REVIEWED head.

For PRE_GAME type guidance, missing wave/readiness/location observations should
remain explicit conditional limitations. The `required_fields` list identifies
what is needed to turn a general draft candidate into a concrete tactical
recommendation; do not populate those observations from picks or type tags.
Likewise, a known source patch does not populate the draft's unknown manual patch.

## Remaining-roster source expansion

All remaining **160 individual champion documents** were fetched from the exact
official `16.20.1/data/en_US/champion/{id}.json` URLs. Each returned HTTP200,
declared `version: 16.20.1`, contained its expected single champion ID, and had four
basic/ultimate spell descriptions plus its passive. The bounded batch used six
concurrent requests, a 45-second per-request cap, no retries and no paid service.
Exact URL, request/retrieval UTC times, status, byte count and SHA-256 receipts are
preserved in [source-receipts.json](../../evidence/queue/q05-expansion/source-receipts.json).
All 160 pinned responses are archived separately from the original sources;
there are no failed or remaining fetch IDs.

The expansion records **800 exact mechanic excerpts** (passive + four spells per
champion). AI audited the source text and added **434 mechanistic label candidates**
across individual ability excerpts for **151** expanded profiles. A label is a
possibility candidate with its own source URL/hash/excerpt/patch boundary and at
least one limit. This is not 434 independent truths, approvals, match observations,
or validated tactical predictions. All rows remain `EXPLORATORY`; actual USER_WEB
reviews, gameplay validations and coaching accuracy remain zero/zero/null.

Candidate evidence links are deliberately sparse. Literal self-rooting is not
enemy catch control; charging a spell/weapon is not movement; pulling up a shield
is not pulling an enemy; a grappling hook into terrain is not enemy capture; an
ally's dash or a pet's jump is not attributed to the caster's own body. Reflecting
or destroying enemy projectiles does not become caster poke. A named spell such
as Grasping Roots without a stated control effect does not establish that effect.
AI-reviewed exclusions and additional direct mechanic readings are recorded in
[audit-decisions.json](../../evidence/queue/q05-expansion/audit-decisions.json),
with the complete excerpt/label audit in
[mechanic-audit.json](../../evidence/queue/q05-expansion/mechanic-audit.json).
The text locator patterns are evidence discovery aids, not executable rule
conditions, a game evaluator, or a USER_WEB review.

Nine expanded profiles have all passive/spell descriptions archived but no
sufficiently clear threat/protection label under this conservative interpretation:
**Gangplank, Hwei, Kalista, Karthus, Kindred, Quinn, Smolder, Teemo, Vladimir**.
Their labels stay null. This records uncertainty rather than declaring that these
champions lack threats or protection. Other expanded rows also retain null
categories where only one kind of mechanic is supported. `detailed_profile_ids`
now records source-examined profiles, including these nine uncertain profiles;
it is not a completeness or approval claim.

Original 13 profile objects, all original source files/receipts, type rules,
priority candidates and the separate 17-spec executable catalog are unchanged.
The expansion does not automatically compile new profile labels into that
catalog. Main owns any later adapter publication after source claims are inspected.
All phase strengths/jungle power styles/cooldown arrays remain null for the full
173-champion roster. For all expanded 160 rows, lane style and positions remain
null too. Combat-class tags do not establish optimal lane positions, and static
build16.20.1 does not fill the unknown gameplay patch.

## Verification and reproducibility

Current expansion verification is separate from the original historical validator:

```sh
python evidence/queue/q05-expansion/classify.py --apply
python evidence/queue/q05-expansion/validate.py
```

The expansion classifier rebuilds solely from the pinned archived bytes plus
the original roster at Main baseline `9f9d9b9`. It does not re-fetch, approve or
activate anything. Running it without `--apply` produces an evidence preview only.
The dedicated validator verifies all 173 unique roster IDs, unchanged original13
profile objects, all160 official documents, all800 exact mechanic bindings,
candidate limits/unknown boundaries, exact source versions, and unchanged
original builds/validators/receipts/rules/executable catalog. Current receipt:
[q05-expansion/validation.json](../../evidence/queue/q05-expansion/validation.json).

The following original commands/receipt document the **initial13-profile delivery
at commit501255d**. They are not the validator for the expanded roster. Do not run
the original builder against the expanded worktree: it recreates that older catalog.

In an isolated checkout of that original content commit:

```sh
python evidence/queue/q05/build_candidates.py
python evidence/queue/q05/validate_candidates.py
```

The historical builder uses only archived official bytes and never changes product
state. Its unchanged historical validator checks source hashes, exact source locators/excerpts, all 173 unique
identities, 13 detailed profiles, 160 unknown-only profiles, ten priorities,
all five role views, unknown unsupported numeric/power fields, and the universal
EXPLORATORY/no-approval/no-coaching boundary. Receipt:
[content-validation.json](../../evidence/queue/q05/content-validation.json).

Source review correction: Sylas E self-pull does not establish enemy control; the
unsupported grab-pick interpretation was removed. Original excerpt/HTTP bytes and
first RED proof remain preserved, and no unarchived gameplay knowledge replaces it.
