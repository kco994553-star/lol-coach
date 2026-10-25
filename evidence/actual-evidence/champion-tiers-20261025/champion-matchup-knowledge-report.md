# Curated champion matchup knowledge implementation

Implemented only the six authorized new files in `/workspace/lol-coach-champion-tiers`:

- `coach_v1/champion_matchup_knowledge.py`
- `scripts/build_champion_matchup_knowledge.py`
- `config/champion_matchup_references.json`
- `web_r4/champion-matchup-knowledge.json`
- `tests_pregame/test_champion_matchup_knowledge.py`
- `docs/gameplan-content/champion-matchup-knowledge-v1.md`

No commits, agents, new network calls, external application writes, approval registry changes, or gameplan-rule connections.

## Result

Public artifact is available to frontend and its exact shape has been communicated. It contains 45 source-scoped records: 39 conditional LANING/JUNGLE candidates and six OVERALL_UNSPECIFIED references, backed by five named public guide sources.

| Champion / position | Difficult | Relatively easier, conditional | Reference-only |
|---|---:|---:|---:|
| Caitlyn / BOTTOM | 4 | 3 | 2 |
| Ezreal / BOTTOM | 3 | 2 | 4 |
| Fiora / TOP | 5 | 5 | 0 |
| Graves / JUNGLE | 5 | 5 | 0 |
| Yunara / BOTTOM | 5 | 2 | 0 |

`select_knowledge(index, champion, position)` returns `difficult`, `easier`, `conditional`, `references`, `coverage`, `limits`. `conditional` combines the two selected candidate lists. Only scope-matching conditional candidates can enter the two lists. Each list has at most five records. Source categories determine display groups; equal-category ties sort by canonical opponent ID, with no invented rank or numeric power. Unresearched champion/position combinations return empty lists and `NO_RESEARCH`; real coverage gaps remain visible.

Canonical source IDs `E:S1` (Fiora) and `B:S1` (Yunara requested original URL) are reused. Three new sources use stable `matchup-guide:<URL-SHA256-prefix>` IDs. Source objects preserve original/final public URLs, author, HTML hash, retrieval time, page/paragraph version limits and access status. All 26.x ↔ Riot16.x mappings remain UNVERIFIED_IF_DIFFERENT.

Categories remain author opinions; Korean reason/action/change_if objects carry field origins and quote references. Overall-only assessments and early-phase contradictions remain excluded from lane lists. `coaching=false`, `tactical_validation=UNREVIEWED`, `tier_independent=true`, `derived_from_statistics=false` are fixed publication metadata. Neither builder nor selector accepts statistical tiers or rates.

## Copyright and provenance

No exact source quotes, full source paragraphs, HTML corpus, local raw paths, tokens, or private fields appear in config/public JSON. Published verbatim quote/paragraph word count is zero. Evidence stores normalized paragraph SHA256, quote SHA256, locator/HTML line and prior normalized matching status. Raw HTML stays in `/workspace/gp23-artifacts/matchup-source-html` outside repository/publication. Builder does not depend on that directory or falsely claim to re-fetch/re-match original HTML during regeneration.

The earlier research step verified source snapshot hashes and canonical champion IDs. The public builder validates stable IDs, retained-source identity reuse, allowed public HTTPS original-guide sources, typed scope/category eligibility, phase consistency, paragraph/quote proof shape, explicit patch uncertainty, paraphrase origin and field allowlists. Unknown source fields or raw corpus fields are rejected.

## Verification

- RED: `python -m unittest tests_pregame.test_champion_matchup_knowledge` initially failed all nine tests because the projector did not exist. Log: `/workspace/gp23-artifacts/champion-matchup-knowledge-red.log`.
- GREEN: focused suite now passes **9 tests**. Log: `/workspace/gp23-artifacts/champion-matchup-knowledge-green.log`.
- `python scripts/build_champion_matchup_knowledge.py --check` passes.
- Tests exercise real coverage and honest gaps, overall/reference exclusion, no tactical promotion/statistical fields, canonical IDs and phase typing, conflicting duplicates, source-ID reuse, unsafe source rejection, copyright/private field rejection, deterministic category grouping, synthetic sixth-entry max-five behavior, and stale artifact detection without rewriting.
- Full suite was intentionally not run while other workers are editing, per parent instruction. Root integration should run it after concurrent edits settle.

## Remaining limitations

This is a conditional guide-reference library, not verified current-patch matchup strength or a global ranked TOP5. Guide paragraphs may be older than their titles; fixed builds/cooldowns/automatic victories are not adopted. No 173-champion completion is claimed. New guide evidence requires human-authored curation and renewed source checking, not extrapolation from statistics or existing categories.
