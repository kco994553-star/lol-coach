# Queue v2 additive integration contract

This implements the user's 2026-10-13 R1–R5 specification. Existing pregame.rule.v1/v2/v3, stored plan lineage, USER_WEB approval source binding, cooldown NOT_AVAILABLE semantics and provider quota ledgers remain unchanged. Main owns this contract and HTTP integration.

## Authenticated local routes

Static `/review-queue`, `/statistics`, `/postgame`, `/setup` are documentation/UI only. Data routes inherit existing loopback Host/Origin/Bearer preflight and explicit body/reply limits. No HTTP operation enables `test_mode`.

- GET `/dev/v1/pregame/review-queue`: bounded top20 and separately deferred top20, exact candidate revisions, archived excerpts, conditional card preview, progress and safe public-source export. Loading/preview/import/defer never reviews knowledge.
- POST `/dev/v1/pregame/review-queue/later`: `{candidate_id,selected_version}`; defers exact revision only in local sidecar. Revisit enabled.
- POST `/dev/v1/pregame/candidates`: existing `{spec}`, optional paired `{rule_id,expected_version}` for structured revision with same immutable proposal lineage and version conflict check. All newly imported/edited versions EXPLORATORY. Explicit user decisions use unchanged native knowledge API; tests never create USER_WEB decisions.
- GET `/dev/v1/pregame/power-catalog`: independent validated datasets keyed by exact `(patch,tier)`, champions and compact per-role collection progress. No mixed-cohort means.
- GET `/dev/v1/pregame/collection-progress`: legacy selected dataset or UNKNOWN. New baseline progress companion is bound to canonical aggregate SHA and mathematically validated; legacy50 lacking per-match sufficient records cannot retroactively supply missing pooled-reference SD.
- POST `/dev/v1/pregame/power-view`: unchanged exact champion/position/patch/tier/opponent input; resolves multi-dataset references without changing original strict schema.
- GET `/dev/v1/postgame/matches`: own local summaries, no identifiers.
- POST `/dev/v1/postgame/import`: `{match,timeline,participant_id,source?,phase_annotations?}`; validates bounded official pair, current selected participant and exact timeline binding. Synthetic sources require internal isolated test fixture flag. Real own raw pairs never enter repository or Actions artifacts.
- GET `/dev/v1/postgame/matches/<64hex>`: private detail with same-patch descriptive reference. Selects matching champion/role reference preferring CHALLENGER→GRANDMASTER→MASTER→other observed seed tiers, labels actual source. Missing references UNKNOWN.
- POST `/dev/v1/postgame/analyze`: `{match_id,plan_id}`; explicit optional saved32hex plan association. Existing plan revalidation applies. Expired or different champion/role/patch plan is UNKNOWN with texts withheld; matching plan still does not prove execution/effect.

Personal raw store is next to app DB under `private/postgame/`. Linux files0600/directory0700; Windows requires user-only folder ACL configured locally (chmod alone is not an NTFS guarantee). Original PC capture folder stays separate. File imports over default1MB require explicit restart with `--max-body-bytes12000000`; there is no implicit global cap increase.

## Statistics and record limitations

`--power-data-dir DIR` accepts independent `power-<patch>-<tier>.json` and strictly bound `progress-<patch>-<tier>.json` companions. Conflicting duplicate scopes reject. Patches/tier sources remain separate. Official source tier is current seed selection, not all participants' historical rank. Target sample counts solve existing Student-t95 precision rule while holding observed SD/champion coverage fixed; unknown SD stays UNKNOWN. Percentages are not made up.

Anonymous sufficient record state preserves only hashed match ID, champion/role resources, timings and bounded events needed for deterministic aggregates. Same bucket overlap dedup is exact; patch change creates separate bucket. Historical aggregate50 lacks originals and is a separate reusable baseline until disjointness with new records is proved; it is never naively summed with overlapping summary means.

Postgame own totals remain separate from unit-correct overlaid reference deltas. MATCHUP uses own minus recorded opposing same-role total; ROLE_POPULATION uses own total per actual received elapsed minute minus sampled pooled-role reference mean. Reference CI applies only to its original delta estimate. Level/item lines preserve observed-frame/purchase ambiguity. Positions sampled once/minute cannot reveal wave/invisible opponents/skills. Phase comparison requires separately verified phase annotations and matched reference conditions; deviation is not wrongdoing. Event contexts are suspected only. Plan premise/execution/effect stay separate, no outcome inference.

## Gemini changed diagnostic

Same trusted Actions job dispatches one concurrent curl/Python identical text body pair ≤120s per selected officially free model. Both timeouts classify provider/network-side timeout with exact status history retained, not credential expiry. Auth/payment/rate-limit responses are terminal. Fallback is explicit `allow_flash_fallback=true` dispatch-only once; schedules/default input do not repeat it. Main records the sole authorized trial in durable evidence. Official model/pricing/stability URLs + current proof are mandatory. Checked selected model/probe are bound to reserve/process; no duplicate probe and no video before text success. Video≤600s, original full-duration conservative charge, no prior charged-ID repeat, reservations never refunded. Manual timestamped summary remains immediately available as EXPLORATORY.

## User-supplied professional reference roster

2026-10-13 steering adds exact `config/pro_reference_players.json`: 25 main players,9 backups, ShowMaker's second account, KR, original spaces/Korean/case preserved. This is a user-reported OP.GG badge/account selection, not verified professional ownership/rank or a Riot League seed cohort. ADC input maps to BOTTOM.

Authenticated GET `/dev/v1/postgame/reference-roster` displays the approved public roster and preparation status. No account lookup occurs on page load. Local `collect_pro_reference.py` does the first Account-V1 by-riot-id lookup, caches successful PUUIDs by stable player/account slot, then uses PUUIDs independently of nickname changes. Aliases count as one player; match hashes dedup shared games. Failed IDs/no recent30day queue420/observed position share below configurable0.5 operational threshold select recorded same-role backups. This activity-share rule is a bounded sample policy, not a complete season or gameplay judgement.

PUUID caches and raw match/timeline pairs remain in private local folders; parent traversal and symlink paths reject. Separate `postgame.pro-reference.v1` anonymous reference stores same-champion/position/patch descriptive absolute totals with Student-t confidence intervals; it never claims CHALLENGER or other actual rank. Explicit private `--pro-reference-data` attaches a separate PRO_ROSTER overlay while preserving ordinary tier-delta references. Original metadata ownership/ranks remain USER_REPORT; actual collection is U3-gated. Personal one-match acceptance remains U1/U3-gated.
