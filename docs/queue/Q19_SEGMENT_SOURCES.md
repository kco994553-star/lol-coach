# Q19 segment official-source audit — 2026-10-11

Read-only source audit. Full downloaded bodies remain in isolated scratch storage; only this report and URL/hash manifest are published. Current public official pages and OpenAPI were downloaded without authentication. No provider model calls or secrets. `manifest.json` records full-body SHA-256 hashes.

## Supported Interactions request

Endpoint: POST https://generativelanguage.googleapis.com/v1beta/interactions
Model: gemini-3.8-flash (official video and structured-output examples; current Standard Free Tier lists input and output free; runtime project free/exclusive/quota gates remain required).

```json
{
  "model": "gemini-3.8-flash",
  "input": [
    {
      "type": "video",
      "uri": "https://www.youtube.com/watch?v=VIDEO_ID",
      "processing": {
        "type": "static",
        "start_offset": "600s",
        "end_offset": "1200s"
      }
    },
    {"type": "text", "text": "Extract only this requested interval. Return original-video timestamps as MM:SS; do not reset the clock at the interval start."}
  ],
  "response_format": {"type": "text", "mime_type": "application/json", "schema": {"type": "object"}},
  "store": false,
  "stream": false,
  "background": false
}
```

The schema object shown above is only a placement illustration; preserve the application's complete strict response schema. YouTube examples omit mime_type, so do not infer a file MIME from the URL. Put text after video as the official guide recommends.

- OpenAPI pointers: /components/schemas/VideoContent/properties/processing; /components/schemas/MediaProcessing; /components/schemas/StaticMediaProcessing/properties/start_offset and end_offset; /components/schemas/TextResponseFormat; /paths/~1{api_version}~1interactions/post. Offset values are strings, google-duration, decimal seconds plus `s`; nonnegative; end greater than start.
- https://ai.google.dev/api/interactions-api#Resource:Content gives the same field types. Short excerpt: “Specified as a decimal number of seconds followed by an 's' suffix”.
- https://ai.google.dev/static/api/interactions.openapi.json has machine-readable matching schema; excerpt: “Optional. Segment start time.”
- https://ai.google.dev/gemini-api/docs/video-understanding#clipping-intervals has Interactions clipping examples. Its numeric 1200/1500 offsets conflict with the API schema; choose schema strings, not guide numbers. Short excerpt from #customize-video-processing: “These customization options are only supported when processing the video in "static" mode.”
- This supports YouTube URI plus static clipping by combining its VideoContent schema (whose own example is a YouTube URI) with official clipping configuration. No live successful clipped request has been measured in this audit. Do not claim operational success from documentation alone.

## Timestamp limits

The official guide supports timestamp references in MM:SS. Neither the video guide nor Interactions VideoContent/StaticMediaProcessing schema explicitly guarantees whether generated claim timestamps use original-video or clip-local origin. Audio WordInfo start/end offsets explicitly refer to audio origin; that is not evidence for video claim semantics.

Contract recommendation: instruct original-video MM:SS explicitly, preserve request segment boundaries and timestamp basis as provenance, and reject/withhold invalid or out-of-range claim timestamps. Do not blindly add start_offset. A returned valid number still does not prove a visually verified moment or the correct timestamp origin. Actual validation remains unverified until a controlled real run and source checking. For adjacent intervals avoid exact-boundary double admission using a documented application ownership rule; the official clipping schema does not specify inclusive/exclusive endpoints.

Structured JSON output is supported on the same endpoint/model via response_format type text, mime_type application/json, schema. It ensures structure, not factual timing. https://ai.google.dev/gemini-api/docs/structured-output short excerpt: “always validate values in your application.”

## Proposed implementation bounds and quota (product decisions)

- Initial video duration <=1200s, max one video per run, split into [0,min(600,D)] and, only if D>600, [600,D]. Each segment duration >0 and <=600s. These numeric limits are user/product policy, not official provider guarantees.
- Request timeout <=600s is a client bound, not a documented guaranteed server completion time. The official video guide recommends streaming/background for long requests; keeping synchronous nonstreaming must preserve safe timeout/401/network failure states and no retries/refunds.
- Official YouTube Free Tier cap is 8 hours/day. Current docs do not specify clipping quota reduction or same-URI repeated-request accounting. Safest unchanged-cap accounting is reserve full original duration per planned segment request before either call, without refund on failures; do not present clip-duration proration as documented.
- If timeout rises from60 to600 while the reservation dispatch bound remains900, conservative charged window must rise from87360 to87900 (=86400+900+600). Recheck deadline before every call. If the dispatch policy is changed, recompute the bound from the new actual maximum, not an arbitrary prior constant.
- Preserve one reservation/attempt identity, progress journal and final source artifact; subsequent segments must not erase the first accepted segment or mark the full source complete early. Preserve per-segment failures honestly. No model cost/latency savings assumed.

## generateContent fallback status

No switch is needed: Interactions supports the requested feature. https://ai.google.dev/api/generate-content lists VideoMetadata.startOffset/endOffset string Duration with `s`, but marks VideoMetadata deprecated and names GenerateContentRequest.processing_options as replacement. The page does not supply a usable replacement schema for that named field. Do not invent processing_options nesting or move Interactions snake_case processing into generateContent. Exact legacy end-to-end Part nesting was not established here and should not be treated as an approved fallback. Short excerpt: “Deprecated: Use GenerateContentRequest.processing_options instead.”

https://ai.google.dev/gemini-api/docs/interactions-overview says generateContent remains supported; endpoint-level migration is outside current need.

Current https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash Standard Free Tier input/output both list Free of charge. Short excerpt: “Free of charge”. This documents model pricing, not the actual selected project's billing state, authorization, quota or request success. Model card also remains present in https://ai.google.dev/gemini-api/docs/models; full source archived.
