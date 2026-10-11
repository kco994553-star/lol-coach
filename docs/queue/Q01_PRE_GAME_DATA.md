# Q01 — PRE_GAME required data and source boundary

Checked **2026-10-11 UTC**. Intake `0337d915633f6ad5719f55de1252f05e06621c9b`.
This is the Queue v1.1 data specification and a public-source acquisition audit,
not a collector implementation, Riot product approval, stored `REVIEWED` knowledge,
or real-match coaching validation. Real Player/Decision/Coach N=0; accuracy=null.
It adds no common-contract or application changes.

## Required inputs and acquisition

PRE_GAME uses information visible to the player before game start, operator
entries with provenance, and patch-bound static knowledge. It never obtains
unrevealed enemy picks, anonymous-player identities, or hidden opponent runes.
A source being readable does not establish permission for every use of its data.

| Required data | Source and acquisition timing | Availability scope and actual collection verification | Use limits and missing handling |
|---|---|---|---|
| `phase`, session/revision and observation time | Manual visible client phase before generation; a future validated local League Client adapter could observe phase during pick window | Existing manual draft stores nullable `phase` and `observed_at`; no automatic phase collector verified. Game Client Live Data is in-game, not a pregame phase source | Confirm PRE_GAME for output. Unknown phase/start transition blocks dynamic gameplan; retain input as an unverified record. A label alone is not automatic start detection |
| Selected position | Explicit user choice: `TOP`, `JUNGLE`, `MID`, `ADC`, `SUPPORT`, before selecting personal advice | Required for all five positions; not limited to the four ADC knowledge examples. Existing capture accepts `BOTTOM` in role assignments, not a separate `my_position` | Product vocabulary uses ADC; legacy BOTTOM must be explicitly mapped at a future adapter boundary. Missing position means no position-specific personal plan; never default ADC |
| `my_position` | Explicit player confirmation, stored separately from participant roles | New required semantic input; absent from existing draft input schema | Intended position is not champion identity or actual observed lane. A changed/swap position invalidates affected prior advice; conflict is preserved |
| `my_champion` and own slot | Explicit selected/locked champion and own team/slot, acquired during visible pick window | Existing draft can hold picks by side/slot but has no separate own-player identity or `my_champion` field. Manual path verified structurally, not against a live client | Keep independent of `my_position`. Never infer the player from the first ally row, champion archetype, name, or selected position. Missing own champion suppresses champion-specific advice |
| All ten champions | Visible picks by `(ALLY/ENEMY, slot 1..5)`; refresh on reveal/lock/swap | Required ten-slot coverage model; partial drafts allowed. Existing capture stores up to ten pick rows with nullable champion. Live all-ten pregame collection NOT_AVAILABLE | Unpicked/unrevealed/unreadable slots are null+reason, never filled from predictions. Store locked vs tentative status if independently known; a pick is not a role |
| All ten roles and uncertainty | Visible role assignment or explicit manual assignment, before plan generation and after swaps | Existing `role_assignments` has side, slot, role or null, and required uncertainty text. No verified automatic all-ten role source | State `KNOWN`, `UNKNOWN`, `CONDITIONAL`, `CONFLICTING` or `STALE` with evidence. Flex picks keep multiple candidates/conditions; role duplicates or contradictory assignments are not silently repaired. Slot order is not role order |
| Runes, per participant/subfield | Own visible pregame rune page/manual entry; other players only what is actually exposed by an allowed source at that time. Static labels from Data Dragon runes file | Static rune catalog HTTP200; no pregame selected-rune collector implemented. Live Client official docs expose active-player full runes versus other-player basic runes **during game**, which does not prove all-ten pregame visibility | Preserve known keystone/tree separately from unknown minor runes/shards; `PARTIAL` must list known/missing fields. Unknown page is null+reason, not a recommended page. No rune-dependent damage/haste conclusion without relevant verified selections |
| Summoner spells, per participant/slot | Visible pregame selection/manual entry, refreshed on selection change; static spell IDs/labels from Data Dragon | Static summoner catalog HTTP200; no pregame selected-summoner collector verified. Live Client player summoner descriptions are an in-game schema example | Each of two slots may be known/unknown independently. Do not infer Flash/Smite/Teleport from role or last match. No claim of current availability, cooldown remaining or use history |
| Patch and static-data build | Player/client version with source and region when available; explicit operator entry remains MANUAL. Resolve Data Dragon component build before reading patch-sensitive values | Data Dragon versions and NA realm fetched: `16.20.1`. This pins downloaded static data only. Runtime/session patch remains UNKNOWN unless separately evidenced; NA does not establish another region | Keep `session_patch`, region, static build and source patch applicability distinct. Unknown/mismatched/unsupported patch disables patch-sensitive numbers and rules; general principles may state their narrower scope. Do not assign session patch from latest DD |
| Source provenance/capability | At every acquisition: source URL/path, received time, observation time, source version/hash, perspective, field visibility and scope | Existing draft declares source author/perspective/description and stores revisions/hash, but declarations remain UNVERIFIED. Public receipts below demonstrate static fetches only | Hash checks detect changed bytes, not semantic truth. Missing field stays null+reason; no synthetic confidence or automatic OBSERVED/REVIEWED promotion |
| Applicable matchup/team knowledge | Existing reviewed catalog with explicit champion/role/patch/required-field scope, read after inputs pass gates | This task creates no rule or review decision. Source candidates and policy checks do not create stored REVIEWED versions | Unsupported cells remain 미확인/NOT_AVAILABLE. A broader ten-player input model does not mean all-champion or all-role knowledge coverage |
| Static ability/summoner base cooldown reference | Patch-pinned static source plus independent mechanics source; acquire before pregame study, never from casts | Candidate collection detailed below. No verified full cooldown catalog or remaining cooldown collection | Base rank arrays may support study only after semantics/patch/review gates. Missing or disputed semantics means NOT_AVAILABLE; no guessed scalar |

