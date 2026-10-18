# Riot game information v1 — additive, not live decision authorization

USER integrated spec applies; retain Frozen Design and earlier contracts. Reuse existing 10pick board, categorical metrics, four independent wave axes, sources/reviews, Windows/manual. No strategy/grade inheritance from item price or API success.

## Functional mapping
|Feature|Source/field|Access/update|Missing/actual proof|
|Riot ID/rank/history|existing ACCOUNT-V1/LEAGUE-V4/MATCH-V5 service|server secret, existing limiter/solo420/private boundary|public API unavailable; no new key present, not expired|
|ten picks|existing Windows champselect adapter/manual input|existing flow|real Windows BLOCKED_EXTERNAL|
|inventory value|allPlayers[].items[].itemID/count/slot + versioned DD gold.total|shared projection; manual public; authenticated PC transport status only|unknown price/patch/count/slot ⇒ total null + partial/omissions; no recursive components|
|cash|activePlayer.currentGold only|same local snapshot|null if missing; no enemy cash inference|
|earned gold|not documented in live sample|Match timeline historical separate|not inferred from inventory/cash; null|
|level/game clock/role|allPlayers[].level / gameData.gameTime / position|same snapshot, role is not coordinates|not wave position or actual jungle route|
|objective events|events.Events EventID/EventName/EventTime|same snapshot, dedup/conflict, future/backward rejected|event history only until patch respawn rules verified; no exact countdown|
|camp timers|no per-camp death/respawn identity coverage in verified sample|unsupported|UNKNOWN, never0|
|ally ultimate timer|sample abilities are active player metadata/level, no ally remainingCD|unsupported|UNKNOWN, never ready0|
|jungle path|no enemy hidden position, no validated route knowledge|static future study queue|no live prediction|

New live service reuses coach_intake.io.fetch fixed loopback2999 endpoint, official CA required, proxy bypass, redirects forbidden, explicit size/timeout. Per-server lock/cache coalesces reads; 1second is IO throttle, not evidence freshness guarantee. Each request rechecks latest transport outcome. Disconnected old values marked STALE, no silent replay as current; a backward game clock replaces session and invalidates prior event history. No raw response/identity logging or persistence. JSON projection strips names/IDs, preserves game/reception clocks and source sample status. This layer is observational; coaching_enabled=false and decision_eligible=false. No dynamic in-game recommendation or overlay policy approval inferred. Real transport/client BLOCKED_EXTERNAL.

Manual public comparison is user-supplied hypothetical inventory, not observation/current match. One entry per held slot; sum count*DDgold.total only, no nested from prices. Empty confirmed inventory0; unknown entry null/partial sum kept. Catalogue total is nominal item value, not cash/spent/earned or power; free/transform cases do not prove acquired gold. Prices only when declared comparison patch major.minor matches archive. No unknown patch coercion, automatic role assignment, winner or new strength score. Item archive immutable/raw hash/provenance reused, not re-collected.

Source-scoped new tactical interpretation appended separately, old claims unchanged. Compact board exposes own/enemy plans and selected wave decisions with existing strength chart and optional Why. Actual source review≠tactical optimality≠N0 real effect. Eight user video URLs remain USER_PROVIDED_PENDING_CONTENT_REVIEW and share existing video ledger; no new schedule/expanded budget. No body claims inferred from title/description.

## Validation and rollback
Meaningful tests: held slots vs nested parts, duplicate/unknown/mismatch/nonfinite/missing values; team counts/partial denominators; names/PUUID absent; events duplicate/conflict/time reversal; coalesced concurrent reads/disconnection state; auth/origin/same-server shared service; public no local requests; PC/mobile manual inputs/results/unknown/reset and existing loading/board regressions. Only affected tests + mandatoryCI; old evidence reused. Normal sourcePR/exactmainCI→explicit allowlist export preserving pro/riot→nativePages/HTTPS changed paths→public UI→results/Handoff. Rollback previous Pages artifact and additive routes/modules; old original sources/grades/Frozen/Windows unchanged.

## Live display boundary
The authenticated /dev/v1/game-info route withholds the internal snapshot (snapshot=null, current=false, display_eligible=false), returning transport status only until actual field coverage and Riot display authorization are confirmed. Server-internal observational projection is not a public/live strategic display approval. Public Pages disables local status calls. Per-server cooldown begins when transport completes, including slow errors; malformed containers/overflow yield structured failures. Champion display names normalize only against the existing hash-verified official roster. Unknown names are omitted. Malformed inventory cannot produce a total; valid unknown-price rows preserve partial amounts, and malformed rows are excluded from partial subtotals; their presence still withholds the complete total.
