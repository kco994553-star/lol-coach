# Learning-room SPEC + QUALITY review

Reviewed 2026-10-25, independently and offline, against `AGENTS.md`, taxonomy v0.1, `contracts/learning-room-v1.md`, and the approved GP23 plan. Baseline HEAD: `a12330d7030c7b74dc748820b68e8b7841940148`; the integration/frontend files are evolving working-tree files. This report does not certify subsequent edits.

**SPEC verdict: CHANGES REQUIRED. QUALITY verdict: CHANGES REQUIRED.** No P0 found. Two integration blockers and one already assigned semantic correction remain at the reviewed snapshot. No repository files were edited, networking performed, private records written, or whole test suite rerun. Only this requested report was written outside the repository.

## P1 — Static and local search implement different contracts

Paths: `web_r4/learning-engine.js:12`, `:16–29`; `coach_v1/learning_room.py:241–290`; `coach_v1/pregame_server.py:454–470`; frontend tests currently validate the divergent behavior rather than cross-runtime parity.

Python uses NFC/casefold, AND text terms, identity/title/taxonomy only, exact case-insensitive identity filters and literal `source_patches`. Frontend uses NFKC, removes all whitespace, searches one contiguous string including resolved tactical prose, requires case-sensitive identities and treats `patch` as `patch_state`. Its state cleaner silently removes a source-patch value or lowercase known champion, broadening the result to every lesson. The approved plan explicitly requires static and local search to share one projection, and the contract explicitly defines source-label patch filtering without implying compatibility.

Reproduced with the real checked-in index and registry, through `search_index` and `stateFromURL(stateToSearch(filters), data, knowledge)` followed by `filterLessons`:

| Input | Python/local matching lessons | Frontend matching lessons |
|---|---:|---:|
| `q='같은 레벨'` | 0 | 11 |
| `q='Caitlyn 웨이브'` | 4 | 0 |
| `champion='caitlyn'` | 8 | 37; champion silently cleared |
| `patch='16.20.1'` | 7 | 37; patch silently cleared |
| `patch='DECLARED_UNVERIFIED'` | 0 | 25 |

Acceptance: choose and document one normalization, token, searchable-field and identity contract; run the same behavioral vectors against both runtimes and assert identical ordered lesson IDs. Keep literal source patch and patch evidence state as separate inputs. A malformed or unknown filter must not silently become an unfiltered successful query. If Python resolves prose from the original registry at query time, the API must supply that registry without copying a second tactical corpus into the index. Verify `26.x` and `16.x` remain distinct and missing patch compatibility remains null.

**Pending work, not verified:** data worker announced NFKC term-AND, optional runtime `knowledge`, and separate `patch_state`. Root API and frontend must integrate these changes; this announcement does not close the finding.

## P1 — Segment schema and frontend permission checks disagree

Paths: `coach_v1/learning_room.py:42–76`; `web_r4/learning-engine.js:32`; `web_r4/learning.js:38`; `tests_pregame/test_learning_frontend.py:test_source_urls_reject_injection_and_segments_need_validated_time`; synthetic fixture in `scripts/browser_learning.py`.

`validate_segment` accepts and projects a permitted TRANSCRIPT with cue references, valid video interval and nullable/independent game clock, but omits `timestamp_state`. The frontend requires the undocumented `timestamp_state='VALIDATED'`, so a server-valid segment never opens. Conversely it never checks access or rights. Adding that magic state to a denied segment produces a link labeled “검증된 영상 구간 열기”. Existing synthetic tests manufacture the extra state while omitting permission fields and valid cross-record video identity, so they cannot establish the data-to-UI path.

Focused reproduction, using `video_id='SA6o_QRPqL8'`, `video_start_ms=32000`, `video_end_ms=45000`, independent `game_clock_ms=90000`, `transcript_cue_ids=['cue:1']`, `evidence_kind='TRANSCRIPT'`, `scene_verified=false`:

