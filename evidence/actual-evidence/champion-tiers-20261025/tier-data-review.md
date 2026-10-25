# Tier/opponent data review — SPEC and QUALITY

Review completed 2026-10-25T11:26 UTC against uncommitted work in `/workspace/lol-coach-champion-tiers`, HEAD `d1d00053dfd3710bb94e08549c7ca256ab0c43ee`. Read-only product review; only this external review artifact was written. No Riot/provider/network requests, credentials, issue comments, git mutations, or whole-suite reruns. Sources reviewed: repository AGENTS.md, prior tier-opponent-audit.md, champion-insights contract, private result/public projection modules, collector/CLI/resolver, policy config, workflow, additive amendment, and relevant fixture definitions.

## Verdict

No remaining confirmed blocking defect in this statistical/privacy/admission scope at the final hashes below. Two defects were identified during this moving snapshot and corrected by their owners; local focused verification confirms both corrected behaviors. This is a bounded review, not a claim that the complete implementation, browser, knowledge research, or all existing suites passed.

### F1 — P1 SPEC: same anonymous match accepted under conflicting patches (corrected)

Earlier `champion_insights.py` `c6262263e37fd75f4769e97f60604b3242c39e5490bb131725a2f60e797424c6` checked overlap only within each patch. Two valid synthetic legacy outcome snapshots built from the same `pair(741)` identifier, one with source/pair patch16.19 and another source/pair patch16.20, had identical member hashes. `build_champion_insights([a,b], allow_synthetic=True)` accepted both and emitted ALL.matches=1 on both patches. This violated the audit's same-hash/different-patch fail-closed requirement.

Owner `champion_insights_data` added a global hash→patch binding across legacy sources and anonymous result records before constructing scopes. Reviewer reran `test_same_hash_different_patch_legacy_and_mixed_sources_fail_closed`: PASS. Acceptance: reject legacy/legacy and legacy/result disagreement regardless of leaf tier or eventual patch filter; identical same-patch evidence keeps existing deduplication behavior. Final module hash below includes the correction.

### F2 — P2 SPEC: unspecified patch was not pinned by reused result evidence (corrected)

Earlier collector `cd29cdb3f2724e2b3dc58292ccea160481e064def6984f06c5585dfe572900a5` admitted a previously retained result when `patch=None` without setting `source.patch`. A later fetched match could pin a different patch, leaving a multi-patch batch inconsistent with first-eligible patch semantics. Owner `all_tier_collector` confirmed this path and now pins source.patch to the first eligible reused result before later details are processed.

Reviewer reran `AllTierResultCollectionTests.test_unspecified_patch_pins_first_reused_result_before_fetching_other_patch`: PASS. Acceptance: reuse pins the exact patch; another fetched patch creates neither a result record nor a timeline request for that batch.

## Confirmed design properties

- SPEC: all ten leaf tiers are admitted; ALL/MASTER_PLUS remain aggregate filters; default public tier is MASTER_PLUS. One bounded tier/division rotation replaces a tier loop. Historical source scope and the separate Challenger-reference policy remain separate; amendment documents the changed authorization. Current seed rank is explicitly distinct from A's unknown historical rank and convenience sampling.
- SPEC: private result union keys by stable anonymous hash, merges seed memberships/provenance, and rejects conflicting winner, canonical roster, sample kind, patch, queue or map. Public rates and Wilson intervals are recomputed from integer wins/N. Legacy partial overlap fails closed; a legacy snapshot fully covered by results must agree on every retained cohort/opponent and aggregate wins before being dropped as redundant.
- SPEC: actual enemy team positions drive cross-role observations; ally champions do not contribute. Reversed role/champion pairs use complementary A-team final wins. Same-role encounter rows remain a separate basis that can retain legitimate legacy evidence; no final winner is inferred from power resources or lost roster membership.
- SPEC: default frequent same-role opponents sort encounter N descending. Statistical best/worst lists independently select at most five eligible N≥20 rows for each enemy role. Deterministic ties, sparse list overlap, all-tied state, CI/multiple-comparison limitations, and fewer-than-five outcomes are represented explicitly. Knowledge hardest/easiest is separate from these rate sorts; its source quality is outside this data-only review.
- QUALITY/privacy: strict record and public field allowlists prevent raw provider fields, participant identifiers, private member hashes and rosters from entering the new public aggregate projection. Private result state and its digest-bound completeness ledger are stored outside public aggregate-directory paths and in the separate sufficient-state artifact. Storage access control of GitHub artifacts was not independently audited.
- QUALITY/completeness: known results are independent of power hashes. Missing result evidence remains eligible for detail-only bounded backfill; successful prior results can be reused for newly discovered seed membership. Same-tier complete records skip the match-work ceiling to avoid starving later backfill. Malformed or contradictory wins withhold results. Public-only restoration does not invent legacy results.
- QUALITY/admission: workflow retains trusted-main-only secret use, pinned action revisions, serial concurrency and the existing 650-request/300-match/40-player/one-page/two-retry/900-second run arguments. No new per-tier parallel jobs or budget resets were added. Request pacing, Retry-After handling and immediate first401/403 stop remain in the shared collector. Config's key window still expired at 2026-10-16T10:16:49Z; this review made no probe and no new acquisition is claimed. Free-only/provider entitlement boundaries were not changed by these files.