Bans may be retained from the existing visible draft capture as optional context;
they cannot substitute for missing champions. Live HP, mana, gold, items, current
level, map positions, vision, minions, events or cast timestamps are not required
PRE_GAME inputs. Planned levels/items/runes are explicit scenarios, never actual
future game observations. Scope here contains no own/allied live feature.

## Existing capture, draft and R5 evidence

- `coach_v1/draft.py`: `_INPUT_FIELDS` contains title/phase/patch/observed_at,
  visible picks/bans, role assignments and source. Nullable input is deliberate;
  records are immutable revisions. It does not acquire client data or generate
  a gameplan. Separate own identity, position, champion, rune and summoner inputs
  above describe the v1.1 requirement, **not existing implemented fields**.
- `coach_v1/capture.py`: one-shot fixed loopback
  `https://127.0.0.1:2999/liveclientdata/allgamedata`, private unverified envelope,
  no polling/advice/upload. This is offline adapter research, not a PRE_GAME
  collector or live cooldown feature.
- `docs/R5_DATA_ACCESS.md` and `evidence/r5/HISTORY.md` distinguish documentation,
  synthetic collector checks and actual game collection. Initial sample failure
  is retained in `evidence/r5/official-sample-20261004/status.json`; the successful
  retry is `evidence/r5/official-sample-retry-20261004/receipt.json` and `audit.json`:
  DOCUMENTATION_SAMPLE, 6,561 bytes, SHA256
  `d754b6c27edf950679dd9478742a8c4b9402e70101a3b46764c28f2aeafd72d3`,
  only one example player, authenticity unverified, coaching disabled. This is
  neither ten-player collection nor a real game.
