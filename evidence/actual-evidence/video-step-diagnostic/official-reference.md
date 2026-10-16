# Official generateContent video diagnostic reference

Observed 2026-10-16T23:13:24Z. Research only: no generation call, test, production change, or cause claim.

The actual route is `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent`. Current video and structured-output guides default to Interactions, including their `?api=generate-content` variants; numeric `processing.start_offset` from those examples does not establish the generateContent field type.

## Verified route-specific evidence

The pinned official Google cookbook at commit `ec8ec410e29a5c4cd79237fad1df6f5dd6b6f8a4` (2025-07-22) demonstrates `client.models.generate_content` using YouTube `file_data.file_uri` and `video_metadata.start_offset='1250s'` / `end_offset='1570s'`. Its no-clip example uses `https://www.youtube.com/watch?v=ixRanV-rdAQ`; the clipping example uses `https://www.youtube.com/watch?v=XEzRZ35urlk`. Full exact public source examples are retained in the JSON companion.

The REST reference defines `Part.videoMetadata.startOffset/endOffset` as protobuf Duration strings, e.g. `"3.5s"`, and fps as a number in (0,24]. Existing `"0s"` / `"120s"` values match the documented type.

Original snake_case aliases are supported by official ProtoJSON rules and the public v1beta proto. The generateContent REST guide also includes literal shell JSON with `file_data`, `mime_type`, and `file_uri`. Snake_case is not an established error cause.

The REST reference deprecates VideoMetadata toward `GenerateContentRequest.processing_options`, but this replacement is absent from its request-field list/JSON and the inspected public proto. Do not invent a replacement shape or transfer Interactions processing fields. Deprecation does not prove an HTTP400 cause.

Existing collector schema keywords are all in the documented supported subset: type, properties, required, additionalProperties, maxItems, items, enum. The current REST reference still lists responseMimeType and responseJsonSchema. It also documents `generationConfig.responseFormat.text` with `mimeType:"APPLICATION_JSON"` and `schema`; this is an alternate documented format, not evidence that existing fields caused400.

## Stage1 official generateContent minimum, not sent

Pinned source: [official cookbook, ec8ec410e29a5c4cd79237fad1df6f5dd6b6f8a4](https://raw.githubusercontent.com/google-gemini/cookbook/ec8ec410e29a5c4cd79237fad1df6f5dd6b6f8a4/quickstarts/Video_understanding.ipynb). The exact source prompt, YouTube URL and part order are translated into documented REST fields:

```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "Find all the instances where Sundar says \"AI\". Provide timestamps and broader context for each instance."
        },
        {
          "fileData": {
            "fileUri": "https://www.youtube.com/watch?v=ixRanV-rdAQ"
          }
        }
      ]
    }
  ]
}
```

POST `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent`. The pinned SDK source passes `model=MODEL_ID`; fixing the route to `gemini-3.6-flash` is an explicit model-selector substitution. This exact wire body is translated from the official SDK sample, not a claim that the notebook contains a literal curl.

No generationConfig, role, MIME, metadata, schema or extra prompt instruction is added. Compared with the existing teaching body, stage1 changes prompt, URI, clipping, generationConfig and optional role/field spelling; these multiple differences are declared. It is the user's requested initial baseline and does not isolate the original400 cause.

Preserve the successful stage1 body for the user's ordered stages: stage2 changes only fileData.fileUri; stage3 adds only videoMetadata interval strings; stage4 changes only output-format configuration. No removal-only test of the old body is recommended. VIDEO3/KST-day includes already1, so at most2 new video calls fit today; later stages must remain gated. Every attempted stage reserves the selected video's full original duration.

## Metadata gate and unknowns

Current guide canonical video: [Building with Gemini 2.0: Multimodal live streaming](https://www.youtube.com/watch?v=9hE5-98ZeCg), Google for Developers. No duration is established by the fetched public oEmbed metadata. Full duration remains null and canonical dispatch is blocked until the existing trusted YouTube Data API metadata path verifies it. No media, transcript, or audio was downloaded. Do not estimate duration or reserve only the requested clip.

Generic HTTP400 INVALID_ARGUMENT and text STOP do not identify the failed video feature. Stage1's selected pinned generateContent example video ixRanV-rdAQ also has no verified duration in this research receipt; trusted metadata and full original-duration budget are required before reservation. The current guide canonical9h URL is retained as a separate Interactions example and is not the recommended stage1 URL.

## Source receipt hashes

- generate_reference: [source](https://ai.google.dev/api/generate-content); SHA256 `9bb2c1cd38fc4a4c1fce3611a78d1294950a1e0c87302ccc543a076c95577255`; 1230174 bytes; last updated 2026-10-13 UTC.
- current_video_guide: [source](https://ai.google.dev/gemini-api/docs/video-understanding); SHA256 `5a808388a71e251da681dadabaf328e5154d99a89c7d29738fc8be87161a85d2`; 320125 bytes; last updated 2026-10-13 UTC.
- query_variant: [source](https://ai.google.dev/gemini-api/docs/video-understanding?api=generate-content); SHA256 `57a9452fa8252ce5b5faa03af4ded8d8405361565ea57cb83ad8b4feaf0f4586`; 320125 bytes; last updated 2026-10-13 UTC.
- pinned_generate_content_example: [source](https://raw.githubusercontent.com/google-gemini/cookbook/ec8ec410e29a5c4cd79237fad1df6f5dd6b6f8a4/quickstarts/Video_understanding.ipynb); SHA256 `7012ea193f4facfc8211ad7f7c13b53c5709ece9ea67ecb9890503e402b19226`; 51991 bytes.
- content_proto: [source](https://raw.githubusercontent.com/googleapis/googleapis/master/google/ai/generativelanguage/v1beta/content.proto); SHA256 `8c01c50c6d6795bf9bc0d4036386fe031feaf67e560ae17e1fbc6c5b47b625e7`; 29085 bytes.
- generative_service_proto: [source](https://raw.githubusercontent.com/googleapis/googleapis/master/google/ai/generativelanguage/v1beta/generative_service.proto); SHA256 `c64e082244f326e528d474d7b78834c2439bdc49811645aa3291dfb12d4499c3`; 75189 bytes.
- protojson: [source](https://protobuf.dev/programming-guides/json/); SHA256 `b1ddf3edca841b66d0f6dca4605447d8db95bc9a6db60a1a073f5d5fc4761982`; 85404 bytes.
- structured_guide: [source](https://ai.google.dev/gemini-api/docs/structured-output?api=generate-content); SHA256 `535768781577e8a26fc5b4a3255a781264a556f26c35b7a68c1bae007fe219e2`; 423340 bytes; last updated 2026-10-13 UTC.
- canonical_oembed: [source](https://www.youtube-nocookie.com/oembed?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3D9hE5-98ZeCg&format=json); SHA256 `38babad21759041712a7a8a7506d99df20e391ef14a2c0dd02071ee211b0082e`; 848 bytes.

Only public excerpts/examples and source receipts are retained. Research scratch downloads were removed after extraction; original cached source files were preserved.

