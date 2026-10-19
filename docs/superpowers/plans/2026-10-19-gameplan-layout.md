# Gameplan reference layout Implementation Plan

> Execute inline with executing-plans; one fresh read-only review at the end.

**Goal:** Match the approved reference information order with actual Caitlyn/Ahri reports.
**Architecture:** Pure report projection and URL codec in loading-presentation.js;
existing coach view gets opt-in presentation mode, existing learning view stays intact.
loading.js owns validated route restoration and same report; shared CSS owns layout.
**Tech Stack:** existing vanilla JS, Python unittest, Chromium/Playwright, Pages.
**Spec:** contracts/gameplan-presentation-v1.md

## Global constraints
Same judgments/evidence, no example prose table, no new API calls, keep original detail paths.
## Review focus
Invalid/stale URL; unavailable official art; narrow/zoom overflow; back/focus after comparison;
unsupported matchup must not acquire Caitlyn tactics or winner.

## Tasks
- [x] Pure projection and bounded route codec: tests_pregame/test_loading_presentation.py;
  actual two champion results, source mutation, unknown scope, route roundtrip/invalid data.
- [x] Responsive master/detail: loading-coach-view.js/loading-presentation.css/loading.html;
  initial detail closed, full-card keyboard/touch, paired perspectives, actions and all old
  tools accessible. loading.js restores encoded report input/period/detail and stale clears.
- [x] Actual PC1440/mobile390 plus tablet/320/200%, Caitlyn/Ahri, back/refresh/direct URL,
  input edit/same result, image/API failure and legacy/matrix/diagram/Why paths. Save screens.
- [ ] Affected tests + mandatory source-bound CI; normal PR/merge/exact-main CI/Pages,
  actual HTTPS/browser, results-only Handoff and final CI; completed writer release.

## Ledger
Intake: main78d6f04, no active writer; stale historical CURRENT_EXECUTION noted.
Ruling: user supplied explicit design and autonomous execution, no repeated approval pause.
Ruling: Ahri mockup wording is not evidence; use current generated limited report.
