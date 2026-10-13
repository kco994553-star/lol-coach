# R4 — newly authorized official-example video diagnostic

Authority: `USER_PRO_REFERENCE_RESUME_2026-10-13`, the user's new distinct-stage diagnosis authorization. This does not renew the consumed alternative-model trial or permit retrying the previously charged video. Main first saved `evidence/queue/pro-resume/prior-full-video400.json`: the complete known sanitized message,400/code400/`INVALID_ARGUMENT`, source run `38387587260`, artifact `11807017561`, and the original safe diagnostic hash. An incomplete/unrecorded prior message blocks the new baseline.

## Official request and model

The current [YouTube guide](https://ai.google.dev/gemini-api/docs/video-understanding#youtube) uses **Interactions**, at `https://generativelanguage.googleapis.com/v1beta/interactions`. The baseline copies its literal video URL, REST input order and prompt exactly. Only the explicitly selected known free model is substituted:

```json
{
  "model": "gemini-3.6-flash",
  "input": [
    {"type": "text", "text": "Please summarize the video in 3 sentences."},
    {"type": "video", "uri": "https://www.youtube.com/watch?v=9hE5-98ZeCg"}
  ]
}
```

The guide's displayed model is3.8; retaining known free3.6 is the user's explicit selection, rather than a new alternative-model trial. The official [Interactions OpenAPI](https://ai.google.dev/static/api/interactions.openapi.json) lists `gemini-3.6-flash` in `/components/schemas/ModelOption/enum`; its model page documents video and structured-output support. Existing fresh model-specific pricing/model/YouTube entitlement checks remain mandatory in every CLI phase, independently from the user's project/exclusive-quota attestations.

The baseline adds no clipping, response format, generation configuration, `store`, tools, retry, stream, background or prior-interaction field. These are public-source diagnostic requests; no response/model text or transcript is saved locally. The exact official example leaves provider storage at its default. No token-related request fields are silently added to alter the baseline.

Only a completed, nonempty, unambiguous model-text response allows the next stage:

1. `BASELINE`: the body above, once.
2. `CLIPPING`: add only `input[1].processing = {"type":"static","start_offset":"0s","end_offset":"min(600,D)s"}`, once, whereD is the verified original duration.
3. `RESPONSE_FORMAT`: keep the clipped body and add only `response_format = {"type":"text","mime_type":"application/json","schema":RESPONSE_SCHEMA}`, once. This uses the existing full claims schema and the official structured-output envelope. The prompt/order are unchanged. JSON output receives independent local structural checks, but no claims are published or factually approved.

The video guide currently shows numeric offset examples. The typed official OpenAPI's `/components/schemas/StaticMediaProcessing/properties/{start_offset,end_offset}` requires duration strings with an`s` suffix; the implementation uses those authoritative typed values. The structured guide and `/components/schemas/TextResponseFormat` document the format envelope. A deprecated ModelInteraction description mentions a separate response MIME field, while current examples use the nested MIME; the exact current envelope is used without inventing an extra field.

This sequence uses a different, explicitly authorized endpoint from the old failed generateContent request. Success on all three stages does not establish the old invalid field or fix the old request. A later400 records which added family preceded the failure, while `exact_invalid_field` remains unknown unless separately established from the preserved message. `manual_summary_default` and `automatic_collection_paused` remain true even after three successful stages.

## Main integration contract

Files: `coach_v1/expert_video_diagnostic.py`, `scripts/diagnose_expert_video.py`. The module exports `ExpertVideoDiagnostic`, `complete_error_receipt`, `validate_complete_error`, `stage_body` and `validate_stage_result`. Main's already saved prior-error shape is accepted without conversion.

Every CLI invocation requires `--authorization USER_PRO_REFERENCE_RESUME_2026-10-13`. Credentials enter from environment only. `--runtime-config` defaults to `config/expert_runtime.json`.

- `--phase discover --ledger RECOVERED_LEDGER --prior-error PRIOR --config CHANNELS --output-dir DIR`: metadata only; no Gemini TEXT/video request. It queries the literal official example ID `9hE5-98ZeCg` once through the existing YouTube metadata transport and verifies public/processed/non-live status and original duration. `--config` remains compatible but does not choose another video. Any historical charge/processed marker for the example blocks before metadata lookup. Unavailable, private, unlisted, live, failed or out-of-bound example metadata blocks without substitution. It writes `selected-video.json`, `entitlement.json`, `receipt.json`. The existing47metadata-request ceiling leaves3video slots within50; this discovery needs at most one metadata request.
- `--phase prepare --video SELECTED_VIDEO --ledger LATEST_LEDGER --prior-error PRIOR --stage STAGE [--previous-result LAST_RESULT] --output-dir DIR`: writes `plan.json`, `quota-ledger.json`, `entitlement.json`, `receipt.json`; emits `reserved=true/false` to `GITHUB_OUTPUT`. The selected video shape is `{id,url,duration_seconds,public_confirmed,metadata_checked_at}`, optionally inside the discovery receipt's `video` field. Duration is1–1200seconds and baseline public metadata must be fresh within900seconds.
- Upload the prepared ledger successfully and obtain its numeric artifact ID **before** processing. No preparation dispatches a Gemini request.
- `--phase process --plan PLAN --reservation-artifact-id ID --output-dir DIR`: at most one actual video request. It writes `result.json`, the unchanged `quota-ledger.json`, `entitlement.json`, `receipt.json`, and `complete-error.json` on HTTP failure. A restrictive exclusive `dispatch-claim.json` precedes the request. Repeating the same CLI process/output directory reads the saved result with `new_requests:0`, rather than issuing another call or overwriting its history. A claim left without a saved result blocks replay.
- Wait at least15seconds after the previous stage's completion (`next_not_before` is supplied) before preparing the next stage. Early preparation consumes no reservation. This is a conservative diagnostic spacing policy, not a claim of a particular account's published rate limit.

`result.json` contains schema `expert.video-diagnostic-result.v1`, stage/status/reason, model/route/session, public video, prior complete-error provenance/hash, ordered stage receipts, cumulative request count0–3, full conserved ledger/hash, optional complete sanitized error, and manual/pause flags. It contains no generated text. Only `READY` permits the next preparation. Main's public-safe projection may omit the ledger; the **local continuation** must use the complete result and latest ledger. Main owns workflow wiring, routine pause/default flags, artifact uploads, actual dispatch and final publication.

## Conservation, stopping and complete errors

Each distinct video stage reserves its **full original duration**, including baseline/no-clipping and clipped requests. The prior ledger's ordered rows remain an exact prefix; no row is refunded, reset or marked processed by this diagnostic. The same-source continuation exception is explicitly authorized and bound to one session, unchanged video/prior error, successful previous stage and its exact ledger. A new baseline on any charged ID, changing source, skipping a stage, rewriting history, a fourth stage or continuation after failure is blocked.

All requests have a600second total process wall bound. The model is fixed3.6; there is no model fallback or hidden baseline text probe. Existing free-project, exclusive-quota, rolling28800second and request-budget gates remain. Provider token quotas still apply;401/402/403/429,400,503, timeout, malformed/incomplete results and missing persistence stop without retry. API acceptance does not establish source truth or coaching accuracy.

Error retention selects **all** of `error.message`, redacts known API keys and encoded variants, the selected video ID/URL and encoded forms, credential assignments, identity/resource fields and opaque identifiers. It never slices to512characters. Raw bodies, output text, transcripts and credential fingerprints are not stored. An oversized/unparseable error body is recorded as message unavailable/`message_complete:false`; a partial message is never asserted complete and no next stage follows.

Main retains this pipeline in the existing quota workflow. Exact reservation names are `expert-quota-reservation-RUN`, `expert-quota-reservation-RUN-CLIPPING`, `expert-quota-reservation-RUN-RESPONSE_FORMAT`; final remains `expert-quota-final-RUN`. Recovery validates every chronologically ordered snapshot as a prefix-preserving extension and selects the latest durable snapshot, including cancellation after either added-stage reservation. Duplicate/missing-middle/out-of-order/expired/corrupt snapshots or a final that removes any intermediate charge become `UNKNOWN`. Successful persistence under any of the three step names requires durable evidence; missing artifacts cannot be treated as zero use.

## Fresh official-source audit

Public documentation GETs only; no provider/Riot/YouTube API or Actions dispatch was performed by this worker. Raw HTML remains transient `/tmp` data and is not checked into Git.

| Official URL | SHA256 | Checked evidence |
| --- | --- | --- |
| https://ai.google.dev/gemini-api/docs/video-understanding | `643d83d555f736fdcdbe7994be73c53a7d5ccb16fbe2a1dbc6cddee892a4cc36` | Fresh final literal-URL audit: YouTube REST baseline `9hE5-98ZeCg`, input order and exact prompt; static-only clipping |
| https://ai.google.dev/gemini-api/docs/structured-output | `36d9bc3bc1a1da0f9d6771776eb530966f2c847c39bcccec8b9baaff16bff05c` | Interactions response-format envelope and supported schema vocabulary |
| https://ai.google.dev/api/interactions-api | `ac7446cd4f9df2a04580bc87bad7bed59aec52a2d6732db8509d15048f169b12` | CreateInteraction request and completed model-output response |
| https://ai.google.dev/static/api/interactions.openapi.json | `96359db699322cbbda61e961561bce92e609cf1169545c4362a282300ba8535a` | ModelOption3.6; VideoContent; StaticMediaProcessing typed offsets; TextResponseFormat |

Short source excerpts: video guide—“You can pass YouTube URLs directly to Gemini API as part of your request”; structured guide—“always validate values in your application”; OpenAPI—“Optional. Segment start time.” The fetched `/api/interactions` URL redirects to the canonical `/api/interactions-api` documented above; this is a public-document redirect, not an inference-request redirect.

TDD evidence: initial15tests failed on missing staged implementation; six new recovery tests showed lost cancelled-stage charges/accepted intermediate refunds before the recovery change. Additional privacy/result-validation/budget cases were RED before correction. The final literal-URL correction was RED on selecting an unrelated source, failing to block the charged official example before lookup, and accepting another public URL; the corrected metadata/CLI checks are GREEN. Main's source-bound verification is the publication evidence.
