# Learning frontend implementation report

Status: implemented and verified on isolated PC and exported public subpath. No deployment or real-video acquisition claim.

## Owned changes

- `web_r4/learning.html`, `learning.css`, `learning-engine.js`, `learning.js`
- `tests_pregame/test_learning_frontend.py`
- `scripts/browser_learning.py`

Root owns shared navigation, server/export/CI and backlinks. No commits were created by this agent, as requested by root.

## Behavior

- Dark/gold shared six-menu shell and independent learning page. Existing `directions.html` and its six scenes remain directly linked.
- 4 groups → 20 topics → 80 leaves, with explicit distinction between taxonomy counts, 29 existing registry claim cards, and 8 unavailable link-only candidates.
- All 11 card fields render. Missing goal/threat/reason/waiting cost/recovery remain unknown; tactical content resolves exact shared registry references rather than storing another corpus.
- Search title/question/taxonomy/identity/condition/claim prose using NFKC case folding and AND across whitespace-separated terms. Champion/role/opponent/situation/evidence filters, literal source-patch filter, and separate patch-state filter.
- URL state uses `#learn=` for compatibility with the PC server's existing query rejection. Public `?` state can be read and converted. Back, refresh, same-document hash changes, lowercase known identity normalization, and safe unknown-filter empty results work. Invalid role/claim and malformed identity/taxonomy contexts preserve a bounded `invalid=context` flag through links and repeated URL roundtrips; results remain empty with an explicit error until reset. Raw malformed values are removed and the session return token survives.
- Only bounded allowed context keys enter learning links. Complete original gameplan/champion/review URLs remain in session storage behind random 128-bit opaque tokens, expire after eight hours, and cannot be restored by an independent browser session.
- Evidence details distinguish existing source text, transcript references, visual review, app interpretation, unknown player knowledge/viewer perspective, source patch and current applicability. Source IDs, hashes, access/license state, review state and unknown fields remain visible.
- Video segment links require canonical segment rights and access both PERMITTED, VALIDATED integer video offsets, valid start/end order, SHA-256, exact video/URL binding, and transcript cue IDs or verified visual evidence as applicable. Nullable game-clock time never becomes a playback timestamp.
- Condition-change reflection reuses source conditions/counterexamples; app-authored questions are labeled, answers remain unsaved, and no automatic grading or tactical answer is generated.
- Loading, empty, review-pending/source-insufficient candidates, failed fetch and retry are explicit. No provider or external media request is required.

## Verification

Observed RED before implementation: five original tests failed because the engine/HTML did not exist. Additional RED→GREEN iterations covered actual dotted taxonomy IDs, fragment state, dashboard returns, AND-term search, separate patch labels/states, segment authorization, source-patch labels with spaces, URL-path parity, the enlarged inactive skip link escaping its hidden position, and invalid role/champion/claim contexts silently broadening into an unfiltered search.

Commands and final results:

- `python -m unittest tests_pregame.test_learning_frontend`: **11 passed**.
- `python -m unittest discover -s tests_pregame -p 'test_learning*.py'`: **37 passed**, 1.627 seconds.
- `python scripts/browser_learning.py --output /workspace/gp23-artifacts/learning-browser`: **33 checks passed**.
- `node --check web_r4/learning.js`: passed.

Search parity covers **37 actual-data query/filter cases**, comparing Python against both the direct JavaScript filter and URL serialization → normalization → filter, including unknown filters and case-insensitive identities. Independent scoped reviewer also reproduced the original contract issues and confirmed they are resolved.

Browser coverage includes PC/public-subpath parity, six menus, all eleven fields, 80-leaf hierarchy, search/filter/empty states, Back/refresh, unknown/mismatched/source patch distinctions, source evidence, reflection without grading, session isolation, invalid private claim rejection, canonical URL context, invalid role/champion/claim fail-closed state after refresh and reset with preserved return links, desktop/tablet/390/320, 200% equivalent viewport, 320px with 200% text, keyboard focus, no horizontal overflow, fully hidden inactive skip link, delayed loading, 503/retry recovery, and synthetic authorized timestamp playback URL construction.

