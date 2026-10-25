# GP23 + learning: independent whole-branch SPEC / QUALITY release review

Reviewed 2026-10-25 in `/workspace/lol-coach-gp23`, against base `8e67cce63a29decae9f64a21f7c387bf73824507`, current HEAD `a12330d` plus integrated working-tree changes. Read AGENTS, both approved GP23 specifications (44 IDs), learning taxonomy v0.1, implementation plan, worker reports, scoped review history, current implementation and relevant tests. The diff package predates the final unsupported-tag correction; this review inspected the current files and confirmed that correction.

**SPEC: CHANGES REQUIRED. QUALITY: CHANGES REQUIRED.** One P1 and two P2 findings below. No P0 found. The P1 prevents final release approval until its constrained-search behavior is corrected. Root has acknowledged the two learning findings and owns the correction/verification wave. This is the pre-correction verdict, not a claim that those subsequent edits failed.

Only this report was written. No product source, protected data/decision, external application, release, or repository metadata was changed. The reported full suite was not repeated. Independent verification used focused Node production-engine/search probes and authenticated requests to an isolated local server; the latter temporary fixture was cleaned up.

## FR-01 — P1: unknown or malformed learning context silently becomes an unrestricted result

`web_r4/learning-engine.js:18–20,30,33–34`.

The URL cleaner retains unknown values for many filters, but explicitly discards unknown roles and unresolved claims. Invalid identifier syntax is also erased for champion/opponent and other identifier fields. This converts an explicitly constrained learning link into successful browsing of all lessons, silently losing the user's requested context. A missing claim is especially problematic for source-bound backlinks: unrelated claims appear as the successful destination. The previous scoped search finding is only partially closed for these input classes.

Reproduced against the real 37-row index using `stateFromURL(fragment,data,knowledge)` then `filterLessons`:

| Fragment | Normalized constraint | Result |
| --- | --- | --- |
| `#learn=role=unregistered` | role becomes empty | all 37 rows |
| `#learn=claim=missing-claim` | claim becomes empty | all 37 rows |
| `#learn=champion=..%2FCaitlyn` | champion becomes empty | all 37 rows |
| `#learn=role=bottom` | `BOTTOM` | correct 21 rows |

The first frontend unit test explicitly expects invalid champion/role/claim to become empty, and the unknown-filter test omits role and claim, so a green suite does not cover this failure.

**Acceptance:** preserve the distinction between absent filter and supplied-invalid/unresolved filter. Return an explicit invalid/empty state, or retain a safe nonmatching constraint; never broaden to all lessons. Apply it to every filter dimension, including malformed encodings/identifiers and claim links. Keep canonicalization of valid lowercase IDs. Unknown private parameter names must still be omitted from canonical URLs. Exercise the real `stateToSearch → stateFromURL → filterLessons` path and a browser reload so normalization cannot erase the rejection state. A stale claim link should visibly explain that its referenced lesson is unavailable and allow an explicit user reset.

## FR-02 — P2: the authenticated search route rejects supported static-search inputs

`coach_v1/pregame_server.py:464–465`.

The HTTP adapter still applies identifier syntax to `patch`, although patches are exact source labels and the actual index contains `12.1 / Season 12`. It also rejects lowercase roles even though both pure engines accept/normalize them. Thus the documented shared search projection is not reachable through HTTP for valid static UI inputs.

Independent authenticated POSTs to `/dev/v1/learning/search`, through the real `create_server` fixture:

| JSON body | Actual HTTP result |
| --- | --- |
| `{"patch":"12.1 / Season 12"}` | 422 `INVALID_LEARNING_SEARCH` |
| `{"role":"bottom"}` | 422 `INVALID_LEARNING_SEARCH` |
| `{"role":"BOTTOM"}` | 200, total 21 |
| `{"patch":"16.20.1"}` | 200, total 7 |

The source patch containing spaces/slash is explicitly covered by the frontend test and rendered in the patch options. This is a real API incompatibility, not missing external content. It is P2 because the shipped static page invokes its local engine and does not depend on the POST route for ordinary browsing.

**Acceptance:** validate patch as a bounded control-free text label, canonicalize recognized role casing before validating it, and compare ordered lesson IDs across HTTP, Python and the browser URL route for all actual source-patch labels and lowercase known identities. Preserve authorization, private-key rejection, input bounds, and rejection of truly invalid roles.

