# Q19 diagnosis-first source audit

Checked2026-10-11. Fresh unauthenticated official-doc GETs only. Main reviewed at bb543a52b0edd5f24834aae748142298358fbd9b. No provider model calls, credentials or Main edits. manifest.json records exact fetch time, URLs, full-body hashes and sizes. This receipt is documentation evidence, not real-request success.

## Route decision

KEEP Interactions POST https://generativelanguage.googleapis.com/v1beta/interactions and gemini-3.8-flash. The conditional generateContent fallback does not apply: current official video-understanding#youtube explicitly shows client.interactions.create and REST /v1beta/interactions with video uri set to a full YouTube URL, using gemini-3.8-flash. OpenAPI VideoContent also has a YouTube URL example.

Video source: https://ai.google.dev/gemini-api/docs/video-understanding#youtube . Sole short quoted excerpt for this source: “You can pass YouTube URLs directly to Gemini API as part of your request”. Same page #clipping-intervals documents Interactions processing.type static, start_offset/end_offset; #customize-video-processing restricts clipping to static; #technical-details-video recommends placing text after the single video. The guide's numeric offset examples conflict with API/OpenAPI string field types; use the typed request schema. The YouTube feature is preview/no-charge, public-only, Free Tier8h/day; no stronger project entitlement or operational-success claim.

Typed reference: https://ai.google.dev/api/interactions-api#Resource:Content ; excerpt: “Specified as a decimal number of seconds followed by an 's' suffix”. Both offsets are strings; end must exceed start. The main CreateInteraction field table also supports input string, model, store/stream/background booleans and response_format.

Machine schema: https://ai.google.dev/static/api/interactions.openapi.json . JSON pointers:
- /components/schemas/ModelInteraction/properties/input and /components/schemas/InteractionsInput/oneOf (string plus ContentList variants)
- /components/schemas/ModelOption/enum (includes gemini-3.8-flash)
- /components/schemas/VideoContent/properties/uri and example (full YouTube URL)
- /components/schemas/VideoContent/properties/processing -> MediaProcessing -> StaticMediaProcessing
- /components/schemas/StaticMediaProcessing/properties/start_offset and end_offset (string, google-duration)
- /components/schemas/TextResponseFormat (type=text, mime_type=application/json, schema object)
- /components/schemas/ModelInteraction/properties/{store,stream,background} (boolean input fields)
- /paths/~1{api_version}~1interactions/post (JSON ModelInteraction request, 4XX/5XX error envelopes)
Sole short schema excerpt: “The URI of the video.”

## Exact supported diagnostic requests

Same-model text request (no video):
```json
{"model":"gemini-3.8-flash","input":"Reply exactly OK.","store":false,"stream":false,"background":false}
```
First video interval, D=actual whole source duration, E=min(600,D), positive integer duration:
```json
{"model":"gemini-3.8-flash","input":[{"type":"video","uri":"https://www.youtube.com/watch?v=VIDEO_ID","processing":{"type":"static","start_offset":"0s","end_offset":"600s"}},{"type":"text","text":"Summarize only this interval. Use original-video MM:SS timestamps."}],"store":false,"stream":false,"background":false}
```
For D<600 use actual E+'s' rather than600s. Exact public video ID remains runtime selection, not invented in this receipt. The existing complete response_format/schema is officially supported and may be retained; removing it is an isolation diagnostic choice, not a known defect. Do not combine Interactions uri/processing fields with generateContent file_data. No URI or model switch is warranted from current source.

Main collector.py:130-137 conforms: video first, text second, type static, offsets strings with s, the fixed endpoint/model, response_format type text/application-json/schema, all three false flags. Independent offline source-field checksPASS; no documented parameter error discovered. Parameter validity does not diagnose prior NETWORK_FAILURE/TIMEOUT or HTTP errors. Source docs do not guarantee global-vs-clip-local generated timing; current explicit original-time prompt plus range checks do not establish visually verified timing.

## Safe errors

Current explicit docs: https://ai.google.dev/gemini-api/docs/api-errors#error-schema and #http-errors. Sole short quoted excerpt: “All errors from the Interactions API return an error object containing a code and message.” Nonstreaming4XX/5XX responses use {error:{code:string,message:string}}; current guide describes code snake_case. The OpenAPI code description calls it a URI, but its examples use not_found/invalid_request. Treat it as bounded observed provider data, not an authorization source. SSE uses event_type=error and is not the current streamfalse format.

Official exact example code invalid_request, with a message explaining an unsupported tool parameter. Do not reuse that fixture as evidence that this collector's offset/URI is wrong. Main REST HTTPError currently discards body, and _request collapses non200 to PROVIDER_HTTP_FAILURE; that is a diagnosis-information gap, not evidence that the route is unsupported.

Recommended diagnostic receipt: actual HTTP status (if present), request stage TEXT or VIDEO_FIRST_CLIP, safe bounded provider code and a redacted/truncated message, timeout bound, actual observed duration, response-size/malformed flags if relevant, and independently preserved source-policy input digest. No raw error body, headers, key/Authorization values, URL-query credentials, transcript or complete model reply. HTTP/code alone may distinguish invalid_request/parameter_unknown, authentication, permission_denied, model_not_found, quota_exceeded, rate_limit_exceeded, payment_required, service_unavailable/deadline_exceeded; do not equate every401/403/timeout with expired keys. Unknown or malformed error bodies should yield UNKNOWN diagnostics while preserving the HTTP status and reservations. Keep existing no-retry/no-refund/payment block rules; source advice to retry does not override the task contract.

Model pricing: https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash Standard Free Tier lists input/output free. Sole short excerpt: “Free of charge”. This is source pricing, not actual project state. Keep fresh pricing proof plus project/free/exclusive and existing quota gates.

The public troubleshooting source https://ai.google.dev/gemini-api/docs/troubleshooting links the API errors guide. No troubleshooting recommendation changes this task's no-retry/no-paid-upgrade constraints. Sole short excerpt: “Check your API calls for model parameter errors”.
