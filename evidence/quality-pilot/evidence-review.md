# Quality pilot v2 evidence review

Packet SHA256: `c9645431acbf3dcd66e7fa2c3babe7083f0386f7f469f3364824a52559e5090d`.

Reviewer `/root/pilot_data_scope`, EVIDENCE role. Seven rows and eleven source facts: facts PASS; no unsupported new mechanical facts found. This is one review role, not another AI vote or USER approval.

The corresponding source_facts, sources, source_excerpts and opponent_right are identical to the byte-preserved v1 packet. The initial direct archive-byte hashes, receipt URLs/hashes, locators and document version 16.20.1 checks are reused only for these unchanged facts. The preserved initial receipt and packet remain under `initial/`; they do not approve the v2 actions. No archived-source full rerun or old test-suite rerun occurred.

| Row | Facts | Changed wording inspected |
|---|---|---|
| QP-20261016-KR-001-v2 | PASS | v2는 응수 확인만으로 진입을 정하지 않고 벽 돌진과 돌진 없는 대응을 비교하며 다른 적·아군·체력 조건을 더했다. 새로운 기술 효과·수치·성공 보장은 추가하지 않았다. |
| QP-20261016-KR-005-v2 | PASS | v2는 ID만 바뀌었고 행동 문구는 v1과 동일하다. 새 기술 효과 주장은 없다. |
| QP-20261016-KR-008-v2 | PASS | v2는 반동 뒤 위치의 무조건 우선을 비교 제안으로 바꾸고 긴급 방어 지연 금지를 명시했다. 이는 적용 조건과 순서의 제한이며 새 기술 효과·반동 거리·회피 성공 주장이 아니다. |
| QP-20261016-KR-015-v2 | PASS | v2는 음파 적중 후 일괄 전진 보류를 전진·현재 자리·보이는 아군 쪽 후보 비교로 바꾸고 긴급 대응 예외를 더했다. 이동이 후속 돌진을 끊는다는 주장이나 새 피해 공식·수치는 없다. |
| QP-20261016-KR-021-v2 | PASS | v2는 ID만 바뀌었고 행동 문구는 v1과 동일하다. 새 기술 효과 주장은 없다. |
| QP-20261016-KR-022-v2 | PASS | v2는 아군 근접 대응·팀 계획과 긴급 대응을 고려하는 조건을 더했다. 특정 보호 능력이 실제 존재한다거나 이동 방향·충격파 회피가 보장된다는 새 기계적 주장은 없다. |
| QP-20261016-KR-026-v2 | PASS | v2는 경로 계획을 비교할 시간과 긴급 방어 예외를 더했다. 정찰 범위·시야 지속 시간·적 부재·이동 안전 또는 리신 후속 접근 무효화 효과를 새로 주장하지 않는다. |

New unsupported factual claims: none identified. The new wording changes comparison order, scope and emergency/proximity conditions. It does not add damage, timing, range, immunity, guaranteed escape, vision coverage or safety facts. `unsupported_claims=[]` is limited to that finding.

Top-level `condition_logic` declares choose_if ALL, stop_if ANY and alternatives as options without a safety guarantee. These are proposal rules, not observed game state. Their tactical adequacy is addressed by the separate tactical reviewer.

All actions remain `UNVALIDATED_CONDITIONAL_PROPOSAL`; all seven rows remain HOLD. Static source correspondence proves neither useful/safe/optimal choices nor USER approval or coaching accuracy.