## FR-03 — P2: a missed opportunity changes the operation sentence but leaves the decision/tag on the previous branch

`web_r4/loading-planboard.js:1043,1056,1069`.

With the production test fixture's ready wave/resource/follow-up assumptions, change only `planning.overrides.opportunity` to `MISSED`. `operationsAction` switches to the recovery/regroup paragraph because it includes `missed`. `decision_id` remains `CONNECT_GAIN`, and the ACTION tag remains `이득 전환 준비`, because both repeat a different predicate that excludes `missed`. The recovery paragraph describes unavailable allies/insufficient resources despite those selected assumptions remaining available/sufficient, so it does not explain the actual trigger.

Focused production output:

- `decision_id: CONNECT_GAIN`
- action begins `아군이 움직일 수 없거나 자원이 부족하면 ... 지원·재집결로 다음 행동의 여건을 바꾼다.`
- ACTION tag `이득 전환 준비`; CONDITION tag `아군 호응 가정`

The stop sentence correctly says not to follow an already-ended fight, so this is a limited coherence defect, not an unsafe pursuit recommendation or P1. It violates the intended single-final-decision derivation for tags and explanation.

**Acceptance:** derive operation decision/action/tag from the same resolved branch, and explain the missed opportunity directly without implying low resources or unavailable follow-up. A one-field AVAILABLE→MISSED pair should change all relevant output together while preserving the selected resource/support facts and exactly five actions.

## Confirmed behavior and bounded scope

- Current v5 situation validation is exact and preserves assumed/unknown/observed/stale provenance. PRE_GAME cannot accept historical observation wrappers. In the independent historical probe, a 2020 observed AWAY record remained retained metadata with effective value null; it did not become a current safe location. Other explicitly chosen wave assumptions can still produce a conditional slow push, which is distinct from using the stale sighting.
- Independent production probes: all-unknown → CHECK_WAVE and combat UNKNOWN; near enemy jungle + large incoming wave + declared handling budget → TRIM_RECEIVE, never FREEZE; unavailable actual contributors → combat BLOCKED, never nominal-count superiority. Advantage remains UNDETERMINED/probability null.
- Current unsupported Ornn scope remains GENERAL_ONLY with STATUS-only tags after the final owner correction. Each probed phase has exactly five actions and at most two tags. Conditional support does not become all-champion tactical approval.
- Top team/user responsibilities, retained comparison, phase prose/details and jungle translations are connected through the same current report/planboard. V1–v4 bypass v5 reconciliation; draft and UI explicitly retain old inputs until new Analyze.
- Per-actor threat ranking remains explicitly UNKNOWN, with unranked capability candidates and mechanisms in disclosure. This is an honest known GP23-23 limitation, not a completed actor-priority model. It must remain PARTIAL in status/evaluation; current source code does not disguise it as validated priority.
- Learning has real taxonomy/filter/card/source/reflection implementation: 4 groups / 20 topics / 80 leaves, 29 registry claim references, 8 link-only video candidates and 29 reflection practices. This is not 80 acquired lessons or newly verified video content. Actual accepted transcript/visual samples remain zero.
- Existing claims are referenced rather than copied into a second approved tactical corpus. Recovery remains null unless explicitly sourced; counterexamples are not relabeled as recovery. Permission-bound offline transcript records remain speech candidates, with disabled coaching and independent game/video clocks. No runtime provider/AI acquisition path was found.
- Public assets are explicitly listed. POST search authorizes before handling its body. Learning return URLs use opaque session tokens; gameplan full state stays session-local. Champion/role/opponent links and review-selection session restoration preserve their bounded context; source links suppress referrers. The FR-01 invalid-context loss is the exception noted above.
- No new auth relaxation, paid/provider call, protected decision manipulation, tactical approval, knowledge-registry rewrite or claimed gameplay efficacy was found in the inspected change. The old six practice scenes remain linked and their implementation remains intact.

## Existing P2 follow-ups and release evidence boundaries

The prior scoped review's validator-membership limitation and support/lane-pair discovery limitation remain applicable. The normal builder binds claims directly to the registry, while the offline bridge creates no tactical claims; do not describe `validate_index` alone as claim authentication. Lux/SUPPORT has no role-qualified results for bottom-pair claims; do not guess a new supported role to hide that coverage limitation.

