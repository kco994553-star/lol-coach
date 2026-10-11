# Q03 additive expert-video contract v1 — 2026-10-11

Authority USER_QUEUE_V1.6_2026-10-11. Main owns this contract. Expert speech and
AI summaries are unverified source statements, never observations or executable
conditions. Legacy research/knowledge/frozen contracts remain intact. No raw
video, full transcript, credentials or player identifiers enter public artifacts.

## Public artifact and local validation

Module `coach_v1/expert_contract.py`: validate_expert_artifact(value) returns a
copied strict object or ValueError; normalize_gemini_claims(value,duration_seconds)
returns (claims,rejections). No network, approvals or writes in these functions.

Artifact exact keys: schema_version=expert.claims.v1, video, processing, claims,
rejections, visual_verified=false, coaching_accuracy=null.
video exact keys: id (11 YouTube-safe characters), url (canonical
https://www.youtube.com/watch?v=ID), title (1..200 chars), channel_id (UC followed
by22 safe characters or null for manual input), channel_name (1..200), speaker
(1..200, UNKNOWN allowed), speaker_verified (bool), published_at (ISO UTC or null),
upload_date (ISO date or null), duration_seconds (positive integer <=28800),
language (bounded language tag or UNKNOWN). Publication date is not upload date.
Neither date establishes a patch. independent_group_id is always YOUTUBE:ID.
processing exact keys: method=MANUAL_SUMMARY|GEMINI_YOUTUBE, model (UNKNOWN for
manual or bounded model identifier), processed_at (ISO UTC), input_sha256
(64 lowercase hex). It is a hash of the canonical safe request/input metadata,
not a proof of original-video or paraphrase truth. No raw model responses saved.

Each accepted claim exact keys: timestamp (MM:SS, minutes may exceed59),
timestamp_seconds (nonnegative integer <duration), paraphrase (1..500), champion
(canonical ASCII ID or UNKNOWN), position (five canonical roles or UNKNOWN),
stage (EARLY|MID|LATE|UNKNOWN), conditions (list0..10 nonempty strings <=200),
context (EXPLANATION|JOKE|EXAGGERATION_SUSPECTED|UNKNOWN), measurable (bool),
patch_range (numeric patch/range or UNKNOWN), counterexamples and limitations
(each list1..10 nonempty strings <=300), measurement (null or typed criterion),
independent_group_id=YOUTUBE:ID. No direct quote field. One claim per utterance;
deduplicate exact timestamp+canonical claim body. No free prose becomes a
predicate. For unverified speakers show UNKNOWN, retain channel identity.

Gemini's strict JSON top-level is {claims:[...]}; each model claim has exactly
timestamp,paraphrase,champion,position,stage,conditions,context,measurable.
Normalizer adds UNKNOWN patch, null measurement and explicit generic limitations
AI_SUMMARY_NOT_FACT_CHECKED / VIDEO_CONTEXT_REQUIRES_USER_REVIEW and counterexample
COUNTEREXAMPLE_NOT_ESTABLISHED. It rejects missing/invalid/out-of-range timestamps,
unknown fields, nonfinite/oversized values and duplicates with safe enum reasons.
JSON format checks do not verify factual content. Empty/malformed response is
FAILED_FORMAT or NO_ACCEPTED_CLAIMS, never a successful empty acquisition.
rejections exact entries {index:nonnegative integer,reason:bounded enum}. Manual
artifacts also pass the strict validator; timestamps are mandatory.

## Measurement comparison (Q15)

Optional explicit measurement exact keys: kind=MOVEMENT_MEAN_DISTANCE,
cohort_id (64hex), patch (numeric), tier (existing Riot tier), minute (integer>=0),
operator=LE|GE, threshold (finite nonnegative), criterion_source_url (HTTPS URL),
rationale (1..500), origin=MANUAL|REVIEWED. This is a caller-supplied numerical
criterion, never extracted or guessed by AI from prose. Collector emits null.
Unknown gameplay meanings such as 'near the main body' have no invented radius.
Main `coach_v1/expert_bridge.py` compare_claim(claim,movement_data,test_mode=False)
returns {status:AGREES|DISAGREES|INSUFFICIENT|UNMEASURABLE,reasons,statistic|null}.
No criterion or measurable=false => UNMEASURABLE. No real matching dataset,
patch/tier/cohort/minute, verified state-based stage or visible CI => INSUFFICIENT.
Strict Q15 validator and sample-kind gate apply. Claim's known champion/role/stage
must match selected cohort; UNKNOWN or mismatch cannot establish agreement.
LE: CI high<=threshold agrees; CI low>threshold disagrees; GE reversed. CI crossing
the boundary => INSUFFICIENT (inconclusive), not zero/no/false. Attach digest,
formula, source, n, interval, threshold and rationale. This only compares the
specified aggregate and numerical claim; no causal/tactical/approval conclusion.

## Existing notes → EXPLORATORY proposal

