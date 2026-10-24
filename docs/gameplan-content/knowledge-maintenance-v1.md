# Authored direction maintenance registry v1

This is an offline, read-only registry over existing production content, not a new tactical engine or a claim of universal coverage. Run from the repository root:

```sh
python scripts/gameplan_registry.py tree
python scripts/gameplan_registry.py impact official:Caitlyn:E official:Ahri:Q
python scripts/gameplan_registry.py tree > evidence/gameplan-registry-before.json
# After an intentional content change:
python scripts/gameplan_registry.py tree > evidence/gameplan-registry-after.json
python scripts/gameplan_registry.py compare evidence/gameplan-registry-before.json evidence/gameplan-registry-after.json
python -m unittest tests_pregame.test_gameplan_registry tests_pregame.test_gameplan_direction
```

The CLI writes JSON to stdout only. Snapshot arguments and source bindings must resolve inside the repository, including through symlinks. It does not fetch URLs, modify external sources, restore files, or post review decisions. Python callers can use `build_registry`, `patch_impact`, and `compare_snapshots` directly.

## Inspect and edit

The tree has champion → skills, scopes, rules → output paths. Every official skill carries its retained source path, JSON locator, URL, patch, and binding audit. A `BOUND` skill means its stored hash and excerpt match the retained document; it does not establish tactical truth, live game state, or current-patch freshness.

Edit `web_r4/loading-direction-profiles.js` for baseline gain, method and explanation; use each rule's `locator`. Bump its version after intentional changes. Phase `keys` describe direct references, while `required_slots` gates the entire profile. Thus changing Caitlyn E affects all three registered phases, even though lane prose does not use E. The production `resolveDirectionProfiles` validates the complete module, checks role/patch/required facts, and expands skill names. The registry invokes that production validator, rather than maintaining a competing parser. It reuses `build_loading_catalog.located` and `sha256` for retained source checks.

Official facts continue through `scripts/update_official_catalog.py` and `scripts/build_loading_catalog.py`; this registry does not replace those collection/build pipelines. Preserve source snapshots. Do not edit retained official prose to make a hash check pass. Patch mismatch or a bad binding yields `SOURCE_REVIEW_REQUIRED` for an authored scope. The runtime still applies additional report-context gates, so `AUTHORED_CONDITIONAL` means an available authored baseline, not a guarantee that every report applies it.

## Current scope and provenance

| Champion | Registered role | Baseline phases | Provenance |
| --- | --- | --- | --- |
| Caitlyn | BOTTOM | lane, operations, fight | Existing version 1 authored profile |
| Ezreal | BOTTOM | lane, operations, fight | Existing version 1 authored profile |
| Fiora | TOP | lane, operations, fight | Existing `enrichCoaching:if(fiora)` prose in `loading-planboard.js` |
| Graves | JUNGLE | lane (early jungle), operations, fight | Existing `enrichCoaching:if(graves)` prose in `loading-planboard.js` |

Version 2 extracts the latter two baselines from already authored Korean text and bound mechanics. Their `provenance` identifies the source block. This is migration of existing interpretation, not new tactical validation. All profiles remain `TACTICAL_UNREVIEWED`; actual-match evidence remains absent. Fiora MID remains unsupported by this profile bundle even though another production role rule may cover it. Ahri and Sejuani role principles are not promoted into profiles by this work.

Every catalog champion has explicit statuses for all five roles and three phases: `MISSING_PROFILE`, `UNSUPPORTED_ROLE`, `SOURCE_REVIEW_REQUIRED`, or `AUTHORED_CONDITIONAL`. Matchup and composition coverage explicitly remain `NOT_INDEXED`. Unlisted champions are missing authored profiles, not weak, unsafe, or tactically impossible.

## Impact, versions and rollback

`impact` accepts champion IDs, official fact IDs, profile IDs, or repository source paths. Results retain both affected rule/output pairs and untracked changes. A known official Ahri fact remains untracked in this authored-baseline dependency graph. `complete` is always false: composition, matchup, state reconciliation, non-profile principles and runtime overrides are not exhaustively indexed. Existing report-local `dependencyTree`/`affectedOutputs` continues to provide contextual lineage; this registry supplies complementary file-wide baseline maintenance.

The manifest hashes exact profile, catalog, resolver, formation, compiler, registry-code and referenced official-source bytes. The canonical UTF-8 JSON snapshot hash excludes only its own hash field; timestamps and machine paths are excluded. Repeated runs over unchanged inputs produce the same hash. Snapshot comparison verifies the canonical hashes before reporting changed files, rules and scopes. Hashes provide integrity/reproducibility, not signatures, review approval, or proof that tactics work.

Rollback is manual and revision-bound: inspect the compare output, select the reviewed git revision, restore its matching authored profiles, retained official files, catalog and projection code together, rebuild the catalog using the established pipeline, regenerate the registry and run focused direction/coaching tests. Do not restore only a profile while retaining an incompatible patch. The CLI never performs destructive rollback automatically.

## Queue accounting

The queue 23–30/38–39/43 maintenance infrastructure now has a concrete inspectable tree, editable locations, explicit scope gaps, patch-impact diagnostics, version manifest and comparison workflow. The beyond-two-profile slice now covers four authored champions in three roles. These are infrastructure and bounded content-extension results only: full champion coverage, full dependency coverage, every matchup/composition rule, actual-match validation and broad role coverage remain incomplete. No user decision is inferred, no approval is fabricated, and this document is not a seal or final queue completion certificate.
