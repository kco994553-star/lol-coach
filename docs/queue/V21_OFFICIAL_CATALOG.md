# Queue v2.1 공식 한국어 전체 챔피언 자료

2026-10-15 실제 `https://ddragon.leagueoflegends.com/api/versions.json`의 첫 버전은 **16.20.1**이었다. 같은 버전 `ko_KR/champion.json`에서 **173명**을 확인하고, 전원 패시브와 Q/W/E/R **865개**의 한국어 이름·설명을 보관했다. HTML은 표시할 때 제거하고 원본 바이트는 그대로 보존한다. 이전 고정 13명 `official_reference`와 동결 계약은 수정하지 않았다. 그 13명의 원본은 기존 manifest의 SHA-256과 정확히 일치하는 경우에만 재사용했다.

## 저장 및 출처

`data/official_catalog/current.json`은 버전과 manifest SHA-256을 가리킨다. `versions/16.20.1/`에는 수집 당시의 `versions.json`, `champion.ko_KR.json`, `챔피언-16.20.1.ko_KR.json` 원본, `manifest.json`이 있다. manifest는 각 원본의 정확한 HTTPS URL, SHA-256, 버전, locale, 수집 시각을 보존한다. 스킬의 `source.locator`는 해당 JSON의 실제 필드를 가리킨다.

새 버전은 임시 디렉터리에서 전체 명단·설명·해시를 검증한 후 별도 버전 디렉터리로 이동한다. `current.json`은 `os.replace`로 원자적으로 교체한다. 기존 버전은 덮어쓰거나 삭제하지 않는다. 같은 버전을 재확인할 때는 보관 자료 전부를 다시 검증하고 포인터만 유지한다. 자료 하나라도 잘못되거나 다운로드가 실패하면 이전 포인터를 유지한다.

## 호출 인터페이스

```python
from coach_v1.official_catalog import facts_response, request_facts, refresh_if_due

facts_response()                         # 전체 명단, 외부 연결 없음
facts_response(['Ahri', 'Yunara'], patch='16.20')
request_facts({'champions': ['Ahri'], 'patch': '16.21'})
status = refresh_if_due()                 # 로컬 앱 시작 때 한 번 호출
```

`facts_response(champions=None, patch=None)`는 기존 `official-reference.v1` 형태를 유지한다. `approval_required=False`, `reference_only=True`, `game_patch`, `reference_status`, `champions`, `unavailable` 및 챔피언별 `facts`를 제공한다. 추가 메타데이터는 `source_patch`, `locale`, `catalog_champion_count`, `catalog_schema_version`, `refresh_status`다. `request_facts(body)`는 `{champions, patch}`만 받으며 최대 300명, 안전한 챔피언 ID, 문자열 또는 null patch를 검증한다. 잘못된 요청은 기존 `ServiceError(422, 'INVALID_OFFICIAL_REFERENCE_REQUEST')`다.

`patch`는 사용자가 실제 입력한 값을 그대로 보존한다. 입력이 없으면 `GAME_PATCH_UNKNOWN`, 보관 버전 `16.20.1` 또는 그 게임 패치 `16.20`과 일치하면 `MATCHING_ARCHIVE`, 그 외에는 `GAME_PATCH_MISMATCH`다. CDN 최신 버전을 사용자의 실제 게임 패치로 대신 기록하지 않는다. 자료 손상·미보관 챔피언은 `unavailable`로 반환한다. manifest·명단 검증이 실패하면 전체 상태는 `UNAVAILABLE`이다.

공식 설명은 참고 사실이며 전술 검증이나 USER 승인·결정을 생성하지 않는다. 수치·툴팁의 런타임 계산이나 전술 해석을 추가하지 않는다.

## 자동 갱신 및 오프라인

`refresh_if_due(*, max_age_seconds=86400, force=False, fetch=None)`를 런처에서 서버 시작 전에 호출한다. 기본 성공 재확인은 하루 간격이며 실패 후에는 한 시간 간격으로 재시도한다. `force=True`는 간격을 무시한다. `update_catalog(*, fetch=None)`는 무조건 새 버전 확인을 수행한다. `fetch`는 테스트나 별도 전송 계층에 사용할 선택 인자로 `(url, byte_limit, timeout_seconds) -> bytes`다.

```sh
python scripts/update_official_catalog.py
python scripts/update_official_catalog.py --force
python scripts/update_official_catalog.py --max-age-seconds 86400
```

반환 상태는 `UPDATED`, `UNCHANGED`, `FRESH`, `OFFLINE_FALLBACK`, `UNAVAILABLE`이며 `refresh-status.json`에 최근 실제 시도 시각과 실패 이유를 저장한다. 오프라인에서도 검증된 전체 보관 자료가 있으면 `OFFLINE_FALLBACK`으로 읽기를 계속한다. 보관 자료도 없으면 `UNAVAILABLE`이다. 명령 종료 코드는 사용할 자료가 있으면 0, 없으면 1이다. UI의 `facts_response`는 읽기만 하므로 요청마다 인터넷에 연결하지 않는다.

공식 HTTPS URL만 허용하고 리다이렉트는 거절한다. 요청별 timeout은 12초, 동시 작업은 8개로 제한한다. 최대 버전 목록 200 KB, 명단 5 MB, 챔피언 원본 각각 2 MB, 명단 300명이다. 버전·ID·필드·패시브 및 정확히 네 스킬·전체 명단 일치·해시를 검증한다. `versions.json`의 과거 `lolpatch_*` 명칭은 허용하되 실제 수집할 첫 버전은 안전한 숫자 버전만 허용한다. `.refresh-lock` 파일에는 PID·호스트·획득 시각을 기록하고 네이티브 배타 잠금(Unix `flock`, Windows `msvcrt`)으로 중복 갱신을 막는다. 프로세스가 강제 종료되면 OS가 잠금을 해제하므로 다음 시작에서 자동 복구한다. 남은 PID 메타데이터만으로 활성 프로세스의 잠금을 탈취하지 않는다.

## 검증

`python -m unittest tests_pregame.test_official_catalog -q`는 버전 발견, 완전 수집, 정확한 원본·해시, 새 버전 보존, 수집 실패 시 포인터 유지, 오프라인 및 재시도 간격, 실제 패치 불일치, 개별 손상·미보관 챔피언, 잘못된 명단·크기·버전, 레거시 재사용, 전체 실자료의 한국어 5개 설명을 검증한다. 네트워크는 테스트에 필요 없다.
