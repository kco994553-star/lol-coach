# Champion tier and opponent insights implementation plan

## 최신 티어·상대 출고 영수증 — 2026-10-25
PR145 head `d9f18a84352204f21a7da1ba00d555e4624b74ed` 정상병합12:06:14UTC → 이전main `b0a2be870184e3893ca4c9d6b8d1bf3414e36fa7`, PR3 SUCCESS40191299959/40191299982·이전main3 SUCCESS40191661761/40191661643. 이전artifactaf297cac8c3f5827a40429409e94db9a614176b0/native40192218449SUCCESS이나전체LIVE는320bodyCSS200%실패했다.
PR146 head `7e319acc27c4f4fa564b87ae64239b4100322c10` 정상병합12:42:12UTC → 이전main `b236bd736a2de4413a257604d338d9221d21b7a7`,PR3SUCCESS40193983033/40193983036. artifact `e1f273fae59c51e9df1441889831f314577a0600`/native40194626840SUCCESS후body·100.0%는통과했으나native-dialog가실패해전체LIVE_FAILED_DIALOG다. 두실제실패는각각 `live-initial-responsive-failed/`, `live-second-dialog-failed/`에보존한다.
세번째CSS/native-dialog·browser전용[PR147](https://github.com/kco994553-star/lol-coach/pull/147) head `f196a47a225709f29b4b1f18a6cd54ce5e2f04ec` 정상병합13:16:46UTC → 최신제품main `be0b83faf24db19a5f2ff05410c9c2ed979f33db`. PR147필수3 SUCCESS40196588961/40196588989. 정확최신main필수3 **SUCCESS3**(40196881621/40196881598). 새Pages artifact **9fc318cc6725e4e5ccb3fdf3be1c0e44a9590049** /native **40197492425** /상태 **SUCCESS**. 새실제HTTPS/강화브라우저 **ACTUAL_PUBLIC_HTTPS PASS:109/109assetSHA·14private404·root/.nojekyll200·71browser(29old+31tier+11responsive)·74uniquePNG;8saved200cases/6tablekeyboard/3touchEMULATION;errors/external/API/nonGET0**,관측시각 **2026-10-25T13:26:14.324558~13:27:04.403035UTC**. 최종증거 `evidence/actual-evidence/champion-tiers-20261025/result.md`.
e1/sourceb236은dialog문제가있던이전공개제품이며현재9fc318cc/sourcebe0로교체후실제검증통과했다. 두nativeSUCCESS나개별정상검사를전체LIVE_SUCCESS로승격하지않는다. 초기wrapgreen도saved100.0%case로무효화해재수정한역사를유지한다.


최신POST-DIALOG전체1018PASS/159.188s(13:13:42~13:16:21UTC)·CURRENTstart/endSHA동일·변경0,sourcechecks/buildcheckPASS. 수정전1018PASS149.999s/POSTCSS155.284s는역사범위로보존한다. 최신repo36+legacy55/targeted43·독립LOCALPASS. 같은strongharness전체가LOCAL_STAGE에서두번PASS:8saved200cases·touchEMULATION3(실물기기아님)·keyboardtables6·11checks/9PNG·109assetSHAstable. **LOCAL_STAGING_NOT_LIVE**이며로컬stage를거친뒤위별도실제공개71검사로최종통과했다. pointer+.focus()후키입력없이focus-visibleoutline을요구한초기단언은HARNESS_FALSE_POSITIVE로확인했고realTab/ShiftTab으로같은outline을검사해수정했으며이력보존했다. 실제dialogoverflow실패와harness단언오류를서로구분한다.

기존CHALLENGER-seed50경기만보유;MASTER_PLUS/ALLpartial·다른9leafEMPTY,A경기당시rankUNKNOWN,crossrole0·N20순위eligible0(maxpairN6),newacquired/provider0.5champ-role/5author39조건부+6전체참고,source26.x↔Riot16.20.1대응미검증,USER/TACTICAL승인0·coaching=false·게임효과N0 UNMEASURED.갱신허용창은저장기준2026-10-16종료이며새403관측아님.

관리추정은동일160행0/.5/1,전체74/160=**46.25%정확값**,FE84/160=**52.5%**.변경은2.4.1/2.4.4/2.4.7overall0→.5만이며FE그대로·PARTIAL/full_feature_acceptance=false.코드·통계·sourcecoverage와전술검증을혼동하지않는다.2.4.2/3운영·한타와2.4.5선택상대상세·더넓은지식/패치검토는미완료다.새Notion4페이지상태 **SYNCED_READBACK4_OF4 (기존본문/자식ID보존)**.10,000상태capacity/rollover는후속이다.

## 이전 설계·출고전 기록 — 당시 상태 보존

> Use disjoint owners and source-bound RED→GREEN checks; the user's tier/statistics amendments are approved for routine implementation.

**Goal:** Default statistics to MASTER_PLUS, admit all ten leaf tiers within existing collection limits, replace the large manual context form with frequent lane opponents, source-based lane difficulty references, and enemy-role outcome lists.
**Architecture:** Existing outcome/power v1 data and validators remain; an identity-free private result/roster companion permits exact future cross-role aggregation. A static public index shares the same typed selection as the authenticated read-only API. Knowledge references are source-author opinions/paraphrases, separate from wins and tactical approval.
**Tech stack:** Existing Python, vanilla HTML/CSS/UMD JavaScript, unittest and Chromium. No new framework, paid service or runtime AI.
**Spec:** User's 2026-10-25 all-tier/default-Master+ and screenshot replacement instructions; contracts/champion-insights-v1.md; docs/gameplan-content/all-tier-collection-v1.md; docs/gameplan-content/champion-matchup-knowledge-v1.md.

## Constraints and review focus
IA v2.0 retains160 IDs. MASTER_PLUS = MASTER/GRANDMASTER/CHALLENGER; ALL=ten tiers; aggregate unique samples and recompute wins/N/Wilson, never average percentages. Current seed cohort does not establish A's historical rank. Missing tiers never fall back to CH. Same-role encounters cannot manufacture other-role associations. Preserve650 requests/300 matches/40 players/one page/900s and original cron/free/auth stops. Expired renewal window blocks real collection. Public data contains aggregates only; roster/result ledger remains private. Internet categories require correct lane/jungle phase and disclosed patch uncertainty; do not pad to five. Invalid URLs must fail closed. Preserve existing champion selection, drafts, saved picks, source evidence and learning roundtrips.

## Owned deliverables and acceptance
- [x] Audit actual tier admission, retained data and screenshot flow; record unrecoverable cross-role outcomes and expired credential window.
- [x] Data: matchup_results.normalize_match/build/merge; champion_insights build/select; strict unique hash/patch/roster/winner conflict tests, band coverage, N20/ties/overlap.
- [x] Collection: dated user admission amendment, bounded40-slot leaf/division rotation, separate private result completeness and detail-only backfill; original budgets and stops retained.
- [x] Knowledge: curated direct-lane/jungle references for five champion profiles; source URL/hash/locators, short paraphrases, overall-only exclusions and fewer-than-five disclosure.
- [x] Frontend: tier state, frequent opponents, separate hard/easy reference cards, five enemy-role outcome sections, advanced manual controls, empty/invalid/error and mobile states.
- [x] Integration: return-state tier remains reference metadata; explicit assets/API and source CI inventory, exact-scope tests. Clamp Wilson floating boundary without weakening strict validator.
- [x] Independent whole-branch review and bounded final addendum: F1 advanced-table exact tier, Recall collection regression and negative source-binding fixture reviewed after correction. Local scoped browser/regression evidence exists; counts below are not an overall suite pass.
- [x] Latest post-dialog stable1018PASS159.188s/CURRENT unchanged0 and exact product source-check receipts.
- [x] Exact PR145/146/147/mainCI,109asset/private14 export boundary,9fc318cc/native40197492425,actual71checks74PNG and existing4Notionreadbacks complete. Prior GP23 evidence remains separate. Root results-only seal/PR/CI/merge work remains active.

Ruling: one bounded daily target rotates all tiers instead of increasing request limits — respects existing free budget — acquisition breadth takes multiple runs and remains blocked until an allowed renewed key window.
Ruling: statistical ranking requires at least20 observations per exact opponent row — avoids ranking tiny counts as broad evidence — current N<=6 yields honest empty lists.
Ruling: top/bottom5 are independent rate sorts; overlap and rate ties are disclosed — preserves the requested math — small eligible populations can appear in both lists and do not imply causal opponent strength.
Ruling: only direct lane/jungle evidence enters difficulty lists; overall/scaling categories stay reference-only — avoids changing source meaning — some profiles have fewer than5 supported entries.
Ruling: only generated projection changes; old raw datasets/approval records are untouched — preserves evidence — actual cross-role counts await fresh permitted collection.

## Canonical feature mapping and pre-release checkpoint
Code99a4c2f then normal merge origin/main f366d75 → current31449814089966b4dd2966c7b6314d146cebf119. GP23 results PR144 mainf366 required3 SUCCESS40190174719/40190174841 is previous results scope. Current new tier product CI/deploy/live/Notion remain PENDING; public artifact47e241d remains unchanged.

Canonical aggregation/source rows are2.2.2/2.2.5;2.2.1 means basic champion directions. Frequent/opponent outcome selector maps2.2.3/2.2.4/2.2.5, knowledge references2.4.1/2.4.4/2.4.7, state/return2.1/2.6, acquisition7.2. Operations/fight2.4.2/3 and selected-opponent detailed response2.4.5 remain unsupported. Existing160 denominator and45.3overall/52.5frontend estimate unchanged.

First full1016/177.882s had2FAIL and is retained. Root corrected exact-source negative fixture to an explicitly unregistered synthetic path, and collector accepted-work counting to preserve old Recall behavior; original Recall regression test unchanged. Targeted post-review48PASS/2.663s,collection111PASS,frontend16/newbrowser18/legacychampion55+learning33/GP23threeviewport are bounded receipts. Independent final addendumPASS; bounded20PASS/0.691s. Final full stable rerun stillPENDING.

Actual CH50 only: MASTER_PLUS missingMASTER/GRANDMASTER,ALLmissing9tiers;crossrole0,rankingN20eligible0(maxsameN6),newacquisition0. Five sourced conditional profiles39candidate/6reference are not USER/tactical approval, not80content. Old allowed credential window expired; no fresh403/provider probe. Future10,000statecapacity without rollover is a known fail-closed/history-preserving risk before sustained new acquisition.