## Reviewer-executed evidence

Five focused tests passed in the first invocation: global cross-patch conflict rejection; unique seed union/no tier fallback; weighted nonuniform rate/Wilson recomputation; enemy-vs-ally cross-role and reverse complement; legacy partial overlap/disjoint/repeated evidence. That invocation also had one test-loader ERROR because the collector method was initially addressed under the wrong class; the corrected class-specific invocation passed. The mirror-role fixture test independently passed. No full test run was performed.

`python scripts/build_champion_insights.py --check`: PASS, deterministic checked-in projection matches validated local evidence.

A direct `project()` inspection confirmed REAL sample kind; default MASTER_PLUS PARTIAL, only CHALLENGER available, MASTER and GRANDMASTER missing; 50 unique retained matches, zero roster-result matches, zero ENEMY_TEAM_ROSTER rows, largest same-role N=6, zero READY matchup rows. No all-tier coverage or N20 ranking is fabricated from current local evidence.

## Final reviewed snapshot hashes

```text
ccd4bc6a1d71c5f03a9bcc304e1516103d383cc6adcd2b48cb6e9e46b5ea8cb5  coach_v1/matchup_results.py
df3d10db95bcded661de999b9ecc4877e9a5ff31ae3f01f95983f76d7e0aae9d  coach_v1/champion_insights.py
cc04027e83070a71ad5602f8238990cd3e24e29e5972f87ecdd0e070505b3ad6  coach_v1/riot_collector.py
9eb2f7b700b25ba069311350a61e300303f4951d30c2ef7abda5625cea780226  coach_v1/riot_collection_policy.py
749b038c7eb2737e3d40efe84f6d871a36b6a7deb139351d5ae0e7a29a8d2d05  scripts/collect_power_stats.py
93db9af4c1b727ea7926e86a3f40447586436f3396b8b485c0645a6f7a088013  scripts/resolve_riot_collection.py
72c1c02a9ed6db7265f3679b47d8aea53d11fc43af0847c59c83c61f778c47a3  scripts/build_champion_insights.py
45e8fb3513aac12346b22cf4f561553a1a11f2338c2be2a1ee45679552a1e1d5  config/riot_collection_policy.json
3a4f46a267ecd1af451f7b8587793a9eaacc9811d1f0a3d8470034a0e6b574d4  .github/workflows/riot-power-collection.yml
6d3c033d85dfee7cfa375f115a8ed989fe1c13b482a8675f130122ac933ab5c6  contracts/champion-insights-v1.md
366287cc6c294c46113420d7fd753e2e937987cacf2f6ae4823d6b70924a7bc6  web_r4/champion-insights.json
```

## Pending changes / limits

Product files changed during review. Final verdict applies only to the listed hashes. No additional correction was pending from either contacted data owner at completion. Frontend state/handoff behavior, knowledge artifact/source research, artifact hosting access controls, live API behavior and end-to-end deployment require their respective independent review/verification; this review provides no broad untested completion claim.