- `evidence/r5/local-connectivity-status.json`: 2026-10-04, local PAYLOAD_DOWNLOAD
  failed with `ENDPOINT_UNAVAILABLE`; official CA preparation succeeded. No new
  local client connection is claimed in Q01. **BLOCKED_EXTERNAL** applies only
  to real local collection/adapter validation requiring the game PC. Public
  source audit, manual PRE_GAME specification and other queue work can continue.

A future automated draft adapter must separately verify endpoint field semantics,
player-visible scope, draft/start timing, own slot binding, phase changes and
revision invalidation on the game PC, and disclose its endpoints through Riot's
Developer Portal. LCU is unsupported; it is not equivalent to the documented
in-game Live Client API. No account/API-key/client/registration access was obtained.

## Official policy checked by actual HTTPS access

Public HTTPS retrievals on **2026-10-11** returned HTTP200. Exact source hashes,
URLs, receipt times and extracted text are retained under `evidence/queue/q01/`.

| Official URL | Verified content and consequence |
|---|---|
| https://developer.riotgames.com/docs/lol | Developer API Policy, Game Integrity: “Products must not use or incorporate information not present in the game client that would give players a competitive edge (e.g., automatically or manually allowing tracking enemy ultimate cooldowns), especially when such data is not already accessible through regular gameplay.” Therefore no enemy live timer, estimate, inferred remaining cooldown or manual tracking flow |
| https://developer.riotgames.com/policies/general | Product Registration requires registration/audit and audits of feature changes; Game Integrity prohibits unfair advantage/de-anonymization and permits highlighting important decisions with multiple choices. Reading this page is not registration or Riot's approval of this product |
| https://developer.riotgames.com/policies/game-specific | Reachable game-policy index, displaying LAST UPDATED AUGUST 21, 2026. It does **not** itself contain the LoL cooldown clause; that clause is verified in `/docs/lol` above |
| https://developer.riotgames.com/docs/lol#data-dragon | Static champion/item/rune/summoner data are made available for third-party developers. Updates are manual and may lag; DD/client regional versions can differ. This is static-data coverage, not live-state access |
| https://developer.riotgames.com/docs/lol#league-client-api | League Client API is locally served and not officially supported for third-party use; no guarantees of complete documentation/uptime/change communication. Riot asks developers to register or annotate their application with endpoints and usage |
| https://developer.riotgames.com/docs/lol#game-client-api | Game Client APIs are HTTPS and locally available to native applications. Live Client describes active-player full runes, player basic runes and summoner descriptions. These are in-game documentation, not a draft-data guarantee |

Fragment links identify document sections; the actual retrieval receipt is for
`/docs/lol`. Static PRE_GAME study under these constraints is the project's
permitted scope; this audit is not a blanket official compliance ruling. No
additional live feature follows from static-data availability. On game start or
unknown phase, the PRE_GAME gameplan obeys DESIGN's gate; Q01 defines no live
cooldown display, including own or allied tracking.

## Cooldown source model and collection coverage

Data Dragon alone cannot confirm a cooldown's gameplay meaning. Every candidate
needs champion ID, spell slot/variant, rank basis, base seconds array, DD build,
applicable game patch/mode, primary URL/hash, second-source URL/hash/check date,
mechanic category, conditions, source conflicts, review state and missing reason.
Arrays are usually **ability rank**, not champion level; if a mechanic scales by
champion level, record that separately. Retain arrays rather than selecting an
unobserved rank or converting them into cast/reuse times.

Verified candidate primary URLs (HTTP200, **2026-10-11**):

- `https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/champion/{Ashe,Caitlyn,Kaisa,Yunara,Ahri}.json`
  denotes five individually fetched URLs; exact expanded URLs and 20 Q/W/E/R
  records are in `source-checks.json`. The chosen five do not establish all-ten
  selected champions' or all-champion coverage.
- https://ddragon.leagueoflegends.com/api/versions.json
- https://ddragon.leagueoflegends.com/realms/na.json
- https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/runesReforged.json
- https://ddragon.leagueoflegends.com/cdn/16.20.1/data/en_US/summoner.json

