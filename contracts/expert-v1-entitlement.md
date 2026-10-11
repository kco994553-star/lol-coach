# Free documentation entitlement refresh — 2026-10-11

Daily collection must not turn yesterday's documentation into a current price
claim. Additive coach_v1/expert_entitlement.py owns
verify_free_entitlement(*,transport=None,clock=None) → {status:VERIFIED_FREE|
UNKNOWN|PAID_REQUIRED,checked_at:UTC ISO date,model:gemini-3.8-flash,
sources:[{url,sha256}],reasons:[fixed codes]}.

Only unauthenticated fixed HTTPS ai.google.dev pricing, video-understanding and
models documentation URLs may be fetched. No keys or model/API calls, redirects
or arbitrary fetch URLs; timeout10s/body2MiB/strictUTF8HTML, bounded stdlib DOM
100knodes/depth128 ignoring script/style. Deterministic selectors established
against the2026-10-11 official source archive: unique pricing model h2, matching
code/link and Standard subsection/table; exact Free Tier column with unique
Input price and Output price (including thinking tokens) cells. Both literal
'Free of charge' plus exact YouTube h3#youtube preview/no-charge notice, free-tier
8hours/day and public-only statements, plus unique matching model card Stable
label ⇒ VERIFIED_FREE. No prose/AI semantic pricing interpretation.

Only a recognized positive currency amount in the exact Free Tier cells under
otherwise valid source scopes ⇒ PAID_REQUIRED; unknown, duplicate, relocated,
unsupported/Not available, network/format/body failures ⇒ UNKNOWN. All fetched
source hashes/dates retained; factual content scope is documentation entitlement,
not configured-project billing proof. User's separate free/no-Billing project
attestation remains mandatory. No paid/model fallback.

Collection CLI obtains this fresh public-source proof before reserve and before
process; passes its status/date to policy_from_runtime as an explicit argument.
VERIFIED_FREE supplies current entitlement unless an explicit false operator
variable disables it. UNKNOWN blocks actual requests; PAID_REQUIRED records
BLOCKED_PAYMENT before any provider request. Unit callers retain injected policy
fixtures and execute no actual acquisition. Persist only safe proof receipt,
never full downloaded HTML in public pipeline artifacts.
