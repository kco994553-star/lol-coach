# Actual V6 public data audit

Audited 2026-10-15T11:57:13.143027+00:00. Only newly acquired public-safe run 38728134121 / artifact 11969029431, trusted head `f4fa37a501fe78679d3a11e39162437c89f58cab`. No provider calls, raw/private-cache access, source edits, or completed-check reruns.

Strict dataset validation passes for both datasets; 16/16 source-file SHA256 values match `git show actual_commit:path`, including workflow and extraction contract. Both raw JSON hashes and sample counts match source-binding; both bind `FRAME_ORIGIN_AND_CADENCE.v2`. Recursive public input key scan found 0 identifier/raw/credential keys; dataset schema uses a strict recursive allowlist. This does not independently inspect unavailable raw inputs.

|Population / patch|Distinct matches|Participant observations|
|---|---:|---:|
|PRO_REFERENCE total|89|108|
|PRO_REFERENCE 16.19|Not reconstructible across roles|13|
|PRO_REFERENCE 16.20|Not reconstructible across roles|95|
|CHALLENGER 16.20|291|2910|

Per-patch PRO unique matches cannot be inferred by summing role match counts; the public aggregate discards cross-role match linkage. JSON contains exact per-role counts, full timing/gold distributions, exclusions, low-health outcomes, and nine sensitivity cells.

The Challenger workflow ended `failure` / `DEADLINE_EXHAUSTED` at 600 requests and 1 retry. Its 291 valid matches are accepted partial observations, not a successful full 300 match acquisition. PRO offline extraction completed with 0 provider requests. Routine acquisition/import is complete; no retry was made.

|BOTTOM query / patch|Exact valid timing matches|Chosen scope|Chosen valid matches / participant purchases / missing|
|---|---:|---|---|
|pro Yunara 16.19|0|UNKNOWN|UNKNOWN; pooled valid 1|
|pro Ashe 16.19|0|UNKNOWN|UNKNOWN; pooled valid 1|
|pro Kaisa 16.19|0|UNKNOWN|UNKNOWN; pooled valid 1|
|pro Caitlyn 16.19|0|UNKNOWN|UNKNOWN; pooled valid 1|
|pro Ezreal 16.19|0|UNKNOWN|UNKNOWN; pooled valid 1|
|pro Yunara 16.20|0|ROLE|12 / 12 / 6|
|pro Ashe 16.20|0|ROLE|12 / 12 / 6|
|pro Kaisa 16.20|1|ROLE|12 / 12 / 6|
|pro Caitlyn 16.20|1|ROLE|12 / 12 / 6|
|pro Ezreal 16.20|0|ROLE|12 / 12 / 6|
|challenger Yunara 16.20|18|CHAMPION|18 / 18 / 14|
|challenger Ashe 16.20|0|ROLE|250 / 373 / 209|
|challenger Kaisa 16.20|26|CHAMPION|26 / 26 / 14|
|challenger Caitlyn 16.20|30|CHAMPION|30 / 30 / 13|
|challenger Ezreal 16.20|31|CHAMPION|31 / 31 / 22|

Minimum 5 means distinct matches with valid first-purchase timing, not all cohort matches. CH Ashe has no exact BOTTOM cohort and uses same patch/position pooled fallback; all five PRO 16.20 queries use pooled fallback. PRO 16.19 queries are UNKNOWN.

|Population / patch, all positions|Purchase observations|Stay observations|Excluded|
|---|---:|---:|---:|
|pro 16.19|6|1|6|
|pro 16.20|36|3|56|
|challenger 16.20|949|107|1854|

BOTTOM 30%/120s outcome denominators follow below as valid distinct matches / participant windows / unknown windows. Unknown windows retain missing values, never known 0. Outcomes are match-weighted descriptive means; same event may enter overlapping participant windows.

**pro 16.19 BOTTOM:** purchase 1 matches/1 observations; stay 0 matches/0 observations; exclusions [{"count": 1, "reason": "DEATH_BEFORE_ACTION"}, {"count": 2, "reason": "NEXT_FRAME_NOT_OWN_LANE"}].