Verified **second mechanics source** candidates (public LoL Wiki, not Riot
approval; HTTP200 on **2026-10-11**, original HTML hashes and text excerpts retained):

- https://wiki.leagueoflegends.com/en-us/Ashe
- https://wiki.leagueoflegends.com/en-us/Caitlyn
- https://wiki.leagueoflegends.com/en-us/Kai%27Sa
- https://wiki.leagueoflegends.com/en-us/Yunara
- https://wiki.leagueoflegends.com/en-us/Ahri
- https://wiki.leagueoflegends.com/en-us/Ability_haste

Wiki pages are mutable, contain both current descriptions and historical patch
notes, and are not automatically pinned to DD `16.20.1`. Review must distinguish
current ability text from historical changes and establish patch applicability.
URL access, matching numbers, or two AI readings is insufficient for REVIEWED.
Initial Wiki requests without the audit User-Agent returned403; those failed
attempts remain alongside successful retries. A Meraki aggregate request reached
HTTP200 but its bounded payload was truncated and failed JSON parsing; it is
**rejected as usable evidence**, not a confirmed second source.

| Category | Collected examples and source semantics | Required handling |
|---|---|---|
| `normal` | Ashe R DD `[100,80,60]` seconds at ability ranks1–3; Wiki current R text matches. Caitlyn Q DD `[10,9,8,7,6]` seconds at ranks1–5 matches current Wiki Q text | Candidate numeric agreement only. Before display require applicable patch/mode and completed knowledge review; zero-haste statement only under conditions below |
| `charge` | Caitlyn W DD `[0.5,0.5,0.5,0.5,0.5]` is cast lockout; Wiki separates lockout0.5 from recharge `[26,22,18,14,10]`. Ashe E DD `[5,5,5,5,5]` is cast lockout while Wiki recharge is `[90,80,70,60,50]` | Store inter-cast lockout, recharge and max charges as separate quantities. DD array alone cannot represent replenishment or available charges. Require conditional mechanics source URL; otherwise NOT_AVAILABLE |
| `refund-reset` | Kai'Sa W DD `[20,18.5,17,15.5,14]`; Wiki current evolved-W text says hit on enemy champion refunds75% of cooldown. Yunara R/current state descriptions include ability cooldown reset/reduction on entering/exiting her transformed state | Preserve trigger and spell variant. Base array is not an unconditional interval; no live hit/cast/takedown event processing. Missing conditional source or unresolved trigger means NOT_AVAILABLE |
| `stack` | Ashe Q and Yunara Q DD arrays are all zero; Wiki describes Focus/Unleash stack requirements | Zero is not READY or freely recastable. Retain stack prerequisites as static mechanics only; no live stack count/reuse calculation. Without verified condition/source, NOT_AVAILABLE |
| `evolve` | Kai'Sa Wiki describes stat-triggered ability evolution and evolved W refund; Yunara has transformed spell variants rather than permanent evolution | Identify variant, prerequisite and mechanic separately; do not collapse transformation into evolution or assume pregame evolved state. Conditional source URL required; without it NOT_AVAILABLE |

Categories can overlap (`evolve`+`refund-reset`, `charge`+`refund-reset`). Do not
force a mechanic into `normal` merely because DD has a `cooldown` array. Every
conditional record must retain the URL that establishes the condition; a generic
reference to “Wiki” or a sourced champion name is not enough.

**Zero-haste upper bound:** for a reviewed conventional mechanic, same known
ability rank, same patch/mode/variant, nonnegative applicable haste and modifiers
that only shorten the cooldown, its base zero-haste value is an upper bound on
the full nominal interval. Unknown rank requires the full rank array, not a
chosen number. Negative haste, extension effects, mode overrides, charge rules,
refunds/resets, stacks or unresolved mechanics require separate conditions and
may invalidate a general upper-bound claim. Do not calculate effective cooldown
from assumed haste. Even a valid bound describes a static mechanic; it never
establishes remaining cooldown, current readiness, time of cast, or enemy reuse.
Summoner haste has its own scope; ability haste must not be applied to summoners
by default. No effective/live formula is implemented in Q01.