Main `expert_bridge.py`: import_expert_artifact(store,artifact,*,max_bytes),
list_expert_claims(store,*,max_bytes,movement_data=None,test_mode=False).
Use existing VIDEO resource + cue_index anchor + immutable four-field note
revision + KnowledgeStore.propose only. Report carries the validated artifact
and safe cue metadata. Idempotent by exact artifact digest and claim anchor;
restart/partial retry resumes without a duplicate proposal or overwriting notes,
and never creates USER_WEB decisions. Serialize imports with a process lock;
existing owner lock excludes another app process. Preserve source_refs/hash/
revision/version. New artifact revision preserves old source and proposals.
Same video multiple summaries share independent_group_id. Count distinct videos
and verified speakers for exact normalized (paraphrase+scope) claim groups;
report counts separately, do not declare causal independence or semantic equality.

New authenticated bounded routes in additive PregameHandler (legacy unchanged):
GET /dev/v1/experts/claims returns {claims:[rows],new_candidates:0,
coaching_accuracy:null}; rows {artifact,claim,resource_id,anchor,proposal,comparison,
independent_sources:{videos,verified_speakers}}. POST /dev/v1/experts/import accepts
exact {artifact} and returns {new_candidates,claims}; atomic shape validation
before any write. Startup --expert-claims-dir imports bounded *.json from a
configured local directory; absent directory means unavailable, not fake data.
Corrupt files fail explicitly, no silent skip. Defaults data/expert_claims if
present. Notifications only '새 전문가 후보 N개'. New /experts UI uses same local
bearer auth; manual artifact entry allowed; safe textContent and canonical
timestamp URL &t=SECONDS. Existing USER_WEB-only decision endpoint is used only
by trusted human browser event with confirmation, scope completeness and source
immutability guards; tests never click real approval or create USER_WEB rows.
Review scope fields may be filled by the user. Even approved speech has no
executable spec until a separate explicit Q03 typed contract/review connects it.

## Free-only automated collection

Agent owns `coach_v1/expert_collector.py`, `scripts/collect_expert_claims.py`,
new `.github/workflows/expert-video-collection.yml`, `config/expert_channels.json`,
tests_expert/test_collector.py; no changes to shared contracts/bridge/server/UI.
Config exact {schema_version:expert.channels.v1,channels:[{channel_id,name,speaker,
speaker_verified,main_position,language,uploads_playlist_id|null}],topics:[strings],
min_duration_seconds,max_duration_seconds,max_videos_per_run}. Empty channels is
BLOCKED_EXTERNAL, not permission to invent a channel. Duration bounds are
operational budget/filter choices, not gameplay thresholds. Default max1800s,
min60s, max2videos; keywords explicit Korean/English teaching/gameplay terms.

Allowlisted uploads via channels.list contentDetails if needed, playlistItems.list
then videos.list; public video metadata only, no search.list or scraping. Persist
processed ID only with a valid nonempty artifact; failures are explicit and
reserved duration remains charged. No model tool execution/fetch arbitrary URLs.
Pin documented gemini-3.8-flash and current official Interactions endpoint/body;
structured schema + local validation. Credentials in headers, never query URLs,
logs, output, artifacts or error text. Bounded bytes/requests/timeouts/retries;
safe errors (no service response body). A mutable preview failure never triggers
paid/model fallback. Public published_at vs unknown upload_date distinction.

Actual Gemini dispatch requires nonempty keys + approved channel list + explicit
project FREE_TIER attestation (repository variable GEMINI_FREE_TIER_CONFIRMED=true,
operator confirmed it applies to the configured Secret's project) and current
documented model/input/output/YouTube free entitlement. Missing attestation is
BLOCKED_EXTERNAL; known paid/pricingchange BLOCKED_PAYMENT before request.
The key alone cannot attest billing. Conservative persistent rolling24h reservation
ledger, project-wide workflow concurrency, reserve duration before dispatch,
cap<=8h total; unknown/failure remains charged. Ledger must survive failed runs:
publish safe reservation state before calling Gemini via serialized Actions
artifact persistence/download; failed persistence => no call. Never reset on
missing ledger when prior project use is unknown; initial explicit project quota
attestation/ledger initialization required. No other project usage assumed known.
GitHub Actions schedule/manual trusted main only, never PR/fork secrets. Safe
state/brief artifacts committed through a small PR only (no autoapproval), fresh
Main owner protocol guards repository writes. Workflow collection must not steal
Main claim: produce anonymous safe outputs/artifact and publication PR only when
the shared ref is terminal; otherwise record PUBLICATION_DEFERRED. Main can
publish validated artifacts later. Artifacts are public in this public repo, so
all saved files must be public-safe. Missing keys/config/billing proof ledger =>
BLOCKED_EXTERNAL receipt; acquisition is not workflow exit success. No actual
network acquisition in unit/browser fixtures; label TEST, N0 coaching.
