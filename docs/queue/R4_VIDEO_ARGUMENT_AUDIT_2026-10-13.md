# R4 video argument audit —2026-10-13UTC

**Exact invalid field: UNKNOWN.** The sole authorized fallback trial, Actions run `38387587260`, selected `gemini-3.6-flash` after primary `gemini-3.8-flash` returned503 from both text clients. Both fallback plain-text clients returned200. The one subsequent video request returned400, `INVALID_ARGUMENT`, with the sanitized message **“Request contains an invalid argument.”** No field name or parameter location appears in the retained diagnostic. Accepted claims:0. Plain-text success does not test video clipping or the structured schema.

Observed sources are the safe artifact `11807017561`'s `expert-front/front-diagnostics.json`, `expert-final/diagnostics.json` and `expert-final/receipt.json`. Recovery identifies earlier run `38349297786`, artifact `11790310968`, as `FOUND`. Main owns byte-level ledger reconciliation; this audit does not recalculate or reset quota. Video ID `lSy9NeB5Ue4` remains charged and must not be retried. The alternative-model trial is consumed.

## What the current official sources establish

| Request feature | Official evidence | Bounded finding |
| --- | --- | --- |
| Selected3.6 model | [Model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash), supported data types and capabilities | Video input and structured output are explicitly supported. A claim that this model categorically lacks either capability is unsupported. |
| Video metadata placement | [Part](https://ai.google.dev/api/generate-content#Part), `Part.FIELDS.video_metadata` | Video metadata accompanies video data in `fileData` or `inlineData`. The builder places metadata beside `file_data`, as documented. |
| Clipping offsets | [VideoMetadata](https://ai.google.dev/api/generate-content#VideoMetadata), `start_offset`/`end_offset` fields | The reference accepts duration strings with an `s` suffix. The builder emits `0s` and `min(600, original duration)s`; these string forms do not establish an invalid argument. |
| Snake-case field names | [ProtoJSON](https://protobuf.dev/programming-guides/json/#field-names-as-json-keys) | Original proto field names and lowerCamelCase are both accepted by specification. Snake case alone is not a confirmed cause. |
| Omitted source MIME | [FileData](https://ai.google.dev/api/generate-content#FileData), `mime_type`/`file_uri` fields | `mimeType` is optional; `fileUri` is required and present. The reference does not establish omission as the rejected field. |
| JSON output arguments | [GenerationConfig](https://ai.google.dev/api/generate-content#GenerationConfig), MIME/schema fields | JSON MIME is listed, and JSON-schema handling excludes simultaneous `responseSchema`. The builder supplies JSON MIME and `responseJsonSchema`, without `responseSchema`. |
| Claims schema vocabulary | [Structured output](https://ai.google.dev/gemini-api/docs/structured-output), supported schema properties | All used keywords—`type`, `properties`, `required`, `additionalProperties`, `items`, `maxItems`, `enum`—are documented. This checks vocabulary, not operational acceptance of the complete request. |
| YouTube and clipping combination | [Video guide](https://ai.google.dev/gemini-api/docs/video-understanding#youtube), customization/clipping sections | YouTube input and static clipping are documented; current examples use Interactions. No exact example of selected3.6 **generateContent + YouTube URL + legacy video metadata + this structured schema** was established. |

Two documentation limitations remain material. The REST reference marks `VideoMetadata` deprecated and points to `GenerateContentRequest.processing_options`, without establishing a usable replacement request structure in the inspected reference. GenerationConfig marks its older schema path deprecated and gives an internal-detail description for the visible `responseJsonSchema` field that refers back to the same name. These inconsistencies do not identify which argument the provider rejected. Do not invent a replacement nesting or treat deprecation as proof of rejection.

The current builder was reviewed offline. It emits one video part, followed by a text prompt, `candidateCount:1`, JSON MIME and the existing claims schema. The actual raw wire body was not retained; this audit compares the current builder's shape with documented fields, rather than asserting an independently captured request body.

## Safe excerpts and evidence boundary

Short excerpts from official sources, one per URL:

- Model3.6: “Inputs Text, Image, Video, Audio, and PDF”; “Structured outputs Supported”.
- generateContent: “If set, responseSchema must be omitted, but responseMimeType is required.”
- Structured output: “additionalProperties: Controls whether properties not listed in properties are allowed. Can be a boolean or a schema.”
- Video guide: “By default, video inputs use static processing (extracting frames at 1 FPS).”
- ProtoJSON: “Parsers accept both the lowerCamelCase name”.
- API error guide: “The request payload is malformed or contains invalid parameters.”

The official [API error guide](https://ai.google.dev/gemini-api/docs/api-errors) describes generic400 request-parameter failures; it does not resolve this specific `INVALID_ARGUMENT`. Fresh source hashes, exact locators and safe local-diagnostic hashes are in `evidence/queue/v20/r4-video-argument-audit.json`. The video documentation fetch initially failed and a second public-document GET succeeded; neither was a provider inference request. No raw HTML, model output, transcript or credential is saved in these audit artifacts.

Next actionable step is field-specific clarification from the provider, using the selected model, sanitized400 and documented request-field names. Meanwhile use the authenticated local manual timestamped-summary route described in `R4_RECOVERY.md`. No additional provider/Riot/YouTube API request, model trial, charged-ID retry or code change was performed or proposed by this audit.
