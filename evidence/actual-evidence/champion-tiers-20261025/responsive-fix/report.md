# Champion responsive correction — frozen final report

Worker implementation is frozen. Root owns Git, PR/CI, attestation, export and publication. This worker edited only `web_r4/champion.css` and `scripts/browser_champion_insights.py`; no HTML, controller, statistic, knowledge, source-data or tactical content changed. No commits, full-suite runs, paid/provider calls or deployments were performed by this worker.

## Actual failure and root cause

Live QA reproduced published source `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7` / publication `af297cac8c3f5827a40429409e94db9a614176b0` at `champion.html#state={champion:Caitlyn,position:BOTTOM}`, viewport320x780, `document.documentElement.style.zoom='2'`. Root scrollWidth was436 while innerWidth320. Local reproduction matched436. At390 CSSzoom2 the root was436;820 CSSzoom2 was831;320 font200 was403.

Structural measurement traced overflow to unbreakable status/source-basis tokens in filter notes, nowrap badges, nonwrapping section headers, fixed minimum grid columns, and metric value widths. CSS zoom narrows actual content without changing viewport media-query matches; the original test applied CSS zoom only at desktop1440 and missed this condition. A first new regression also found desktop card-internal baseline overflow even when the root fit.

Exact320 RED: `python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/tier-responsive/red-browser-exact320` failed `mobile320 csszoom200 expanded evidence overflow {width:320,scroll:436}` before CSS correction. The receipt is preserved.

## Bounded correction

- Permit long filter-note/phase tokens and badges to wrap; badges stay within their available width.
- Permit section headings/badges to wrap into multiple rows.
- Establish report inline-size containers and reflow metrics, phases, qualitative/ranking columns, context fields, frequent opponents and search tools based on actual report width below480px.
- Give metric grids a font-relative intrinsic12rem minimum, so enlarged type can reduce the number of columns.
- Adapt narrow metric-card horizontal padding with `clamp(2px,calc(10cqi - 8px),16px)`, preserving the full `100.0%` value as one line without reducing its font.

No `overflow-x:hidden`, clipping, artificial font reduction, discarded content or statistical fallback was introduced. Wide numeric tables retain their existing local horizontal scroll regions; the browser test verifies keyboard focus and ArrowRight scrolling for all three tables at320 CSSzoom2 and font200. No HTML change was needed in the tested Chromium target.

## Saved-context correction record

The first36-check passing receipt (`green-browser-first`, then `green-browser`) used an empty-opponent state and is historical evidence only. A supplemental probe with saved Ezreal/BOTTOM/Lux/Nautilus context found an internal third metric overflow despite a fitting root: cardclient92 minus32px padding left60CSSpx, while `100.0%` needed87.58CSSpx at24px. At820font200 cardclient179 minus32px left147px, while the value needed175px at48px.

`red-saved-context/runner.json` preserves the meaningful new failing regression. The regression now enters saved context for every enlarged case, asserts those selected values remain unchanged, checks every relevant card's internal scrollWidth, and verifies the percentage text occupies one complete line. The final intrinsic metric minimum and compact padding address these measured widths. Font-relative query-threshold-only experiments were not used as the final solution; the actual font-relative grid minimum provides the needed reflow.

## Final verification

`python scripts/browser_champion_insights.py --output /workspace/gp23-artifacts/tier-responsive/green-saved-final` -> **PASS36 checks,6 screenshots**, source unchanged. This preserves all18 original checks and adds eight saved-context width/enlargement combinations:1440/820/390/320, each with CSSzoom2 and separately root font200. Expanded evidence, advanced fields and tables are exercised;320 also checks the change dialog, table keyboard scrolling and focus restoration. Root/card bounds, complete percentage text and saved-context values all pass.

`python scripts/browser_champions.py --output /workspace/gp23-artifacts/tier-responsive/legacy55-saved-final` -> **PASS55 original checks,18 screenshots**, source unchanged, actual approvals created0. No original assertion was removed or weakened.

Both final receipts have empty browser-error/HTTP-failure/external-request lists; the legacy console-error list is also empty. A canceled local static response occasionally printed a harmless BrokenPipe traceback during navigation; it did not produce a browser or HTTP failure and is retained in raw process output rather than hidden.

No semantic unit change was required for this layout-only correction. Root owns the full regression suite and independent review.

`geometry-after.json` binds the final CSS hash and records all eight saved-context combinations with innerWidth==scrollWidth (320,390,820,1440), zero overflowing cards, and preserved Ezreal/BOTTOM/Lux/Nautilus values. The original live/local failure, first incomplete pass, saved-context RED and final GREEN receipts remain outside the repository.

## Frozen source hashes

- `web_r4/champion.css`: `5aa7f42411bea4f952f72858abd0d6f7fc855e2047f70a5954976112d88bd8ab`
- `scripts/browser_champion_insights.py`: `1d8238e2d206f442f6234fab438eb89321adeab930d155dfbb8883f2892d39a1`

Final machine-readable summary: `final-summary.json`. This report establishes the tested local Chromium layout/navigation behavior; it does not establish deployed correction, tactical effectiveness, or new statistical coverage.
