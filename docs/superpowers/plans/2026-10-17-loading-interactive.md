# Loading Interactive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** One real10pick→preference→milestone→future condition→plan comparison→map→why flow.
**Architecture:** Add a pure bounded exploration module above existing loading report; keep
normalized user preferences, hypothetical assumptions and UI selection separate. Reuse all
existing DOM/skill formatter/map renderer and source catalog, no framework swap.
**Tech Stack:** Plain JavaScript UMD, HTML/CSS/SVG, Python unittest, Chromium/Playwright.
**Spec:** contracts/loading-interactive-v3.md

## Global Constraints
Legacy inputs default BALANCED; unknown stays unknown; feasibility before preference;
DESIGN_HYPOTHESIS/N0, no scalar risk/strength scores; six comparison dimensions; no provider
calls, new champion/scenes or old advice23 expansion; all original evidence/grades preserved.

## Review Focus
- Dirty picks while exploration is open: hide all old results, including map/why.
- Missing patch/fact or swapped bot roles: no inherited viable follow/map.
- Unknown condition after ready: no selected attack or stale ready badge/route.
- Keyboard map/zoom state: same selected action and readable card.
- Unsupported milestone/champion: existing analysis accessible, controls explain limits.

### Task1: Contract + pure decisions
Files loading-exploration.js, loading-engine.js, tests_pregame/test_loading_interactive.py.
Interface evaluate(report,catalog,state) returns supported,row,plans,selected_plan_id,
selection_reason,same_choice_across_preferences,required_checks,evidence,map_scenario.
- [x] Write failing semantic action-ID/gate/version compatibility tests; run RED.
- [x] Implement six-dimensional bounded candidates and feasibility-first preference selection.
- [x] Run focused new and affected legacy engine tests GREEN; preserve report originals.

### Task2: Responsive state and map integration
Files loading.html/js/css, loading-map.js, loading-interactive.js.
Interface LoadingInteractive.mount({report,catalog,host,onPreference}) returns controller
with destroy(); onPreference(risk) reanalyzes same validated pick input synchronously.
- [x] Add real browser assertions for controls and transitions before UI changes (RED).
- [x] Connect L1 panels/milestones/future conditions/plan cards/why/trace and map controls.
- [x] Reuse exact official skill owner/name(key), old full table and six scene links.
- [x] Verify keyboard/zoom/mobile/stale input and independent shared browser regressions.

### Task3: Source-bound verification and publication
Files verifier/export/server/static tests/browser scope, evidence/Handoff/queue/seal.
- [x] Register only new code/contract/test files and affected tests/browser sources.
- [x] Fresh independent review; fix important findings with focused tests.
- [x] Verify changed scope and mandatory CI; normal merge; postmain exact-source checks.
- [x] Publish exact allowlisted artifact; actual native Pages + public PC/mobile flow.
- [x] Prepare verified receipts/Handoff result-only PR.

Postcommit gate: actual result-only normal merge/postmain CI and common-claim closure are
recorded on work/main-execution-claim, not predicted inside this commit.

Ruling: existing synthetic-only Python R3 cannot run as production loading inference; reuse
its six dimension vocabulary only, no synthetic VALID/REVIEWED promotion. Existing completed
baseline CI is reused per user; no reinstall/full old test rerun. Existing autonomous authority
covers routine design/worktree/publication choices without another permission loop.
