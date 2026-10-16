# Independent actual-safe artifact audit — 2026-10-16

No integrity or count-reconciliation discrepancy found in the two imported safe artifacts. This is a read-only artifact audit, not a repeat code review, private-source recalculation, provider availability test, or coaching-accuracy assessment.

## Provenance and bytes

Read-only GitHub run metadata independently confirms [run 38895508259](https://github.com/kco994553-star/lol-coach/actions/runs/38895508259) completed successfully on `main`, `workflow_dispatch`, attempt1, workflow `.github/workflows/resource-recovery-offline.yml`, at commit `1e261c55897d21303052eeef6d1fe7c4d631acdc`.

GitHub lists exactly two artifacts for this run. Both are unexpired; their IDs, names and byte sizes match the downloaded ZIPs:

| Artifact | ID | ZIP bytes | ZIP SHA256 |
| --- | --- | ---: | --- |
| resource-recovery-public-safe | 12043129466 | 106634 | `58ec3e3e02d65b7d6e8f64ef4c017b863da69a6390eaaa4939614afa63ee8d5e` |
| pov-metadata-public-safe | 12044195188 | 2743 | `094ff6edf46d6a4c716e1d3ab3be65252695e28c04e90766fca113b6de491cd9` |

Each ZIP has exactly its expected two files. Every imported member is byte-identical to its ZIP member. Both local import receipts match the ZIP/member hashes, run, attempt, artifact ID and actual commit.

| Member | Uncompressed bytes | SHA256 |
| --- | ---: | --- |
| resources.json | 3717928 | `9d2cd1f5479513e6dfb0fad49766bdd9df036793c64165e0ba3f78aabb3d3c4e` |
| source-binding.json | 1579 | `f55908b9a9fd9809fb5022d85e15f20258f1bb2d5cbce394b57fea4bac618db4` |
| pov-metadata.json | 7893 | `9ece66abdb0b71613a68c0a98cffbe8de4c43c03b745ffa263158e76990e92b5` |
| metadata-binding.json | 855 | `0a54e26f3dc4b4936dac026690c897574e6558052abc2cbe7b7cd38397145461` |

Both binding report hashes match their report bytes. All **9 resource source hashes and 4 POV source hashes** independently match both `git show <actual_commit>:<path>` bytes and the corresponding current working-tree bytes at audit time.

Resource bound paths: `.github/workflows/resource-recovery-offline.yml`, `coach_v1/postgame_match.py`, `coach_v1/private_pro_bundle.py`, `coach_v1/pro_checkpoint.py`, `coach_v1/resource_recovery.py`, `contracts/actual-evidence-v1.md`, `scripts/private_pro_bundle.py`, `scripts/recover_pro_cache.py`, `scripts/recover_resource_checkpoint.py`.

POV bound paths: `coach_v1/pov_metadata.py`, `config/pov_channels.json`, `contracts/actual-evidence-v1.md`, `scripts/verify_pov_metadata.py`.

The in-progress `resource_view.py` change and Gemini/legacy-collection migration changes are outside these source bindings. The artifact source-hash match does not claim those other files were executed or verified by this run.

## Resource meanings and reconciliation

The source is labeled `REAL`, population `RECORDED_PRO_REFERENCE`: **89 distinct matches, 108 selected participant observations/cache entries**, zero duplicate participant entries. The label does not establish professional-player status. The private checkpoint binding retains run `38410710876`, artifact `11822391323`.

All-participant inspection reports **2384 received match frames / 23840 participant frames**; gold and XP are each present in all23840. Level is present23714, missing126. The selected-participant inspection is separate:2833 frames, gold/XP2833 present, level2801 present and32 missing. These broad inspection counts are distinct from the108 selected observations at each target minute.

| Selection | Valid selected observations | Distinct matches | Missing | Original timestamp range | Offset from nominal target |
| --- | ---: | ---: | ---: | --- | --- |
| Exact600000ms | 0 | 0 | 108, all EXACT_TIMESTAMP_ABSENT | none | none |
| Exact900000ms | 0 | 0 | 108, all EXACT_TIMESTAMP_ABSENT | none | none |
| Latest received in [600000,660000) | 108 | 89 | 0 | 600068–600317ms | +68–317ms |
| Latest received in [900000,960000) | 108 | 89 | 0 | 900169–900405ms | +169–405ms |

Gold, XP and level, including own/opponent/paired-difference summaries, each have108 valid observations and89 distinct matches in both observed bins. Exact-time summaries remain empty; observed-bin results do not replace exact results. Each observed bin reports one received frame per selected observation and zero selected final-received frames. The offsets are milliseconds, not seconds or rounded exact-minute states.

Patch16.19 has13 selected observations/13 matches;16.20 has95 selected observations/76 matches. Totals reconcile to108/89. The99 champion/role/opponent cohort summaries sum to108 selected observations. Independently summing all patch and cohort `n_valid`/`missing_n` counts for every gold/XP/level own/opponent/difference summary reconciles to each of the four global measurements. Cohort distinct-match counts are not treated as independent observations or blindly summed as unique matches.

The report records8175 transform comparisons and0 mismatches. This audit confirms the reported counters and artifact/source binding, without independently recalculating those comparisons from private originals. The binding records0 network attempts and0 provider requests. Timestamp inspection reports89 received frames after reported match end; that marginal diagnostic does not imply any such frame was eligible for the selected bins. The policy retains original timestamps, excludes frames after reported end, and disclaims interpolation, bin borrowing, interval coverage and scene reconstruction.

The resource report's exported fields are aggregate counts/statistics, patch/champion/role/opponent categories and explicit limitations; no account, match, PUUID, participant-identity or credential field was found. It reports accuracy null, approval NOT_ASSESSED and0 evaluable scenes.

## POV meanings and limits

The metadata artifact reports two canonical channel ID/handle pairs verified, with3 candidate videos per channel,6 total. The preserved supplied handles differ from returned canonical custom URLs only by case. Supplied metadata remains separate from returned public metadata.

There are8 dated source receipts with HTTP200: for each channel, channel-by-ID, channel-by-handle, playlistItems and videos. Every receipt includes its public request URL and transient-response SHA256. The report/binding agree on8 METADATA requests,0 TEXT_PROBE,0 VIDEO_CLIP,0 retries,0 media downloads and0 transcript downloads. This audit read those receipts and did not issue new YouTube/provider requests or attempt to reconstruct deliberately unretained raw responses.

Both channels retain `official_status=UNKNOWN`, `channel_owner_is_player=UNKNOWN`, `view_type=UNKNOWN`, `continuity=UNKNOWN`, and `expert_source=false`. Every candidate video retains UNKNOWN view type, continuity, game date, game link, opponent, patch and intent. Publication timestamps explicitly mean upload publication, not game date. The report has0 matched games and0 evaluated scenes. Canonical public-channel metadata does not prove actual player POV, continuous footage, player identity, official status, same-game linkage, expert-source eligibility or scene suitability.

## Audit boundaries

Only safe ZIP members, imported safe JSON, Git objects/current source bytes, and filtered GitHub run/artifact metadata were read. No validator, old test suite, private checkpoint, raw media, transcript, secret, new collection, or provider call was used. The only repository file written by this audit is this document. Gemini TEXT200/VIDEO200 availability is not established by these artifacts; no expert or professional status, tactical validity, user approval, or coaching accuracy is asserted.
