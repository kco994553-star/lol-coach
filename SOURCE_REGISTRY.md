# 출처 등록 및 갱신 정책
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
