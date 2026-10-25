# Native champion dialog responsive correction — frozen final report

Implementation is frozen. Worker edits are limited to `web_r4/champion.css` and `scripts/browser_champion_insights.py`. No HTML, production JavaScript, selection/persistence logic, data/source artifact or tactical content changed. No Git mutations, provider calls, full-suite runs or publication were performed by this worker. Root owns the central PR/CI/publication.

## Measured real failure

Actual public QA of source `b236bd736a2de4413a257604d338d9221d21b7a7` found the native dialog failed at320x780 + CSSzoom2, after saved Caitlyn/BOTTOM/Ezreal/Lux/Nautilus context, expanded evidence and all three keyboard-scrollable tables. The page and percentages fit, but modal clientWidth120/scrollWidth123, header92/109, and the modal rectangle was top-366/bottom1146/height1512 physical pixels. The entire header/close was above the viewport even at modal scrollTop0. Original actual receipts remain under `/workspace/gp23-artifacts/tier-live/release-b236-final/`.

Root cause: viewport-unit `max-height:calc(100dvh - 24px)` stayed756CSSpx under CSSzoom2 and became1512physical pixels. Native centering then placed the header offscreen. Flex auto minimum widths also pushed the header beyond its narrow content box; at root font200 the close glyph needed a font-relative target size.

Meaningful REDs before CSS edit:

- `python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/tier-dialog-responsive/red-dialog-browser` failed the exact320 dialog internal/rectangle assertions, recording top-366/bottom1146 and client120/scroll123.
- A real PUBLIC export was built at `stage-red`, and the entire QA verifier run with `python /workspace/gp23-artifacts/tier-live/run_staging_responsive.py --staging-directory /workspace/gp23-artifacts/tier-dialog-responsive/stage-red --output /workspace/gp23-artifacts/tier-dialog-responsive/strong-stage-red` failed desktop CSSzoom2 modal top-452/bottom1452/height1904. It was explicitly labeled LOCAL_STAGING_NOT_LIVE.

## Bounded CSS fix

The modal uses fixed positioning and a percentage max-height against its zoomed fixed containing block, preserving the original desktop48px/mobile24px allowance. The header can wrap, its text child can shrink and wrap long tokens, and its close button keeps a minimum font-relative target. Fonts and all content remain intact. No hidden/clip workaround or production focus/selection change was introduced.

Measured320 CSSzoom2 result: modal top24/bottom756, header top66/bottom374, close inside that header; the search input also remains in the native initial viewport. At320 font200 the modal is top12/bottom768 with header/close inside. Native vertical scrolling intentionally reaches the footer and roster; there is no invented requirement for a sticky header during intentional scrolling.

## Strengthened repository regression

The same36-check suite retains all previous tests and all eight saved-context zoom/font combinations,100.0% single-line coverage and keyboard table access. The full staged verifier separately guards font-size nonreduction. Every enlarged case now checks modal internal width, the full native initial header before scrollTop reset, the header after scrollTop0, every relevant title/search/selection/grid/chip internal width, focused control viewport bounds, usable footer after selecting valid temporary Ahri, actual Tab/ShiftTab focus with a solid nonzero visible outline, Escape restoration and unchanged saved selections. Fresh pages per enlarged case match the actual verifier and avoid a preexisting harness race from same-document readiness checking only the tier.

The actual pointer-open + programmatic `.focus()` sequence legitimately did not match `:focus-visible`. A staged strong-verifier attempt therefore stopped at its keyboard-modality assertion after geometry passed. Independent QA reproduced the modality distinction, preserved the false-positive attempt, and corrected the verifier to send real Tab/ShiftTab while retaining the visible-focus assertion and adding a solid nonzero outline check. It also selects a valid temporary candidate before asserting Apply enabled. Production validation/focus behavior was not changed to satisfy a test. Evidence: `/workspace/gp23-artifacts/tier-live/focus-contract-investigation/contract-result.json` and local `focus-modality.json`.

## Final GREEN verification

- `python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/tier-dialog-responsive/green-browser-final` -> **PASS36 checks /6 screenshots**, source unchanged; browser/HTTP/external errors empty.
- `python scripts/browser_champions.py --output /workspace/gp23-artifacts/tier-dialog-responsive/legacy55-green` -> **PASS all55 original checks /18 screenshots**, source unchanged; browser/console/HTTP/external errors empty. Every original assertion is preserved.
- `python /workspace/gp23-artifacts/tier-live/run_staging_responsive.py --staging-directory /workspace/gp23-artifacts/tier-dialog-responsive/stage-green-first --output /workspace/gp23-artifacts/tier-dialog-responsive/strong-stage-green-final` -> **PASS LOCAL_STAGING_NOT_LIVE**,8/8 saved-context zoom/font cases,3/3 actual tap flows under Chromium touch emulation,6 keyboard-table checks,11 checks/9 screenshots. All browser/console/HTTP/external/API/nonGET lists are empty; fixture_routes0/numerical_injectionfalse. The unchanged strong QA script hash is `4000d07f6f1164d8d56ddf74ea1c9bcb460f03e64f18b784932c1a3505b8aa87`.

The full strong verifier was reused on the staged PUBLIC artifact, rather than replaced with a local approximation. All109 manifest-bound staged assets were rehashed after the worker's final strong run and remain unchanged. Candidate source CSS exactly matches that staged CSS. Independent QA additionally passed the same full verifier on the same artifact at `/workspace/gp23-artifacts/tier-live/LOCAL-STAGING-dialog-modality-final/`.

This is local staging/Chromium emulation evidence, not an actual HTTPS correction claim or physical-device test. Root performs actual verification only after normal main integration/publication. No semantic unit change was needed for this CSS-only behavior; root owns full-suite checks. Some standalone loopback runs retain harmless canceled-response BrokenPipe diagnostics; the final browser/HTTP error lists remain empty.

## Frozen hashes

- `web_r4/champion.css`: `ce458d2e512379a724245667e46d29028edbff934c2fd28f832cc588a5d88ef3`
- `scripts/browser_champion_insights.py`: `9cac9d6e21f10cfd394a8779e5ab4205e3570ef0b337f790ac883072eb6c24bd`

Machine-readable receipts/hashes: `final-summary.json`. All task probes/stages/screenshots are outside the repository. No further source changes are pending from this worker.
