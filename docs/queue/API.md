# PRE_GAME API v1 — finalized consumers

Server CLI: `python3 -m coach_v1.pregame_server --db private/workbench.sqlite --port 8765 --token-file private/token.txt --max-body-bytes 1000000 --max-observations 100 --max-actions 100 --max-scenarios 100 --max-comparisons 100 --max-pending-jobs 10`.
Page `/pregame`; legacy page `/` and every old `/dev/v1` route inherited without modification.
Same bearer token and Host/Origin protection. JSON request/response; error_code on failure.
All new route paths below start `/dev/v1/pregame`.

| Method/path | Request | Response |
|---|---|---|
| GET /status | — | {mode:PRE_GAME,automatic_collection:UNAVAILABLE,current_patch:null,knowledge_count:int,accuracy:null} |
| GET /inputs | — | list[{session_id,title,revision,input_sha256}] |
| POST /inputs | {input:InputDraft}, Idempotency-Key | saved input record201 |
| GET /inputs/{session_id} | — | saved current input record200 |
| PUT /inputs/{session_id} | {input:InputDraft,expected_revision:int}, Idempotency-Key | new input record200 |
| GET /inputs/{session_id}/history | — | list[all immutable input records] |
| GET /import-draft/{capture_id} | — | InputDraft from original current DraftStore capture; my_position/champion/slot null |
| POST /inputs/{session_id}/plans | {expected_revision:int}, Idempotency-Key | stored plan201, including validity/expiry_reasons |
| GET /inputs/{session_id}/plans | — | list[all stored plans with validity] |
| GET /plans/{plan_id} | — | stored plan with current validity and expiry_reasons |
| GET /knowledge | — | list[{proposal:exact current PR10 report,spec:RuleSpec|null}] |
| GET /candidates | — | list[RuleSpec] from executable candidate catalog, all EXPLORATORY |
| POST /candidates | {spec:RuleSpec} | {proposal:EXPLORATORY report,spec:RuleSpec},201; only proposes, never approves |
| GET /roster | — | {static_version:str|null,champions:list[{id,name,roles:list[Position]}]} |
| GET /export | — | {schema_version:pregame.archive.v1,inputs:list[records],plans:list[stored records],operations:list[exact retry receipts],sha256:str} |
| POST /restore | {archive:exact export object} | {status:RESTORED}; only empty pregame DB, otherwise409 |

Saved input record {schema_version:pregame.input.v1,id:32hex,session_id:32hex,revision:int,parent_id:32hex|null,created_at:UTC ISO,input:InputDraft,input_sha256:64hex}.
Plans return evaluator contract from contracts/pregame-v1.md + id/session_id/revision/input_revision/input_sha256/created_at/validity/expiry_reasons.
404 unknown IDs,409 CAS/idempotency/restore nonempty,422 typed errors. Max body and output inherited server limit.

## User review in new page
POST /candidates is a native import button (AI candidate authorship preserved). View full spec and sources.
Review button must require event.isTrusted and navigator.userActivation.isActive and native confirm,
then fetch existing `/dev/v1/knowledge/proposals/{rule_id}/decisions` with mode:same-origin,
Origin:location.origin, bearer token. Body selected_version=proposal.version,expected_version=proposal.version,
decision REVIEWED or REJECTED, patch_range/applicability exact proposal fields.
Import/propose code never sends decisions. Disable approve if patches empty or pending import/read/write.
Real browser verification must never approve actual candidate knowledge; synthetic approved fixtures isolated only.

## UI contract
Simple separate login (sessionStorage key lol-coach-dev-token reused), connection/logout;
10 row inputs, champion string/roster suggestions, definite position/candidates, provenance,
my_position/my_champion/my_slot independent; null/empty means unknown. Default patch null.
Runes/orders FULL/PARTIAL/UNKNOWN plus comma/newline values and source declarations.
Existing draft selector reads `/dev/v1/draft-captures` and uses import route. Golden example button fills only declared test input and labels demonstration; never imports knowledge approvals.
Save must capture exact body/key; ambiguous response retry reuses original operation then preserves later edits.
Any edits hide/currently expire local displayed plan; reopen requires confirmation for dirty form.
Create plan only from acknowledged saved input revision. Display seven cards:
① five map rows ② jungle ③ composition ④ my role ⑤ lane/route ⑥ fight/survival ⑦ changes/unknown.
Details reveal full saved input/evaluation trace/spec/source/version/exclusions. Apply text verbatim; UNKNOWN no invented advice.
Knowledge candidate review displays all sources/spec/counterexamples/limitations, current state/version; updates invalidate old view.
Logout/navigation/late reads cannot revive old plan or knowledge. No in-game view/timer/countdown/cooldown input.
Export button includes saved pregame input/plan histories; label existing backupformat1 excludes this sidecar.
