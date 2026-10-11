# Q19 current free documentation entitlement

`coach_v1.expert_entitlement.verify_free_entitlement(*, transport=None, clock=None)`
refreshes the public documentation proof for the pinned `gemini-3.8-flash` model.
The authority is the additive [contract](../../contracts/expert-v1-entitlement.md).
It never reads credentials, infers project billing, calls a model, downloads a
video or requests a transcript. The configured project's separate user
FREE_TIER attestation and exclusive rolling 24-hour quota ledger remain required.

The exact result keys are `status`, `checked_at` (current UTC ISO date), `model`,
`sources` (ordered `{url, sha256}` receipts), and `reasons` (safe fixed codes).
`VERIFIED_FREE` means current documentation establishes the specified entitlement;
it does not guarantee the Secret belongs to a free project. `UNKNOWN` blocks
collection as BLOCKED_EXTERNAL. A recognized positive dollar price in a required
Free Tier cell under otherwise verified scopes produces `PAID_REQUIRED`, which
blocks collection as BLOCKED_PAYMENT. There is no paid or alternate-model fallback.

Only these three fixed unauthenticated HTTPS URLs are fetched, in this order:

1. <https://ai.google.dev/gemini-api/docs/pricing>
2. <https://ai.google.dev/gemini-api/docs/video-understanding>
3. <https://ai.google.dev/gemini-api/docs/models>

Each request has a 10s network timeout, no redirect following, a 2MiB body cap,
exact response URL/HTTP200/text-HTML checks, and strict UTF-8 decoding. The stdlib
DOM caps 100,000 element nodes and depth 128 and ignores script/style text. Only
selector-relevant duplicate attributes (`id`, `class`, `href`, `colspan`,
`rowspan`) invalidate parsing. Official navigation repeats unrelated analytics
attributes; those do not establish evidence. Transport exceptions and document
ambiguities produce safe codes without exposing provider response/error text.

Deterministic selectors preserve the established official document scopes:

- Pricing: unique `h2#gemini-3.8-flash`, matching model code/link, through the next
  model heading; unique Standard section and `table.pricing-table`; exact
  `Free Tier` column in the table header; unique `Input price` and `Output price
  (including thinking tokens)` rows. Both cells must read `Free of charge`.
  The Paid Tier, Batch, other-model and grounding cells cannot supply this proof.
  Unsupported cells, including `Not available` or `$0.00`, stay UNKNOWN. Only
  literal positive dollar decimals, optionally followed by `per 1M tokens`, are
  recognized as positive charges. No prose interpretation is used.
- Video: unique `h3#youtube`, following siblings until the next h2/h3 (nested
  sample headings do not end the section), unique `aside.preview` whose normalized
  text is exactly `Preview: The YouTube URL feature is in preview and is available
  at no charge. Pricing and rate limits are likely to change.` Required unique
  list statements are `For the free tier, you can't upload more than 8 hours of
  YouTube video per day.` and `You can only upload public videos (not private or
  unlisted videos).` HTML entities and whitespace are normalized.
- Models: unique matching `a.gemini-card-centered` model URL, matching model h3,
  and unique `p.status-subtext`. Only a known `span.gemini-api-new` containing
  `New` is omitted; the remaining status must be exactly `Stable`.

Any required fetch or scope failure takes precedence over a positive price in
another verified document. Safe reason codes are `DOCUMENTED_FREE_ENTITLEMENT`,
`FREE_TIER_POSITIVE_PRICE`, and the combinations
`PRICING|YOUTUBE|MODEL` + `_SOURCE_UNAVAILABLE|_SCOPE_UNVERIFIED`.
The injected transport receives `(url, timeout=10, max_bytes=2097152)` and returns
`{status, body:bytes, url, content_type}`. The injected clock returns an aware
datetime. These injection points support offline tests, not production bypasses.

## Verification receipt

Tests first failed because the new module did not exist. The initial live parsing
failure identified duplicate analytics attributes in official navigation; a new
authored regression fixture failed before the selector-only duplicate check was
implemented. All 13 offline tests then passed. Fixtures contain small authored HTML
layouts and omitted code examples, no full documentation or transcripts.
The archived 2026-10-11 source snapshots also passed the same selectors.
The complete expert test suite at the assigned baseline passed all 56 tests
without skips (`python -m unittest discover -s tests_expert -v`).

An authorized unauthenticated public-document refresh completed at
`2026-10-11T06:40:06.260103+00:00`, yielding `VERIFIED_FREE`, checked_at2026-10-11,
and `DOCUMENTED_FREE_ENTITLEMENT`. Source hashes were:

| Source | SHA256 of fetched HTML |
| --- | --- |
| pricing | `056708fb61023e897427391083ab63307b12c5f2a646d9a0f27fc6d0ae1fb023` |
| video-understanding | `08088be2d548316a1a40e8d17039a62ecb50e5a65042c70cdd423c6f7c03ff58` |
| models | `f62e31b43561e08875282e1b2c95e4da2fdef4bd25c5437511344ad85c7d9a05` |

HTML hashes can change with dynamic site markup. A hash is a receipt of fetched
bytes, not a permanent allowlist. The literal scoped selectors are rechecked
every time. No YouTube Data API or Gemini model calls occurred in these tests or
this refresh. No HTML body is retained in public pipeline artifacts.

## Supplemental official Google REST key-header source

Source 18 supplements the immutable original 17-source audit without modifying it.
Requested <https://cloud.google.com/apis/docs/system-parameters> redirected to
<https://docs.cloud.google.com/apis/docs/system-parameters>; retrieved
`2026-10-11T06:36:38Z`, page updated 2026-10-09 UTC, raw HTML SHA256
`ee1e59d7c6e8e5995510e657c7aec56a548618ad4dc26f449bc3c4b624429076`.

The opening scope says: "These parameters are available across all Google REST
APIs and gRPC APIs. A system parameter can be specified either using an HTTP
query parameter or an HTTP header." The system-parameter table maps `$key`,
`key` to HTTP header `X-Goog-Api-Key`, description `Google API key.` This supports
the collector's header-only YouTube REST key policy through the official general
Google REST rule. It is not a YouTube-specific example or an actual authenticated
endpoint acceptance test. This supplemental source is not fetched by the runtime
entitlement verifier, whose three source URLs remain fixed.
