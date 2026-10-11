# Q19 generateContent official-source audit

Checked 2026-10-11 UTC. Main reviewed 1ea54c77a528ce941b51df674f7f803de69be903. Public documentation/source GET only; provider calls 0, Secrets/key reads 0, shared/Main edits 0. This route is the user's new instruction, not a demonstrated explanation of the previous Interactions HTTP400. Previous Interactions audits are preserved.

## Recommended field contract

POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent

```json
{
  "contents": [{"role":"user","parts":[
    {"file_data":{"file_uri":"https://www.youtube.com/watch?v=VIDEO_ID"},
     "video_metadata":{"start_offset":"0s","end_offset":"600s"}},
    {"text":"PROMPT_REQUIRING_JSON_AND_ORIGINAL_VIDEO_TIMESTAMPS"}
  ]}],
  "generationConfig":{
    "candidateCount":1,
    "responseMimeType":"application/json",
    "responseJsonSchema":{"type":"object","properties":{"claims":{"type":"array","maxItems":100,"items":{"type":"object"}}},"required":["claims"],"additionalProperties":false}
  }
}
```

The displayed schema is an abbreviated shape placeholder, NOT a replacement for the existing complete RESPONSE_SCHEMA. Copy that schema's exact validated JSON value. The schema-bearing fields responseMimeType/responseJsonSchema are explicitly mapped by the current official Developer API SDK converter, and named by the REST reference. Do not substitute responseSchema: it is an OpenAPI Schema subset with a different vocabulary. Do not send both responseSchema and responseJsonSchema, or the reference's private-looking _responseJsonSchema field.

No top-level model/input/response_format/store/stream/background (Interactions fields). Model is in the generateContent URL. Video part precedes prompt. video_metadata is a sibling of file_data, not a child. Do not invent a MIME type from the YouTube URL; FileData.mimeType is optional. No SDK automatic retries because they exceed the user-directed policy.

The API reference writes these fields fileData.fileUri and videoMetadata.startOffset/endOffset; its REST uploaded-video example itself uses file_data.file_uri. Official ProtoJSON specifies accepting lowerCamelCase and original proto field names. The user-requested snake names are that proto spelling. Do not send duplicate snake/camel aliases in the same object.

Offsets are protobuf Duration strings, ending in s, up to nine fractional digits. First clip S=0, E=min(600,D); enforce 0<=S<E<=D and E-S<=600. The 600s restriction is user/product policy, not a claimed API hard limit. VideoMetadata is deprecated in the API reference in favor of GenerateContentRequest.processing_options; the replacement request schema is absent from this reference. Keep the user's explicitly selected legacy metadata fields rather than invent a replacement wire field. No official guarantee found that generated timestamps are original/global versus clip-local: keep original-video timestamp prompting and strict original absolute clip bounds; never add offsets by assumption.

## Important current documentation/SDK mismatch

REST #GenerationConfig, #ResponseFormatConfig, #TextResponseFormat explicitly describe a NEW flat shape:

```json
{"generationConfig":{"candidateCount":1,"responseFormat":{"text":{"mimeType":"APPLICATION_JSON","schema":{"type":"object"}}}}}
```

APPLICATION_JSON is an enum spelling (not application/json). responseFormat is an object, not a list, in this REST reference. Its text.schema accepts a JSON value. This new field is recommended in deprecated responseSchema/_responseJsonSchema descriptions.

However, current official python-genai main (identical to pinned tree969d0e7fb329d4da7a41fc12e626a1a85cc70674) types.py:11464 explicitly says ResponseFormat is not supported in Gemini API, and _GenerateContentConfig_to_mldev models.py:1147-1352 maps response_mime_type/response_json_schema but has no response_format mapping. The response_format list mapping models.py:2669 is in a Vertex conversion, not Developer API. Thus do not claim SDK corroboration or actual acceptance of the new flat shape. REST documentation is explicit; the SDK disagrees/has not implemented it. The conservative contract above uses the mutually corroborated existing fields; a Main decision to use the new REST field must preserve this limitation. No provider call was made to resolve it.

## Response parser

