# Cause diagnosis implementation plan

> For agentic workers: follow systematic debugging and test-driven development; Main integrates isolated parallel work. User has already authorized autonomous execution and normal gated merge.

**Goal:** Diagnose Riot front responses and make the user-directed Gemini generateContent request without wasting video quota.
**Architecture:** Independent transport changes consume the additive contract. Main owns contracts, workflow gates, CLI receipts and final evidence.
**Tech Stack:** Python standard library, curl, trusted GitHub Actions.
**Spec:** contracts/cause-diagnosis-v2.md and latest user decision.

## Global constraints
Free only; no credentials/raw responses/player identifiers published; archived/Frozen history immutable. One shared execution claim. Four total TEXT attempts maximum only for503, zero VIDEO retries; one first <=600s clip of <=1200s video.

## Review focus
- Credential/header/body echoes must redact before bounding.
- Invalid key must suppress both diagnostic clients and collection.
- Mixed pair statuses must suppress further collection.
- Exhausted TEXT503 or malformed200 must not reserve video.
- Archived plans and failed quota history must not be reinterpreted/refunded.

## Task 1 Riot — q15_stats
Files: coach_v1/riot_collector.py, new coach_v1/riot_front_diagnostics.py, scripts/diagnose_riot_front.py, tests_pregame/test_riot_front_diagnostics.py and affected Riot tests. Public pair JSON produces statuses and safe403 fields; Main workflow consumes READY.
- [x] Add meaningful failing UA/pair/echo/mixed-status/invalid-shape tests; save RED.
- [x] Implement bounded pair and all-request UA; save GREEN and commit isolated scope.

## Task 2 Gemini — v14_server
Files: coach_v1/expert_collector.py and affected tests_expert collector tests. Official source audit freezes exact generateContent field/parser mapping before implementation. CLI consumes existing probe/plan interfaces with additive route/retry receipt fields.
- [x] Add failing generateContent payload/parser/TEXT503-only retry/legacyplan/quota tests; save RED.
- [x] Implement v4, official request/response and bounded retry; save GREEN and commit isolated scope.

## Task 3 Main integration and publication
Files: workflow pair gate, expert CLI route-safe receipts, launcher test minimums, decision/handoff/evidence.
- [x] Verify both source audits/commits and add integration tests where contract changes.
- [x] Run affected suites and required source-bound CI; independent review; normal merge exact verified head.
- [x] Dispatch one trusted Riot pair and one trusted generateContent acquisition, inspect safe outcomes; use actual-data browser runner only when accepted real data exists.
- [x] Preserve actual outcomes/history and exact PR24 CI/source proof; actual detail14/five-role36 PASS, exact anonymous archives prepared.
- [ ] Fresh archivepublication CI/normalmerge and exact final common-claim terminal release.
