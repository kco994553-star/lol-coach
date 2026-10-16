# Independent review: staged VIDEO diagnostic

Reviewer: separate code/safety review role. Scope: uncommitted implementation on
`work/video-api-diagnostic-20261017` against
`0ad505b09a7e378c9a898f4e91208adbd6ce72c1`, including new payload/policy/CLI/tests,
shared daily state/recovery, workflow, contract, plan, reference and evidence verifier.
Read repository AGENTS.md. No provider requests, source edits, full suite, or user
knowledge decision issue changes were made. Only this report was written.

Initial assessment (superseded by the resolution review below):
**request changes before actual diagnostic publication/dispatch**.
No Critical finding. Four Important findings follow.

## I1 — malformed HTTP200 metadata breaks failure persistence

Location: `scripts/run_video_diagnostic.py:78-82`; shared
`coach_v1/gemini_daily.py:preparation_failure` / `validate_state`.

The exception handler supplies no explicit failure reason except missing keys.
ExpertCollector raises its typed MALFORMED_RESPONSE error with http_status200 for
an unparseable successful metadata response. The handler calls preparation_failure
with200/no reason, which classifies it as TEXT_ONLY_SUCCESS; that classification is
forbidden for PREPARATION_FAILURE. A new exception escapes the handler before any
state or receipt is written. This also loses the useful diagnostic failure category.

Offline reproduction: invoke the real prepare CLI with existing isolated fixtures,
injected entitlement/support verifiers, and transport returning `(200, {}, b'not-json')`.
Observed: `ValueError: INVALID_DAILY_STATE`; receipt written=False; state written=False.
No network was used.

Requested correction: normalize typed preparation failures before appending them;
preserve MALFORMED_RESPONSE even when HTTP status is200, and ensure safe paired state
and a bounded failure receipt are still emitted. Add a focused mocked CLI regression.

## I2 — authentication metadata failures can repeat the date

Location: `scripts/run_video_diagnostic.py:78-82`;
`coach_v1/video_diagnostic_policy.py:37-39`.

Preparation classification uses HTTP status and missing-key reason only. Safe provider
authentication/permission evidence in error.status/reason is not promoted to a terminal
classification. An HTTP400 metadata response with error.status UNAUTHENTICATED becomes
ARGUMENT_CONFIGURATION. Unlike a failed reserved stage, a preparation failure has no
stage reservation, and choose_stage ignores that classification; the next run repeats
external metadata diagnosis. Google can also report invalid API keys through400 plus
typed API_KEY_INVALID details, so HTTP401/403 alone is not sufficient auth detection.

Offline reproduction through real prepare CLI with injected GET transport returning
400/error.status UNAUTHENTICATED: receipt.classification=ARGUMENT_CONFIGURATION,
provider_error.error_status=UNAUTHENTICATED, then choose_stage on the emitted pair at
the next second returns1. No network was used.

Requested correction: use allowlisted provider status/reason facts to classify auth
and permission failures before durable recording; enforce their same-date external
stop. Preserve UNKNOWN for unsupported facts. Add a focused retry-prevention test.

## I3 — date stop is absent from the shared normal reservation path

Location: `coach_v1/gemini_daily.py:reserve_text` and normal pretext workflow route;
compare diagnostic-only guards in `video_diagnostic_policy.py:37-39` and
`run_video_diagnostic.py:64-65`.

The new contract requires a date stop across configuration fingerprints. The guard is
implemented only for diagnostic selection/dispatch. reserve_text still checks persistent
failures only for its own fingerprint and excludes429 from its persistent set. If the
normal route is selected after a diagnostic429/auth failure (e.g. active=false, or a
later normal configuration revision), it can reserve and dispatch a TEXT that same
date. Existing unrelated400 can mask this in the current normal configuration but is
not a global date guarantee.

Offline pure-policy reproduction: use a valid prior-day successful normal pair,
append today's diagnostic-fingerprint PREPARATION_FAILURE429, and call reserve_text
with the normal config and a fresh proof. Observed:
`NORMAL_TEXT_RESERVATION_AFTER_DIAGNOSTIC_429=ALLOWED`.
No network was used.

Requested correction: centralize the global same-date terminal guard and run it before
external preflight as well as reservation/dispatch on both routes. Keep ordinary1/day
limits and existing historical body/prefix compatibility. Add a cross-fingerprint,
cross-route regression. An explicit future override should need a documented amendment.

## I4 — public diagnostic error_code retains arbitrary provider strings

Location: `coach_v1/gemini_daily.py:247-253` and
`scripts/run_video_diagnostic.py:81-82`.

The strict new parser safely replaces provider_error.error_status/error_message in the
VIDEO result, but provider_error.error_code remains the original safe_http_error value.
That helper accepts any symbolic string, including private names or identifiers. The
preparation handler also copies unrestricted symbolic error_status/error_code. These
values enter durable state and the safe-public receipt, bypassing the new typed
allowlist and message redaction.

Offline pure dispatch reproduction with a valid reserved stage and mocked400 body
`error={code:'PRIVATE_PERSON', status:'INVALID_ARGUMENT', message:'PRIVATE_PERSON'}`:
provider_error.error_code retains `PRIVATE_PERSON` verbatim while the message is redacted.
No network was used.

Requested correction: retain only bounded numeric error codes and allowlisted status
symbols for the new public diagnostic path; redact unsupported string codes/statuses.
Apply the same normalization to metadata failures. Test the actual dispatch/receipt
boundary, since safe_error_details-only tests do not cover this retained field.

## Positive checks and limits

- Payload stages isolate URL, then offsets, then JSON config. Neutral prompt change
  from the historical official baseline is explicitly disclosed; no HTTP400 cause is
  claimed from alias/Duration/schema spelling.
