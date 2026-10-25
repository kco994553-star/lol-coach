# 티어·상대 최종 인수 — 실제 공개 검증 완료

## 최신 티어·상대 출고 영수증 — 2026-10-25
PR145 head `d9f18a84352204f21a7da1ba00d555e4624b74ed` 정상병합12:06:14UTC → 이전main `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7`, PR3 SUCCESS40191299959/40191299982·이전main3 SUCCESS40191661761/40191661643. 이전artifactaf297cac8c3f5827a40429409e94db9a614176b0/native40192218449SUCCESS이나전체LIVE는320bodyCSS200%실패했다.
PR146 head `7e319acc27c4f4fa564b87ae64239b4100322c10` 정상병합12:42:12UTC → 이전main `b236bd736a2de4413a257604d338d9221d21b7a7`,PR3SUCCESS40193983033/40193983036. artifact `e1f273fae59c51e9df1441889831f314577a0600`/native40194626840SUCCESS후body·100.0%는통과했으나native-dialog가실패해전체LIVE_FAILED_DIALOG다. 두실제실패는각각 `live-initial-responsive-failed/`, `live-second-dialog-failed/`에보존한다.
세번째CSS/native-dialog·browser전용[PR147](https://github.com/kco994553-star/lol-coach/pull/147) head `f196a47a225709f29b4b1f18a6cd54ce5e2f04ec` 정상병합13:16:46UTC → 최신제품main `be0b83faf24db19a5f2ff05410c9c2ed979f33db`. PR147필수3 SUCCESS40196588961/40196588989. 정확최신main필수3 **SUCCESS3**(40196881621/40196881598). 새Pages artifact **9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049** /native **40197492425** /상태 **SUCCESS**. 새실제HTTPS/강화브라우저 **ACTUAL_PUBLIC_HTTPS PASS:109/109assetSHA·14private404·root/.nojekyll200·71browser(29old+31tier+11responsive)·74uniquePNG;8saved200cases/6tablekeyboard/3touchEMULATION;errors/external/API/nonGET0**,관측시각 **2026-10-25T13:26:14.324558~13:27:04.403035UTC**. 최종증거 `evidence/actual-evidence/champion-tiers-20261025/result.md`.
e1/sourceb236은dialog문제가있던이전공개제품이며현재9fc318cc/sourcebe0로교체후실제검증통과했다. 두nativeSUCCESS나개별정상검사를전체LIVE_SUCCESS로승격하지않는다. 초기wrapgreen도saved100.0%case로무효화해재수정한역사를유지한다.


최신POST-DIALOG전체1018PASS/159.188s(13:13:42~13:16:21UTC)·CURRENTstart/endSHA동일·변경0,sourcechecks/buildcheckPASS. 수정전1018PASS149.999s/POSTCSS155.284s는역사범위로보존한다. 최신repo36+legacy55/targeted43·독립LOCALPASS. 같은strongharness전체가LOCAL_STAGE에서두번PASS:8saved200cases·touchEMULATION3(실물기기아님)·keyboardtables6·11checks/9PNG·109assetSHAstable. **LOCAL_STAGING_NOT_LIVE**이며로컬stage를거친뒤위별도실제공개71검사로최종통과했다. pointer+.focus()후키입력없이focus-visibleoutline을요구한초기단언은HARNESS_FALSE_POSITIVE로확인했고realTab/ShiftTab으로같은outline을검사해수정했으며이력보존했다. 실제dialogoverflow실패와harness단언오류를서로구분한다.

기존CHALLENGER-seed50경기만보유;MASTER_PLUS/ALLpartial·다른9leafEMPTY,A경기당시rankUNKNOWN,crossrole0·N20순위eligible0(maxpairN6),newacquired/provider0.5champ-role/5author39조건부+6전체참고,source26.x↔Riot16.20.1대응미검증,USER/TACTICAL승인0·coaching=false·게임효과N0 UNMEASURED.갱신허용창은저장기준2026-10-16종료이며새403관측아님.

관리추정은동일160행0/.5/1,전체74/160=**46.25%정확값**,FE84/160=**52.5%**.변경은2.4.1/2.4.4/2.4.7overall0→.5만이며FE그대로·PARTIAL/full_feature_acceptance=false.코드·통계·sourcecoverage와전술검증을혼동하지않는다.2.4.2/3운영·한타와2.4.5선택상대상세·더넓은지식/패치검토는미완료다.새Notion4페이지상태 **SYNCED_READBACK4_OF4 (기존본문/자식ID보존)**.10,000상태capacity/rollover는후속이다.

- [x] PR145/146/147 정상병합·각PR필수3SUCCESS·POSTDIALOG전체1018PASS159.188s/sourceunchanged. af297body실패/e1dialog실패이력보존.
- [x] 정확main필수3성공 영수증.
- [x] nativePages·공개HTTPS자산SHA·실제브라우저/복귀·private/pro보존·rollback.
- [x] 기존4페이지fetch→append→readback;IDs/history/children보존.
- [ ] 전10tiers새획득/crossrole실관측:BLOCKED허용창미확보,0.
- [ ] USER/전술검증·실경기효과:UNMEASURED N0.

---

## 이전 출고전 체크 — 당시 상태 이력

# 티어·상대 확장 릴리스 준비 — 출고 전 동결
코드99a4c2f + origin/main f366d75 정상병합 소스3144981. 현행160ID/관리추정45.3/52.5유지. 아래는현재tier제품이며뒤GP23체크는기존출고이력이다.

- [x] canonical집계ID2.2.2/2.2.5,상대2.2.3/4/5,지식2.4.1/4/7 분리.2.2.1기본방향과혼동없음.
- [x] CH50/Master+·ALLpartial/다른9tierempty/crossrole0/N20eligible0·당시rankunknown 공개. 새획득0,성장275별도.
- [x]5source/5profile39conditional+6reference,USER/TACTICAL_UNREVIEWED/coaching=false·patchmapping미확인·원문공개경계유지.
- [x] 첫full1016검사2FAIL과수정이력보존. 미등록path음성fixture/collectorRecall집계수정,원래Recalltest불변. F1고급표selectedscope수정.
- [x] targeted48PASS2.663s·collection111PASS·frontend16/newbrowser18/legacy55+learning33+GP23threeviewport를로컬scope로기록. 독립최종addendumPASS/별도20PASS0.691s.
- [x] 만료된허용창으로provider0/BLOCKED. 실제HTTP403신규관측아님;기존650/300/40/1/2retry/900s·cron·인증stop유지.
- [x]10,000state한도/rollover미구현capacity위험공개·failclosed/history보존.
- [ ] **최종stable전체검사1018PASS159.188s**,7개문서동결뒤실행.48/111등집중검사를전체성공으로대체하지않음.
- [ ] 현재tier제품sourcechecks/PR145·146·147/main필수CI **PASS**.
- [ ] 새export/privateboundary/protyped보존·nativePages·실제HTTPS·browser·rollback **PASS**. 기존47e241d공개제품은새제품PASS증거아님.
- [ ] 현재tier제품Notion4readback/행별partial평가 **완료**. overall46.25/FE52.5. 실제수집/전술효과N0상태유지.

---

## 기존 GP23 출고 — 별도 이력

# GP23·학습실 릴리스 확인 — 2026-10-25
제품 main `d1d00053dfd3710bb94e08549c7ca256ab0c43ee` / PR143. GP23결과PR144는main f366d75 정상병합·필수3 SUCCESS40190174719/40190174841이며결과만추가해동일제품재게시없음. 아래 체크는 명시한 제한 범위에 적용한다.

## 계약·보존
- [x] 승인2+3방향과 구현선택 구분, 기존160ID·Frozen350·보호결정 보존.
- [x] input-v5/17필드의 assumed/unknown/observed/stale 검증, observed를 현재정보로 승격하지 않음. legacy/v1~4·report/delivery/share 호환 검사.
- [x] 비교표·단계5행동·항상보이는 코칭·전환/상세·지도·legacy 보존. 판단/태그/화면 동기화와 reset 검사.
- [x] 웨이브/자원/다이브/아군기여/기회종료/탱커보호충돌 반례·독립검토 PASS. 해당출고 P0/P1 없음; GP23-23/26/39 PARTIAL·P2범위 공개.

## 로컬·원격 검증
- [x] 전체965 PASS/164.112s source unchanged; 관련학습/GP23·챔피언 및 기존widget/current/directions/gameinfo/presentation5그룹 PASS. 최초구제목단언 실패/수정/재실행 로그 보존.
- [x] PR143(head739851e) 필수3 SUCCESS:40186976680/40186976699.
- [x] 정확main 필수3 SUCCESS:40187456643/40187456649. 강화본문단언도 원격CI실행.
- [x] 입력원문5쌍EXACT_COMMIT6e2e255·seed20261025·10회재현·수동JSON교정없음. 점수7/8/7/7/8·30GENERAL_ONLY 공개.

## 게시·실환경
- [x] Pages artifact `47e241dbf8ddddc612b22902141ed3a2e2411372` /native40188291641 SUCCESS.
- [x] 실제HTTPS11:23:28~44UTC106/106assetSHA·29검사·24PNG,1440/768/390/320·200%·키보드.
- [x] GPv5→학습→정확복귀·챔피언복귀·실제기존공개PRO_REFERENCE복기복귀 PASS. provider/API요청0,pro해시·typed검증 보존.
- [x] rollback이전artifactb0ec3cb8e15f0fa4cc6aa0454897317c23e979c9 확인. 실패한IPv6harness와최종성공분리.
- [ ] 실제source outage/retry: **NOT_RUN**, 실제장애없음. 로컬fixture오류/재시도검사PASS와구분.

## 학습·실제효과·동기화
- [x] taxonomy4/20/80,29claim참조/29성찰/8LINK_ONLY 구분. source/patch/hash/접근상태·private notes/세션토큰/복귀 경계검사.
- [x] 발언/자막/장면/앱해석/USER검토 분리; 후보coaching_enabled자동승격없음. 오프라인허용자막어댑터검사PASS.
- [ ] 실제허용자막/새영상장면/시각검토: **N=0**, 허용원문미확보.
- [ ] 실제게임코칭효과: **UNMEASURED N=0**. 평가계획기록완료이며 효과검증아님.
- [x] 기존Notion5개fetch→append-only→readback;ID/본문/자식보존. `notion-sync.json`.
- [x] 160행동일가중0/.5/1 관리추정45.3/52.5,학습실50/61.8;실제상태와분리.
- [x] GP23결과PR144 정상병합mainf366d75·필수3SUCCESS. 새tier제품검증/배포와별도.

USER티어/상대포지션확장은 별도IN_PROGRESS·신규확보0·실제수집BLOCKED(만료키/호출창),본릴리스/추정제외. 근거 `evidence/actual-evidence/gameplan-2plus3-20261025/result.md` 및 각 JSON/로그.
