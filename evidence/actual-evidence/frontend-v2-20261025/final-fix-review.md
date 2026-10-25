# Frontend v2 verification-fix re-review

Scope: `/workspace/frontend-v2-artifacts/final-fix-review.diff` and the directly relevant current source/diagnostic artifacts. This is a read-only, fix-scoped re-review; no suites were rerun and no repository/index/branch/external state was changed.

## Strengths and fix dispositions

| Finding/change | Disposition | Assessment |
| --- | --- | --- |
| Mobile navigation retained five columns after adding the sixth menu | **ADDRESSED** | `web_r4/coach-theme.css:5` changes the mobile grid to six equal columns. The existing ResizeObserver still reserves the actual navigation height. The retained green probe shows a single 81.375px-high navigation row at both 390px and 320px; all six links remain at least 52px wide and 68.375px high, without horizontal overflow. Hero cycling retains scrollY=0, account-field focus and form geometry. This fixes the actual overlapping second-row behavior rather than weakening the interaction assertion. |
| Existing browser suite expected five menu entries | **ADDRESSED** | `scripts/browser_loading.py:202` now requires six entries and checks their exact ordered Korean labels. Current-menu, overflow, shared-theme, mobile positioning and interaction assertions remain. |
| Unit CI jobs could not import Playwright; browser helper assumed a local Chromium path | **ADDRESSED** | Both evidence-mode unit jobs install the same pinned `playwright@1.62.1` already used by browser jobs, then export NODE_PATH and the hosted Chrome executable through GITHUB_ENV before invoking the verifier. `tests_pregame/test_champion_handoff.py:124` consumes that executable with the existing local fallback. Child Node processes inherit these variables. Tests are neither skipped nor replaced with mocks, and the dependency installation remains outside runtime product code. |
| Opponent headline used generic A/B labels without its own small-sample/interval context | **ADDRESSED** | `web_r4/champion-page.js:32` names the selected champions, explicitly attributes the result to the reference champion, and displays the opponent cohort's own N warning and existing Wilson interval. Missing/incompatible scope still yields missing data through the unchanged `opponentScope`; numerical aggregation, filtering and data remain unchanged. |

## Issues

Critical: none found.

Important: none found in this fix scope.

No reviewed fix remains unaddressed. The existing whole-branch approval did not detect the mobile six-menu wrapping regression; this follow-up corrects that review gap with concrete browser geometry and interaction evidence.

## Verification boundaries

I read the complete fix diff, the handoff browser helper and surrounding CI step order, the existing navigation-height observer, and `/workspace/frontend-v2-artifacts/frontend-nav-green.json` plus its log. The controller reports 906 pregame tests and 24 focused tests passing; those results were not independently rerun here. The existing broad browser rerun and new remote CI results remain pending at review time.

The changed CSS and champion label renderer invalidate prior screenshot/source-hash equivalence for those files. Refresh the evidence seal and regenerate or explicitly scope affected current-byte browser/screenshot receipts before claiming final exact-source verification. Previously captured receipts remain historical evidence.

## Declined to judge

- Unchanged product paths and full vision-level completion: this review is deliberately limited to the supplied fixes; the earlier whole-branch review and explicit pending-feature boundaries remain applicable.
- Success of the active broad browser run and remote CI rerun: no completed result was supplied for those runs at review time.
- Refreshed source seal, final current-source screenshot inventory, merge, deployment/live verification and Notion updates: these are execution/publication steps still owned by the controller and require their own final receipts.

## Assessment

**SPEC verdict: APPROVE. QUALITY verdict: APPROVE.** All four reviewed fixes address their stated causes without weakening the required contracts or introducing a material defect found in this scope.

**Ready to merge: Yes, after the refreshed seal and outstanding required checks pass.** This approval does not claim those pending execution steps have completed.