|Action|Outcome|Valid matches / windows / unknown|
|---|---|---:|
|purchase|opponent_jungle_objectives|1 / 1 / 0|
|purchase|opponent_other_lane_involvements|1 / 1 / 0|
|purchase|opponent_plates|1 / 1 / 0|
|purchase|self_deaths|1 / 1 / 0|
|stay|opponent_jungle_objectives|0 / 0 / 0|
|stay|opponent_other_lane_involvements|0 / 0 / 0|
|stay|opponent_plates|0 / 0 / 0|
|stay|self_deaths|0 / 0 / 0|

**pro 16.20 BOTTOM:** purchase 10 matches/11 observations; stay 2 matches/2 observations; exclusions [{"count": 1, "reason": "DEATH_BEFORE_ACTION"}, {"count": 1, "reason": "NEXT_FRAME_NOT_OWN_LANE"}, {"count": 3, "reason": "NO_LOW_HEALTH_FRAME"}].

|Action|Outcome|Valid matches / windows / unknown|
|---|---|---:|
|purchase|opponent_jungle_objectives|10 / 10 / 1|
|purchase|opponent_other_lane_involvements|9 / 9 / 2|
|purchase|opponent_plates|10 / 10 / 1|
|purchase|self_deaths|10 / 10 / 1|
|stay|opponent_jungle_objectives|2 / 2 / 0|
|stay|opponent_other_lane_involvements|2 / 2 / 0|
|stay|opponent_plates|2 / 2 / 0|
|stay|self_deaths|2 / 2 / 0|

**challenger 16.20 BOTTOM:** purchase 199 matches/245 observations; stay 34 matches/35 observations; exclusions [{"count": 88, "reason": "DEATH_BEFORE_ACTION"}, {"count": 14, "reason": "NEXT_FRAME_LANE_UNKNOWN"}, {"count": 37, "reason": "NEXT_FRAME_NOT_OWN_LANE"}, {"count": 9, "reason": "NEXT_FRAME_UNOBSERVED"}, {"count": 154, "reason": "NO_LOW_HEALTH_FRAME"}].

|Action|Outcome|Valid matches / windows / unknown|
|---|---|---:|
|purchase|opponent_jungle_objectives|194 / 238 / 7|
|purchase|opponent_other_lane_involvements|161 / 188 / 57|
|purchase|opponent_plates|194 / 239 / 6|
|purchase|self_deaths|194 / 239 / 6|
|stay|opponent_jungle_objectives|34 / 35 / 0|
|stay|opponent_other_lane_involvements|25 / 26 / 9|
|stay|opponent_plates|34 / 35 / 0|
|stay|self_deaths|34 / 35 / 0|

**Concrete integration findings reported to main:**

- Original PC loader rejected the 12,366,272 byte Challenger dataset because its cap was 12,000,000 bytes. Independently reproduced `INVALID_NEWEST_ARCHIVE`; main is fixing size bound plus strict startup validation. This audit records the pre-fix finding and does not claim the integration fix passed.
- Original PRO card title implied final selected pro players. Receipt proves recorded user-roster participants only and may include preselection candidates; main is correcting the population label/caveat.

**Timing and interpretation limits:**

- First purchase is the first purchase strictly after 120 seconds, bundled through the following 30 seconds. It is a recall proxy, not exact recall start/completion or recommended timing; previous deaths exclude first-recall observations. Gold comes from the preceding received frame.
- Low-health uses first received frame at <=30% per participant per sensitivity cell. Its 120 second result window begins at low health and can contain prepurchase events; stay requires next own-lane frame. It is not every low-health episode. Nine 20/30/40% and 60/120/180 second sensitivity cells remain separate.
- Displayed cohort match count can exceed valid timing match_n. Individual low-health outcome n can be below 5 even when first purchase fallback passes 5; retain each outcome denominator.
- Challenger seed matches do not prove every participant is Challenger. PRO_REFERENCE does not mean every player in each match. Populations and patches remain separate.
- Q15 resource/gold-delta plots are not waveclear speed, health sustain, finishing ability, causal recall benefit, or coaching accuracy evidence. No tactical/causal accuracy judgment is made.

Verdict: strict public datasets are valid and source bound. Original Challenger PC size blocker and PRO labeling issue were sent to main for correction; final browser/performance evidence belongs to main.