- Both permission fields `PERMITTED`: Python projection accepted, frontend `segmentURL` returned null.
- Add `timestamp_state='VALIDATED'` and set both permissions `DENIED`: frontend returned `https://www.youtube.com/watch?v=SA6o_QRPqL8&t=32s`.

Current actual index has zero segments, so this is an offline-bridge integration blocker, not evidence of a current acquired-video leak.

Acceptance: the documented server projection and frontend must agree; rights/access must both be `PERMITTED` before creating an interval link. Use a fixture passed through the real adapter and validator, not a frontend-only object. Verify unknown/denied access, absent or boolean timestamps, invalid interval, wrong video binding, missing cue references, and independent/unknown game clock. Speech must remain speech with `scene_verified=false`; a valid timestamp must not imply visual or tactical review. Segment labels should identify valid timing without implying scene verification.

**Pending work, not verified:** data worker announced a bridge projection retaining `timestamp_state='VALIDATED'`. Frontend permission checks and real projected-fixture verification remain necessary. `learning.js:30` also hardcodes transcript “미확보” for every lesson; any newly displayed transcript-backed record needs evidence rendering from the supplied evidence kind instead of that constant.

## P1 — Counterexamples are presented as sourced recovery guidance

Path: `coach_v1/learning_room.py:180–181`; contract card-field table; `web_r4/learning.js:44`.

Every registry claim's `counterexamples` are assigned to both `stop_or_switch` and `alternative_or_recovery`. This is source text retention but semantic promotion: a counterexample can explain when a claim fails without supplying a recovery action. For example `A-SUSTAINED`'s counterexample says that immobilized Kai'Sa or a large Caitlyn minion/health advantage means time alone does not reverse the trade; it does not supply a sourced “대안·회복” procedure. The UI nevertheless renders it under that field.

Acceptance: leave recovery null/미확인 unless the original registry provides an explicit recovery field; retain counterexamples in the counterexample/stop context. Update the contract and regenerated index and assert a counterexample-only claim leaves recovery null.

**Pending work, not verified:** root has already asked the data worker to make this change. This report does not assume it is completed.

## P2 — Reference validator does not validate claim membership

Path: `coach_v1/learning_room.py:123–138`; `web_r4/learning-engine.js:15`.

Offline probe replaced the first lesson's `claim_ids` and action reference with `DOES-NOT-EXIST`; `validate_index` accepted the index. The UI then silently renders the action as unverified while retaining the original source metadata. The normal current builder selects claims directly from the registry and therefore does not create this corruption. The gap matters when adding the requested offline adapter or treating `validate_index` as the boundary for externally supplied index records.

Acceptance: validate actual claim membership and named reference fields against the authoritative registry when ingesting/projection-validating extensions; reject a reference not in that lesson's claim IDs or whose source binding contradicts the referenced claim. If the validator intentionally cannot establish this without a registry argument, document that limitation and enforce it at the adapter boundary.

## Coverage note — Role scope needs explicit treatment

`build_index` labels all allies in a matchup with only `matchup.role` (`coach_v1/learning_room.py:174–175`). Consequently `champion='Lux', role='SUPPORT'` yields zero despite eight Lux-containing bottom-pair claims. Champion/gameplan links pass the selected player's position. This is an honest empty result, not false tactical advice, but supports cannot discover these existing pair references through their own role context. Do not guess individual roles or grant applicability from the champion name. Either document these records as lane-pair scope and offer that scope explicitly, or add separately sourced actor-role metadata and verify the SUPPORT round trip.

## Confirmed boundaries at the reviewed snapshot

