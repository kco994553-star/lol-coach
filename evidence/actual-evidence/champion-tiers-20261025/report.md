# Final frontend browser and F1 correction verification

Implementation is frozen. No commits or repository-local task probes were created. All task output and generated `.cjs` files are under this outside-repository directory.

## Latest exact commands/results

- `python -m unittest tests_pregame.test_champion_frontend tests_pregame.test_champion_insights_frontend` -> 16 passed in 1.298s; `f1-unit-green.log`.
- `python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/tier-final-browser/f1-browser-green` -> passed 18 checks, 4 screenshots, source unchanged, zero browser errors/HTTP failures/external requests.
- `python scripts/browser_champions.py --output /workspace/gp23-artifacts/tier-final-browser/f1-legacy-green` -> passed original 55 checks, 18 screenshots, source unchanged, actual user approvals created 0; browser/console/HTTP/external error lists all empty. Every original assertion remains.
- `python scripts/browser_learning.py --output /workspace/gp23-artifacts/tier-final-browser/learning` -> passed 33 checks, 7 screenshots, approvals created 0, provider requests 0, browser/HTTP/external error lists empty.
- `python scripts/browser_gameplan_2plus3.py --output /workspace/gp23-artifacts/tier-final-browser/gp23` -> passed desktop1440/mobile390/narrow320 results; two overview cards, 15 phase actions, assumed/stale/unknown scenario semantics, reset/share/reload/Back/keyboard/200% text/unsupported/partial stale behavior and current-claim learning-link regression all passed. GP23 runner does not contain external-request instrumentation; no provider invocation was introduced.

Read each script's `--help` before invocation. Learning/GP23 covered asset hashes were compared to the current tree and remained unchanged; per root direction those already passing runs were not repeated after the bounded champion-only F1 correction.

## Failure and correction record

The first legacy run `champions/runner.json` had all55 DOM checks passing but the runner correctly rejected the receipt because `scripts/build_directions_web.py` changed during the run (hash1375e6e3... to920072a8...). Its complete initial source hashes and receipt remain preserved. After root declared the exporter frozen, `champions-stable/runner.json` passed55 with source unchanged.

Independent review then found the advanced opponent search/sort table still read the legacy CHALLENGER object, so future GOLD data would be ignored and combined-tier data could disagree with selected statistics. Root authorized a bounded correction only after their stable full suite finished.

RED evidence: `f1-unit-red.log` captures the missing exact-scope advanced-row adapter. `f1-browser-red/runner.json` captures a meaningful actual DOM failure: GOLD advanced rows were empty while a local isolated synthetic response contained Ashe N40/wins30 and Ezreal N30/wins3. No synthetic statistics were written to a public file.

GREEN correction changed only `web_r4/champion-insights.js`, `web_r4/champion-page.js`, `tests_pregame/test_champion_insights_frontend.py`, and `scripts/browser_champion_insights.py`. `I.opponentRows` now adapts exact `I.select(...).frequent_opponents`; existing advanced name/sample/rate sorts, query behavior, A-team N/wins, selection buttons and manual controls remain. Advanced rows expose their exact patch/tier/SAME_ROLE_ENCOUNTERS scope and Wilson95 intervals. Local synthetic GOLD and MASTER_PLUS responses deliberately use distinct numbers; the browser verifies both datasets, search/rate sorts, CI/scope display and compare-button synchronization. Fixture interception affects only that test page's localhost JSON response.

Final new18 and legacy55 browser runs are source-hash stable. No unresolved frontend failure remains in these checks. This report does not claim tactical correctness, actual cross-role statistics availability, real match effects, deployment verification, or whole-suite success; root owns full-suite integration and the unrelated collector fixture investigations.
