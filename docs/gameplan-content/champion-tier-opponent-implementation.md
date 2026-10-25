# 챔피언 티어·상대 통계 확장 실행 대장

기준 main d1d00053dfd3710bb94e08549c7ca256ab0c43ee. GP23/학습실 출고 이후 별도 사용자 지시이며 그 44개 완료 이력에 합산하지 않는다. 기존 IA160 번호·원자료·승인·실패 이력을 보존한다.

| 작업 | 기능 ID | 구현·의존성 | 수용/반례 | 현재 상태 |
|---|---|---|---|---|
| CT01 조사/계약 | 2.2,2.4,7.2 | 기존 tier schema와 Master+ admission, 원문·실제 소스 추적 | 과거 outcome/power로 cross-role 승패 복원 불가 | DOCUMENTED |
| CT02 밴드·집계 | 2.2.1,2.2.4 | MASTER_PLUS/ALL/10tiers; unique hash와 승패 재계산 | 중복/patch충돌/누락티어/평균승률 금지 | IMPLEMENTED/targeted tests |
| CT03 결과 동반자료 | 2.4,7.2 | 비공개 해시·양 팀 역할·승리 팀, 공개 집계만 | 모르는 역할 추정 금지, 아군을 상대에 포함 금지 | IMPLEMENTED/fixture tested; 실제 신규0 |
| CT04 수집 범위 | 7.2 | 사용자 승인에 따라10tiers/40슬롯 회전·기존cron |650/300/40/1/900 유지, 인증중단·private90d/public7d | IMPLEMENTED; 실제 수집 BLOCKED |
| CT05 자주 만나는 상대 | 2.4 | 같은 역할의 실제 대면N 내림차순·팀 최종승률 | N작음 경고, 50 CH자료만 부분 표시 | IMPLEMENTED/targeted browser |
| CT06 지식 상성 | 2.4.1~3 | 라인전/정글 직접 근거·조건부 어려움/수월함 최대5 | 승률에서 만들지 않음, 전체경기 평가와 단계 혼동 금지 |5개 챔피언 프로필/39조건부·6참고 |
| CT07 상대 역할별 순위 | 2.4 | TOP/JUNGLE/MID/BOTTOM/SUPPORT별 team-final-win top/bottom5 | N>=20, 동률·중복 공개, 원인·교전승률 아님 | IMPLEMENTED; 실제 적격 자료0 |
| CT08 상태/저장/UI | 2.1,2.2,2.4,2.6 | 기본MASTER_PLUS, URL/변경창/복귀·고급 수동 비교 | GOLD/INVALID에서CH 수치·그래프 금지, 저장픽 보존 | IMPLEMENTED/targeted tests |
| CT09 API/배포경계 | 2.2,2.4,7.4 | 공개3자산 + 인증POST selector | private roster/ledger/notes 미공개, query·CSP 보존 | IMPLEMENTED/HTTP3 PASS |
| CT10 수치 보정 | 2.2 | Wilson p=0/1의 부동소수점 끝값 보정 | 엄격 validator 그대로, 20전20패/20승 허용 | RED→GREEN49 tests |
| CT11 전체 검증/출고 | 7.4 | source seal/회귀/브라우저/독립검토/CI | 실패와 source/tactic/live 구분 | IN_PROGRESS |
| CT12 문서/Notion | 관련2.x | 실제 main·배포 확인 뒤 진행률/근거 연결 | 분류·코드 구현을 실제 수집으로 세지 않음 | PENDING |

실제 현재 자료는 CHALLENGER 수집 출발 집단50경기다. MASTER_PLUS는 MASTER/GRANDMASTER 자료가 없는 PARTIAL, ALL은 나머지9티어가 없는 PARTIAL이다. A의 경기 당시 티어는 UNKNOWN이다. 다른 티어는 EMPTY이며 대체 수치를 표시하지 않는다. 경기 결과 표본과 별도 성장275참고를 합산하지 않는다.

기존 등록 키 허용기간은2026-10-16에 끝났다. 새 갱신·허용 창이 없으므로 이번 작업은 Riot 요청을 보내지 않는다. 실제 키 만료/HTTP403을 새로 관측했다고 주장하지 않는다. 재개 조건은 보안 설정의 갱신 키와 명시한 허용 기간이며, 무료 예산·인증 중단·작업당 한도를 유지한다.

새 원자료의 상대 역할 기록이 없어 cross-role 순위는 미확보다. 같은 역할의 기존 행도 현재 최대N6으로 N20을 충족하지 못한다. 0% 또는 임의 상대5명을 채우지 않는다. 이는 기능 코드 검증과 실제 통계 확보 상태의 차이다.

공략 참고 프로필의 어려움/수월함은 Caitlyn4/3, Ezreal3/2, Fiora5/5, Graves5/5, Yunara5/2다. 동순위 안의 명칭순은 강약 순위가 아니다. 패치26.x와Riot16.x의 대응은 확인되지 않았으며 현행 전술 검증·사용자 승인이 아니다. source/claim과 전술 엔진을 자동 승격하지 않는다.

최종 명령·SHA·검증·배포·Notion·남은 문제는 evidence/actual-evidence/champion-tiers-20261025/result.md에 기록한다. 우선 재개는 갱신된 허용 키 창에서 예산 내 결과 동반자료를 누적하는 것이다.
