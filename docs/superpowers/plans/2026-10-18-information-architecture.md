# Information Architecture Implementation Plan

> **For agentic workers:** use superpowers:executing-plans inline; one final read-only review.

**Goal:** five clear menus and a short working account/guest-to-gameplan flow using current data.
**Architecture:** reuse shared shell/tokens, dashboard hash views and current engine report;
no replacement backend or independent per-screen advice.
**Tech Stack:** native HTML/CSS/JS, existing Python loopback/export, Playwright/unittest.
**Spec:** contracts/information-architecture-v1.md

## Global Constraints

Preserve old engine/review/raw/holds/budgets/Windows. No paid/provider/game/video calls.
N0, human30secUNMEASURED and WindowsBLOCKED_EXTERNAL. No fake recommendation/live/replay.
One source-backed report for summary/detail/maps; preferences never alter objective metrics.

## Review Focus

- Deep-link review with no selected record must stay empty, not restore another identity.
- Account input invalidation must clear selected review record and visible old profile.
- Keyboard/mobile bottom menu must not cover controls or dialog content at200% text.
- Unsupported matchup/patch remains unsupported through the new four-item briefing.
- Expanded old map/skill/step flows keep their selected state and source originals.

## Tasks

###1 Navigation and existing account/review routes
Files coach-shell.js/coach-theme.css/dashboard.html/dashboard.js; browser_loading.py.
Consume existing profile/pro projection; produce five actual links, common active state,
search/dashboard/review views, safe memory-only selected record and direct guest loading.
- [x] RED browser primary links count5/status outside, guest→loading, route views.
- [x] Implement same DOM links in desktop sidebar/mobile bottom bar, safe-area spacing.
- [x] Render real safe recent record to review; clear on invalidation; local review gate kept.
- [x] GREEN browserPC/mobile, API failure/empty/no identity in URLs, stable art.

###2 Briefing and focused details
Files loading-planboard.js/loading-coach-view.js/loading.html; tests_player_planboard.py.
Consume same normalized report; additive briefing_v2 four one-sentence items. Preserve
legacy summary and all metric/selection/source fields. Details use same selected result.
- [x] RED actual report briefing schema/values, preference/period/scope invariance.
- [x] Implement four concise conclusions; lane purpose/grid/direction/change first,
  operations placement/connection/fallback, fight role/threat/start/exit first.
- [x] Fold existing context/procedures/maps/comparisons/Why; maintain maps/step state.
- [x] GREEN affected unit + browser10pick/edit/details/risk/unsupported/zoom.

###3 Helper, learning, status responsibility
Files game-info.html/js, directions.html, loading-study.js, status.html.
Consume unchanged GameInfo/knowledge/status. No new observation or tactical rule.
- [x] RED helper active menu/status first and learning registry/practice links.
- [x] Rearrange connection first; one inventory feature; unavailable capabilities in
  details with exact reasons; local observation remains withheld.
- [x] Learning overview links existing role/matchup/scenario resources, no new lessons.
- [x] Document unsupported recommendations/timers/jungle/review in spec/queue.
- [x] GREEN targeted browser, preserved data and no private public calls.

###4 Verify and publish
- [ ] Record fresh public audit, official field/policy read, source-preservation proofs.
- [ ] Relevant tests/full protected browser; review current diff, fix substantive issues.
- [ ] Source seal, normal PR/required CI/merge/exactmainCI, Pages/pro/riot preservation.
- [ ] Actual HTTPS and PC/mobile, result-only PR/Handoff with finished-check reuse.
- [ ] Final exact-main CI/common writer release. Report functional/knowledge/effect separately.
