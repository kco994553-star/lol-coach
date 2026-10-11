# Q19 official source audit and free-only execution boundary

Audit date: 2026-10-11 UTC. Authority: USER_QUEUE_V1.6_2026-10-11.
This is a public-documentation audit, not successful YouTube API discovery,
Gemini extraction, expert-source approval, billing verification or coaching
validation. No API key value was read, no YouTube API request was made, and no
Gemini request, video download or transcript scraping was performed.

The live automated Gemini feature is **BLOCKED_EXTERNAL** until an approved
channel allowlist, usable credentials and independently verified free-project
binding are available. Secret existence was not inspected by this audit.
`config/expert_channels.json` and `data/expert_claims/` were absent in the
integration checkout when inspected. Existing R5 research names PekinWoof and
video `CejHqSces8Q`; that history does not supply an approved Q19 channel ID,
known speaker attribution or permission to populate a new allowlist. Dopa is
an example in the user instruction, not a verified channel identifier.

## Verified documentation sources

All requests below were HTTPS GETs of public official documentation and returned
HTTP 200. SHA-256 covers the exact retrieved HTML bytes, including navigation;
it identifies the source version, not the truth of any generated expert claim.
Raw snapshots, extracted text and HTTP receipts are retained in the execution
workspace at `/tmp/q19-official-20261011/`. No video or transcript is archived.
The Cloud Billing URL redirected to its official `docs.cloud.google.com` URL.

| Source | Requested official URL | Retrieved UTC | Page last updated UTC | Original HTML SHA-256 |
| --- | --- | --- | --- | --- |
| youtube-playlistitems | https://developers.google.com/youtube/v3/docs/playlistItems/list | 2026-10-11T06:10:42.247901+00:00 | 2026-09-14 | `0208f7f4862ff0bee7be0529fe281fcaf3e5767a6920b9486bebd78a1e9034b9` |
| youtube-videos | https://developers.google.com/youtube/v3/docs/videos/list | 2026-10-11T06:10:42.248416+00:00 | 2026-09-14 | `8b8c27467c1136f7d494cebd99261b42f4bebe7eafa1c1845119c9e598f225a4` |
| youtube-quota | https://developers.google.com/youtube/v3/getting-started#quota | 2026-10-11T06:10:42.248820+00:00 | 2026-09-14 | `0bdc4dd64864019d7af9b5ffad0976a028423fb3c53a27f4a2f846398248a331` |
| youtube-quota-costs | https://developers.google.com/youtube/v3/determine_quota_cost | 2026-10-11T06:10:42.248975+00:00 | 2026-10-08 | `9f2aabc97b648c197108a4c957ef148aade63679f0bdb69dd735e60641ea996b` |
| youtube-channels | https://developers.google.com/youtube/v3/docs/channels/list | 2026-10-11T06:10:42.249108+00:00 | 2026-09-14 | `5243e43f3663760ab683fd792142215b3baf091d88c201d7c15d3a4be8c49493` |
| gemini-video | https://ai.google.dev/gemini-api/docs/video-understanding | 2026-10-11T06:10:42.249679+00:00 | 2026-10-09 | `1e0a6ff5e8c46ef2cf6a7c43ed043535372f073c1d204069fe561ecf28a74697` |
| gemini-pricing | https://ai.google.dev/gemini-api/docs/pricing | 2026-10-11T06:10:43.832634+00:00 | 2026-10-09 | `1075d42d74a4679046f9d397061acc07dff08c3740531a05e28f9ec4d5834b15` |
| gemini-billing | https://ai.google.dev/gemini-api/docs/billing | 2026-10-11T06:10:43.869008+00:00 | 2026-09-28 | `f0eda423aa236fdccec037147f9aa147d9c1023a1fc8e0e031d1ce112463f12b` |
| gemini-json | https://ai.google.dev/gemini-api/docs/structured-output | 2026-10-11T06:10:44.116780+00:00 | 2026-09-23 | `634e24c458ca8df3392bcfa23e1ab7dacb605bb661d3197b55f9f36fe255fbcf` |
| gemini-keys | https://ai.google.dev/gemini-api/docs/api-key | 2026-10-11T06:10:44.272912+00:00 | 2026-10-06 | `a93448e2a34e20463774c0c0774e0cdc8e32d150585daf99c799a3d5e289fcfc` |
| gemini-rate-limits | https://ai.google.dev/gemini-api/docs/rate-limits | 2026-10-11T06:10:44.317373+00:00 | 2026-10-09 | `8b17a4d749803946a0f600cfe9d681c864ec34b525eed6f461b97398fc6a1aa2` |
| cloud-billing-status | https://cloud.google.com/billing/docs/reference/rest/v1/projects/getBillingInfo | 2026-10-11T06:12:33.704967+00:00 | 2025-09-04 | `75404bcdfb9a63d59e25c1c722e23388ced93c644515cfcfce01e70ddf51f814` |
| gemini-models | https://ai.google.dev/gemini-api/docs/models | 2026-10-11T06:12:37.086908+00:00 | 2026-10-09 | `4b15d4dadfcf91c4be3d1e497e0147b54c3b70ced28d8cf6e6c47bd4a85b2bd6` |
| youtube-video-resource | https://developers.google.com/youtube/v3/docs/videos | 2026-10-11T06:13:21.673736+00:00 | 2026-10-08 | `c57bb3854c2f8611336f64a637be6fbb6cb6c7792913a87db88ac9fb691c2d13` |
| gemini-interactions | https://ai.google.dev/gemini-api/docs/interactions-overview | 2026-10-11T06:15:56.999746+00:00 | 2026-10-09 | `f8514a80b8f78dc57441b38480f45bd9b30b44236e86988ebd62c6134a0862d2` |
| gemini-interactions-reference | https://ai.google.dev/api/interactions-api | 2026-10-11T06:16:24.834517+00:00 | 2026-10-09 | `052344af68443a8310ee1d63eb6a299e45ca74586922545647195720607906a3` |
| gemini-errors | https://ai.google.dev/gemini-api/docs/troubleshooting | 2026-10-11T06:18:30.035276+00:00 | 2026-10-01 | `462232a8c36a5cc5ba94b3093583f164595d0624766c1016a7f754e4f205732c` |

