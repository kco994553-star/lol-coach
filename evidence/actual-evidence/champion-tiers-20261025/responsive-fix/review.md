# Champion responsive follow-up review — 2026-10-25

Verdict: **PASS for bounded CSS/browser-regression scope**. No confirmed blocker found.

Reviewed only the three appended production CSS lines and the new browser regression coverage relative to `work/champion-responsive-20261025` base. No source, Git, provider, credentials, issue, data or controller mutations were performed.

## Behavior and regression risk

- Long diagnostic tokens and phase labels wrap instead of forcing a wider card. Badges retain their font size/padding and become bounded, wrapping inline blocks. Header rows may wrap where their content no longer fits.
- `container-type:inline-size` is applied to report sections, which are ordinary full-width block descendants of the main element. Their inline size comes from the available parent width; this does not introduce an intrinsic shrink-to-zero size, fixed height, clipping, or hidden content.
- The grid reflow and stacked metric treatment are conditional on the actual report content width being at most480px. Normal wide desktop report grids retain their previous columns and styling. Narrow effective width under CSS zoom can now reflow even when viewport media queries still see the original viewport width.
- No `overflow:hidden`, `clip`, reduced font size, forced fixed height, text truncation or disabled zoom is introduced. Existing tables retain native horizontal scrolling (`overflow-x:auto`); they are not compressed into unreadable cells or clipped by the new container.
- New checks retain all previous assertions and add all320/390/820/1440 × CSS-zoom200/font200 cases, expanded evidence, card/control geometry, keyboard control focus, narrow dialog open/Escape return, and native table focus + ArrowRight scrolling. No test sets `tabindex`, hides overflowing content, or changes production styles to make the assertion pass.

## Evidence reviewed and independent checks

- Inspected the retained failing exact320/zoom2 receipt: width320/scroll436; it remains recorded as a failure, not overwritten or reclassified.
- Read latest `green-browser/runner.json`: PASS,36 checks,6screenshots, zero page errors, source unchanged during run.
- Read `legacy55-green/runner.json`: PASS,55 checks,18screenshots, source unchanged during run.
- Read native table keyboard receipt: all three scroll wrappers accepted focus and ArrowRight moved scrollLeft; no artificial tabindex injection.
- Independently ran the bounded unit/publication command below: **19 tests PASS in1.541s**. This is not a full-suite or independent new browser execution claim.

```sh
python -m unittest -q tests_pregame.test_champion_frontend tests_pregame.test_champion_insights_frontend tests_pregame.test_champion_publication
```

Browser evidence is Chromium-specific; no Safari/Firefox or new public deployment/live verification was performed by this reviewer. Root's final browser/CI/live checks remain separate release evidence.

## Reviewed source hashes

```json
{
  "web_r4/champion.css": "f1dc1ee05f074fd437f05ac5db2b48a5744bafba15e1d29dc9907f84d512028f",
  "scripts/browser_champion_insights.py": "c795fa83df6e3cee45de389d7f9491298d293a09472a4f0dc515fa0f9b4ac01b"
}
```

## Hold — saved-context counterexample discovered after this snapshot

The PASS above is historical for the recorded source hashes and empty-opponent cases. The saved Ezreal/Lux/Nautilus context exposes a100.0% metric intrinsic-width overflow at320 CSS zoom2 (client92/scroll104), plus tablet font200. Production completion remains pending the strengthened saved-context fixture and final fix/review. No final-current PASS is claimed here.

## Final saved-context follow-up — source frozen

Final verdict: **PASS for the final recorded CSS/browser scope**. The historical PASS, HOLD and saved-context counterexamples above remain intact. No confirmed remaining blocker was found in this bounded review.

- The metric grid now uses `repeat(auto-fit,minmax(min(100%,12rem),1fr))`. Its intrinsic font-relative minimum grows with the text size, so tablet font200 no longer squeezes100.0% into a narrow three-column card. Empty tracks collapse; the three actual cards retain three columns where they fit on a wide desktop.
- Compact report containers now reduce only horizontal card padding via `clamp(2px,calc(10cqi - 8px),16px)`, keeping positive padding and the existing text size. This frees sufficient inline space for an unbroken100.0% at320/CSSzoom2. No middle-digit breaking, font shrinking, clipping or overflow hiding was introduced.
- The strengthened eight-case loop begins from the saved Ezreal/BOTTOM/Lux/Nautilus URL in every viewport/zoom case, asserts all selected values survive, checks each card and the viewport fit, and uses a text Range to require the percentage remain a single complete line. This directly covers the previously missed saved-state failure.
- Native horizontal table scrolling/focus and narrow dialog open/Escape focus return remain asserted; existing earlier18 functional assertions remain present.

Reviewed final receipts (not independently rerun by this reviewer):

- `green-saved-final/runner.json`: PASS36 checks,6screenshots, no page errors, source unchanged during run.
- `legacy55-saved-final/runner.json`: PASS55 checks,18screenshots, source unchanged during run.

Independently reran the same bounded19-test frontend/selection/publication command against this frozen source; exact output:

```text
----------------------------------------------------------------------
Ran 19 tests in 1.830s

OK
```

No full suite, provider call, source/Git edit, new public deployment or live verification was performed by this reviewer. Cross-browser behavior outside Chromium remains unmeasured.

Final reviewed source hashes:

```json
{
  "web_r4/champion.css": "5aa7f42411bea4f952f72858abd0d6f7fc855e2047f70a5954976112d88bd8ab",
  "scripts/browser_champion_insights.py": "1d8238e2d206f442f6234fab438eb89321adeab930d155dfbb8883f2892d39a1"
}
```
