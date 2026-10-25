# Data review

**Spec review: APPROVE. Quality review: APPROVE.** No material findings.

Reviewed the task brief/report, supplied diff, plan and AGENTS.md, current implementation, strict upstream outcome validator, source manifests and generated public artifact. Existing `data-green.log` records 43 passing targeted tests; those unchanged tests were not rerun. Root owns the full-suite check.

- Exact scope is preserved for champion, role, patch, tier and optional opponent. Absent opponent scopes return empty results without the older selector's all-opponent fallback. Resource/power points never become ending outcomes.
- Total wins and N sum disjoint ending observations; Wilson 95% is recomputed from those totals. Upstream validation rejects overlapping hashes and validates matchup partitions, source scope, rates and intervals.
- Duration entries cover thirteen disjoint five-minute intervals including the open 60+ tail. Empty gaps retain null rates; drawable is fixed at N>=100. Current real data cannot meet this threshold. Descriptive statistics remain separate from strength, causal or coaching-accuracy claims.
- Role N unions member hashes from CHAMPION_ROLE cohorts, rather than adding minute rows or counting opponent cohorts. Distinct coverage inputs must share the outcome scope.
- The operational generator binds the actual October 11 REAL50 archive to compressed SHA, decoded SHA and canonical digest. It also verifies the October 13 POWER275 archive but correctly explains why its absent per-cohort member hashes prevent exact role-union counts. The retained outcome50 coverage and separate considered-source provenance are explicit. Synthetic fixtures exercise the helper without becoming operational public data.
- The public projection is constructed from an allowlist and excludes account/player IDs and member/match-hash lists. Unsupported metrics are explicit. Source/raw data and legacy APIs are outside the changes.

An independent read-only audit of the current file passed compressed/decoded/canonical source bindings and all 583 projected cohort totals, bin boundaries/counts, drawable flags, role unions and exclusion of every source member hash. It confirmed 50 REAL matches. No repository files were changed by this review.

Nonblocking payload observation: the artifact is 2,572,878 bytes with pretty JSON; compact serialization preserves the schema at 1,063,283 bytes (59% smaller). Standard gzip reduces those variants to 40,763 and 18,032 bytes respectively. Compact JSON in the generator is a practical optional improvement, especially if a host serves JSON without compression; the compressed payload does not justify blocking approval.
