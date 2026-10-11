# Q02 — existing implementation audit

Queue v1.1, audited 2026-10-11 against intake
`0337d915633f6ad5719f55de1252f05e06621c9b`. Scope is read-only implementation
analysis plus this document and `evidence/queue/q02/`. Frozen v1.0 payloads,
legacy behavior, old fixtures/expected values, PR10 contracts and historical
receipts remain unchanged. Main owns the supplemental queue contract and
integration; this audit does not activate a capability.

## What exists, and what its evidence proves

| Layer | Actual implementation and reusable path | Boundary or missing connection |
|---|---|---|
| Preserved legacy rules | `legacy/backend/decision/engine.py:analyze`, `permission.py:calculate_permission`, `evaluator.py:evaluate_actions`, `selector.py:select_recommendation` execute permission/commitment, jungle uncertainty and action selection rules. | These are executable legacy rules, not a champion knowledge catalog. Frozen validation explicitly preserves 16 action enums/9 definitions and return-path insensitivity as known gaps. Legacy VALID/P0–P5 cannot be translated into v1 sufficiency/assessment. |
| R3 symbolic evaluator | `coach_v1/engine.py:run_review` executes state/evidence eligibility, action missingness/feasibility/expiry, scenario sufficiency, six-dimension dominance, comparison contradiction detection and timely information requests. | Entry requires `mode=TEST`, `evidence_kind=SYNTHETIC`, and `allow_synthetic=True`. Feasibility, favorable/unfavorable assessments and comparison relations are supplied annotations. It does not calculate combat, matchups, damage, cooldowns, win chances or a gameplan; `recommendation=None`. |
| Evidence/state | `coach_v1/models.py` immutable Pydantic contracts and `coach_v1/state.py:reduce_snapshot`, `canonical`, `digest` implement provenance, event/reception cutoffs, patch/clock matching, conflict/lineage handling and UNKNOWN/CONDITIONAL/STALE states. | MANUAL and INFERRED remain CONDITIONAL. Role strings or captured screenshots do not become independently verified player facts. No guessed TTL, geometry or intent is computed. |
| Saved knowledge workflow | `coach_v1/knowledge.py:KnowledgeStore` creates EXPLORATORY proposals, exact immutable versions, source bindings and CAS heads; PR10 adds explicit USER_WEB REVIEWED/REJECTED decisions. | Storage of knowledge and existence of an approval route do not establish that actual user-approved content exists. The evaluator never reads this store. |
| Manual draft | `coach_v1/draft.py:DraftStore` saves immutable operator captures, CAS history, exact downloads, retries and explicit deletion. `web_r4/draft.js` preserves nulls, membership/order and unedited strings. | Every stored record remains UNVERIFIED, `gameplan_status=NOT_GENERATED`, `coaching_enabled=false`. It provides neither automatic client collection nor a gameplan. |
| Research/capture | `coach_v1/capture.py` makes an exclusive, bounded one-shot loopback capture; `coach_intake/audit.py:inspect`, `video.py:index_transcript` and `coach_v1/research.py` support diagnostic imports and saved notes. | A hash establishes byte identity, not game authenticity, phase, patch confirmation, player visibility or match end. Research imports are not evaluator input adapters. |
| Real-source diagnostics | `coach_audit/extraction.py:extract` and `coach_audit/postgame.py:diagnose_postgame` retain diagnostic/raw/derived provenance and archive scope. | They do not supply a player information state or eligible decisions; postgame `decision_candidate.facts=[]`, status BLOCKED, coaching remains false. No real coaching denominator is added. |
| Private web service | `coach_v1/server.py:Workbench`, `Handler.dispatch` run an authenticated loopback service, two SQLite stores and one-worker TEST job queue. | Actual namespace is `/dev/v1`; Frozen `/v1` API table is design, not evidence that every endpoint exists. Status reports SYNTHETIC_ONLY and no gameplan. |

`tests_r3/helpers.py:case` uses `knowledge_status=REVIEWED` with
`knowledge_ref=fixture://annotation/v1`, patch SYNTHETIC-1 and manually supplied
relations. `run_review` checks the inline status and exact assessment patch, but
does not dereference `knowledge_ref`, validate a stored USER_WEB decision or
interpret knowledge applicability. Such fixtures cannot seed approved product
knowledge or certify real match quality.

