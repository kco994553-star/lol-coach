# Native champion dialog responsive review — 2026-10-25

Status: **CSS logic reviewed; final verdict pending strengthened staging evidence/source freeze**.

Bounded read-only review against responsive-release base `b236`; only appended dialog CSS and its browser regression coverage are in scope. No source/Git/provider/issue/data changes or new full-suite/browser execution occurred in this review.

## CSS behavior and risk

- `position:fixed` gives the modal a viewport-based containing block. Percentage max-height follows that fixed block under CSS zoom; the previous `dvh`/viewport-unit bound could remain too large in zoomed layout coordinates. The existing global border-box sizing includes padding and borders in the maximum.
- ID-specific bounds override both the generic champion dialog rule and the shared mobile `.coach-page dialog` height bound. The original mobile24px/wide48px clearance is retained using percentages instead of viewport units.
- Header wrapping and a shrinkable title column allow long title/eyebrow text to reflow. The close button remains an independent flex item with a font-relative minimum target and at least44px height; no font shrinking or text clipping is added.
- No overflow hiding, fixed content height, sticky-header requirement, modal controller changes, autofocus changes or fake viewport geometry are introduced. The dialog/grid can scroll when the expanded header, filters, results and footer exceed the available height. Header visibility is tested at the start/reset and after close receives focus; footer controls are intentionally reached at the end, rather than requiring every region be simultaneously on-screen.
- Existing initial search focus, native Escape behavior, focus return, apply/cancel semantics, saved state and data are preserved. Tests should continue checking native title/search/grid/chips/footer intrinsic width and actual target rectangles, not merely document scroll width.

## Evidence handling

The retained actual public320/CSSzoom2 failure (modal top-366/bottom1146 and internal/header overflow) remains a failure. The earlier root/card/percentage PASS did not establish native dialog geometry correctness.

The first strengthened staging run reached the focus-visible check after geometry passed, but mouse-open followed only by programmatic focus does not itself establish keyboard input modality. A real Tab/Shift-Tab action while retaining the outline assertion is an appropriate harness correction; it must not bypass the geometry or visibility assertions. Final full staging eight-case and touch receipts are still pending and will be reviewed before a final PASS.

## Reviewed initial candidate hashes

```json
{
  "web_r4/champion.css": "ce458d2e512379a724245667e46d29028edbff934c2fd28f832cc588a5d88ef3",
  "scripts/browser_champion_insights.py": "e9076cfd35f84637fecf472da52580d0e997c0441979051db0ffbe66d51ef6a8"
}
```

## Final frozen-source review — local staging

Final verdict: **PASS for the bounded native-dialog CSS and regression scope on LOCAL STAGING**. This verdict does not establish a new public deployment or live-site PASS.

- Production CSS remains `ce458d2e512379a724245667e46d29028edbff934c2fd28f832cc588a5d88ef3`. No HTML, data, modal-controller or state logic changed.
- Read the manifest-bound public-export staging summary and full browser receipt from `LOCAL-STAGING-dialog-modality-final`:13:04:06–13:04:22UTC, all109 staged asset bytes unchanged,8 saved-context CSSzoom200/font200 cases,3 actual-tap touch-emulation flows,6 native keyboard table checks,11 checks and9screenshots PASS. Browser/console/HTTP/external/API/nonGET errors or requests are all zero; no fixture route or numerical injection was used in that strong staging run.
- The exact320/CSSzoom2 native-open geometry is checked before any programmatic scroll reset: the dialog is bounded inside the viewport, and the complete initial header/close control is visible. End-of-scroll apply/cancel remain reachable. Returning focus to close brings its header into view; no always-sticky header requirement was invented.
- The focus-visible false positive was resolved through actual Tab then Shift+Tab, preserving the focus-visible and solid nonzero outline assertion. A valid pending Ahri selection enables apply before testing footer controls. Escape restores the original Caitlyn/Ezreal/Lux/Nautilus saved context.
- Latest repository browser `green-browser-final/runner.json` PASS36 checks/6screenshots, no page errors and unchanged source; legacy `legacy55-green/runner.json` PASS55 checks/18screenshots with unchanged source. Inspected the strengthened repository assertions for native-initial geometry, candidate validity, real keyboard modality, footer/header reachability and unchanged selected context.

The original public failure and first local keyboard-modality harness false positive remain retained separately. The new staging result is explicitly `LOCAL_STAGING_NOT_LIVE`, `live_verification:false`. Physical touch devices, Safari/Firefox, actual gameplay/media acquisition and new public deployment/live verification remain unmeasured by this reviewer.

No confirmed remaining blocker was found in this bounded review. No independent new full-suite/browser run, provider request, source mutation or Git mutation occurred in this follow-up; the receipts above were inspected read-only.

Final source hashes:

```json
{
  "web_r4/champion.css": "ce458d2e512379a724245667e46d29028edbff934c2fd28f832cc588a5d88ef3",
  "scripts/browser_champion_insights.py": "9cac9d6e21f10cfd394a8779e5ab4205e3570ef0b337f790ac883072eb6c24bd"
}
```
