# Expert source recovery and bounded views — 2026-10-11

Independent review reproduced six boundary faults; this additive amendment
defines their correction. Original artifact bytes are retained in VIDEO report.
Rows.artifact is now a metadata envelope containing only schema_version, video,
processing, visual_verified and coaching_accuracy. Each row adds artifact_sha256
and source_claim_count; claim is separate. Full original remains available at
GET /dev/v1/research/{resource_id}, report.artifact. This avoids repeating a whole
100-claim artifact100times. Exact JSON HTTP byte budget is preflighted against
current+prospective rows before new source/note/proposal writes. Count bounds in
the internal preview are response-size upper bounds, never published statistics.

Combined note/context fields exceeding the legacy2,000char cap use a compact
conditions SHA256 pointer. Full conditions remain in immutable original report;
no condition is interpreted or silently lost. Original generated note revision1
is checked against its deterministic payload on every partial recovery and
remains the bound source even after a user edits later note revisions.

Private import sidecar records STARTED before propose, FAILED only when propose
raises a rollback exception, COMPLETE after the exact source-bound proposal is
recorded. Process loss during STARTED with no surviving proposal is ambiguous:
do not recreate a possibly user-deleted candidate; mark WITHHELD. Current heads
with changed resource/anchor/original-note source_refs are also withheld from
the original video row. Optional top-level withheld entries contain only safe
reason/reference metadata. They never authorize a review. Completed deletions
are never resurrected. Preserve this private journal alongside research DB on
local backups; legacy backupformat1 does not silently include the new sidecar.

Runtime attestation fallback file (Main-owned config/expert_runtime.json) exact
keys: schema_version=expert.runtime.v1, project_name (bounded text),
confirmation_source=USER_QUEUE_V1.6_2026-10-11, confirmed_at (ISO UTC),
free_tier_confirmed (bool), entitlement_checked_at (ISO date),
quota_exclusive_confirmed (bool), initial_zero_usage_confirmed (bool).
CLI --runtime-config accepts this strict safe file when optional repository
variables are absent; explicit variables override file values, never let a true
file override a false variable. Current official free entitlement is valid for
the pinned model only; an expired/mismatched entitlement fails closed, no paid
fallback. User's free project confirmation is already true; quota/exclusive
answers remain false until the user supplies those facts. No key/project linkage
is inferred from HTTP success. State with no prior ledger observed can initialize
only under explicit zero/exclusive attestation; missing expected/corrupt/ambiguous
ledger stays blocked. This fallback avoids requiring inaccessible repository
variable APIs when the user already supplied the same source assertion.