- Real data: 80 taxonomy leaves, 33 sources, 8 videos, 37 lessons (29 existing claim references + 8 link-only candidates), 29 reflection practices, zero video segments, zero new visual reviews and zero provider calls. These counts were read from the real deterministic builder, not inferred from taxonomy coverage.
- All root/lesson/practice coaching flags remain false; all practices have `auto_grade=false`. Registry review labels are carried as references, and frontend wording explicitly denies tactical-effect and USER-approval claims. No automatic tactical promotion path found in these files.
- Existing acquisition failures are preserved as typed metadata; titles/channel/patch/access remain unknown for link-only videos. No network acquisition is performed by builder, UI or search API. Candidate UI does not show the typed acquisition reason; it remains available in the index.
- Source/claim prose resolves through the existing registry. Projection omits private notes, transcript text, account/PUUID/match IDs and arbitrary extra keys. Public build and server asset lists name only the intended learning assets; local search authorizes before processing and does not read private storage.
- Learning URL creation carries bounded public filter/claim context. Full return URLs remain under opaque session-storage tokens; source links suppress referrers. Review-selection memory remains session-local and deliberately omits account/match IDs.
- Video and game clocks are independent in the Python contract; unknown clock/perspective remain unknown. Existing source patches are preserved without aliasing 26.x to 16.x or declaring current compatibility.
- Existing six-scene practice remains linked from the new learning page; the shell retains six entries. Browser accessibility, mobile layout, deployment and the full suite were not independently rerun in this read-only review.

## Snapshot identifiers

SHA-256 at focused-probe time:

```text
coach_v1/learning_room.py 6a95618192386ccac7076426475b3235777ec50d1f0889ab915ea57945447f64
web_r4/learning-engine.js 7aad5f8657bea771368a9433f67709dd967401a0cd1bdc8220da98cdef3781aa
web_r4/learning.js c0461f9bce1fb2e3f009d497f15eb93a680f1543b693413f38edc5100718f666
contracts/learning-room-v1.md 007a6c8d826aae867901f2fcccb9d79128a43f6fcf0c318b5311be33e8092a94
```

Verification performed: direct read-only Python/Node behavioral probes shown above, registry/index counts and flag inspection, source/API/navigation/privacy code inspection. These are narrower than a full browser/API regression. Close P1 findings only against the final common tree with the exact accepted inputs and a projected segment fixture.

## Scoped rereview — current implementation supersedes initial P1 verdict

Rereviewed 2026-10-25 after the data, frontend and root API corrections. **Current SPEC verdict: PASS for the three reviewed P1 corrections and permitted offline bridge. Current QUALITY verdict: PASS WITH P2 FOLLOW-UPS. No remaining P0/P1 was found in this scoped rereview.** The initial findings above remain as historical reproduction evidence, not current blockers. This verdict is not a deployment, full-suite or tactical-efficacy certification.

The data follow-up report and its 20-test green log were read. The frontend report file was not yet present at the time of rereview; its author reported 10 focused tests and expanded 37-case parity checks. Independently rerun focused Python/Node probes verified the concrete results below; no whole test suite was rerun.

### P1 search parity: CLOSED

All initial exact inputs now agree through the actual frontend URL route, `stateToSearch → stateFromURL → filterLessons`, compared with Python `search_index(..., knowledge=registry)`:

| Input | Both runtimes |
|---|---:|
| `q='같은 레벨'` | 11 |
| `q='Caitlyn 웨이브'` | 5 |
| `champion='caitlyn'` | 8 |
| `patch='16.20.1'` | 7 |
| `patch='DECLARED_UNVERIFIED'` | 0 |
| `patch_state='DECLARED_UNVERIFIED'` | 26 |

Additional focused vectors also agreed: fullwidth `Ｃａｉｔｌｙｎ 웨이브` (5), safe unknown champion (0), lowercase `opponent='kaisa', role='bottom'` in the pure/search-state path (21), lowercase evidence `source_reference` (29), and lowercase state `unknown` (11). Known identities are canonicalized; safe unknown champion/source-patch constraints survive URL cleaning and produce empty results. This last URL-cleaner correction was necessary: the first rereview still reproduced the broadening bug, and the final correction was independently reprobed before closing it.