`tests_mvp/test_knowledge.py:rule` starts with UNKNOWN applicability and a
synthetic claim. `test_knowledge_review.py:fixture` creates a temporary rule and
supplies browser-header fixtures plus prose scope (`26.20`, 애쉬, etc.). The
actual HTTP/SQLite and Chrome tests verify the decision workflow. Their
temporary REVIEWED rows and actor labels are not user-reviewed champion content.
No tracked SQLite/database file or production knowledge catalog is supplied in
this worktree. An external personal database was not inspected: its content and
number of current REVIEWED rules are **unverified**, not inferred to be zero.
PR10 approval of the workflow is separate from approval of any knowledge claim.

## Draft, self selection, runes and patch confirmation

The accepted capture has exactly `title`, `phase`, `patch`, `observed_at`,
`visible_picks`, `visible_bans`, `role_assignments`, `source`.
`coach_v1/draft.py:_capture` rejects extra fields. Picks/bans are up to ten exact
rows `{side: ALLY|ENEMY, slot: 1..5, champion: null|string}` with no duplicate
side/slot per list. Role rows are `{side,slot,role,uncertainty}`; role is null or
TOP/JUNGLE/MID/BOTTOM/SUPPORT and uncertainty is required text. Champion strings
have no champion-ID registry or canonical alias validation. There is no rule
enforcing champion uniqueness or cross-list pick/ban consistency.

| Needed concept | Existing field or mechanism | Consequence for Q03 |
|---|---|---|
| Confirmed pregame phase | Nullable free text `capture.phase`, with UTF-8/nonblank/length validation only | No allowlist, observed transition, confirmation flag or game-start invalidation exists. A nonempty string is not verified pregame status. |
| Patch input | Nullable free text `capture.patch`; legacy TEST session patch is required text | No available client/official patch confirmation adapter, parsed patch syntax/range matcher, supported patch registry or explicit confirmation state. UI label “확인한 패치” is an operator entry prompt, not attestation. |
| Knowledge patch scope | Prose `patch_range` plus applicability strings in KnowledgeStore | PR10 `_review_scope` rejects empty/UNKNOWN/미확인 values; it explicitly does not verify patch existence, syntax, claim correctness or compatibility with a draft. Preserve original prose; define structured matching additively. |
| Own draft identity | ALLY slots and declared roles | No `self_slot`, own champion identity, own role selection or mapping to the actual active player. BOTTOM alone does not identify the user. Persist explicit own side/slot selection with its source revision. |
| Spatial self position | R3 arbitrary field key `self:position` (usually synthetic string `lane`) | This is an in-game observation, distinct from team role, own draft slot and lane assignment. The R3 scalar value union is not a vector geometry schema. |
| Runes | No draft rune fields, rune API or UI | A future exact user-selected rune set needs its own additive contract. Unknown runes must not be replaced by champion defaults. |
| Observation time/source | Nullable offset timestamp plus `{author,perspective: PLAYER|UNKNOWN,description}` | Operator declarations stay UNVERIFIED; server `received_at` is separate UTC storage time, not game time. |

Two existing rune/position data paths are diagnostic only:

* `coach_audit/extraction.py:EXTRA_PATHS` reads keystone ID at
  `/allPlayers/0/runes/keystone/id`, champion and `position` role label from the
  same first roster row. It explicitly marks that roster row **not
  identity-joined to activePlayer**, and every fact `decision_eligible=false`.
  The preserved official documentation sample
  `evidence/r5/official-sample-retry-20261004/raw.json` also has
  `activePlayer.fullRunes`; no draft/full-rune adapter consumes it. Documentation
  samples are not actual player rune confirmation.
* `coach_audit/postgame.py` joins exact pinned Match/Timeline archive identities,
  reads Match `info.gameVersion`, participant `teamPosition`, and cutoff-bound
  timeline `position.x/y`. Those are archive patch/role/coordinates. Opponent
  coordinates have `player_known=false`; no PRE_GAME patch or own draft-slot
  confirmation follows from them.

## Existing API and persistence seams

