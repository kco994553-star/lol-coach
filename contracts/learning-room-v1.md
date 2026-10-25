# Learning-room reference index v1

2026-10-25. Additive implementation under IA v2.0 **6.1–6.6**; taxonomy follows
[`video-topic-taxonomy-v0.1.md`](../docs/learning-room/video-topic-taxonomy-v0.1.md).
The 160 IA feature IDs and existing six-scene practice are unchanged. Index
publication makes references discoverable; it grants no tactical approval.

## Inputs and deterministic build

`python scripts/build_learning_room.py` reads only:

- `config/learning_topics.json`: the exact four groups, five middle topics each,
  four leaves each, and manually assigned existing claim→topic references.
- `web_r4/loading-knowledge.json`: the existing public source/claim registry.
- `config/user_lesson_candidates.json`: eight already recorded YouTube links
  and prior acquisition failures.

It writes `web_r4/learning-room.json`; `--check` compares the exact generated
bytes and exits 1 if absent/stale. No current-time field changes the output.
Provenance includes SHA-256 of sorted, compact, UTF-8 JSON input values
(`ensure_ascii=False`, separators `,` and `:`), **not raw-file byte hashes**.
No networking, source scraping, provider call, private database access, review
journal, or approval write is involved. The existing transcript importer and
expert bridge remain separate and unchanged. Existing USER decision history
is never duplicated or replaced by the index.

## Root and identity

Root `format` is `lol-coach-learning-room-v1`. Root fields:
`taxonomy`, `registry_url`, `sources`, `videos`, `segments`, `lessons`,
`practices`, `provenance`, `coaching_enabled:false`.

Taxonomy is `{groups:[{id,label,topics:[{id,label,leaves:[{id,label}]}]}]}`.
IDs are `topic:1`…`topic:4`, `topic:1.1`…`topic:4.5`, and
`topic:1.1.1`…`topic:4.5.4`. All 104 IDs are unique; 80 leaves exist even when
they have no content. Null primary topics are **unclassified**, never the first
leaf by default. A lesson has one primary leaf and optional related leaves.

Every source, video, segment, lesson and practice has a unique ID in its own
collection. The same video and segment may appear in multiple lesson references
when those lessons have distinct IDs. The current actual data contains
**29 existing claim references, 8 link-only candidates, 29 reflection practices,
0 video segments, and 0 newly visually reviewed videos**. These are reference
and exercise counts, not independent expert sources or verified tactical claims.

## Normalized records

Source:
`{source_id,title,canonical_url,source_patch,publication_time,access_state,
license_or_access_state,kind,source_hash,patch_compatible:null,registry_ref?}`.
Only HTTPS links without URL user/password are accepted. `registry_ref`, when
present, is `{collection:'sources',id:<existing source ID>}`. Existing excerpts,
transcripts and private notes are not copied into the index. `source_hash` is
the canonical JSON hash of the original source/candidate object.

Video:
`{video_id,canonical_url,title,channel_id,publication_time,source_patch,language,
license_or_access_state,access_state,transcript_state,scene_state,patch_state,
acquisition,source_hash}`.
All eight candidates retain null unverified metadata, `UNKNOWN` access,
transcript, scene and patch, and `UNKNOWN_LINK_ONLY` rights. A link is not proof
of access or a title. `acquisition` is
`{state:'NOT_ACQUIRED',attempted:boolean,reason:<recorded typed result>}`.
Only the two IDs in the recorded metadata attempt list carry
`WEB_TOOL_FETCH_THROTTLED`; other IDs carry `NOT_ATTEMPTED`. No retry is made.

Segment (currently none):
`{segment_id,video_id,video_start_ms,video_end_ms,game_clock_ms,
transcript_cue_ids,scene_verified,viewer_perspective,source_hash,evidence_kind,
access_state,license_or_access_state}`.
`validate_segment(segment)` rejects negative/noninteger/bool timestamps,
missing ends, `end <= start`, negative game clock and unpermitted access/rights.
Video interval and nullable game clock are independent; no global offset or
past knowledge is inferred. Rights/access must both equal `PERMITTED` for a
segment reference. `TRANSCRIPT` needs cue IDs; `VISUAL` needs
`scene_verified:true`; `AI_INTERPRETATION` remains interpretation. Supplied
verification assertions are not independently authenticated by this validator.
Nothing in this release creates a real transcript/visual segment or promotes
an expert statement to a visual observation. Player perspective remains unknown
unless separately established; spectator visibility is not player knowledge.