Worker browser receipts and the root-reported 960-test run are supporting evidence, not independently rerun results here. Root must run stable verification after fixes, refresh exact source/artifact evidence and then record actual CI/deployment/rollback status. Unfinished results documents, external synchronization and deployment status are not counted as product defects in this review. No claim is made that all 44 GP23 items, per-actor threat prioritization, actual-video verification, or real-match effects are complete.

## Final scoped rereview — FR-01 / FR-02 / FR-03 closed

Rereviewed after the declared product-source freeze on 2026-10-25. **Current SPEC verdict: PASS for the bounded implementation and declared partial capabilities. Current QUALITY verdict: PASS WITH P2 FOLLOW-UPS. No remaining P0/P1 release-blocking product defect was found.** This supersedes the initial changes-required verdict above; those sections preserve the original reproductions. It does not certify pending full-suite/CI, release-document completion, deployment, actual-video acquisition, or tactical efficacy.

### FR-01 CLOSED — independent focused verification

The cleaner now distinguishes missing context from invalid supplied context with an `invalid=context` sentinel. Filtering fails closed, canonical URL serialization preserves the sentinel, and the page presents an explicit connection-condition error with reset. Reset preserves the safe session return token. Unknown private parameter names remain excluded.

Independently executed the real parser/serializer/filter path for unknown role, missing claim, malformed champion, malformed percent-encoded opponent, nonexistent lesson, control-character topic and control-character patch. Every vector returned zero rows and retained invalid state across three successive serialization/restoration cycles. Valid lowercase `role=bottom&champion=caitlyn` still produced eight rows; an unknown `private_match=secret` parameter did not survive serialization.

Inspected current DOM rendering/reset code and the frozen-source browser receipt `/workspace/gp23-artifacts/learning-browser/learning-browser.json`: passed true, 33 checks, no browser/HTTP/external-request errors. The receipt explicitly covers invalid role/champion/claim across reload and explicit reset with retained session return on PC and public static pages. Receipt hashes match the current engine and renderer. Browser execution is worker evidence; the focused engine probes above were independently rerun.

### FR-02 CLOSED — independent HTTP verification

The adapter allows bounded control-free patch labels and canonicalizes roles before validating its existing allowlist. Independently started an isolated real local server and compared complete JSON results with `search_index` for **all 12 actual source-patch labels**, including spaces, slash, parentheses and archived-description labels. Every authenticated request returned 200 and identical Python results. Lowercase `bottom` returned the same 21 rows as uppercase BOTTOM. An unauthenticated request still returned 401; an authorized private-context key still returned 422. No auth relaxation was needed or observed.

### FR-03 CLOSED — independent one-condition production pair

The implementation now uses one `operationsDecision` for its decision/action/reason/tag. Independently changed only opportunity AVAILABLE→MISSED with ready resource/follow-up inputs. Output changed from CONNECT_GAIN to RESET_OPPORTUNITY, its tag to `다음 기회 준비`, and its action/reason explicitly described the ended opportunity. The action no longer invents insufficient resources. Canonical resources remained SUFFICIENT and follow-up AVAILABLE. Exactly five actions and equality with retained delivery actions were verified.

### Remaining P2 / coverage follow-ups

- `validate_index` by itself does not authenticate claim membership/source binding against the authoritative registry. The normal builder and speech bridge maintain the safe bindings described above; keep this validator limitation documented until its boundary is extended.
- Bottom-pair claim scope does not become Lux/SUPPORT applicability. Role-qualified discovery can be empty; improve explicitly sourced scope/discovery in future without inventing role support.
- Named current-threat priority remains UNKNOWN and real accepted transcript/visual/tactical-effect samples remain zero. These are declared partial capabilities, not newly discovered blockers, and must remain separate from software validation in final status.

No whole suite was rerun in this rereview. Root's stable verification, source seal, CI, and publication work remain independent release gates.

Frozen product hashes checked in this rereview:

```text
web_r4/learning-engine.js 98ab2e87a3de8350bec45a01bd35eff9bb3533e4318b3a773dbefce98cb18196
web_r4/learning.js ccd1bca3869479e2e32480950edeb15d1525dc72efde591f967c09ae9c8723d3
coach_v1/pregame_server.py b0a09df6fe769563f20b278649d130537910403b77cb33b6f522e70d4e27ac9b
web_r4/loading-planboard.js a91c174dc15b08ea96bb75b012a5452d856d89e2a9d428b01a8480b95f3f35e0
```