`Workbench` constructs `DraftStore(db)` and
`KnowledgeStore(str(db)+'.research.sqlite')`. Main DB schema2 comprises
`sessions/cases/jobs/idempotency/tombstones/draft_captures/draft_snapshots`;
research schema2 comprises `resources/note_history/knowledge_rules/
knowledge_delete_receipts`. A numeric version 2 means different schemas in these
two databases; they cannot be treated as interchangeable.

The following are actual reusable routes in `coach_v1/server.py:Handler.dispatch`:

| Routes under `/dev/v1` | Behavior |
|---|---|
| `/draft-captures`, `/{id}`, `/{id}/history`, `/{id}/revisions/{revision}` | Create/list/read/edit/history/delete operator captures. POST and PUT require `Idempotency-Key`; PUT/DELETE compare expected revision. |
| `/knowledge/proposals`, `/{id}`, `/{id}/versions/{version}` | Create/list/current or exact-version read, CAS append and whole-chain deletion. List entries include `current`, but both current and historical versions are returned. |
| `/knowledge/proposals/{id}/decisions` | Dedicated authenticated same-origin browser metadata gate; selected exact version plus expected current head, decision and patch/applicability. |
| `/research`, `/{id}`, notes/history/revisions routes | Saved diagnostic/transcript resource and exact immutable note revisions; source deletion cascades knowledge references. |
| `/sessions`, `/{id}/case`, `/{id}/reviews`, `/jobs/{id}`, `/reviews/{id}` | Separate TEST sessions/cases/job evaluation and stale-revision results. No pregame generation route. |

Knowledge source binding requires a saved VIDEO or RAW_DIAGNOSTIC resource and
exact `{resource_id,anchor,note_revision}`, recording report/note hashes.
`KnowledgeStore.decide` preserves selected content/source and selected payload
hash, changes only patch/applicability, appends a new version with
`supersedes=expected_version`, and allows historical selected candidates. A later
proposal returns to EXPLORATORY; historical REVIEWED content must not silently
override a current rejection or edited head. Current and selected version IDs
are intentionally different concepts. `_WEB_REVIEW_AUTHORITY` is internal;
trusted-click/native-confirmation UI and browser metadata are bounded local
controls, not cryptographic proof of a human. See PR10 contract for exact limits.

Useful storage mechanisms to reuse are `Store._db`/`ResearchStore._db`
transaction patterns (foreign keys, BEGIN IMMEDIATE, rollback), canonical JSON
hashing, append-only parent chains, exact CAS/idempotency checks, response byte
budgets and pure stored-content validators. Existing main/research schema
validators compare exact SQLite objects/SQL/PK/FK sets. Adding a table, trigger,
column or payload field directly causes incompatibility; old record validators
also require exact key sets and existing status constants.

The original `Store` constructor supports schema1 only; the live server uses
DraftStore schema2. `ResearchStore` constructor is likewise legacy schema1;
KnowledgeStore performs the schema2 migration. Do not open a schema2 DB with
legacy constructors or relabel new records as an old schema to evade validation.

Main's Q03 integration decision is an additive `PregameWorkbench` subclass,
separate pregame sidecar and `/pregame` page that import original draft snapshots
while preserving original server/UI/DB bytes. Self slot, phase/patch confirmation
and runes can reference an immutable draft ID/revision/input hash. Structured
specifications will bind an existing Research RAW_DIAGNOSTIC resource, immutable
note and proposal marker/hash, reuse PR10 native user approval, and select
current REVIEWED heads only. These are selected **new implementation seams**,
not capabilities already present at intake. Typed scope/specifications must be
checked explicitly; existing free prose must never be interpreted as a rule.
If an existing DB is extended in future, that requires a versioned migration,
pre-migration recoverable backup, read-only validators and backup/restore
support. `coach_v1/backup.py`
currently accepts versions 1/2 with exact schemas and exactly two database
members plus manifest; a new sidecar is **not automatically included**. Its
backup/deletion lifecycle needs an explicit design either way.