Lesson metadata:
`{lesson_id,title,primary_topic_id,secondary_topic_ids,champions,roles,opponents,
ally_support,enemy_support,situation_tags,phase,claim_ids,source_ids,segment_ids,
registry_url,review_state,evidence_state,evidence_kinds,source_patches,
patch_state,patch_compatible,patch_limits,coaching_enabled:false}` plus the
eleven card fields below and `question_origin`. Link-only lessons also have
`video_id`. Claim IDs, source IDs and review states are references to the
unchanged registry. Registry-backed evidence is explicitly labeled
`SOURCE_TEXT_REFERENCE` plus `AI_INTERPRETATION`, never visual verification or
new transcript evidence. Existing review labels are not USER approval.

| Card field | Available content |
|---|---|
| `question` | App-authored condition-change reflection, or null |
| `goal` | null until explicitly sourced |
| `threat` | null until explicitly sourced |
| `action` | Existing claim `display_text` or `text` reference |
| `reason` | null until explicitly sourced |
| `required_conditions` | Existing `conditions` reference, or null |
| `stop_or_switch` | Existing `counterexamples` reference, or null |
| `waiting_cost` | null until explicitly sourced |
| `alternative_or_recovery` | Existing `counterexamples` reference, or null |
| `practice_id` | Existing reflection ID, or null |
| `source_refs` | Array of `{source_id}` references; empty if unavailable |

A tactical field reference is exactly `{claim_id,field}`, resolved by looking
up the existing claim ID inside `loading-knowledge.json`'s `matchups[].claims[]`.
Only the named existing field is rendered. No duplicated tactical text, new
conditions or inferred missing paragraph are stored. Missing values display
as **미확인**. `question_origin` is
`APP_AUTHORED_REFLECTION_NOT_SOURCE_QUOTE`, or null.
Current `ally_support`, `enemy_support`, phase and situation metadata remain
null/empty rather than guessing them from a champion name or prose.

Practice:
`{practice_id,lesson_id,claim_ids,kind:'CONDITION_CHANGE_REFLECTION',question,
question_origin:'APP_AUTHORED_REFLECTION_NOT_SOURCE_QUOTE',condition_ref,
counterexample_ref,auto_grade:false,coaching_enabled:false}`.
The learner changes one existing condition and reflects against the existing
counterexamples. No generated answer, automatic correctness judgment, executable
condition evaluator, or tactical recommendation engine is added.

## Pure search API

```python
build_index(root: Path | str, *, knowledge=None, candidates=None) -> dict
validate_index(index: dict) -> dict
validate_segment(segment: dict) -> dict
search_index(index, query='', *, topic_id=None, role=None, champion=None,
             opponent=None, situation=None, evidence_state=None, patch=None,
             limit=100, offset=0) -> dict
```

`build_index` optional dictionaries support offline boundary tests; normal
builds always use the three explicit files. Its public projection is an
allowlist, omitting account/PUUID/match identity, private notes, transcript text,
source excerpts and arbitrary extra input keys. No private store is an input.

Search AND-combines filters. NFC/casefold literal text terms search title,
lesson/claim IDs, champion/opponent/role/situation identities, and all three
taxonomy labels. Tactical prose is resolved from the registry for display; it
is not copied into a second full-text corpus. Topic selection accepts group,
middle or leaf IDs; `UNCLASSIFIED` selects null primary topics. Unknown filter
values produce an empty result. Champion, role, opponent, situation and
evidence-state filters use exact case-insensitive identities. Unknown situation
tags never match a guessed situation. Stable lesson-ID order and a deep-copied
page prevent mutation of the original index.

Search output:
`{format:'lol-coach-learning-room-v1-search',total,offset,limit,lessons,facets,
unknown_patch_count,patch_mismatch_count,coaching_enabled:false}`.
Facets are `roles`, `champions`, `opponents`, `situations`, `evidence_states`,
derived from all selected rows before pagination. `1 <= limit <= 500`, integer
`offset >= 0`; booleans are invalid integers.

`source_patches` contains exact preserved source labels. Patch filtering is
literal, **not a current-patch compatibility assertion**. In particular 26.x
and 16.x are not mapped. Null source patch is never filled from the catalog's
official patch. `patch_compatible` stays null. `unknown_patch_count` counts
otherwise-matching lessons with no known source patch; `patch_mismatch_count`
counts otherwise-matching lessons with known labels but none matching the
requested label. Both counts precede pagination; unknown rows are excluded when
a patch is requested. Existing `patch_limits` remain a registry reference.

## Boundaries and verification

Every index/lesson/practice keeps coaching disabled. Validation rejects coaching
promotion, duplicate identities, dangling source/segment/practice references,
unsafe URLs, mismatched video URLs, invalid taxonomy and unpermitted segments.
Search and build neither mutate sources nor create USER/PC/GitHub decisions.
`python -m unittest tests_pregame.test_learning_room` covers exact taxonomy
searching, unknown video state, preserved failures, filters/patches, privacy,
rights, time intervals, clocks, shared segments, unique IDs, pagination,
deterministic regeneration and approval boundaries. Integration/browser/deploy
and real coaching effectiveness are separate evidence scopes.
