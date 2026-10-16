# Independent actual-evidence branch review — 2026-10-16

Reviewed the uncommitted working-tree delta against parent `103b8b80c915accba7d7e5c82951d020b17d6e09`, root `AGENTS.md`, `contracts/actual-evidence-v1.md`, and `docs/superpowers/plans/2026-10-16-actual-evidence.md`. This is a read-only source review except for this report. It does not authorize collection or relax any contract.

## P2 — Fixed historical recovery selects the newest checkpoint before applying its pin

Location: `.github/workflows/resource-recovery-offline.yml:31–45`.

The new historical resource job calls the unchanged `scripts/recover_pro_cache.py`. That helper intentionally selects and downloads the **newest** trusted PRO checkpoint, for continued collection. Only after downloading does the new workflow require run `38410710876` / artifact `11822391323`.

Consequently, one newer valid PRO checkpoint makes this fixed historical recovery fail with `PINNED_EXISTING_CHECKPOINT_UNAVAILABLE`, even while the exact required artifact is present and usable. A newer unresolved collection can also block recovery of this otherwise independent pinned historical snapshot. The job additionally downloads an unintended newer ciphertext before rejecting it. This affects repeatable recovery of the specifically preserved 89-match/108-participant source, rather than the legacy collector's correct newest-cache policy.

New isolated in-memory counterexample, executed with `python` and injected run/artifact lists only: supplied the required pinned run/artifact plus a newer valid main checkpoint. `select_checkpoint` returned run `38410710999`, artifact `11822391999`; the new workflow's fixed-ID check evaluated false. No provider, GitHub, secret, or private cache was accessed, and no historical test was executed.

Fix expectation: give this new fixed-snapshot workflow an additive recovery path that validates the exact pinned run and artifact identity/trusted provenance, expiry, ciphertext size and archive format before downloading/decrypting that exact artifact. Preserve the existing newest-checkpoint behavior for continued PRO collection. Add a new isolated negative/positive fixture showing that newer valid, expired or unresolved PRO history cannot substitute for or unnecessarily block a valid pinned historical artifact.

## Reviewed properties

- Resource calculation keeps exact 600000/900000 timestamps separate from the last received eligible point in the corresponding floor-minute bin. It excludes post-end frames, permits the final received eligible point, does not interpolate/borrow/zero-fill, and retains separate gold, XP and level values.
- Own/opponent differences use an unambiguous opposite-team same-role participant from the same frame. Own values survive unavailable opponents. Per-metric valid/missing counts, disjoint missing reasons, distinct-match counts, patch and champion/role/opponent cohorts are exported. Aggregate partition counts and weighted means are checked.
- Private participant/account/match identities remain in memory. The public resource schema is allowlisted; exact report bytes, source-file bytes, commit ancestry, pinned checkpoint identity, and the required 89/108 population are checked before PC display. Socket-denied extraction and ephemeral-directory cleanup are present. The future PRO preservation audit is additive and does not replace encryption/checkpoint steps.
- PC integration adds only the measured-resource card projection. Matching requires patch, champion, role and actual opponent; there is no position-pool substitution. Cards explain observed-time semantics and retain exact results separately. Existing launch/token/manual/LCU source files are preserved. Windows LCU remains external and unverified.
- POV user configuration remains pending and distinct from independent dated URL/hash metadata receipts and Q19. Canonical uploader identity is not promoted to player identity, official affiliation, verified POV, continuity or same-game linkage. Upload dates remain upload dates.
- The already documented daily-safety findings were checked against their fixes rather than rerunning that review. CLI ACK validation binds the run/path/main/attempt, artifact and exact paired reservation state. Claim directories no longer depend on output directory or `RUNNER_TEMP`. Empty/malformed/excluded output is separate from nonempty extraction. Pre-reservation typed failures are retained for subsequent-day stops.
- Daily VIDEO output remains exploratory or model-reported/unreviewed, with provider offset isolation explicitly unproven and blind evaluation disabled. No confirmed-game field filling, frozen-advice evaluation, or valid scene evaluation is claimed by these modules. No future-isolation or coaching-effect proof is established by this review.
- Both modified CI workflows select evidence mode before pilot/v2.3/historical modes. The new verifier explicitly enumerates only the six new test modules; predecessor verifiers and browser suites are behind other mutually exclusive scope conditions. The supplied `implementation-delta.log` records **63 new tests**, not an actual-provider execution. The browser runner tests absent-dataset fallback now and selects a bound actual cohort when a report is published; actual dataset/browser results still require subsequent trusted execution.

## Limits and disposition

One P2 is open at the reviewed snapshot; no additional concrete P1/P2 was found. No original sources, test files, ledgers, decisions, frozen evidence, commits, or external applications were changed. No old test suites were rerun. The one counterexample above is newly constructed and isolated. No real provider request, raw-cache restoration, private identifier inspection, actual 200 receipt, extraction validation, scene evaluation, Windows LCU completion, or coaching accuracy is asserted.

## Main disposition

P2 fixed before any provider execution: new `scripts/recover_resource_checkpoint.py`
fetches the exact pinned run/artifact, checks source commit/main/path/first attempt/
artifact identity/expiry/size, then downloads only that ciphertext. The legacy
newest-checkpoint collector recovery is byte-preserved. New fixed-checkpoint3tests
RED→GREEN and new resource15tests PASS; final affected scope66tests PASS. Newhelper
is included in resource report source binding. Logs fixed-checkpoint-{red,green}.log
and final-implementation-delta.log preserve the evidence. No deferred findings.
