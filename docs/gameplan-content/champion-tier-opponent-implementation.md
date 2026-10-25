# 챔피언 티어·상대 통계 확장 실행 대장

## 최신 티어·상대 출고 영수증 — 2026-10-25
PR145 head `d9f18a84352204f21a7da1ba00d555e4624b74ed` 정상병합12:06:14UTC → 이전main `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7`, PR3 SUCCESS40191299959/40191299982·이전main3 SUCCESS40191661761/40191661643. 이전artifactaf297cac8c3f5827a40429409e94db9a614176b0/native40192218449SUCCESS이나전체LIVE는320bodyCSS200%실패했다.
PR146 head `7e319acc27c4f4fa564b87ae64239b4100322c10` 정상병합12:42:12UTC → 이전main `b236bd736a2de4413a257604d338d9221d21b7a7`,PR3SUCCESS40193983033/40193983036. artifact `e1f273fae59c51e9df1441889831f314577a0600`/native40194626840SUCCESS후body·100.0%는통과했으나native-dialog가실패해전체LIVE_FAILED_DIALOG다. 두실제실패는각각 `live-initial-responsive-failed/`, `live-second-dialog-failed/`에보존한다.
세번째CSS/native-dialog·browser전용[PR147](https://github.com/kco994553-star/lol-coach/pull/147) head `f196a47a225709f29b4b1f18a6cd54ce5e2f04ec` 정상병합13:16:46UTC → 최신제품main `be0b83faf24db19a5f2ff05410c9c2ed979f33db`. PR147필수3 SUCCESS40196588961/40196588989. 정확최신main필수3 **SUCCESS3**(40196881621/40196881598). 새Pages artifact **9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049** /native **40197492425** /상태 **SUCCESS**. 새실제HTTPS/강화브라우저 **ACTUAL_PUBLIC_HTTPS PASS:109/109assetSHA·14private404·root/.nojekyll200·71browser(29old+31tier+11responsive)·74uniquePNG;8saved200cases/6tablekeyboard/3touchEMULATION;errors/external/API/nonGET0**,관측시각 **2026-10-25T13:26:14.324558~13:27:04.403035UTC**. 최종증거 `evidence/actual-evidence/champion-tiers-20261025/result.md`.
e1/sourceb236은dialog문제가있던이전공개제품이며현재9fc318cc/sourcebe0로교체후실제검증통과했다. 두nativeSUCCESS나개별정상검사를전체LIVE_SUCCESS로승격하지않는다. 초기wrapgreen도saved100.0%case로무효화해재수정한역사를유지한다.


최신POST-DIALOG전체1018PASS/159.188s(13:13:42~13:16:21UTC)·CURRENTstart/endSHA동일·변경0,sourcechecks/buildcheckPASS. 수정전1018PASS149.999s/POSTCSS155.284s는역사범위로보존한다. 최신repo36+legacy55/targeted43·독립LOCALPASS. 같은strongharness전체가LOCAL_STAGE에서두번PASS:8saved200cases·touchEMULATION3(실물기기아님)·keyboardtables6·11checks/9PNG·109assetSHAstable. **LOCAL_STAGING_NOT_LIVE**이며로컬stage를거친뒤위별도실제공개71검사로최종통과했다. pointer+.focus()후키입력없이focus-visibleoutline을요구한초기단언은HARNESS_FALSE_POSITIVE로확인했고realTab/ShiftTab으로같은outline을검사해수정했으며이력보존했다. 실제dialogoverflow실패와harness단언오류를서로구분한다.

기존CHALLENGER-seed50경기만보유;MASTER_PLUS/ALLpartial·다른9leafEMPTY,A경기당시rankUNKNOWN,crossrole0·N20순위eligible0(maxpairN6),newacquired/provider0.5champ-role/5author39조건부+6전체참고,source26.x↔Riot16.20.1대응미검증,USER/TACTICAL승인0·coaching=false·게임효과N0 UNMEASURED.갱신허용창은저장기준2026-10-16종료이며새403관측아님.

관리추정은동일160행0/.5/1,전체74/160=**46.25%정확값**,FE84/160=**52.5%**.변경은2.4.1/2.4.4/2.4.7overall0→.5만이며FE그대로·PARTIAL/full_feature_acceptance=false.코드·통계·sourcecoverage와전술검증을혼동하지않는다.2.4.2/3운영·한타와2.4.5선택상대상세·더넓은지식/패치검토는미완료다.새Notion4페이지상태 **SYNCED_READBACK4_OF4 (기존본문/자식ID보존)**.10,000상태capacity/rollover는후속이다.

## 이전 설계·출고전 기록 — 당시 상태 보존

시작 main d1d00053dfd3710bb94e08549c7ca256ab0c43ee → 코드99a4c2f → origin/main f366d75 정상병합 소스31449814089966b4dd2966c7b6314d146cebf119. GP23결과PR144는main f366d75와필수3검사SUCCESS(40190174719/40190174841)로완료했으나새tier제품의원격CI/배포/실환경증거는아니다. GP23/학습실 출고 이후 별도 사용자 지시이며 그 44개 완료 이력에 합산하지 않는다. 기존 IA160 번호·원자료·승인·실패 이력을 보존한다.

| 작업 | 기능 ID | 구현·의존성 | 수용/반례 | 현재 상태 |
|---|---|---|---|---|
| CT01 조사/계약 | 2.2,2.4,7.2 | 기존 tier schema와 Master+ admission, 원문·실제 소스 추적 | 과거 outcome/power로 cross-role 승패 복원 불가 | DOCUMENTED |
| CT02 밴드·집계 | 2.2.2,2.2.5 | MASTER_PLUS/ALL/10tiers; unique hash와 승패 재계산 | 중복/patch충돌/누락티어/평균승률 금지 | IMPLEMENTED/targeted tests |
| CT03 결과 동반자료 | 2.4,7.2 | 비공개 해시·양 팀 역할·승리 팀, 공개 집계만 | 모르는 역할 추정 금지, 아군을 상대에 포함 금지 | IMPLEMENTED/fixture tested; 실제 신규0 |
| CT04 수집 범위 | 7.2 | 사용자 승인에 따라10tiers/40슬롯 회전·기존cron |650/300/40/1/900 유지, 인증중단·private90d/public7d | IMPLEMENTED; 실제 수집 BLOCKED |
| CT05 자주 만나는 상대 | 2.2.3,2.2.4,2.2.5 | 같은 역할의 실제 대면N 내림차순·팀 최종승률 | N작음 경고, 50 CH자료만 부분 표시 | IMPLEMENTED/targeted browser |
| CT06 지식 상성 | 2.4.1,2.4.4,2.4.7 | 라인전/정글 직접 근거·조건부 어려움/수월함 최대5 | 승률에서 만들지 않음, 전체경기 평가와 단계 혼동 금지 |구현·참고자료5profile/39조건부·6참고;USER/전술승인아님 |
| CT07 상대 역할별 순위 | 2.2.3,2.2.4,2.2.5 | TOP/JUNGLE/MID/BOTTOM/SUPPORT별 team-final-win top/bottom5 | N>=20, 동률·중복 공개, 원인·교전승률 아님 | IMPLEMENTED; 실제 적격 자료0 |
| CT08 상태/저장/UI | 2.1,2.2,2.4,2.6 | 기본MASTER_PLUS, URL/변경창/복귀·고급 수동 비교 | GOLD/INVALID에서CH 수치·그래프 금지, 저장픽 보존 | IMPLEMENTED/targeted tests |
| CT09 API/배포경계 | 2.2,2.4,7.4 | 공개3자산 + 인증POST selector | private roster/ledger/notes 미공개, query·CSP 보존 | IMPLEMENTED/HTTP3 PASS |
| CT10 수치 보정 | 2.2 | Wilson p=0/1의 부동소수점 끝값 보정 | 엄격 validator 그대로, 20전20패/20승 허용 | RED→GREEN49 tests |
| CT11 전체 검증/출고 | 7.4 | source seal/회귀/브라우저/독립검토/CI | 실패와 source/tactic/live 구분 | 독립addendum/전체1018/PR·mainCI/Pages/실제live PASS |
| CT12 문서/Notion | 관련2.x | 실제 main·배포 확인 뒤 진행률/근거 연결 | 분류·코드 구현을 실제 수집으로 세지 않음 | 최종문서·Notion4readback·3행partial평가완료;root결과PR인계진행 |

실제 현재 자료는 CHALLENGER 수집 출발 집단50경기다. MASTER_PLUS는 MASTER/GRANDMASTER 자료가 없는 PARTIAL, ALL은 나머지9티어가 없는 PARTIAL이다. A의 경기 당시 티어는 UNKNOWN이다. 다른 티어는 EMPTY이며 대체 수치를 표시하지 않는다. 경기 결과 표본과 별도 성장275참고를 합산하지 않는다.

기존 등록 키 허용기간은2026-10-16에 끝났다. 새 갱신·허용 창이 없으므로 이번 작업은 Riot 요청을 보내지 않는다. 실제 키 만료/HTTP403을 새로 관측했다고 주장하지 않는다. 재개 조건은 보안 설정의 갱신 키와 명시한 허용 기간이며, 무료 예산·인증 중단·작업당 한도를 유지한다.

새 원자료의 상대 역할 기록이 없어 cross-role 순위는 미확보다. 같은 역할의 기존 행도 현재 최대N6으로 N20을 충족하지 못한다. 0% 또는 임의 상대5명을 채우지 않는다. 이는 기능 코드 검증과 실제 통계 확보 상태의 차이다.

공략 참고 프로필의 어려움/수월함은 Caitlyn4/3, Ezreal3/2, Fiora5/5, Graves5/5, Yunara5/2다. 동순위 안의 명칭순은 강약 순위가 아니다. 패치26.x와Riot16.x의 대응은 확인되지 않았으며 현행 전술 검증·사용자 승인이 아니다. source/claim과 전술 엔진을 자동 승격하지 않는다.

최종 명령·SHA·검증·배포·Notion·남은 문제는 evidence/actual-evidence/champion-tiers-20261025/result.md에 기록한다. 우선 재개는 갱신된 허용 키 창에서 예산 내 결과 동반자료를 누적하는 것이다.

## 검증·수정 이력과 출고 전 동결
- 첫전체1016검사/177.882s는2FAIL이며성공으로표시하지않는다. sourceauthority음성fixture가새로등록된collector를미등록으로간주한문제와기존RecallCollector의offpatch작업집계회귀를각각수정했다. 전자는명시미등록가상path를CURRENT에없음을단언하고,후자는companion범위작업과legacyacceptedpair집계를구분했다. 원래RecallCollectionTests는변경하지않았다.
- F1고급상대표도I.select(...).frequent_opponents로선택tier/patch/role의검색·정렬·N/CI를맞췄다. GOLD/MASTER_PLUS가CH자료를몰래공유하지않도록fixture/실제UI검사를수정후재실행했다.
- 후속targeted48PASS/2.663s,collection111PASS,frontend16/newbrowser18/legacychampion55+learning33+GP23의3viewport통과를해당로컬scope로기록한다. 숫자를전체suite에추가합산하지않는다. 독립최종addendum은F1/Recallfix와sourcefixture를재검토PASS했고bounded20PASS/0.691s를별도로기록했다.
- 최종stable전체검사는아직PENDING. 현재tier제품의source-seal최종영수증/정확PR·mainCI/배포·실제HTTPS·Notion도PENDING. 이전GP23live47e241dbf8ddddc612b22902141ed3a2e2411372는새게시전까지공개제품이다.
-10,000건상태누적한도에rollover가없어장기수집capacityP2를공개한다. failclosed/history보존을유지하고새허용창이생긴뒤한도도달전archival계획을검토한다.

기존관리추정160행전체45.3%/FE52.5%는그대로다. sourcecoverage39/6·검색UI·허용10tiers는실제획득이나full2.4완료가아니다.2.4.2/3운영/한타본문과2.4.5선택상대상세는여전히자료부족이다. 최종검사·출고·미측정상태를확인한뒤root가증거폴더를채우고후속평가/Notion을동기화한다. 실제신규획득0/crossrole0/전술효과N0.

## 현재 제한과 root 인계
최종출고는위현재절대로완료했다. root결과writer는최종봉인/정상PR·CI/병합진행중이며같은앱을재게시하지않는다. 실제outage/retry는장애없어BLOCKED,실물touch/Safari/FirefoxNOT_RUN이다. 전체160행중overall세행만각0.5증가해74/16046.25%exact,FE84/16052.5%유지. source후보를USER/tactic승인으로승격하지않았고실제새획득/crossrole/영상/코칭효과N0.
