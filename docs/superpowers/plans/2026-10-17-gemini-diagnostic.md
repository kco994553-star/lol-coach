# Gemini response diagnosis and matched PC phases

Goal: diagnose the actual REST failure without weakening complete-output checks;
use at most five total TEXT calls on2026-10-17 Asia/Seoul and at most one total VIDEO.
Spec: USER limited diagnosis instruction2026-10-17; prior contracts preserved.

Bounded approach: add safe staged diagnostics around the existing strict parser,
first verify the already merged v2 body with one actual request, and stop additional
TEXT on success. The existing stricter one-call guard remains until a diagnosed
failure actually requires the approved extension; never bypass a durable reservation.
On429/auth/permission stop for the date. Same project/key/model/v1beta REST route,
stdlib urllib transport (no provider SDK), no retries/fallback/paid switch. Existing
VIDEO1/full-original-duration/quota/purpose gates unchanged. TEXT has no internal
VIDEO charge but API requests and reported token usage are recorded separately.

- [x] Read main25b9682, AGENTS/handoff/queue, actualrun38897072108 and active work.
  Original response was not retained, so exact old cause is UNKNOWN; synthetic
  structures cannot be asserted as a replay of that actual response.
- [x] Add isolated tests_expert/test_gemini_response_diagnostics.py RED; implement
  coach_v1/gemini_response_diagnostics.py and attach output to daily dispatch/receipt.
  NormalSTOP/thoughts/signatures; truncatedMAX_TOKENS; duplicateJSON; blocked prompt;
  unsupported parts/missing content; no raw text/thoughts/IDs in diagnostics.
- [x] Check official REST GenerateContent/Part/UsageMetadata and project rate limits;
  preserve URL/date/hash/excerpts. Numeric project dashboard limits unavailable:
  do not invent RPM. First request has >10h since old request; if VIDEO follows,
  use conservatively >=60s separation and report unobserved project quota details.
- [x] Independent whole-branch review; affected-only CI/source seal; normal merge.
  One actual TEXT tests hypothesis that prior8-token request ended before STOP;
  this remains a hypothesis until observable finishReason. Changed request vs old:
  remove8-token cap only, plus safe diagnostics, unchanged model/project/API route.
  If first valid complete TEXT: no additional diagnostic calls. Conditional VIDEO
  expert priority; original charge, no retry, no blind-scene eligibility claim.
- [x] Independent matched PC phase measurement with scripts/measure_pc_phases.py;
  source-bound evidence only, no production edits and no baseline acceptance rerun.
  Reuse resource original/store8175 comparisons and report 108selected participant
  observations across89matches, separately per target, never108newmatches.
- [ ] Publish actual receipts/results through required CI and verify postmain.

Ruling: user's explicit free reversible execution/publication authority supersedes
redundant design approval, baseline reruns and separate worktree setup; use fresh
feature branch in existing task checkout. No dependencies or completed suites rerun.
Ruling: preserve full existing parser and request body for first diagnostic; detailed
structure instrumentation first, not a speculative parser relaxation. First call
under the normal one-call guard is within the approved five ceiling. Extend only if
specific new evidence requires another diagnostic. Do not report known root cause
from syntheticMAX_TOKENS alone or claim full quota recovery from HTTP200.

Review fix pass: P2surrogate diagnostics loss and root-array misclassification both
RED2→GREEN46 affected tests. Existing strict complete parser untouched; no extra API.

Actualrun38977859350 TEXT1 HTTP200/STOP complete, usage66. VIDEO1 HTTP400 generic
INVALID_ARGUMENT, noextraction, fulloriginal1102s charge kept; no retry. Textdiagnostics
ended after success, so the five-ceiling extension was not needed. Exact oldcause stays
UNKNOWN; video rejectedfieldUNKNOWN. Result-only publication follows requiredCI.
