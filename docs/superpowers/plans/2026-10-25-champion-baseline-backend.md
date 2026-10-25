# Champion baseline backend implementation plan

> Execution: inline, test-first; no independent subagent is available.

Goal: add deterministic champion search and standalone baseline retrieval without changing the existing ten-pick validator or introducing a server/AI service.
Architecture: reuse the shipped catalog and loading-direction-profiles through a pure UMD module; a separate input/result contract isolates baseline and composition. Content stays authored/unreviewed and incomplete content is never padded.
Spec: docs/gameplan-content/champion-search-baseline-v0.1.md (PR #137, blob 37343d9460dd36b5fa6a098a2e3206b3a1447f8c).
Base: main 944c0ef64e59e94b19d3ebe5694efefae41cc8cc.

## Global constraints
- No top-level navigation or UI redesign, no new server, no AI/Riot request at lookup time.
- No change to protected user decision issues, tactical approvals, candidate freezes, or historical evidence.
- Baseline has composition=null and unknown actual conditions; no fake picks or advantage estimates.
- Strict role/patch/source/phase support; unsupported is not another role's prose.
- Five actions and traceable tags only when supplied by authored content; no automatic padding.
- Existing ten-pick analysis and evidence binding must remain intact.

## Tasks
1. Obtain an isolated checkout with source history through the available GitHub connector; direct network clone is unavailable. A temporary contents-read-only workflow may package committed public source history as a short-lived artifact; remove the temporary workflow before final changes.
2. Tests first: exact/prefix/substring/aliases, invalid inputs, ambiguity, deterministic sorting, role filters, catalog load errors. Implement search using existing catalog schema.
3. Tests first: baseline input, 4 existing prose-only profiles, phase gaps, missing facts, patch mismatch/unknown, five-action contract, tag provenance, metadata and no-mutation. Implement adapter.
4. Tests first: a composition handoff intent changes no stored draft, conflict detection, no invented picks; preserve ten-pick validation. Implement bounded handoff contract.
5. Register new source/test paths in the existing exact-source checker and regenerate its source manifest, without weakening checks. Run local focused tests, existing gameplan regression and repository CI.
6. Publish isolated PR with actual receipts and limitations; no merge/deploy unless separately verified. Update documentation without claiming complete UI or tactical validation.

## Review focus
Ambiguous aliases must not auto-select; corrupt catalogs differ from empty results; prototype keys are not champion IDs; a new source patch cannot bless old tactics; partial phase data must not suppress another valid phase.