**Conflicts:** preserve both original values, URLs, hashes, patch/rank/variant and
semantic quantities; use CONFLICTING and block the disputed numeric claim if
conditions cannot reconcile them. Caitlyn W/Ashe E lockout-versus-recharge is a
verified coverage gap in DD, not proof that either source is numerically wrong.
No resolved cross-patch conflict or fully reviewed catalog is claimed. A new
patch or source change invalidates affected prior source applicability.

**Remaining coverage:** only 20 primary spell candidates from five champions
were fetched. Patch pinning/independent mechanical verification/review remains
incomplete; uncollected champions, passives, mode overrides, all conditional
variants and summoner cooldown semantics are NOT_AVAILABLE for numeric coaching
until their own gates pass. Every participant's **remaining cooldown is always
NOT_AVAILABLE in this PRE_GAME scope**. No live enemy cooldown tracking, manual
timers, elapsed-time estimates, cast logs, OCR-based timers or inferred ready
states; no own/allied live cooldown feature.

## Verification and delivery boundary

`evidence/queue/q01/source-checks.json` records actual public retrieval results;
`riot-*.txt` contains extracted official document text and `wiki-*-excerpts.txt`
contains source-numbered keyword excerpts, including historical lines for
context. Raw HTML hashes identify fetched bytes; retained-text hashes identify
the extracted artifact, and are different quantities. Public static acquisition
is verified; data accuracy, runtime patch and real local collection are not.

Verification checks doc/receipt linkage, local retained-file hashes, explicit
failure preservation, static candidate counts, required vocabulary and allowed
changed-path scope. This documentation-only change runs no collector and changes
no application runtime. Existing R5 synthetic tests and parent regression checks
are evidence of their own scope, not proof of Q01 real-game collection.

## v1.4 Q15/Q18 additive source inventory
Riot League-V4 KR tier/division entries seed transient PUUIDs; Match-V5 ASIA ranked420/map11 match and timeline provide champion/teamPosition/gameVersion, game time, participantFrames totalGold/xp/minionsKilled/jungleMinionsKilled/level/position and public events. Missing position/field/frame stays unavailable; no wave, vision, enemy last-seen or allied skill readiness inferred. Official sources https://developer.riotgames.com/docs/lol and https://developer.riotgames.com/docs/portal; source retrieval receipts/hashes: evidence/queue/q15/source-metadata.json.

App/method limits and counts come from X-App-Rate-Limit/X-Method-Rate-Limit headers,429 Retry-After; bounded waits/retries/request budget. Development keys expire24hours; personal project keys require Riot portal registration. Keykind remainsUNKNOWN from request status alone;401/403 can mean expiration/authorization/path and are BLOCKED_EXTERNAL. User reports RIOT_API_KEY GitHubSecret present; secret enumeration403 was access restriction, not evidence it is absent. Only trusted main manual/scheduled workflow uses it; no fork PR job. Store no credential values/raw identity-bearing JSON in repository/logs/public artifacts.

Anonymous DERIVED patch/tier aggregates use explicit formula versions, match-hash deduplication, sample counts and95%StudenttCI precision policy. Same-position pooled reference includes overlapping participants through independent match-cluster contributions; tier is current league seed, not all historic participant ranks. Q18 coordinate-median distance is descriptive proxy; minute-only data cannot approve stage tactics. Numeric gameplay patch discovered from eligible collection is collection lineage only, never substituted for the user's patch. See Q15_COLLECTION.md,Q18_MOVEMENT.md and contracts/pregame-v3-amendment.md.
