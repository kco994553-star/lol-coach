# v2.3 trusted recall acquisition integration

Implemented offline reuse plus an optional bounded Challenger acquisition path. No real provider requests, Actions dispatches, GitHub API calls, Secret reads, commits or publication were performed by this worker. Real collection remains pending trusted-main merge and Main's dispatch.

## Public interface

`python scripts/collect_recall_stats.py --private-directory PRIVATE_CACHE_ROOT --output-directory PUBLIC_PRO_DIR`

The default population is `PRO_REFERENCE`. The private root must already contain `private/matches/*.json` recovered from the existing authenticated encrypted pro checkpoint. Each envelope is loaded through the existing `PostgameStore._load` validation, which rejects synthetic source, unsafe paths, invalid raw shape and inconsistent identity binding. No account cache is opened, account lookup repeated, match list fetched or timeline refetched. Missing/corrupt data fail closed. Multiple recorded participants from the same match are combined into one anonymous match cluster. Only each envelope's recorded participant is included; opponents provide context without being labeled pro observations.

The cache can contain roster candidates recorded before an operational position-share replacement decision. This is therefore the **recorded user roster participant** population, including any such cached primary/backup candidates, rather than a claim of exact reproduction of the old final selection list. User-reported pro status is not independently verified.

`--population CHALLENGER --patch MAJOR.MINOR` explicitly requests new collection. The trusted workflow resolves the current exact official Data Dragon patch immediately before it; the CLI itself requires an explicit exact patch and never silently pins the first historical match. It uses `RecallCollector`, a narrow subclass of the existing `RiotCollector`, consuming each original accepted match/timeline response in memory. It does not refetch pairs or change existing Riot transport, key sanitation, authentication stops or rate accounting. This is current Challenger seed **match discovery**, not verified Challenger rank for all ten historical participants.

Fresh caps (defaults and hard maxima): 650 requests, 300 matches, 40 seed players, one league page, two retries, 900 seconds. `--lookback-days` accepts 1..30, default7. Existing local windows remain20 requests/second and100/120seconds per API host, with shared auth-stop on first401/403. The workflow serializes all Riot jobs with `riot-power-collection-main`, waits121seconds before a fresh client, and gates execution on trusted repository/main, explicit `key_renewed=true`, dispatch event, and run_attempt1. Pro reuse requires no Riot key and runs before the optional fresh client; workflow dispatch itself retains the renewed-key gate requested by Main.

The only public outputs per population are `recall-data.json` and `collection-receipt.json`. `extract_match`, `build_dataset`, and `validate_dataset` are imported directly. Output location validation reuses the existing disjoint public/private path boundary. The receipt projects fixed fields and bounded enums/counts, has no raw payload/identity/path and reports samples separately from availability. `HAS_OBSERVATIONS` means original matches were extracted; it does not mean a champion has five independent matches, that raw health exists, or that advice is accurate. Historical anonymous power/pro aggregates are never treated as health evidence. Missing raw health remains excluded/UNKNOWN in the new dataset. All measurement cutoffs remain operational analysis definitions, not recommendations.

## Trusted cache and workflow

`.github/workflows/recall-reference-collection.yml` reuses `recover_pro_cache.py` to select the newest trusted encrypted checkpoint, including interrupted collection handling. It decrypts with the same `private_pro_bundle.py` runtime environment seed as the current pro workflow. Absent/unresolved checkpoint, rotated key or authentication failure stops the job; there is no identity lookup/bootstrap fallback. The cache is read only and is never re-uploaded or replaced by this workflow. Ephemeral decrypted originals and recovered ciphertext are removed in the always cleanup step.

Actions use immutable40-character pins, and pinned existing runtime requirement files are reused. Explicit artifact paths include only the two population datasets/receipts plus `source-binding.json`. The source binding records actual checked-out commit, hashes of extraction/acquisition/privacy/transport/workflow/contract/runtime inputs and exact validated dataset byte hashes/sample counts. Dataset strict validation and paired receipt sample matching happen before artifact publication.

## Verification

`collection-red.log`: initial five tests failed because the helper/workflow were absent.

`collection-green.log`: ten tests pass using synthetic raw envelopes and fake transport only. Coverage includes offline no-provider behavior, exact participant selection, two-player/same-match union, real-shaped synthetic fixture privacy projection, runtime rejection of explicitly SYNTHETIC envelopes, missing/symlink/corrupt-cache fail-closed behavior, stale-output removal, original raw pair reuse without extra requests, actual fake-transport extraction/export with exact historical patch rejection, first401/403 stop, hard caps/request budget and workflow trust/serialization/artifact allowlist.

`python -m py_compile coach_v1/recall_collection.py scripts/collect_recall_stats.py` passed. CLI `--help` passed. No claim is made about an actual number of reusable stored records until the trusted run executes. No real collection or coaching accuracy is claimed.

## Main's post-merge execution and safe receipt

After merging and checking the intended trusted main SHA, Main can dispatch the default offline path with:

`gh workflow run recall-reference-collection.yml --ref main -f key_renewed=true -f collect_challenger=false`

For the renewed-key bounded Challenger path as well, set `collect_challenger=true`. Start a new dispatch if blocked; reruns are intentionally forbidden. Do not download the private encrypted artifact for public receipt; this workflow needs no such publication.

Main should verify the completed run's trusted repository, workflow path, branch, event and attempt; download only `recall-reference-public-safe` into an isolated directory; validate both available `pro/recall-data.json` and `challenger/recall-data.json` through `validate_dataset`; verify their byte hashes/sample counts against `source-binding.json` and check `actual_commit` and source hashes against the intended checked-out source. A failed optional fresh acquisition can preserve valid offline pro data with an explicit BLOCKED_EXTERNAL Challenger receipt. Do not treat this as successful fresh acquisition.

After that validation, place the safe population files in `data/recall/YYYY-MM-DD/pro/` and `data/recall/YYYY-MM-DD/challenger/`, retain the safe source binding and run receipt, and let Main's loader consume those exact population-specific files. Do not merge populations or patches. Respect the app's live-game suppression. Only actual verified receipt counts should be used for the final user update.
