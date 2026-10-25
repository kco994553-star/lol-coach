# 챔피언 맞상대 지식 참고 자료 v1

같은 포지션의 상대가 어려운 이유와 접근 방법을 공략 저자의 설명에서 정리한다. 승률, 통계 티어, 조회 중인 티어 필터로 상성을 계산하지 않는다. 공략 의견과 AI 해석을 전술 검증이나 사용자 승인으로 승격하지 않으며 실제 코칭 제공을 뜻하지 않는다.

## 자료와 재생성

- 편집 원본: `config/champion_matchup_references.json`
- 검증·선택 함수: `coach_v1/champion_matchup_knowledge.py`
- 공개 정적 자료: `web_r4/champion-matchup-knowledge.json`
- 재생성: `python scripts/build_champion_matchup_knowledge.py`
- 일치 확인: `python scripts/build_champion_matchup_knowledge.py --check`
- 집중 검증: `python -m unittest tests_pregame.test_champion_matchup_knowledge`

빌드는 로컬의 공식 카탈로그와 기존 `loading-knowledge.json` 출처 ID만 읽는다. 네트워크, 통계 자료, 사용자 결정 저장소 또는 게임플랜 규칙을 호출하거나 변경하지 않는다. 새 출처는 URL SHA-256 앞 16자리로 안정적인 ID를 만들며, 같은 원문 URL이 기존 출처 목록에 있으면 기존 ID를 재사용한다. 리다이렉트 전 URL과 실제 열람 URL을 각각 보존한다.

## 공개 계약

최상위 `schema_version`은 `champion-matchup-knowledge-v1`, `version`은 `1`이다. `catalog_patch`, `champion_ids`, `sources`, `records`, `coverage`, `limits`를 제공한다. `tier_independent=true`, `derived_from_statistics=false`, `coaching=false`, `tactical_validation=UNREVIEWED`를 고정한다.

각 기록의 `id`는 `champion:position:opponent`다. 챔피언은 공식 로컬 카탈로그의 정확한 ID, 포지션은 TOP/JUNGLE/MID/BOTTOM/SUPPORT를 사용한다. 상대 포지션도 같아야 한다. 같은 쌍의 상충하거나 중복된 기록을 허용하지 않는다.

| 필드 | 의미 |
|---|---|
| `author_category` | 공략 저자의 원래 Extreme/Major/Even/Minor/Tiny 분류. 전체 경기 구간에 대한 분류일 수 있다. |
| `assessment_scope` | LANING, JUNGLE, OVERALL_UNSPECIFIED 중 하나. |
| `assessment_origin` | 직접 구간 설명의 SOURCE_PARAPHRASE 또는 구간 적용을 포함한 AI_INTERPRETATION. |
| `qualitative_difficulty` | DIFFICULT, RELATIVELY_EASIER_CONDITIONAL, UNKNOWN_FOR_SCOPE. 수치 강도나 승률이 아니다. |
| `publication_eligibility` | CONDITIONAL_CANDIDATE는 해당 구간의 조건부 후보, REFERENCE_ONLY는 전체 구간 참고 자료. |
| `reason`, `action`, `change_if` | `text_ko`, `origin`, `source_quote_refs`를 가진 객체. 이유는 저자 설명 요약, 행동은 AI 조건부 해석, 재검토 조건은 AI 제한 조건이다. |
| `source_refs` | 출처 목록의 안정적인 ID. |
| `evidence` | 인용·문단 SHA-256, 원문 위치, HTML 줄 번호, 인용 ID와 대조 상태. 원문 텍스트는 공개하지 않는다. |
| `patch_scope` | 공식 카탈로그 버전, 공략 표기, 대응 미확인 상태, 개별 문단 갱신일 미상. |

