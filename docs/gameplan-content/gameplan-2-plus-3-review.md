# 게임플랜 2+3 비판 검토 대장
2026-10-25 · A~G 각 2개 반례의 사전/사후 기록 틀. **미실행 반례의 사후 결과는 PENDING**이며 설계 검토가 테스트 통과를 뜻하지 않는다. 입력v5 및 최대2태그는 작성자 구현 선택, 2+3 방향은 사용자 승인이다. 실제 사례·명령·SHA와 연결한 후 상태를 갱신한다.

심각도 P0 허위 관측/출처/승인/계약 손상, P1 위험 판단 모순·핵심 흐름 실패, P2 제한 누락·사용성, P3 선택 개선. P0/P1은 해당 출시만 막고 독립 작업은 계속한다. 근거 없이 문제 없음/PASS로 종료하지 않는다.

| 문제ID | 문제/근거 | 확정 요구 또는 제안 | 사전 반례 | 심각도 | 판정/변경 범위 | 수용 기준 | 사후 재검토/상태 | 증거·명령 | 비용·의존성·실패 영향·재개 |
|---|---|---|---|---|---|---|---|---|---|
| A-01 | 사용자 승인과 제안이 섞임; spec의 확정/설계/태그 정책 절 | 확정 방향 + 세부 구현 제안 | unknown을 관측으로 기본화 | P0 | 분리/유지; GP23 A 묶음 | 03/04 매핑과 authority 확인 | 문서 대조 완료; 런타임 판단 검증은 별도; DOCUMENT_REVIEWED / runtime PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 문서 유지 비용 낮음; 승인 오염 영향 큼; 해당 묶음 구현 후 같은 반례 재실행 |
| A-02 | 사용자 승인과 제안이 섞임; spec의 확정/설계/태그 정책 절 | 확정 방향 + 세부 구현 제안 | 최대2태그를 USER 전술 승인으로 표시 | P0 | 분리/유지; GP23 A 묶음 | 03/04 매핑과 authority 확인 | 문서 대조 완료; 런타임 판단 검증은 별도; DOCUMENT_REVIEWED / runtime PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 문서 유지 비용 낮음; 승인 오염 영향 큼; 해당 묶음 구현 후 같은 반례 재실행 |
| B-01 | 출처/출력 계약·신선도 혼동; root registry와 manifest, input-integration, presentation-v1 | 사실 보존 + 호환 선택 제안 | 2초 transport를 정글 TTL로 적용 | P0/P1 | 수정; GP23 B 묶음 | URL/patch/hash/time 기록; 버전별 regression | 로컬 자료/경로 기록 완료; 새 schema compatibility 미실행; DOCUMENT_REVIEWED / runtime PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 호환 bridge/테스트 비용 중간; 구형 공유 입력 영향; 해당 묶음 구현 후 같은 반례 재실행 |
| B-02 | 출처/출력 계약·신선도 혼동; root registry와 manifest, input-integration, presentation-v1 | 사실 보존 + 호환 선택 제안 | 새 input을 기존 소비자가 읽지 못함 | P0/P1 | 수정; GP23 B 묶음 | URL/patch/hash/time 기록; 버전별 regression | 로컬 자료/경로 기록 완료; 새 schema compatibility 미실행; DOCUMENT_REVIEWED / runtime PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 호환 bridge/테스트 비용 중간; 구형 공유 입력 영향; 해당 묶음 구현 후 같은 반례 재실행 |
| C-01 | 정글 위치 하나로 웨이브 행동 강제; GP23 lane contract; 기존 planboard wave | 확정 방향; 선택 모델 제안 | stale 정글을 반대편으로 취급 | P1 | 추가/수정; GP23 C 묶음 | 가능 행동·자원·지원·다이브·대기 비용 반례 | 재검토 PENDING; 새 엔진 실행 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 규칙/우선순위 변경 비용 중간; 잘못된 wave 지시 영향 큼; 해당 묶음 구현 후 같은 반례 재실행 |
| C-02 | 정글 위치 하나로 웨이브 행동 강제; GP23 lane contract; 기존 planboard wave | 확정 방향; 선택 모델 제안 | 정글 근처+큰 웨이브에 무조건 방치 | P1 | 추가/수정; GP23 C 묶음 | 가능 행동·자원·지원·다이브·대기 비용 반례 | 재검토 PENDING; 새 엔진 실행 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 규칙/우선순위 변경 비용 중간; 잘못된 wave 지시 영향 큼; 해당 묶음 구현 후 같은 반례 재실행 |
| D-01 | 명목 인원/직업명만으로 교전 고정; GP23 fight contract; profile/reference scope | 확정 목표·위협·행동 순서 | 적 핵심기 상태 미상인데 소모 확정 | P0/P1 | 추가/수정; GP23 D 묶음 | 실효 인원/도달성/목표 전환/중단 | 재검토 PENDING; 새 엔진 실행 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 전투 문맥/정성 판단 비용 중간; 반례 지원 범위 제한 필요; 해당 묶음 구현 후 같은 반례 재실행 |
| D-02 | 명목 인원/직업명만으로 교전 고정; GP23 fight contract; profile/reference scope | 확정 목표·위협·행동 순서 | 3v2라도 후속 불가/보호 대상 방치 | P0/P1 | 추가/수정; GP23 D 묶음 | 실효 인원/도달성/목표 전환/중단 | 재검토 PENDING; 새 엔진 실행 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 전투 문맥/정성 판단 비용 중간; 반례 지원 범위 제한 필요; 해당 묶음 구현 후 같은 반례 재실행 |
| E-01 | 상하단/태그·본문 불일치 및 핵심 접힘; presentation-v1; 2+3 visible core 요구 | 확정 2+3 + 태그최대2 제안 | 조건 변경 후 오래된 태그 잔류 | P1 | 수정/제거 후보; GP23 E 묶음 | 같은 judgment 소비/원자 갱신; actual screen 검사 | 재검토 PENDING; 320/390/200%/키보드 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 중복 정책 제거는 코드 확인 후; UI검사 비용 중간; 해당 묶음 구현 후 같은 반례 재실행 |
| E-02 | 상하단/태그·본문 불일치 및 핵심 접힘; presentation-v1; 2+3 visible core 요구 | 확정 2+3 + 태그최대2 제안 | 상단 push/하단 pull 또는 핵심 중단문 숨김 | P1 | 수정/제거 후보; GP23 E 묶음 | 같은 judgment 소비/원자 갱신; actual screen 검사 | 재검토 PENDING; 320/390/200%/키보드 필요; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 중복 정책 제거는 코드 확인 후; UI검사 비용 중간; 해당 묶음 구현 후 같은 반례 재실행 |
| F-01 | 잘 나온 문장만 선별/편집해 실제 출력 주장; queue35~39; before raw5 | 확정 원문/재현/역할균형 | 미지원/누락 정보를 결과에서 숨김 | P0 | 추가/보류; GP23 F 묶음 | seed/input/output/prose/SHA/coverage/one-variable pair/6축점수 | 재검토 PENDING; before 원문은 별도 보존; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 원문/평가 실행 비용 중간; 내부점수≠실경기효과; 해당 묶음 구현 후 같은 반례 재실행 |
| F-02 | 잘 나온 문장만 선별/편집해 실제 출력 주장; queue35~39; before raw5 | 확정 원문/재현/역할균형 | 낮은 총점 대신 수동 문구 개선을 엔진 결과로 교체 | P0 | 추가/보류; GP23 F 묶음 | seed/input/output/prose/SHA/coverage/one-variable pair/6축점수 | 재검토 PENDING; before 원문은 별도 보존; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 원문/평가 실행 비용 중간; 내부점수≠실경기효과; 해당 묶음 구현 후 같은 반례 재실행 |
| G-01 | 과거 CI·배포·영상 링크를 새 완료로 승계; queue40~44; old release receipt; learning taxonomy | 확정 증거/상태 분리 | 과거 pages success를 새 SHA deploy로 기록 | P0 | 분리/추가; GP23 G 묶음 | 새 SHA 검사/브라우저/배포·권한·rollback; 실제게임 N 별도 | 재검토 PENDING; CI/live/deploy는 상위 인계 소유; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 외부 권한/환경 의존은 해당 작업만 BLOCKED; 나머지 계속; 해당 묶음 구현 후 같은 반례 재실행 |
| G-02 | 과거 CI·배포·영상 링크를 새 완료로 승계; queue40~44; old release receipt; learning taxonomy | 확정 증거/상태 분리 | taxonomy80을 확보/승인80으로 표시 | P0 | 분리/추가; GP23 G 묶음 | 새 SHA 검사/브라우저/배포·권한·rollback; 실제게임 N 별도 | 재검토 PENDING; CI/live/deploy는 상위 인계 소유; PENDING | 문서/rg/manifest 확인; 새 반례 실행 NOT_RUN | 외부 권한/환경 의존은 해당 작업만 BLOCKED; 나머지 계속; 해당 묶음 구현 후 같은 반례 재실행 |

