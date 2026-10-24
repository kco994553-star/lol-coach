# Gameplan direction hierarchy — bounded GP-0.6 implementation

Goal: make champion baseline goals visible before existing composition coaching, without claiming every matchup is supported.
Architecture: additive direction_hierarchy in loading-planboard, attached after situation reconciliation. Existing summaries and decisions remain authoritative; presentation consumes the same explanation. No independent view tactics.
Stack: existing JavaScript generator + Python unittest/Node contracts.
Specification: LoL_Coach_Gameplan_Spec v0.4 GP-0.6.1–6, GP-0.8, GP-3.7 (partial slice).

## Scope and constraints
- Versioned BOTTOM Caitlyn/Ezreal baseline profiles by phase, backed by retained official mechanics; strategic interpretation remains unreviewed.
- Link existing composition response/pressure and state decisions, explicitly limited classification when comparison is not implemented.
- Visible baseline lead-in must not assert current skill availability, lane superiority, first push, or actual mid-lane opponent.
- Unsupported ally links, missing mechanisms, source mismatch and manual opponents remain limited. Other roles retain authored plans.
- No protected knowledge, runtime AI, billing, scheduler or approval changes.

## Tasks / ledger
1. [x] Intake main/open PR/canonical claim; baseline coaching tests (17 passed).
2. [x] Add failing tests for profiles, composition changes, assumptions, unsupported scope and projection.
3. [x] Implement profile contract and post-reconciliation attachment.
4. [ ] Run coaching, planboard and presentation tests; render responsive screen where available.
5. [ ] Fresh independent review; address findings; publish reviewable PR and release claim.

## Review focus
No increased tactical coverage; no learned-skill/current-state claims; no contradictory lead-in under constrained assumptions; no fixed unsupported change classification. Verify input and other role outputs unchanged.

Validation: 52 targeted tests pass after independent review corrections. Browser download failed (invalid archive), so responsive rendering remains pending CI. composition is explicitly the pre-waiting scenario plan, not state-free analysis.