The root API now allows `patch_state` and supplies the existing public registry as `knowledge`. The contract describes NFKC term-AND and runtime prose resolution; exact source patch and evidence state are independent. Default data still declares compatibility unknown and does not alias patch numbering.

### P1 segment projection/rights: CLOSED

A synthetic transcript was passed through the real `append_transcript` adapter, not manually converted into a frontend-only segment. Its projected segment now includes `timestamp_state='VALIDATED'`; frontend opened the correct video at `t=1s`. Mutating that real projection to denied access, unknown rights, boolean video timestamp, or wrong video identity made `segmentURL` return null in every case. The frontend also requires source hash, correct canonical video binding, cue references for speech and explicit review for a visual record.

Evidence rendering now distinguishes transcript reference, visual reference and interpretation. The actual bridge projection keeps `scene_verified=false`, `game_clock_ms=null`, perspective UNKNOWN and coaching disabled. Supplied transcript permission remains separate from the video's unknown access and scene state. Source-authenticity/duration assertions are documented as operator assertions rather than independent video verification.

### P1 recovery semantics: CLOSED

All 37 default lessons have `alternative_or_recovery=null`; counterexamples remain in their stop/counterexample references. The contract now requires an explicit original recovery field. The frontend resolver whitelist also includes `alternative_or_recovery`, so an actually supplied registry field can be displayed rather than silently omitted.

### Offline bridge boundary: ACCEPTABLE within documented operator trust

Independent in-memory probes verified PUBLIC visibility, exact raw SHA-256 and both PERMITTED flags are required. UNKNOWN access, DENIED rights, PRIVATE visibility and wrong hash each raised the expected rejection. Raw speech and arbitrary provenance sentinel values were absent from the resulting public JSON; raw bytes and the original input index were unchanged. Every new speech lesson retained empty claim IDs, null action, exact emitted `source_refs`/`source_ids` agreement, source hash and valid cue/segment references. Existing acquisition failure remains unchanged. No real transcript was accepted; the checked-in artifact still contains zero segments.

Code inspection confirms the CLI reads raw/manifest inputs, writes only a metadata projection, and rejects output collisions against raw, manifest and existing registry inputs using resolved-path and same-file checks, including hardlink aliases. The data owner's recorded raw-preservation test covers that hardlink counterexample. No raw/private-file mutation was performed for this review. Assignment labels remain explicit operator classifications, not a transcript, visual or tactical approval claim.

The P2 general-purpose validator claim-membership limitation and role-scope coverage note remain open as described above. They do not corrupt the current normal builder or new bridge: the builder derives claims from the authoritative registry, and the bridge creates speech candidates with no claims or tactical action. Do not represent `validate_index` alone as independent claim/source authentication.

### Available frontend receipt and limits

The final worker-produced `/workspace/gp23-artifacts/learning-browser/learning-browser.json` was inspected: `passed:true`, 31 checks, empty browser/HTTP/external-request error arrays. It supersedes the intermediate `passed:false` skip-link/text-zoom receipt observed during rereview. This is inspected worker evidence; the reviewer did not rerun the browser. Root still owns final common-tree/full-suite/release verification.

### Rereview snapshot SHA-256

```text
coach_v1/learning_room.py 12510f38a67ed69e5188e739b61eaadb66908ccdc17ea129daedc8ced1c1ad5c
scripts/build_learning_room.py 958d6a386c9a63ea853e6999b4749225acd8ec243a678461e56e5ff6f5d0b352
web_r4/learning-engine.js af1e595817e1cd01242e9d026948bba8a737463845be69f46edae88fe6db1a07
web_r4/learning.js 142b4ab45ae4a53e9a79590d2fb811ab191301e476a275ca74d1186b0f67eb21
contracts/learning-room-v1.md 71442efb51bc6e538b027a5b987d01056002dd43791e4280fe7f7dbd953ef26c
```
