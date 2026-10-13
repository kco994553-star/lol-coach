# R1 single-candidate review queue

Open `/review-queue` from the private local application and connect with the same Bearer token used for pregame plans. One candidate appears at a time. Previous/next selects another candidate; the batch controls reach candidates beyond the first 20. “나중에 둔 후보 다시 보기” opens persisted deferrals, including their later batches.

Ranking first considers candidates relevant to the Golden10 example and their conditional card targets, then Yunara/Ashe/Kaisa/Caitlyn and the most recent saved selections, then observed champion frequency, then the remainder. These ranks and the displayed previews do not approve a claim. Golden10 has no verified match patch, so its 45 cards across five roles remain explicitly conditional; only actual applied reviewed cards count as filled.

Each candidate shows its claim, declared structured predicates, counterconditions and stop conditions, required inputs, source patch and game patch separately, verified archived source excerpts where available, counterexamples, and a conditional card preview. Saved expert summaries are labeled unverified paraphrases, never source quotations or executable predicates. Descriptive statistics preserve each dataset’s patch, tier, sample kind, resource unit, sample count and confidence interval. Independent patch/tier cohorts are shown separately without merging means or adding overlapping samples.

A catalog entry first needs “검토 후보로 저장,” which creates an EXPLORATORY proposal. Approval and rejection then use the existing browser-only, revision-bound knowledge decision route. Scripted clicks and ordinary API automation have no authority. “수정 후 승인” saves an edited claim and confirmed game patch as a new proposal revision bound to a new immutable source document, then requests the explicitly clicked decision. Changing structured predicates still uses the existing full-spec editor in the pregame page. No review operation silently enables coaching.

Deferral is bound to candidate ID and exact selected revision, stored in a mode-0600 sibling SQLite sidecar. It does not modify the knowledge proposal or create an approval audit. A newer candidate revision becomes reviewable. Deferred candidates can be revisited, navigated or decided normally. Clicking “나중에” on a deferred candidate advances to the next candidate.

The export contains the full ranking’s first 20 pending claims, declared conditions and sanitized public source URLs in plain text. It excludes source bindings, source excerpts, statistics and private research IDs. Private hosts and URL credentials are rejected; sensitive query parameters are removed. YouTube video and timestamp parameters are retained for usable public links. The export is independent of the currently displayed page.

## Integration

Main owns the authenticated routes and navigation:

- `GET /dev/v1/pregame/review-queue`: `queue_response(server)`.
- `POST /dev/v1/pregame/review-queue/page`: exact integer body `{page, later_page}`, each 0–10000; call `queue_response(server, page=..., later_page=...)`.
- `POST /dev/v1/pregame/review-queue/later`: exact body `{candidate_id, selected_version}`; call `defer_candidate(server, body)`.
- Existing `/dev/v1/pregame/candidates` accepts optional paired `{rule_id, expected_version}` for an edited structured candidate in the existing proposal lineage.
- Decisions stay on `/dev/v1/knowledge/proposals/{rule_id}/decisions`.

The queue returns `candidates`, `deferred_candidates`, `pagination`, `progress`, `page_limit` and `export_text`. Each candidate retains the current full proposal/spec plus a presentation projection. A response is bounded by the server body limit; the ordinary page size is 20. Sources and frozen rule schemas are unchanged.

## Verification

Run `python -m unittest tests_pregame.test_review_queue -v` for 11 isolated-store tests: ranking, conditional card targets, exact-revision persistence/conflicts, zero automatic approval, export privacy/bounds, verified archived excerpts, descriptive units/CI, independent imported dataset maps, expert paraphrase labels, and a 21st deferred candidate reachable on page 2.

Run `python scripts/browser_review_queue_v20.py` for fresh Chromium verification at 390px and 1280px. The runner creates only isolated SYNTHETIC proposals. Its ten native-click decisions are intercepted in a disposable in-memory fixture with actor `TEST_FIXTURE`; actual research decision rows must remain zero. It separately verifies ordinary production decision POSTs return 403. It also covers an edited source-bound revision, requery, persisted deferral, multi-deferred navigation/rotation, held old refresh responses, batch pagination and safe text export. The JSON receipt includes source hashes and the actual research decision-row audit.

RED evidence included a missing queue module, missing conditional-card ranking, imported dataset maps returning UNKNOWN, and missing deferred pagination. Initial browser execution caught missing UI, incorrect Fetch Response.ok handling and order-sensitive scope comparisons. Independent review reproduced deferred navigation and stale-refresh ownership failures before the regression checks were added. All such fixes were rerun with the targeted unit and browser checks. Main owns the final whole-branch verifier runs and publication evidence.

This verifies queue behavior, not real-match coaching accuracy or real user approvals.