## 묶음별 더할 것 / 뺄 것 / 고칠 것 / 지금 하지 않을 것

| 묶음 | 사용자에게 주는 판단 | 더할 것 | 뺄 것 | 고칠 것 | 지금 하지 않을 것 |
|---|---|---|---|---|---|
| A | 이번 판 2+3의 의미와 지원 한계를 정확히 이해 | 확정/제안/unknown 분리, 기존 ID 매핑 | 승인·완료로 오해되는 표현만 | 옛 queue44와 새44 혼동 | 사용자에게 승인한 방향 다시 질문 |
| B | 같은 정보에서 같은 근거·불확실성을 읽음 | 출처/시각/상태/호환 기록 | 중복 정책은 실제 확인 후 제거 후보 | transport freshness와 tactical validity 혼용 | 미확인 권한·라이선스·실시간 cadence 단정 |
| C | 가능한 웨이브 행동과 전환을 선택 | 자원/지원/다이브/대기 비용 | 정글 위치만으로 무조건 push/pull | trade와 wave 목표 충돌 | 근거 없는 성공률·ETA |
| D | 나의 목표·위협·공격/보호/이탈 조건 파악 | 문맥/실효 기여/도달성/탱커 전환 | 적 전원 나열·무조건 진입/회피 규칙 | nominal 수적 우세 일반화 | 전체 챔피언 전술 검증 주장 |
| E | 상단 방향과 하단 행동을 바로 읽음 | 2+3/동일 결과 태그/화면검사 | 중복 문장·추상 filler·죽은 정책 경로만 | stale 표시·핵심 접힘·320폭 잘림 | 근거 없이 디자인 수치 확정 |
| F | 원문5건의 성공/실패/한계를 비교 | 재현 입력/버전/쌍비교/내부평가 | 결과 선별/수동 교정 위장 | 낮은 품질 규칙 또는 지원 범위 | 내부 점수를 실경기 효과로 표시 |
| G | 검증/출시/잔여 제한을 구분 | 새 SHA receipts/rollback/정확한 인계 | 과거 성공을 신규 성공으로 복사 | 관리표/그래프/Notion과 실제 상태 불일치 | 무권한 배포·보호된 결정 쓰기·게임 효과 승격 |

