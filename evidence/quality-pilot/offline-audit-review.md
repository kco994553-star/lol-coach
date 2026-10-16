# Independent audit of the existing-cache offline report

Reviewer: `/root/pilot_data_scope`. This is an AI provenance and descriptive-data audit, not an expert gameplay review, tactical approval or coaching-accuracy evaluation. No original private records were downloaded or inspected, and no validators, collection jobs or old tests were rerun. Only this review file was written.

## Provenance and byte reconciliation

The GitHub metadata for run `38890469607` reports main, workflow_dispatch, attempt 1, success, source commit `68d6a94acfc27bfcf223372bb950b97422c8dbfb`. Artifact `12041212904` is `coaching-quality-public-safe`, available and 14,887 bytes. The existing local safe ZIP has SHA256 `6b18d720c1dd22f8b20a506adc3eb5bdf7dbe18472c0426a318702c690e36b98`, matching the import receipt. Its only members are `observations.json` and `source-binding.json`; both exactly match the imported local bytes.

The imported observations SHA256 is `71cc71bdca580e9505a457fd650e5215c66118cc1b1e728babc330a67a2d8114`, matching both binding and import receipt. Each of the nine bound source-file hashes matches both its committed bytes at `68d6a94` and the current workspace bytes. These are the workflow, pilot extractor, postgame envelope reader, recall helper, checkpoint selector, private-bundle implementation, two recovery/decryption scripts and pilot contract. This was a direct byte-hash comparison, not a schema-validation rerun.

The binding names the previously existing encrypted checkpoint from run `38410710876`, artifact `11822391323`; the workflow requires that exact pair. Inspection uses socket connection denial, records zero attempts, and has no Riot client invocation. The binding/import receipt report zero provider requests and zero network attempts; the import receipt reports zero paid calls. These statements apply to provider access during extraction, not to GitHub ciphertext recovery or runtime installation. This review did not repeat the receipt's tampered-byte rejection check or decrypt the checkpoint.

## Population and inspection scope

There are 108 cache entries, 108 selected participant observations, zero duplicate selected participant entries and 89 distinct matches. Patch 16.19 contains 13 matches / 13 selected observations; patch 16.20 contains 76 / 95. Thus 13+76=89 and 13+95=108. These are recorded roster-selected participants, not all match players and not independently network-verified professional status. The 99 matchup cohorts partition the selected observations; adding cohort match counts is not a new distinct-match count.

Inspection counters traverse each distinct match once and include all received participants: 2,384 frames and 23,840 participant frames. Health, position and totalGold are present in all 23,840; a valid frame level is present in 23,714 (126 missing/invalid). These counters are not 23,840 selected-player observations.

Received events include LEVEL_UP 11,448 / duplicate signatures 0, and SKILL_LEVEL_UP 12,596 / duplicate signatures 11. LEVEL_UP has 39 malformed records and zero conflicting participant-level timestamp groups under the extractor's definitions. SKILL_LEVEL_UP is not substituted for champion leveling. Duplicate counts describe the implemented signatures, not an independent finding of provider corruption. A malformed event anywhere in an evaluated participant's recorded LEVEL_UP history, non-increasing history, contradictory frame history or event/frame contradiction conservatively invalidates that participant's level result. Therefore missing results do not imply that no level-2/3 event occurred. Zero conflicting groups alone does not establish complete history.

## Level-2/3 observations

All counts below use selected participant observations as denominator. Own/opponent missing means no usable event or frame interval on that side; ordering unknown also includes incomplete or overlapping/equal timing, so its count need not equal either side's missing count.

| Patch | Level | Selected n | Own exact / frame / missing | Opponent exact / frame / missing | Earlier / later / unknown |
|---|---:|---:|---|---|---|
| 16.19 | 2 | 13 | 10 / 0 / 3 | 11 / 0 / 2 | 8 / 2 / 3 |
| 16.19 | 3 | 13 | 10 / 0 / 3 | 11 / 0 / 2 | 3 / 7 / 3 |
| 16.20 | 2 | 95 | 92 / 0 / 3 | 92 / 0 / 3 | 47 / 44 / 4 |
| 16.20 | 3 | 95 | 92 / 0 / 3 | 92 / 0 / 3 | 45 / 46 / 4 |

“Exact” means the received LEVEL_UP timestamp accepted by the implemented consistency checks, not independent video-grounded timing. No selected result uses frame fallback. The exported lower/upper distributions are explicitly marginal summaries, not paired scenes or a reconstructed joint timeline. Strictly disjoint intervals alone count as earlier/later. The levels policy mentions frame fallback, but reporting this run as a minute-frame estimate would obscure the actual event-based observations.

## Gold and selected jungle involvement

| Patch | Gold 10 valid / missing | Gold 15 valid / missing | Selected JUNGLE eligible | Observed lane involvement / eligible missing |
|---|---|---|---:|---|
| 16.19 | 0 / 13 | 0 / 13 | 0 | 0 / 0 |
| 16.20 | 0 / 95 | 0 / 95 | 20 | 20 / 0 |

Gold requires both same-position participants' totalGold at a frame timestamp exactly 600,000 or 900,000 ms. All 108 values at each target are missing, with null summaries. This is unavailable exact-frame paired evidence, not zero gold difference. Present totalGold fields across inspection do not establish exact target timestamps. The report does not partition the missing reasons; do not infer all failures are a specific timestamp-jitter cause. Q15 pooled role gold-rate differences cannot fill these cells.

The 20 selected JUNGLE observations with a qualifying received event have first observed lane kill/assist involvement in TOP 4, MID 8, BOTTOM 8. Eligibility and missing counts above exclude non-jungle observations; the timing distribution in a non-jungle cohort carries ordinary missing values but those are not failed eligible ganks. The extractor requires an enemy victim and lane geometry at the kill position. It does not identify first gank, first arrival, unsuccessful/nonlethal ganks, or prior actions. Its literal label FIRST_OBSERVED_LANE_KILL_INVOLVEMENT and first_gank=UNKNOWN are appropriate. No first-kill matchup outcome is exported; champion/opponent cohort keys alone do not provide one.

## Remaining evidence gaps

The report explicitly leaves recall NOT_RECOMPUTED and matchup refinement UNAVAILABLE; existing recall aggregates remain separate. It has evaluable_scenes=0, NO_PLAYER_KNOWN_VIEW_OR_MATCHED_VIDEO, accuracy=null and approval=NOT_ASSESSED. Eighty-nine matches must not become eighty-nine evaluated scenes. There is no player POV/known-view reconstruction, matched video, expert outcome comparison or tactical efficacy estimate here.

The public-safe outputs contain anonymous allowlisted aggregates, with no raw match/account identifiers. This review emits no private identities or raw event records. The inspected files establish consistent source/import provenance and the descriptive totals above; they cannot independently prove provider completeness or gameplay truth beyond the trusted existing-cache lineage. Existing source-fact review conclusions are unchanged, and all conditional advice remains unvalidated.
