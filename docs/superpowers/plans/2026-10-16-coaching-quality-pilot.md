# Coaching quality pilot Implementation Plan

Goal: seven source-bound conditional advice revisions with honest alternatives
and a verified inventory of existing observations. Spec:
contracts/coaching-quality-pilot-v1.md, user's 2026-10-16 request.
Architecture: additive candidate/review lineage plus a small PC projection;
offline trusted-cache audit exports anonymous descriptive statistics only.
Tech: existing Python, JSON, PC browser and GitHub Actions.

Global constraints: no newmatches/provider/paidcalls; no original packet or USER
changes; no approval inheritance; numeric v1 gate preserved; only affected
verification. Existing source receipts/CI are reused rather than rerun.

- [x] Read latest main/AGENTS/handoff, prior quality assessment, shared ownership;
  distinguish public/full Q15, recall and private encrypted availability.
- [x] Author seven new records in knowledge_candidates/coaching-quality-pilot.json;
  separate evidence and counter review receipts under evidence/quality-pilot/.
- [x] TDD coach_v1/pilot_advice.py and tests_pregame/test_pilot_advice.py:
  exact lineage/source, no promotion, scope/phase, objection and failure fallback.
  Integrate pc_coach.py and topic label in web_r4/pc.js. Main owns integration.
- [x] TDD offline coach_v1/pilot_observations.py and its new tests: real original
  fields, level events vs investment, duplicate/conflict/interval order, exact
  gold/missingness, anonymous-only output. Trusted offline workflow restores only
  existing checkpoint; no Riot env or collector import, always cleans plaintext.
- [x] New scripts/verify_quality_pilot.py binds exact parent hashes/CI and allowed
  delta; required workflows select pilot only. New browser checks revised topic,
  hypothesis label, no inherited auto/duplicate and phase suppression.
- [x] Independent final review, affected29tests/browser and expected-head CI;
  normal implementation PR39 merge68d6a94, postmain all3jobsSUCCESS. Trusted
  offline38890469607 inspected existing89/108, safe report/binding imported and
  independently reconciled. No provider calls or private records downloaded.
- [ ] Result-only evidence publication and postmerge proof: unchanged pilot tests/
  browser reused; validate actual imported source/data/preserved bindings. Only
  missing known-view/POV and game-PC inputs remain external, no whole30 expansion.

Rulings: User's detailed small-pilot directive and inherited autonomous authority
already authorize implementation/publication/gated merges; no renewed design
approval or baseline-suite rerun. Current fresh branch is isolated from main;
no nested worktree or redundant dependency installation. Original scene inputs
are not reconstructed from aggregates; if known-view/POV is absent, report zero.
Sampled seven are fixed from prior random/purpose selection (overlap KR008),
not chosen to maximize passing count. Source claims and action interpretations
are reviewed separately; new versions remain hypotheses.


Final review fix ledger: checkpoint is pinned to existing38410710876/11822391323
and89/108; level event chronology and frame contradictions are UNKNOWN; imported
output requires report/source/checkpoint binding, not just schema validity.
Review-found functional risks were reproduced RED→GREEN in new tests. Two NEW
synthetic event fixtures had inconsistent earlier levels and were corrected;
completed predecessor fixtures/tests are untouched. No deferred minor findings.