## 학습실 추가 검토
- L-01 (P0): 링크만 있는 영상에 transcript/frame/source_patch/visual review를 만들어 넣지 않는다. video_start_ms와 game_clock_ms를 구분하고 당시 플레이어가 모르는 관전자 정보를 판단 근거로 소급 주입하지 않는다. 수용: unknown/null과 evidence kind가 원문까지 왕복. 사후 PENDING / 실제 영상 N=0.
- L-02 (P0/P1): 같은 구간의 다른 주제 카드는 같은 source segment를 참조하고 claim 승인을 복제하지 않는다. 개인 notes와 공개 index를 분리하며 새 lesson candidate는 coaching_enabled 자동 승격 금지. 수용: 중복/권한/공개export/게임플랜 연결 반례. 사후 PENDING.
- L-03 (P2): taxonomy80/검색/필터/원본시점/복귀/빈결과/삭제/오류와 320/390/200%/키보드를 실제 확인. 사후 PENDING. 새로운 콘텐츠 표본이나 taxonomy 일치도는 실측 전 N=0.

## 첫 검토 → 수정 → 재검토 운용
문서/경로 감사의 수정은 root6문서와44행 상태 대장에 반영했다. A/B 문서 재검토는 아래 무결성 명령으로 수행한다. C~G/학습실의 실제 제품 반례 결과는 구현 담당자가 입력/원문/명령/결과/SHA를 붙이기 전 PENDING이다. 새 P0/P1이 생길 때만 추가 순환한다. 총점으로 P0/P1을 상쇄하지 않는다.

재개: `git diff --check` → 상태44행 고유/필수차원·검토14개 확인 → 구현 파일과 정확 입력 검토 → 해당 scoped tests → 실제 browser → 원문/점수 → CI/배포 receipts. 마지막 두 작업은 상위 실행자 소유이며 이 문서 변경이 통과를 대신하지 않는다.

문서 사후 확인: 상태 고유44행/필수6차원/A~G14반례/기존 matrix160행 구조 검사 통과. 소유8문서 scoped diff-check exit0. 두 공식 archive manifest의 SHA-256이 current pointer와 일치함을 로컬 확인했다. 이는 A/B 기록의 구조·보존자료 무결성만 검사하며 신규 판단/호환/브라우저 반례의 사후 성공이 아니다.

변경 전 비교 기준: 상위 실행자 full baseline906 tests /139.905s OK(`gp23-artifacts/baseline.log`), UI 감사62 tests /9.497s PASS 및 actual current DOM desktop1440/mobile390 두 viewport(`ui-baseline-browser/result.json`). 이 수치는 변경 전 회귀 기준선이며 C~G의 신규 제품 사후 결과를 PASS로 바꾸지 않는다.