Final browser receipt: `/workspace/gp23-artifacts/learning-browser/learning-browser.json`

Browser errors: 0; unexpected HTTP errors: 0; external requests: 0; provider calls: 0; new user approvals: 0. Seven screenshots were saved; desktop and enlarged mobile screenshots were visually inspected. The timestamp check uses one explicitly synthetic local JSON segment and **does not** count as real-video evidence. Actual new visual reviews remain N=0.

A broad `tests_pregame` run was started while other agents were still editing the shared branch, then stopped at root's request to avoid duplicate/inconsistent full-suite runs. Its intermediate log is preserved at `/workspace/gp23-artifacts/learning-pregame-suite.log`. Before interruption, two failures were observed and handed to the owner: `test_champion_handoff.ChampionHandoffTests.test_browser_back_from_detail_keeps_updated_assumptions` and `test_browser_handoff_preserves_coach_edited_scenario`. This is not a final full-suite result; root owns the final stable full-suite verification.

## Invalid-context review follow-up

The final branch review found that dropping invalid role/claim/malformed champion values could expand results. A new test first reproduced two failures, then passed after a bounded sentinel was introduced. The 9-vector regression includes malformed group/topic/leaf, repeated serialization, generated learning links, preserved session return and genuine empty-filter behavior. Browser tests repeat invalid role/champion/claim cases on both PC and public hosts, refresh each error, then reset to all 29 cards and 8 candidates while retaining the original return link.

Evidence: `/workspace/gp23-artifacts/learning-context-red.log`, `learning-context-green.log`, `learning-context-all-green.log`. The final browser receipt passes 33 checks and its source hashes match the current files. Code is frozen for root integration.

## Public API

`window.LearningRoom` is also CommonJS-compatible. Integration entry point:

```js
LearningRoom.createLearningURL(
  {champion, role, opponent, claim, lesson},
  {storage: sessionStorage, returnURL: location.pathname + location.search + location.hash}
)
```

The returned relative string uses `./learning.html#learn=...`. Claim context is a single canonical claim ID. `state.patch` is a literal original source label; `state.patch_state` is the independently selected state. Return URLs allow only same-app relative routes, including `/loading`, `loading.html`, champion pages, `dashboard.html`, index/review and directions. Absolute/external URLs fail closed.

`run(env, out)` in `scripts/browser_learning.py` accepts existing `LOADING_PC`, `LOADING_WEB`, `NODE_PATH`, and optional `CHROMIUM_EXECUTABLE` environment values.

## Scope limits

All actual learning records remain read-only and coaching disabled. No actual transcript/scene acquisition, third-party video fetch, real tactical outcome validation, live-game connection, protected decision edit or production deployment occurred. Existing knowledge registry was read, not rewritten by this agent.

Generated UTC: 2026-10-25T10:44:27.717693+00:00

Browser-bound source SHA-256:

```json
{
  "web_r4/learning.html": "3eb85d1c201e11c8d2a2a13b2707f13dd076be007ac2ba5203df26e38d20ee69",
  "web_r4/learning.css": "eed2c44b7b8bdd57910ea019bc532609451a8bb737a876617c45f88d94829d92",
  "web_r4/learning-engine.js": "98ab2e87a3de8350bec45a01bd35eff9bb3533e4318b3a773dbefce98cb18196",
  "web_r4/learning.js": "ccd1bca3869479e2e32480950edeb15d1525dc72efde591f967c09ae9c8723d3",
  "web_r4/learning-room.json": "b7a71d3bfe809b2388d34b358b7f5f7ebce162d6eccb0571d52f9d36d0e7de6f",
  "web_r4/loading-knowledge.json": "e009820f94407824d71e5df3673e9b7d32dda7e7197cb796711b7b5b391efdfd"
}
```
