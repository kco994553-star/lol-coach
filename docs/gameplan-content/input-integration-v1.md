# Composition input integration v1 — 2026-10-24

## Implemented boundary

`coach_v1/gameplan_input.py` adds a pure, offline normalization boundary. Both manual capture and the existing privacy-filtered `LCUDraftAdapter` projection produce `lol-coach-composition-capture-v1`. Its `input` reuses the eight legacy fields accepted by `web_r4/loading-engine.js`: allies/enemies (champion, position), own_champion, own_position, side, patch, opponent_mode, lane_opponent. Catalogue IDs must come from the trusted local roster; this layer does not resolve arbitrary names or fetch anything.

Unknown positions remain null. No role is inferred from champion popularity, ordering, or team composition. Incomplete teams and unknown self/side remain inspectable with `ready=false`; duplicate champions/confirmed roles and conflicting self roles fail validation. Opponent roles may be unknown while an otherwise complete input is ready, matching the existing evaluator. Null patch remains explicitly unknown. LCU hover or unconfirmed lock state is not a completed pick. Leaving ChampSelect discards the composition rather than silently carrying it into an unrelated game.

Source metadata is outside the legacy evaluator input: caller-generated opaque session token, revision, monotonic observation time, age and current flag. Negative age or expired transport liveness blocks readiness. The default two-second limit is a connection deadline only. A new game/connection must receive a new session token; revisions alone are not a match identity. This stateless boundary does not generate or verify game identity. Never pass a player identifier, credential fingerprint or lockfile data as session_id. All return structures are detached. No network, polling, new endpoint, public display, account lookup or tactical live authorization is added. `live_coaching_enabled` is always false.

## Existing connectors and remaining wiring

- `pc_runtime.PCServices` already polls the pinned local `LCUDraftAdapter`, projects the earlier draft-capture schema via `draft_input`, and expires connection state after two seconds. Its adapter reads only gameflow phase/champion-select session, then confirms phase again. It discards identities and does not acquire a game-entry composition.
- `game_info.GameInfoService` already has a local HTTPS observational transport and safe champion/role projection. Its current projection has no self-player linkage. It marks actual_client_verified=false and freshness_verified=false. `/dev/v1/game-info` deliberately returns snapshot=null and display_eligible=false. These gates are preserved.
- Match-v5 collection and historical anonymous datasets do not constitute current-session identification, ten live picks, or live coaching validation.

The authenticated existing `GET /dev/v1/pregame/pc-status` now adds `gameplan_input` from the already captured privacy-filtered slots. Existing connection/review/weekly fields and polling remain unchanged. Current captures lack trusted session identity, observation time, pick finality and side, so this preview remains `ready=false` with explicit reasons. Outside ChampSelect, stale or fallback captures produce no usable input. A later game-entry bridge still needs evidence-backed self/session linkage and real-client coverage; do not join by champion alone or retain a draft across sessions. Manual choices remain authoritative. Raw Live Client responses are never exposed.

## Observed environment and external blocker

Read-only local check on 2026-10-24 produced platform=Linux, os.name=posix, native_discovery_available=false, discovered_lockfile=false, live_ca_configured=false. `discover_lockfile()` exits immediately on non-Windows; no directories, processes, credentials, private account files or local ports were probed. This is evidence that this execution host has no configured native Windows client integration; it is not evidence about the user's separate desktop. No actual-client successful read occurred. Real auto-fill remains BLOCKED_EXTERNAL, not complete.

A user's game-PC capture must verify ten champion slots, available roles (unknown stays unknown), self linkage, same-session transition, freshness/disconnect/reset, and manual fallback with anonymous evidence. Synthetic tests demonstrate boundary behavior only. No full-suite, publication, commits, or external writes were performed for this subtask.

## Official sources checked 2026-10-24

- [Riot League documentation](https://developer.riotgames.com/docs/lol), League Client API section: LCU is local and not officially supported for third-party applications; Riot asks developers to disclose endpoints/use through the Developer Portal. The local Game Client API is HTTPS/native-only; Live Client Data provides active-game data. These facts do not guarantee role/self coverage in this application's projection or approve its display.
- [Riot general policies](https://developer.riotgames.com/policies/general), last-updated label May 29, 2025: registration/audit applies to products and feature changes; supported ingestion is preferred. The game-integrity restrictions require retaining player decisions and prohibit unfair advantages/de-anonymization. League-specific integrity policy also excludes hidden-player analysis and unavailable competitive information. No product audit status was inspected or inferred.

The historical 2019 LCU announcement surfaced in search, but is not used to declare current region authorization. The current official documentation above is the basis for the limited claims here. Existing live display gates remain in force; this adapter does not certify compliance.

## Historical observation readiness (local receipts, not new collection)

| Local evidence | Recorded coverage | Meaning / limitation |
| --- | --- | --- |
| data/coaching_quality/2026-10-16/import-receipt.json and source-binding.json | REAL; 89 matches; 108 participant observations; 0 duplicate participant entries; source_binding_valid=true | Receipt records offline import; coaching_accuracy=null. No independent re-download or gameplay efficacy claim. |
| data/recall/2026-10-15/pro/collection-receipt.json | 89 reused unique matches; 108 participant observations; EXTRACTED | Same underlying observations; do not add to the quality-pilot total. Roster provenance is not all-player professional-rank verification. |
| data/recall/2026-10-15/challenger/collection-receipt.json | 291 matches; 2910 participant observations; HAS_OBSERVATIONS | Collection status BLOCKED_EXTERNAL / DEADLINE_EXHAUSTED; challenger seed selection does not verify all participant ranks; coaching_accuracy=null. |
| data/pro_reference/2026-10-13/collection-receipt.json | 87 unique recorded matches; 25 selected; READY | Earlier distinct receipt scope; roster USER_REPORT_NOT_NETWORK_VERIFIED; tier UNKNOWN. Not combined with later receipts. |

These are safe aggregate receipt observations, not proof that all private raw files are available on this host or that a matchup recommendation works. Queue42 historical-data readiness is partial; gameplan efficacy remains unmeasured.

## Verification

`python -m unittest tests_pregame.test_gameplan_input -v`: six focused tests passed. They cover manual/automatic normalized parity, detached results, unknown role preservation, stale/future observations, session metadata, forbidden live source, conflicts/private extra fields, hovered picks, disconnection and disabled live coaching. Fixtures are synthetic; the server contract test uses authenticated localhost HTTP and verifies 401 without credentials. No external network is used.
