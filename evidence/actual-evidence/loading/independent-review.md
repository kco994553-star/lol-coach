# Loading Strategy MVP — independent implementation/source-boundary review

Date: 2026-10-17 UTC. Reviewer: separate `loading_review` agent; not the engine,
catalog, or UI author. Scope: new loading engine, catalog/compiler, UI/map,
manual/PC draft boundary, server/export changes and new tests on
`work/loading-strategy-mvp-20261017`. AGENTS.md and
`contracts/loading-strategy-v1.md` were read. No protected issue was changed;
no game/video/provider request or old complete regression suite was run.

This is code and retained-source review, not expert coaching approval. Functional
checks, source-fit review, matchup interpretation and real-game effect are
different evidence. Real coaching N=0; accuracy=null; no AUTO/USER promotion.

## Findings and disposition

| Priority | Original finding | Disposition after author changes |
|---|---|---|
| P1 | `signature()` picked the first skill in a multi-function rule's source list. Example 2 described Ashe E (Hawkshot / 매 날리기) as the PICK/control and PRESSURE means. Lee Sin COVER incorrectly pointed at Q; Kai'Sa ACCESS at W; Zed ACCESS at Q. | Closed in the reviewed bytes: explicit function-to-slot bindings replace source-list ordering. The 20 champion / 50 function-slot bindings were read against their preserved official Korean descriptions. Unmapped functions remain champion-level exploratory candidates without a specific skill claim; FRONT does not falsely inherit one skill's effect. Direct reproductions confirmed Ashe PICK=R/PRESSURE=W and Lee Sin COVER=W. This does not verify the tactical classification or optimal use of those skills. |
| P2 | The public export produces `index.html`, but the current-page navigation linked to unexported `loading.html`, causing a public-site 404. | Closed by `./index.html`; server routes still support the local loading aliases. Verified against the explicit export allowlist. |
| P2 | Input/source patch mismatch was only explained in detailed evidence. | Closed: a 16.19 input with source 16.20.1 now produces a summary uncertainty naming both versions and the application limit. |
| P2 | ASSIGNED jungle input treated the enemy jungler as a fixed lane opponent despite the UI's stated boundary. | Author also found this boundary; independently confirmed the fix: JUNGLE/ASSIGNED has `lane.opponent=null`. Opposing jungle identity remains separately named without inferring location or a first gank. |
| P2 | The first-three threat cap silently omitted known candidates based on type/roster order; example 1 omitted Nautilus. | Closed: details retain all five observed classification candidates in example 1, including Nautilus. The two-name summary is a display truncation, not a validated importance ranking. Unclassified enemy functions remain unknown. |

No unresolved blocking implementation/source-attribution finding was identified
in the reviewed bytes. Browser integration, required CI, merge and live public
deployment evidence are separate Main-owned completion gates, not asserted here.

## Boundaries and substantive limitations to report

- Ten-pick input reaches a shared deterministic analysis path without economy
  inputs. Composition, role, actual skill names, counterpart context and maps
  change with relevant picks/position. Search coverage is not a claim that every
  champion has a fully authored strategy.
- The six lane milestones deliberately retain unknown matchup advantage and
  skill learning/readiness. Much of their action text and operations fallback is
  a reusable conditional framework. `interactions` largely combines official
  descriptions with a small number of champion-specific hypotheses; it is not a
  complete, expert-verified matchup-interaction library.
- Source facts retain URL/version/hash/locator. Existing rule classes remain
  EXPLORATORY and incomplete. Official movement, control, damage or shielding
  descriptions support those mechanics, not an optimal plan or success rate.
  Accepted coaching lecture evidence remains zero.
- Recall references are existing champion/position/patch descriptive purchase
  proxies, not opponent-matchup observations or recommended first-buy timing.
  UNKNOWN metrics stay unknown in the UI even when a raw median is present.
- Existing six scenes remain bounded to Caitlyn recall, Fiora side/group and
  Ornn objective roles. Maps are approximate explanatory geometry, show actual
  allied picks only and do not establish enemy positions, safe paths, exact
  ranges or current skill readiness. Numbered steps are explanatory sequences.
- Manual and cached-draft input use the same engine. Public UI does not request
  a local PC API; local import requires an explicit click, an existing session
  token and CONNECTED/ChampSelect. `fromDraft()` whitelists pick/position fields.
  This is not actual Windows/LCU verification; BLOCKED_EXTERNAL remains.
- Guidance is pre-game learning/postgame review. No live tactical permission,
  economic auto-classification, player intent or hidden-position inference is
  established by this work.

## Reviewer checks

Read-only local Node reproductions checked the corrected functional references,
patch warning, jungle counterpart boundary, all-five threat details and a fully
unknown-classification Gangplank fallback (no forced arrows or scene reuse).
Those checks passed. An earlier new-engine substitution smoke over 164 valid
own-champion changes produced no exception/undefined result; this is only
implementation evidence. Author test files were inspected rather than rerunning
their completed suite. No real match scene or coaching outcome was evaluated.

## Reviewed source SHA-256

These identify the reviewed working-tree bytes, not a future commit or CI result.
Material later edits need their affected review/checks; these hashes must not be
silently rewritten to imply an unperformed review.

| File | SHA-256 |
|---|---|
| `web_r4/loading-engine.js` | `a882663e39856489a6dd6c9053ce1746237d80c4f6fad4aca8f810c092ad24c5` |
| `web_r4/loading.js` | `a64c1387bfad7950f36d5494f5b20a77ab7ce16f9b04f78b7f101a73124549ac` |
| `web_r4/loading-map.js` | `7555f5c879f590f18f647d320deeec7ce563b2f13f611c4a25ab290e5052062d` |
| `web_r4/loading.html` | `0c13fa0550b50afe12422caf5414d9d9a24513c62a6967385310a3c782d2c73e` |
| `web_r4/loading.css` | `0915d633c1e041642b6d341ea5623577a3eee4a769c0eaae61fa9b0a48b961ec` |
| `web_r4/loading-data.json` | `923c57741d552d28e2be5b07329617c3b219ac9f4b79637ce3f22e2d735368b1` |
| `scripts/build_loading_catalog.py` | `db4ad3deac1b906f17da780bfc7bb5246357701fa892a92e40aa57dddfd6549b` |
| `scripts/build_directions_web.py` | `e7f757d84ab512cff5841dbd3440a7b99f646fdfac4d551ad03ff5b5608acd43` |
| `coach_v1/pregame_server.py` | `09361ae0bda2c614aa8597ac94644c4991957c96302218bd418a871bd9f705b5` |
| `tests_pregame/test_loading_strategy.py` | `e1577a74b6cd3b38591f4da70795268d8b65b503e69f74f6182c7c4fb3e00b17` |
| `tests_pregame/test_loading_catalog.py` | `a6fb609d0c6fcd010a86f7de3618e869da28e5c2b05ba8c9d6a69e740b8d3b46` |
| `tests_pregame/test_loading_http.py` | `e8bc8f3802da61264c4bef161389b2999e74b763acd054133d482eae33bed542` |