Extreme/Major만 어려운 후보에, Tiny/Minor만 상대적으로 쉬운 조건부 후보에 들어간다. 전체 구간 참고 기록은 OVERALL_UNSPECIFIED 및 UNKNOWN_FOR_SCOPE만 허용한다. 같은 저자의 낮은 전체 분류와 강한 초반 설명이 충돌하면 쉬운 라인 목록에 넣지 않는다. 예를 들어 이즈리얼 공략의 케이틀린·루시안 Minor 분류는 초반 강함 경고와 함께 별도 참고 기록으로만 보존한다.

공식 16.20.1과 공략 26.x의 패치 대응을 확인하지 않았다. 페이지 갱신일은 개별 문단 갱신 증거가 아니다. 피오라의 현행 제목 아래에도 과거 아이템 용어가 남아 있어 현재 빌드, 정확한 쿨타임, 확정 승리나 고정 성장 분기점으로 채택하지 않는다. 원문에 설명 없이 강하다고만 적힌 항목도 후보에서 제외한다.

## 선택 함수와 표시

`select_knowledge(index, champion, position)`는 `{difficult, easier, conditional, references, coverage, limits}`를 반환한다. `conditional`은 실제 선택한 difficult와 easier의 합이다. 전체 구간 자료는 `references`로만 반환한다. 정글은 JUNGLE 구간, 나머지는 LANING 구간만 후보에 포함한다.

두 후보 목록은 각각 최대 다섯 개다. 어려움은 Extreme 다음 Major, 쉬움은 Tiny 다음 Minor로 표시하며 같은 분류 안에서는 상대의 카탈로그 ID로 안정적으로 정렬한다. 이것은 출처의 분류 순서와 표시 안정성을 위한 규칙이며 내부 순위나 전 세계 TOP5를 뜻하지 않는다. 번호로 상성 순위를 표시하지 않는다. 부족한 자리를 다른 구간·같은 분류·통계 승자로 채우지 않는다.

| 챔피언 / 포지션 | 어려운 후보 | 상대적으로 쉬운 조건부 후보 | 별도 전체 구간 참고 |
|---|---:|---:|---:|
| Caitlyn / BOTTOM | 4 | 3 | 2 |
| Ezreal / BOTTOM | 3 | 2 | 4 |
| Fiora / TOP | 5 | 5 | 0 |
| Graves / JUNGLE | 5 | 5 | 0 |
| Yunara / BOTTOM | 5 | 2 | 0 |

39개 조건부 후보와 6개 전체 구간 참고, 5개 출처만 보유한다. 그레이브즈는 정글 추적, 캠프 성장, 침입, 역갱, 교전 접근과 목표물 판단으로 설명한다. 다른 챔피언과 지원하지 않는 포지션은 `coverage.status=NO_RESEARCH` 및 빈 목록을 반환한다. 173개 전체 챔피언의 상성을 안다고 표시하지 않는다. 포지션 선택은 현재 역할 인기도나 통계 분포의 증명이 아니다.

## 원문 보존과 제한

공개 파일과 편집 설정에는 원문 전체 문단, HTML, 정확한 인용 문자열, 로컬 스냅샷 경로, 인증·개인 정보 필드를 넣지 않는다. 공개하는 연속 원문 인용은 0단어이며 분류 이름·제목·저자명만 출처 식별에 사용한다. 원문 대조는 출처 HTML SHA-256, 인용 SHA-256, 정규화 문단 SHA-256 및 위치로 추적한다. 원본 HTML과 원문 문단은 저장소·공개 경로 밖의 별도 연구 산출물로 보존한다. 빌드는 그 외부 자료가 없어도 재현되며 새 원문 대조를 수행했다고 주장하지 않는다.

현재 허용 출처는 인증 없이 HTTPS로 읽은 MOBAFire 원문 공략이다. 유료·인증·영상·내부 주소, URL 자격 증명이나 쿼리 토큰은 허용하지 않는다. 기존 지식 검토 결정과 동결 후보는 보존하며 이 자료를 승인 목록이나 게임플랜 실행 규칙으로 자동 연결하지 않는다.