REST #GenerateContentResponse: candidates[], promptFeedback, usageMetadata. #Candidate: content.parts[], finishReason. #Part: text and optional thought boolean. No Interactions status/steps/model_output parser.

Product acceptance gate: bounded JSON object, exactly one candidate, finishReason STOP, join non-thought text parts as one JSON string, validate complete existing claims schema/max100/200KB/timestamps. Missing candidates, promptFeedback.blockReason, MAX_TOKENS, safety/other finish reasons, malformed text, no text, or unsupported non-text output must withhold. Joining parts and STOP-only are conservative product choices, not a claim all provider responses have exactly one text part. Never expose/retain thought text, raw error bodies, or credentials.

## Model/free/YouTube scope

The current generateContent reference includes an official SDK example client.models.generate_content(model='gemini-3.8-flash', contents=[uploaded_video,prompt]); models lists the model; pricing lists standard 3.8 Flash input/output free of charge. This demonstrates documented generateContent model availability and published free pricing, not current private-project eligibility. Preserve project, exclusive use, fresh official proof, quota, and payment gates.

The fresh video guide explicitly permits public YouTube URLs (not private/unlisted), preview/no charge, free limit 8h/day. Its current exact YouTube examples use Interactions, while REST generateContent FileData accepts a URI and the reference's generateContent video example uses an uploaded URI. We did not find a current guide example of the EXACT generateContent + YouTube + legacy metadata + structured JSON combination. Route is user-directed and field schema is documented; actual combination acceptance remains UNKNOWN until authorized actual diagnosis.

## HTTP503 retry policy

Gemini troubleshooting recommends exponential backoff for transient 503 UNAVAILABLE. It does not require a particular delay/retry count and its SDK retries other conditions automatically, so do not inherit those defaults.

User policy: TEXT-only, literal HTTP503, at most 3 retries after initial call (4 attempts maximum, make this count explicit), separated by bounded increasing waits (e.g. 1/2/4 seconds are product choices derived from the official example). Every attempt must retain its literal HTTP status and safe selected error fields. Do not retry VIDEO, 400/401/402/403/429, timeout/network exceptions, malformed HTTP200, or schema failures under this instruction. No quota refund; no silent retry. Check free/payment gates before each actual attempt; preserve max total request accounting. A 503 is a transient service failure, not proof that the video/schema/key/project works.

## Evidence locators and short excerpts

One excerpt per source URL, each <=25 words. Full source bytes/hashes are in manifest.json.

| Official source | Locator | Short excerpt |
|---|---|---|
| https://ai.google.dev/api/generate-content | #ResponseFormatConfig | "This is a flat object where each optional sub-field configures a specific output modality." |
| https://ai.google.dev/gemini-api/docs/video-understanding | Pass YouTube URLs / Limitations | "You can only upload public videos (not private or unlisted videos)." |
| https://ai.google.dev/gemini-api/docs/structured-output | Overview | "In addition to supporting JSON Schema in the REST API" |
| https://ai.google.dev/gemini-api/docs/pricing | Gemini3.8Flash / Standard / Free Tier | "Free of charge" |
| https://ai.google.dev/gemini-api/docs/models | Gemini3.8Flash | "gemini-3.8-flash" |
| https://ai.google.dev/gemini-api/docs/api-errors | Common API errors | "503 Service Unavailable" |
| https://ai.google.dev/gemini-api/docs/troubleshooting | Retry strategy | "we recommend implementing an exponential backoff strategy" |
| https://protobuf.dev/programming-guides/json/ | Field names as JSON keys | "Parsers accept both the lowerCamelCase name" |
| https://raw.githubusercontent.com/googleapis/python-genai/main/google/genai/types.py | ResponseFormat:11464 | "This data type is not supported in Gemini API." |
| https://raw.githubusercontent.com/googleapis/python-genai/main/google/genai/models.py | _GenerateContentConfig_to_mldev:1228 | "responseJsonSchema" |

## Limits

No confirmed invalid field causing the prior Interactions400; no provider calls; no project/key assertions; no guaranteed timestamp origin; no official clipping quota proration; no stronger free or success claim. Public HTTP documentation retrieval failures are listed as failed fetches in manifest and are not evidence.
