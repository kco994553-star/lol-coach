# Q03 outcome v1 aggregate consistency — 2026-10-11

Additive clarification; outcome-v1.md and its field-type amendment are preserved.
The complete dataset emitted by build_outcome_dataset is required at import,
not a selected view or manually trimmed cohort collection.

For each champion/position/patch/tier/ending-minute, MATCHUP input hash sets
partition the CHAMPION_ROLE input hash set without overlap. Their n and wins
sum to the CHAMPION_ROLE n and wins. Every MATCHUP has the reverse opponent/
champion cohort in the same position/patch/tier/minute with the identical input
hash set and n; their wins sum to n. Thus aggregate counts cannot contradict
each other while each row separately has a valid Wilson interval. Missing base,
reverse or partition cohorts are rejected; no missing values are generated.

Nonempty samples require source patch >=11.20 and declared MATCH_V5_MATCH and
MATCH_V5_TIMELINE endpoints. An empty old-patch request may remain an explicit
INSUFFICIENT_DATA dataset, never usable observations. These checks verify public
arithmetic/lineage consistency; they do not independently authenticate a
producer's private original inputs.
