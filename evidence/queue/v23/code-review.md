# Queue v2.3 independent code/spec review

Reviewer: `/root/v23_code_review`. Base: `fedc30060259b5eeac4ab2ca096daa6259e354b6`.

Read `AGENTS.md`, `contracts/queue-v23.md`, and the implementation plan first. Reviewed new extraction/aggregation, official item archive, acquisition/CLI/trusted workflow, candidate gates, PC/HTTP/postgame projections, delta verifier and affected test/browser source. This is a read-only review except for this report. No provider requests, private records, old completed checks, or already completed new tests were executed. Existing reports/logs were reused. Separate candidate evidence/counter reviewers own the packet's factual review.

## Initial findings sent to Main

1. **P2 — accepted full-version request fails with a loaded dataset.** `validate_request` accepted `16.20.1` but `recall_view` accepts only `16.20`; normalize or reject consistently. Main corrected normalization and supplied new RED/GREEN evidence (`pc-patch-*.log`); the eight-test GREEN log includes the full-version regression.
2. **P2 — direct recall HTTP endpoint bypasses live suppression.** PC preview/UI suppress recall cards during a live game, but `/recall-reference` initially called the reference projection without inspecting live phase. Corrected: the projection now checks the observed live phase before dataset/item projection and returns empty suppressed aggregates. `pc-phase-green.log` and `pc-final-green.log` include the targeted regression.
3. **P2 — low-health outcome window falsely described as post-purchase.** Outcomes start at the low-health frame, so an opponent roam before the subsequent purchase can produce a positive group outcome. Corrected: aggregate copy explicitly describes the low-trigger window and includes pre-purchase events; private extraction separately computes `(action_time, original_window_end]` outcomes and requires their positive known roam count for the individual signal. Public extraction/aggregate windows are unchanged. The 25-test statistics GREEN includes pre-purchase, post-purchase, and beyond-original-window regression cases.
4. **P2 — preceding-frame gold distribution incomplete in card details.** Corrected: card details separately show gold Q1/Q3, valid distinct matches/participant count and missing count, while preserving UNKNOWN suppression for inadequate gold samples.
5. **Presentation/source concern — pro marker on a Challenger resource line.** Corrected: graph title explicitly labels the Challenger resource series and the separate marker population; the resource dataset has its own hash-bearing source entry.

## Reviewed boundaries

- Raw identities, match IDs and private clustering digests do not enter the strict public aggregate schema. Selected pro participants remain separate from Challenger discovery cohorts; private postgame observations are assigned neither public population.
- First-purchase death exclusion, undo handling, distinct-match sufficiency, role fallback, missing-window outcomes, match-weighted means and explicit limitations are implemented. Low-health grouping excludes deaths before an observable action and requires actual next-frame lane position for STAY.
- Official item URL/hash/version archive reads fail closed. HTTP projection performs no refresh. Patch mismatch suppresses item rows/prices; full costs remain explicitly approximate because owned components/discounts are unknown.
- New tactical rows remain HYPOTHESIS/UNKNOWN. Known source gaps veto automatic promotion even if receipts agree. No new USER decisions or protected issue writes are introduced.
- Trusted acquisition requires main/first dispatch, restores the existing encrypted cache without account lookup fallback, publishes only enumerated anonymous outputs, and cleans ephemeral raw files. Existing collector transport/rate/auth rules remain unchanged.
- Delta binding preserves existing source/test/contract/evidence bytes against the exact base Git tree and trusted completed CI receipts. New affected sources are separately sealed; predecessor tests are not rerun. Final seal and fresh remote delta receipts remain Main's responsibility.

## Verdict

Final spec verdict: **PASS within the reviewed v2.3 implementation scope**. Final code-quality verdict: **PASS; no unresolved important code findings**. Reviewed the final scoped correction diff and complete `recall_pc.py`, plus private extractor correction and affected regression source. All findings above are resolved without changing the public measurement window or old frozen checks.

Reused final evidence: `pc-final-green.log` reports nine passing new PC tests; `statistics-green.log` reports 25 passing new statistics tests. `browser-20261015T110957120440Z/runner.json` reports eight passing Chromium checks, zero browser errors/unexpected writes/USER approvals, 682.5/708.1/495 ms input-to-visible-card observations, and 163.87 ms private postgame import-to-visible-context observation. It verifies two positive selected-owner signals and no signals for a separately selected participant. No checks were rerun by this reviewer.

Browser source hashes were compared read-only with the checkout: every recorded source matched except `recall_stats.py` (receipt `450c663e9eaa7e4fe572088fd1a8c2680316641d088674a342f9166ba728048c`; reviewed final source `e543abc385e5526c424cbdf4154a056a18d3c6eec3d72aa6289bf7012c684bb5`). The private post-action correction is covered separately by the new 25-test statistics evidence. The existing browser receipt must retain its original binding and be reused only for unaffected rendering/import behavior; it must not be claimed as execution of the final statistics bytes. Final source sealing and remote delta receipts remain Main's responsibility.

Synthetic unit/browser evidence demonstrates implementation behavior, not coaching accuracy or actual Windows/LCU behavior. No broad full-data performance claim is established by the small synthetic browser fixture. Independent packet reviews remain authoritative for candidate factual/counterexample judgments; this review does not promote any candidate.
