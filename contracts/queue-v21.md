# Queue v2.1 — 2026-10-15 사용자 결정

## 경계와 등급
기존 350개 후보, 원본 30개, USER 결정과 동결 계약은 변경하지 않는다.
새 `auto-review.packet.v1`은 원본 후보와 명세 해시를 연결한다. 후보 해시는
`candidate_sha256`·`source_excerpts`를 제외한 후보의 정규 JSON SHA256이다.
근거 검사와 반론 검사는 작성자와 다른 역할의 별도 에이전트다. 다수결은 없다.
검사 산출물은 패킷 원본 해시·후보 해시·역할·검토자·항목별 사유를 보존한다.
모든 기계 검사와 두 역할 검사 PASS만 AUTO_VERIFIED다. 누락·실패는 HOLD다.
AUTO_VERIFIED는 KnowledgeStore REVIEWED로 변환하지 않으며 USER 행을 만들지 않는다.
자동 검토는 출처와 반례의 한정된 검토이며 코칭 정확도 보장이 아니다.

## 화면 투영
기존 저장 계획은 그대로 둔다. 별도 `pc-coach.v1`은 엄격한 경기 전 입력에서
공식 사실·통계·USER·AUTO_VERIFIED·EXPLORATORY 내용을 근거 수준별로 투영한다.
가설은 출처 원문을 해시로 확인한 항목만, 조건과 보류 이유를 붙여 보여준다.
패치 미확인·불일치 자료는 참고용이라고 표시하고 전술 카드에는 적용하지 않는다.
UNKNOWN/게임 중에는 전술을 노출하지 않는다. 공식 정적 설명은 참고용으로 남긴다.
사용자 이의는 별도 이력으로만 기록하고 해당 후보를 모든 투영에서 즉시 제외한다.
사용자 승인 이력은 변경하지 않는다. 과거 계획도 새로운 투영 시 이의를 반영한다.

## 공통 HTTP 계약
인증·동일 출처 보호는 기존 로컬 서버와 같다. 접두사는 `/dev/v1/pregame`.
- POST `/pc-preview`: `{input:<기존 엄격한 InputDraft>,draft_revision?:<정수>}`.
  응답 `{schema_version:'pc-coach.v1',phase,stage,patch,cards:[{id,title,evidence_level,
  evidence_label,lines:[최대3줄],details,sources,patch_status,candidate_id?}],
  counts:{...등급별 수},review_summary:{passed,held,reasons},draft_revision}`.
  `stage`: OWN / LANER / JUNGLE / COMPOSITION / EMPTY. `details`는 문자열이다.
- GET `/pc-status`: `{connection:<LCU snapshot>,review_summary,weekly_report}`.
- POST `/pc-objection`: `{candidate_id,reason,candidate_sha256}`. 실제 사용자 버튼만 호출.
  거짓 USER 승인을 만들지 않으며 자동 시스템은 이 엔드포인트를 호출하지 않는다.
- GET `/official-catalog`: 전체 공식 한국어 설명. POST는 `{champions,patch}`.
  기존 official-reference.v1 응답과 호환된다.

## PC 화면·연결
새 `/pc`는 PC 우선 경량 화면이다. 기존 `/pregame` 편집·저장·복원은 유지한다.
LCU poll 결과는 선택·확정·역할·밴·단계만 남긴다. 계정 정보를 요청/저장/표시하지 않는다.
연결 자격은 서버에만 두며 loopback·명시 pairing·인증서 지문을 확인한다.
연결 실패 시 수동으로 전환하고 이유를 기록한다. 실제 PC 검증만 BLOCKED_EXTERNAL.
Windows 시작 도구는 설치·실행·바로가기·접속키 fragment 자동 연결을 제공한다.
접속키는 URL query/서버 로그에 남기지 않고 브라우저에서 fragment를 즉시 지운다.
공식 자료는 매일 갱신 확인, 버전별 원문 보존. 주간 무작위 최대 5개는 로컬 보고서로 보존한다.

## 검증과 보고
근거 검사는 원문 발췌를 비교, 반론 검사는 실제 Q15 측정 가능 주장만 비교한다.
전문가 근거는 서로 다른 발언자 두 명 이상이 필요하다. 같은 영상 요약은 한 출처다.
출처 해시·URL·자료 패치와 적용 패치를 검증하며 근거 없는 수치는 허용하지 않는다.
실제 브라우저로 입력부터 카드 렌더까지 시간을 측정한다. 합성 입력과 실제 PC를 구분한다.
보고 첫 다섯 줄은 된 것·안 된 것·사용자 할 일을 쉬운 한국어로 적는다.