No current gameplan persistence, selected rule-version set, draft-to-result
link, generated expiry record or cross-store transaction exists. A generation
must pin draft/self/rune/patch inputs and exact accepted rule versions/hashes,
handle current-head changes/source deletion, and mark older results stale while
retaining immutable history. Avoid assuming a SQLite FK can span two DB files.
Draft deletion currently removes all draft snapshots; source deletion currently
cascades knowledge versions and records a non-private deletion receipt.

## Evaluator reuse without pretending product integration exists

Preserve `coach_v1/engine.py:run_review` and legacy gates as regression targets.
Its evidence/sufficiency/expiry/dominance rules are reusable conceptual and
test mechanisms, but feeding actual draft records into TEST or relabeling them
SYNTHETIC would violate the existing boundary. `reduce_snapshot` can be reused
only for genuine observation-shaped inputs while preserving manual uncertainty;
it is not a patch/applicability matcher.

For the authorized pregame path, Main must define an additive deterministic
evaluator that selects explicit applicable current REVIEWED knowledge and emits
only source-bound claims or “미확인”. Existing stored `claim/mechanism/
counterexamples/limitations/required_fields` are prose/list content, not a
machine-executable rule language or fixed gameplan-cell mapping. Never infer
bot lane advantage, jungle synergy, level-three timing, damage or an invented
number from approval status alone. `contracts/scenarios.json` contains
DESIGN_EXPECTATION/NOT_RUN cases; its existence does not demonstrate executable
coverage. Frozen TEAM_DRAFT/KNOWLEDGE/SCOPE remain the design basis, with the
queue v1.1 supplemental contract owned by Main.

## Verification and evidence disposition

Fresh Q02 receipts are under `evidence/queue/q02/`: intake/source hash binding,
preservation, PR10 binding, protected9 and unchanged scoped unittest reports.
`verification-summary.json` records PASS for all thirteen checks; the unchanged
unittest suites ran 293 tests with no failures/errors/skips. Protected9 ran in a
temporary copy and Frozen27 hashes matched. No implementation was modified.
The fresh audit checks do not run Chrome, access a personal production catalog,
acquire real game data or increase Player/Decision/Coach evidence. Optional
pinned postgame-source tests require private exact source files and remain a
separate execution claim. Historical PR10 CI receipts at
`evidence/mvp/knowledge-review-pr10-ci.json` and
`knowledge-review-postmerge-ci.json` record Chrome124/124 and regression success;
they are reused historical evidence, not fresh Q02 browser execution.

Main's required unchanged regression commands, from repository root:

```sh
python -m pip install --disable-pip-version-check -r requirements-r3.txt
python scripts/verify_mvp.py
python scripts/browser_mvp.py
```

The existing full MVP verifier checks old111, protected9/Frozen27, legacy
backup23, draft store31/HTTP17/backup19, note history19/HTTP5, knowledge
store42/HTTP5/backup19/review13, postgame synthetic schema13 and deterministic
Node/UI guards. Browser launcher requires Playwright 1.62.1 and a supported
Chromium executable (`NODE_PATH`/`CHROMIUM_EXECUTABLE` as in
`.github/workflows/private-mvp-ci.yml`); it requires exactly 124 unique checks.
Do not weaken existing literal case IDs, expected values, timeouts or source
bindings to accommodate the new path. New queue tests belong in additive suites
and source-version bindings under Main's contract.

Optional real archive diagnostics are explicitly separate:

```sh
python scripts/verify_mvp.py --postgame-raw-dir /path/to/pinned-private-source-directory
```

Without that directory, pinned integration4 is NOT_RUN in default CI; synthetic
schema13 passing is not a substitute. `python -m validation` writes historical
evidence, so run through the MVP verifier's `protected_validation` temporary-copy
helper or an isolated copy. The untouched historical `verify_r7.py` binds a
pre-repair UI identity and is not a replacement for authorized MVP verification.

Q03 acceptance must add meaningful cases for explicit self selection, unknown
patch/phase/runes, scope mismatch, rejected/exploratory/current-head knowledge,
missing required inputs, stale draft/rule edits, source deletion, exact download,
restart/backup, delayed responses and mode/game-start gating. No actual approved
knowledge supplied means a valid “미확인” result, not automatic approval or
synthetic knowledge injected into the product. Real coaching N remains 0 and
accuracy null unless a separate qualifying validation establishes otherwise.