## YouTube discovery and metadata

The [playlistItems.list overview](https://developers.google.com/youtube/v3/docs/playlistItems/list#overview)
says: “A call to this method has a quota cost of 1 unit.” Its `maxResults`
parameter accepts 0–50, default 5. Each pagination request consumes quota.
The [videos.list overview](https://developers.google.com/youtube/v3/docs/videos/list#overview)
likewise states a cost of 1 unit. Use only known uploads playlists and known
video IDs; `search.list`, downloads and scraping are excluded from this design.

An uploads playlist must be independently configured or resolved from an
approved known channel with `channels.list(part=contentDetails,id=...)`.
The [channels.list part parameter](https://developers.google.com/youtube/v3/docs/channels/list#parameters)
explicitly includes nested uploads properties when `part=contentDetails` is
requested. Do not manufacture a playlist ID by transforming a channel string.
The channel allowlist should carry verified channel ID, display name, intended
speaker, positions and language; uploader identity alone does not verify who
speaks in each segment or authorize arbitrary guest attribution.

Request `videos.list` metadata parts `snippet,contentDetails,status` and use
published date, ISO 8601 duration and explicit public status. Missing/invalid
length, unavailable videos, private/unlisted videos and live/upcoming content
are ineligible for this pipeline. This is a proposed filter, not a discovered
video list. Set bounds on pages, accepted duration and videos per run.

The [video resource `snippet.publishedAt`](https://developers.google.com/youtube/v3/docs/videos#snippet.publishedAt)
states: “The date and time that the video was published. This time might be
different than the time that the video was uploaded.” Store `published_at` with
API provenance. A true upload date or recording date stays UNKNOWN without
separate evidence. `contentDetails.duration` is ISO 8601 and may differ from
playback duration slightly, “for example, by 1 second”; duration is metadata,
not evidence that a claimed speech timestamp is correct. Publication time does
not authenticate the video's gameplay patch.

The current [quota guide](https://developers.google.com/youtube/v3/getting-started#quota)
says projects have 100 `search.list` calls, 100 `videos.insert` calls, and
“10,000 units per day combined for all other endpoints.” Default quota is
subject to change. The current costs table describes separate search/insert
quotas; do not copy an old 100-unit search assumption. Search remains unused
regardless of its current cost. Project-specific quota availability is UNKNOWN
until independently verified; invalid requests also consume quota.

## Current Gemini model and documented request format

The [models guide](https://ai.google.dev/gemini-api/docs/models#gemini-3.8-flash)
lists `gemini-3.8-flash` as **Stable**. The current video and structured-output
examples use this model. The [Gemini 2.5 section](https://ai.google.dev/gemini-api/docs/models#gemini_25_flash)
says access to 2.5 models is limited to users who actively used them in the past
and directs new projects to 3.5 Flash-Lite or 3.8 Flash. A stale remembered 2.5
model name is therefore not a suitable new-project availability assumption.
This audit verifies public documentation; actual access in a particular project
remains untested. Pin a specific supported model and source version, and fail
closed on retirement, unsupported response format or missing access.

The [video guide YouTube section](https://ai.google.dev/gemini-api/docs/video-understanding#youtube)
says: “The YouTube URL feature is in preview and is available at no charge.”
It immediately warns: “Pricing and rate limits are likely to change.” It states
that YouTube URLs can be passed directly in the request. The current REST
example uses `POST https://generativelanguage.googleapis.com/v1beta/interactions`
and `input` entries with `{type: "video", uri: "https://www.youtube.com/watch?v=..."}`.
No sample video from the documentation was submitted by this audit.
Use the current documented wire format, with an explicit adapter version;
do not claim an older `generateContent` request shape was verified here.

The same section states: “For the free tier, you can't upload more than 8 hours
of YouTube video per day.” It also states: “You can only upload public videos
(not private or unlisted videos).” Gemini 2.5 and later permit up to 10 videos
per request; the proposed pipeline uses one eligible video per request so input
lineage and failures remain attributable. Full video duration is reserved
before dispatch. Track attempted and uncertain dispatches conservatively,
serialize work for a project, keep processed IDs and prevent retry duplication.
The YouTube-duration statement does not specify its reset timezone; do not
silently equate it to the separate RPD quota's midnight-Pacific reset. A
conservative rolling 24-hour ledger with smaller per-run bounds is appropriate.
Unknown usage by other consumers remains an external limitation.

## Free-only gate and billing uncertainty

The [3.8 Flash standard pricing table](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.8-flash)
lists **Free of charge** for both Free Tier input and output, including thinking
tokens. The same model has paid token rates: input $0.75 and output $3.75 per
million tokens through 2026-12-31, increasing to $1.50 and $7.50 respectively
from 2027-01-01. These prices are dated documentation, not permission to incur
cost. Batch, priority, grounding, caching and paid fallbacks are outside the
proposed free-only request policy unless independently shown free and authorized.
A free YouTube input feature does not prove model output is free on a paid project.

The [billing guide](https://ai.google.dev/gemini-api/docs/billing#projects-api-keys)
is explicit: API keys “have no independent billing settings; they inherit the
tier limits and billing status of the project.” Projects linked to a billing
account inherit its tier. Key presence, a successful model response, a 429, an
8-hour cap, no credits, or a zero-dollar budget alert does not establish that
requests cannot incur charges. The [billing status section](https://ai.google.dev/gemini-api/docs/billing#verify-billing)
points to AI Studio's Projects page Billing Tier and Status columns. A project
can change billing accounts and tiers; old evidence is not current verification.

[Cloud Billing `projects.getBillingInfo`](https://docs.cloud.google.com/billing/docs/reference/rest/v1/projects/getBillingInfo)
is a documented read-only way to retrieve project billing information. It
requires `resourcemanager.projects.get` permission and one of the documented
OAuth scopes (`cloud-platform`, `cloud-billing` or `cloud-billing.readonly`).
A Gemini API key alone is not a documented credential for this authenticated
project-billing check. This audit neither acquired that identity nor invoked
that API. A billing response also needs trusted binding to the actual configured
key's project; a free project unrelated to the key proves nothing.

Therefore a real Gemini request requires current, independently sourced free
project evidence bound to the configured credential's project, a currently
free standard model/input/output policy, and an eligible duration/quota budget.
If that proof is unavailable, use **BLOCKED_EXTERNAL** and continue local
schema, manual-note intake and synthetic transport tests. If documentation or
verified project state shows that the intended request requires payment, use
**BLOCKED_PAYMENT** and state the cost/purpose before seeking the user's paid
exception. Never test an unknown project by making a potentially paid request,
attach billing, automatically upgrade, or fall back to a paid model.

The [rate-limits guide](https://ai.google.dev/gemini-api/docs/rate-limits#current-rate-limits)
says limits depend on tier/account state and “Specified rate limits are not
guaranteed and actual capacity may vary.” RPD limits are per project, not per
key, and reset at midnight Pacific. No fixed RPM/RPD availability is inferred
from public tables. The current API-key guide also describes restrictions and
key-security changes; credentials remain server-side GitHub Secrets and must
never appear in source, URLs, reports or logs.

## Exact collector wire format from current documentation

Two additional official references above were retrieved to verify the response
shape and default storage, The error guidance below brings the documentation audit to 17 sources.
The [Interactions reference](https://ai.google.dev/api/interactions-api#CreateInteraction)
uses `POST https://generativelanguage.googleapis.com/v1beta/interactions`,
`x-goog-api-key` authentication and JSON content. The beta route is the route
actually checked here; do not silently switch API versions.

The following is a proposed combined request **template**, combining the
verified video and structured-output examples. All placeholder values must
come from approved metadata and the local bounded schema. It was not sent.

```json
{
  "model": "gemini-3.8-flash",
  "input": [
    {"type": "text", "text": "BOUNDED_EXTRACTION_PROMPT"},
    {"type": "video", "uri": "CANONICAL_PUBLIC_VIDEO_URL_FROM_YOUTUBE_METADATA"}
  ],
  "response_format": {
    "type": "text",
    "mime_type": "application/json",
    "schema": {"type": "object", "properties": {}, "additionalProperties": false}
  },
  "store": false,
  "stream": false,
  "background": false
}
```

The empty schema above is a placeholder, not the extraction contract. Main owns
its real claims schema and adapter. Exclude tools, grounding, caching requests,
background processing, paid fallbacks and previous-interaction reuse.

The [reference's actual response example](https://ai.google.dev/api/interactions-api#CreateInteraction-simple)
has `object: "interaction"`, `status: "completed"`, and a chronological `steps`
array. A model response step is `{type: "model_output", content: [{type: "text",
text: "..."}]}`. The REST response inspected here is **not** an `outputs` or
`candidates` array. For this narrow nonstreaming extraction path, require a
completed interaction and an unambiguous final model-output text payload, then
parse that payload as JSON and run independent local validation. Reject missing,
ambiguous, failed or changed response shapes. Never save the complete provider
response or thinking/transcript content into the public candidate artifact.

The [Interactions overview retention section](https://ai.google.dev/gemini-api/docs/interactions-overview#data-storage-retention)
says storage defaults to `store=true`, with Free Tier interactions retained for
one day. It explicitly permits `store=false`; that option is incompatible with
background execution and previous-interaction reuse. The proposed collector
therefore opts out of interaction storage and runs a fresh bounded stateless
request per video. This does not alter the Free Tier's separately documented
product-improvement data-use policy and does not guarantee extraction accuracy.

The [official retry guide](https://ai.google.dev/gemini-api/docs/troubleshooting#retry-strategy)
identifies `429 RESOURCE_EXHAUSTED` and `503 UNAVAILABLE` as transient examples
and says to use bounded exponential backoff, while not retrying client errors
such as 400, 402 or 403. It notes that SDKs may automatically retry transient
failures up to four times. For this duration-bounded free-only collector, prefer
explicit REST attempts or disable implicit SDK retries; every retry must reserve
its entire input duration before dispatch. A failed/uncertain request is not a
zero-duration success. Do not repair payment/prepay errors by enabling billing
or retrying a paid project. Record sanitized transport status and failure reason,
not key values, raw model output or a fabricated successful empty extraction.
The guide's wording calls 2.5 models deprecated, while the models guide says
restricted legacy access and not deprecated; this source disagreement reinforces
using the independently documented current 3.8 model rather than assuming 2.5.

## JSON extraction and candidate boundaries

The current [JSON schema documentation](https://ai.google.dev/gemini-api/docs/structured-output#json-schema-support)
configures `response_format` with `type: "text"`, `mime_type: "application/json"`
and `schema`. It supports a subset of JSON Schema. The
[best-practices section](https://ai.google.dev/gemini-api/docs/structured-output#best-practices)
warns: “While output is syntactically correct JSON, always validate values in
your application.” Schema compliance does not verify a speaker's words,
timestamp, gameplay state or coaching conclusion.

Use a strict bounded schema for timestamp, short paraphrase, champion/position,
stage, composition/situation conditions, speech context and measurability.
Apply independent local checks for required fields, unknown enums, extra keys,
text limits, duplicate statements, valid MM:SS and seconds within the metadata
duration. Missing timestamps yield no candidate. Unknown speaker/champion/
position/stage/patch values remain UNKNOWN rather than being invented. Keep
rejected-item reasons and batch failures; an empty or changed provider response
is not evidence of successful extraction.

Accepted records retain canonical video URL, timestamp link, publication date,
short independent paraphrase, context/conditions, model/adapter version,
processing time and input hash. Repeated AI summaries of the same video share
one independent source group. A different upload or speaker is not automatically
an independently verified fact. Store no public transcript or video payload.
All resulting notes and knowledge proposals stay EXPLORATORY with
`visual_verified=false`; only the user can review the original timestamp and
make an actual approval decision. Do not turn free prose into executable rules.
Data comparison needs an explicit measurable metric and eligible Q15/Q18 data;
otherwise report measurement unavailable or insufficient data. No current
expert claim or coaching rule was authored by this source audit.
