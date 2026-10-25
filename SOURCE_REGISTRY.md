# 출처 등록 및 갱신 정책

## 최신 티어·상대 출고 영수증 — 2026-10-25
PR145 head `d9f18a84352204f21a7da1ba00d555e4624b74ed` 정상병합12:06:14UTC → 이전main `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7`, PR3 SUCCESS40191299959/40191299982·이전main3 SUCCESS40191661761/40191661643. 이전artifactaf297cac8c3f5827a40429409e94db9a614176b0/native40192218449SUCCESS이나전체LIVE는320bodyCSS200%실패했다.
PR146 head `7e319acc27c4f4fa564b87ae64239b4100322c10` 정상병합12:42:12UTC → 이전main `b236bd736a2de4413a257604d338d9221d21b7a7`,PR3SUCCESS40193983033/40193983036. artifact `e1f273fae59c51e9df1441889831f314577a0600`/native40194626840SUCCESS후body·100.0%는통과했으나native-dialog가실패해전체LIVE_FAILED_DIALOG다. 두실제실패는각각 `live-initial-responsive-failed/`, `live-second-dialog-failed/`에보존한다.
세번째CSS/native-dialog·browser전용[PR147](https://github.com/kco994553-star/lol-coach/pull/147) head `f196a47a225709f29b4b1f18a6cd54ce5e2f04ec` 정상병합13:16:46UTC → 최신제품main `be0b83faf24db19a5f2ff05410c9c2ed979f33db`. PR147필수3 SUCCESS40196588961/40196588989. 정확최신main필수3 **SUCCESS3**(40196881621/40196881598). 새Pages artifact **9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049** /native **40197492425** /상태 **SUCCESS**. 새실제HTTPS/강화브라우저 **ACTUAL_PUBLIC_HTTPS PASS:109/109assetSHA·14private404·root/.nojekyll200·71browser(29old+31tier+11responsive)·74uniquePNG;8saved200cases/6tablekeyboard/3touchEMULATION;errors/external/API/nonGET0**,관측시각 **2026-10-25T13:26:14.324558~13:27:04.403035UTC**. 최종증거 `evidence/actual-evidence/champion-tiers-20261025/result.md`.
e1/sourceb236은dialog문제가있던이전공개제품이며현재9fc318cc/sourcebe0로교체후실제검증통과했다. 두nativeSUCCESS나개별정상검사를전체LIVE_SUCCESS로승격하지않는다. 초기wrapgreen도saved100.0%case로무효화해재수정한역사를유지한다.


최신POST-DIALOG전체1018PASS/159.188s(13:13:42~13:16:21UTC)·CURRENTstart/endSHA동일·변경0,sourcechecks/buildcheckPASS. 수정전1018PASS149.999s/POSTCSS155.284s는역사범위로보존한다. 최신repo36+legacy55/targeted43·독립LOCALPASS. 같은strongharness전체가LOCAL_STAGE에서두번PASS:8saved200cases·touchEMULATION3(실물기기아님)·keyboardtables6·11checks/9PNG·109assetSHAstable. **LOCAL_STAGING_NOT_LIVE**이며로컬stage를거친뒤위별도실제공개71검사로최종통과했다. pointer+.focus()후키입력없이focus-visibleoutline을요구한초기단언은HARNESS_FALSE_POSITIVE로확인했고realTab/ShiftTab으로같은outline을검사해수정했으며이력보존했다. 실제dialogoverflow실패와harness단언오류를서로구분한다.

기존CHALLENGER-seed50경기만보유;MASTER_PLUS/ALLpartial·다른9leafEMPTY,A경기당시rankUNKNOWN,crossrole0·N20순위eligible0(maxpairN6),newacquired/provider0.5champ-role/5author39조건부+6전체참고,source26.x↔Riot16.20.1대응미검증,USER/TACTICAL승인0·coaching=false·게임효과N0 UNMEASURED.갱신허용창은저장기준2026-10-16종료이며새403관측아님.

관리추정은동일160행0/.5/1,전체74/160=**46.25%정확값**,FE84/160=**52.5%**.변경은2.4.1/2.4.4/2.4.7overall0→.5만이며FE그대로·PARTIAL/full_feature_acceptance=false.코드·통계·sourcecoverage와전술검증을혼동하지않는다.2.4.2/3운영·한타와2.4.5선택상대상세·더넓은지식/패치검토는미완료다.새Notion4페이지상태 **SYNCED_READBACK4_OF4 (기존본문/자식ID보존)**.10,000상태capacity/rollover는후속이다.

## 이전 설계·출고전 기록 — 당시 상태 보존
2026-10-25 · 로컬 보존 자료 확인. 이 변경은 네트워크 재수집/라이선스 확인/자동 수집 운영 증거가 아니다.

| 출처 | 확인한 URL·버전·보존 위치 | 갱신·실패·신선도 경계 |
|---|---|---|
| Riot 공식 챔피언 | `https://ddragon.leagueoflegends.com/api/versions.json`; `https://ddragon.leagueoflegends.com/cdn/16.20.1/data/ko_KR/champion.json`; 동일 경로 `champion/{Champion}.json`. `data/official_catalog/versions/16.20.1/manifest.json`에 URL/파일별 SHA. collected_at `2026-10-15T10:19:35.604285+00:00` | source_patch 16.20.1 / game_patch 16.20. `scripts/update_official_catalog.py`→`coach_v1.official_catalog.refresh_if_due`, 기본 86400초는 재확인 자격이고 운영 scheduler 또는 현재 패치 증거가 아님. 실패는 마지막 검증 archive와 실패 상태를 함께 유지. |
| Riot 공식 아이템 | `https://ddragon.leagueoflegends.com/cdn/16.20.1/data/ko_KR/item.json`; `data/official_items/versions/16.20.1/manifest.json`; retrieved_at `2026-10-15T10:59:54.562761+00:00` | version 16.20.1. inventory 870은 전술 지원 수가 아님. 새 버전의 원문/hash 검증 없이 최신 선언 금지. |
| 공식 자료 바인딩/프로필 | `web_r4/loading-direction-profiles.js`: schema v1, data version 2, source_patch 16.20.1, `TACTICAL_UNREVIEWED`; Caitlyn/Ezreal BOTTOM, Fiora TOP, Graves JUNGLE | 원문 URL/해시/발췌의 BOUND는 무결성만 의미. 패치/역할/필수 슬롯 불일치 시 SOURCE_REVIEW_REQUIRED. 조합·매치업 인덱스는 불완전. USER 승인/실경기 효과로 승격 금지. |
| Riot 경기 API/역사 자료 | 상세 수집 receipts와 범위는 `docs/gameplan-content/input-integration-v1.md` | 조회 권한/호출 제한/표본/기간/실패를 작업별 기록. 역사 데이터는 현재 세션/정글 위치가 아님. 겹치는 수집 표본 합산 금지. |
| LCU/로컬 선택 | `coach_v1/gameplan_input.py`, `coach_v1/pregame_server.py`; MANUAL/LCU_CHAMP_SELECT만 허용, 미확정 포지션 null | 연결 이벤트/세션 변경 시 입력 갱신·폐기. 2초는 전송 liveness만 검사. 클라이언트·본인·동일 경기 연결이 검증되지 않으면 ready/display gate를 열지 않음. 제공되지 않는 시야/정글/스킬/ETA 생성 금지. |
| 수동 상황 입력 | 사용자가 선택한 가정과 초기화 이벤트 | `assumed`, 실제 관측 아님. 관측 상태에는 별도 source/observed_at 필요. source별 전술 TTL은 미정이면 unknown; 단일 초 기준 적용 금지. 오래된 관측은 stale로 제한하고 태그/문장 함께 갱신. |
| 전문가/영상·학습 | 기존 source/claim registry, `coach_intake/video.py`, `coach_v1/expert_bridge.py`, `docs/learning-room/video-topic-taxonomy-v0.1.md` | LINK_ONLY·speech·visual·claim·게시를 분리. 원본 URL/영상 구간/자막 시점/게임 시각/해시/접근 상태를 보존. 링크만으로 transcript/프레임/패치 확보를 선언하지 않음. 접근/라이선스 미확인은 unknown; 권한 없는 수집 금지. |

`data/official_catalog/current.json` manifest SHA: `e61307d1acf1f8b27e66dd144b4136384dda35451a22e932a307e06c8885c406`. `data/official_items/current.json` manifest SHA: `d7b89641deccbf91e076386a3bc60a4065e4edce35293fc65238d5686dd738ee`. 실제 manifest 파일 해시 검증과 최신 CDN 확인은 별도 명령/결과로 기록한다.

공식 정책 참고 URL: `https://developer.riotgames.com/docs/lol`, `https://developer.riotgames.com/policies/general`. 기존 입력 문서는 2026-10-24 확인 기록을 보존한다. 이번 문서 변경은 현재 라이선스·제품 감사·LCU 승인·호출 권한을 재확인한 것이 아니다. LCU의 제3자 지원·개발자 포털 공개 의무 등은 해당 원문과 제품 범위로 다시 판단한다.

AGENTS.md의 USER 결정 보호 규칙을 적용한다. 공식 한국어 사실 확인과 전술 검토는 별개다. 기존 350 후보·동결 계약·결정 원문을 보존한다. 관련 상세: `docs/gameplan-content/knowledge-maintenance-v1.md`, `input-integration-v1.md`. 실경기 효과 UNMEASURED / N=0.

## 챔피언 티어·상대 확장 — 출고 전 확인 (2026-10-25)

코드99a4c2f 및 origin/main f366d75 정상 병합 후 소스3144981 기준이다. 이 절은 신규 자료 확보·원격 CI·배포 성공 증거가 아니다.

| 원천/투영 | 실제 보유·출처 의미 | 실패·검토·공개 경계 |
|---|---|---|
| 기존 결과 원천 → champion-insights.json | REAL CHALLENGER-seed50경기, patch16.20, source digest1f6f276d153bc11978670b0644ee31b16b28f260deb1be23196aabf0053d64fc. MASTER_PLUS=CH만50/PARTIAL(MASTER·GRANDMASTER없음),ALL=같은50/PARTIAL(다른9tier없음) | seed현재리그≠A/전참가자 경기당시티어; A당시티어UNKNOWN. 타leaf EMPTY;50을각필터에서더하지않음. 성장275참고와도별도. |
| 미래 익명 결과 동반자료 | coach_v1/matchup_results.py의해시·익명양팀관측역할·승리팀·seed/provenance. 기존power자료에서승패/적역할복원안함 | 실제신규수집0/retainedroster-result0/cross-role0. 같은역할최대N6,N20순위적격0. privatecompanion/ledger는공개금지;공개는aggregate만. |
|10tiers 수집 정책 | all-tier-collection-v1.md의승인범위·40slot1target·기존cron/650requests/300jobs/40players/1page/2retry/900s공유상한 | 허용창2026-10-16T10:16:49Z종료,새창미확보로실제수집BLOCKED/요청0. 새403·키검증실패관측아님. 갱신키+명시허용창전probe금지. |
|지식상대5profile | config/champion_matchup_references.json → coach_v1/champion_matchup_knowledge.py → champion-matchup-knowledge.json. MOBAFire5author/5champ-role,39CONDITIONAL_CANDIDATE+6REFERENCE_ONLY | LANING/JUNGLE구간만조건부. 통계에서전술생성안함;USER승인0/TACTICAL_UNREVIEWED/coaching=false. Riot16.20.1↔source26.x대응미검증,페이지갱신≠문단갱신. |

저자·출처는 rowzkit(Caitlyn),Pengwan(Ezreal),Anoying bro5(Fiora),Coach Myga(Graves),inFinem(Yunara)다. 정확URL/finalURL·retrieved_at·HTML/quote/paragraphSHA·locator는공개정적자료의sources/evidence와원본연구산출물에분리보존한다. SOURCE_PARAPHRASE/AI조건부행동/AI제한조건을구별하며원문전체HTML·인용문단은공개하지않는다.39/6은sourcecoverage이지80완료콘텐츠·전챔피언전술·전문성독립검증이아니다.

현재상태누적경로의10,000건한도와rollover미구현은미래장기수집P2capacity위험이다. 한도도달시failclosed하며기존history를삭제하거나성공으로표시하지않는다. 별도privatecompanion100,000record validator상한과혼동하지않고실제장기획득전보존형archival/rollover를설계한다.

최종stable전체검사·현재tier제품원격CI·배포·실환경·Notion은모두PENDING이다. GP23제품PR143/결과PR144와이미공개한47e241d는기존출고범위만증명한다. 신규실제경기효과UNMEASURED/N0. 결과영수증예정위치:evidence/actual-evidence/champion-tiers-20261025/result.md.