- Diagnostic mode suppresses new TEXT generation; existing successful TEXT receipt is
  required. One staged VIDEO is issued per workflow run.
- Reservation charges fresh full-original duration, counts legacy+daily rows without
  collapsing distinct legacy video identities, and preserves historical prefixes.
- Success alone does not advance: reviewed content receipt binds exact reservation,
  result digest, stage, allowed decision and separate-review role.
- Pending VIDEO outcomes block new diagnostic requests; failed stage does not retry on
  a later day or revision. Normal VIDEO remains1/day.
- Dispatch verifies remote paired-artifact ACK before generation and uses the shared
  exclusive claim and trusted first-attempt workflow checks. Recovery's VIDEO-only
  exception is restricted to a sole typed v2 diagnostic reservation for its run.
- Dispatch recomputes time after conservative separation and daily.dispatch rejects a
  reservation when its Seoul date differs; a midnight crossing does not consume a
  next-date generation slot through the old reservation.
- Redacted typed error details and bounded unreviewed content are kept separate from
  reviewed facts, source correctness, expert adoption and blind evaluation.
- Reused `affected-green.log`:71 affected tests PASS; no full suite rerun. Reviewed
  new focused test modules and CI selection. The four probes above were isolated
  offline boundary checks; they exposed paths absent from the existing green tests.

These findings require correction and affected regressions before treating the
implementation as ready for actual staged requests. This report grants no claim about
provider success, source fact correctness, or coaching accuracy.


## Resolution review — final assessment

Rechecked 2026-10-16T23:32:53.619736+00:00. **GO for normal gated integration and the authorized stage1
workflow dispatch; no outstanding Critical or Important findings in reviewed scope.**
Required CI/source binding and the runtime free/support/metadata/quota/ACK gates still
apply. This is implementation readiness, not provider success or source fact approval.

All four findings are resolved in the final source snapshot:

- I1: preparation records a permitted MALFORMED_RESPONSE for malformed HTTP200 instead
  of manufacturing TEXT_ONLY_SUCCESS; safe receipt and state remain durable.
- I2: allowlisted UNAUTHENTICATED/PERMISSION_DENIED/RESOURCE_EXHAUSTED metadata status
  overrides a generic HTTP code. Shared date guard checks recorded status/classification
  and nested or legacy top-level safe provider status across fingerprints.
- I3: shared date guard is used in normal TEXT/VIDEO reservation and all dispatch;
  normal CLI applies it immediately after pair/project validation, before _gate or
  any other provider preflight. Diagnostic selection and dispatch reuse that guard.
- I4: new diagnostic parser retains numeric-only bounded codes and known status enum;
  VIDEO dispatch and metadata failure receipts consistently copy those strict fields.
  Arbitrary symbolic error code no longer reaches the public-safe output.

I inspected the final diff and independently ran the six focused regressions for
malformed metadata persistence, HTTP400 auth, POST privacy, normal preflight gate
suppression, cross-revision date stop, and generic-HTTP auth stop: **6 PASS** in0.091s.
All transport/document verification boundaries were injected or mocked; no provider
requests occurred. Reused final `review-fixes-green.log`: **76 affected tests PASS**
in0.123s. `git diff --check` passed. No full suite was run.

The cross-midnight dispatch time is reread after separation; the shared dispatch
validator rejects a reservation from another Seoul date before a generation call.
Public documentation access errors remain unverified-support holds rather than
unproven project authentication claims. Separate result-bound diagnostic content
review remains required before every following stage.

Final reviewed file SHA256 values (the report itself is intentionally excluded):

| File | SHA256 |
| --- | --- |
| `coach_v1/gemini_daily.py` | `2901d8267ed12a2962e8cefe5269ad9598fb54481ec090a8683032de961dac5a` |
| `coach_v1/video_diagnostic_payload.py` | `1bdc1e0d2357b057d5ecd0e977a5e8c3f008d394cce84f5a4e9c6d8f685418bd` |
| `coach_v1/video_diagnostic_policy.py` | `e4be1c58bc7716ebc74f42431cdbeeea5f68fa15f658c5027fed92f6121a8704` |
| `scripts/run_gemini_daily.py` | `90ba4cbddfc3f654a23c73571ec56f0e7b5316c2f3ac14a0ea2490403a9da4cd` |
| `scripts/run_video_diagnostic.py` | `0abe20547de11cfbc3d8c56567d8f719796fcb3671a5cfc74ec11cbac458d1fd` |
| `.github/workflows/expert-video-collection.yml` | `b69cd9195200874149f01cdac8c37efabef8a02ace3cfcbb07048d92845ec7a2` |
| `config/video_api_diagnostic.json` | `4556e0e1d597deb15f575ce7f4a543132c030aa8c8b84094bec6023f195af302` |
| `contracts/video-step-diagnostic-v4.md` | `2911067b48372f760460de16c12c9c2f8b5d15b2ce8102bb3e3cd042b63988a1` |
| `tests_expert/test_video_diagnostic_cli.py` | `70c5b339ef42e89ba101dc5da7456cede3be20996a51b9eb34f1d177e26fd4ab` |
| `tests_expert/test_video_diagnostic_policy.py` | `c372b9cac02733a446cf717e70986dc022fc919b66b3c68d0556d52d0093aa61` |
| `tests_expert/test_video_diagnostic_payload.py` | `79b3636f4ea310778e94735d66de2b775beefa848494955cae8d1e43e573388e` |
| `scripts/verify_actual_evidence.py` | `5237e28d45a7e310e751dc8a8b7c53658b63c24df7e6cdb011aeca0b0a261ca7` |
| `evidence/actual-evidence/video-step-diagnostic/review-fixes-green.log` | `151ad571fe59a15ea746a3fa543be3cd5b970a0029d17ed3d238cfb9053bca37` |
