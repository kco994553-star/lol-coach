# Current gameplan web replacement implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and one final independent review.

**Goal:** Replace the existing gameplan web content with the currently approved gameplan, as explicitly requested on 2026-10-24 KST.

**Architecture:** Keep the current engine and input/share contracts. The public loading page mounts only the current delivery projection. Historical DOM survives solely in a non-exported test fixture; original knowledge and decision records remain preserved.

**Tech Stack:** Existing vanilla JavaScript, Python unittest, Chromium/Playwright CI.

**Spec:** Current user instruction plus `contracts/gameplan-presentation-v1.md` and `docs/gameplan-content/backend-design-v1.md`.

## Design and approach

Replace the old result DOM and stop mounting its renderers. Keep the agreed team comparison, role commentary, three phases with exactly five actions and visible prose. Details expose current conditions, alternatives, source facts and input controls. No invented tactics or extra product domains. Retaining the old full-report panel would fail the request; rewriting the analysis engine would unnecessarily change already tested behavior. This is an implementation choice under the user's explicit replacement authorization.

## Global constraints

- Only gameplan page; account dashboard, in-game helper and study pages unchanged.
- Original source data, Frozen350 and USER decision history are preserved.
- Unsupported current delivery fails rather than silently showing the old report.
- Same input, conditions, reset and shared URL must reproduce current output.
- Historical browser fixture is never in public export; its passes are not current-page proof.

## Review focus

Missing current contract; stale form edits; condition reset; growth-period refresh; mobile/jungle layout and missing old DOM.

### Task 1: Replace the shipped result

Files: `web_r4/loading.html`, `web_r4/loading.js`, `web_r4/loading-presentation.js`, `web_r4/loading-coach-view.js`.
Consumes: `report.coach.planboard.delivery` and existing input/history.
Produces: only current phase headings, five actions, paragraphs and conditions in public DOM.

- [x] Write missing-current-DOM and current-headline/fail-closed tests in `tests_pregame/test_loading_presentation.py`.
- [x] Observe both failing on the original page/projection.
- [x] Remove old result DOM and mount only current view. Preserve old HTML in test-only fixture.
- [x] Run presentation tests: 8 PASS.

### Task 2: Verify, review and publish

Files: `scripts/browser_current_gameplan.py`, existing browser harnesses, source binding.
Consumes: actual PC route and exact public export, plus separate legacy DOM fixture.
Produces: independent current-page and historical-widget receipts.

- [ ] Run full Python suite and source integrity checks.
- [ ] Run exact-source Chromium checks for current desktop/mobile, five actions, three phases, reset, period refresh, jungle labels and stale input.
- [ ] Review final changes independently; fix material findings.
- [ ] Publish verified branch, merge with successful CI, update existing Pages export while preserving separately refreshed pro data.
- [ ] Verify public interaction and report the published URL.

## Execution ledger

Task 1: RED→GREEN, 8 presentation tests pass. New page removes duplicate old full report; current headline overrides old concept. Historical widget tests use a test-only preserved HTML fixture, while a separate check loads the actual shipped page without interception.

Independent review: preserve risk controls in current conditions, populate the empty scope disclosure, and test output change/reset plus fresh-context sharing. All addressed in this change. Initial full suite: 823/824; the single failing assertion required the intentionally removed legacy DOM. Updated that assertion to require absence in production and presence only in the historical fixture.
