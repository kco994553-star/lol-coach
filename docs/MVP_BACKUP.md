# 개인 로컬 데이터 백업·복원

2026-10-05. 위험 DEEP. 기존 저장소·판단 코어·동결 설계는 변경하지 않는 추가 CLI다.
기존 `Store.backup()`은 합성 복기 DB 하나만 포함한다. 아래 명령은 합성 복기 DB와
`<db>.research.sqlite`의 자료·전체 노트 revision 이력을 함께 보관한다.
웹/API 백업 버튼은 없으며, 이 CLI가 완전한 **Workbench 저장 데이터** 복구 경로다.

## 백업

저장소 루트에서 기존 Python 3.12+ 앱 환경과 `requirements-r3.txt` 의존성을 사용한다.
현재 `ReviewInput` 계약의 검증을 재사용하므로 기존 Pydantic 설치가 필요하다.
새 패키지·클라우드·유료 서비스는 사용하지 않는다.

1. 로컬 서버를 `Ctrl+C`로 종료하고 종료가 끝날 때까지 기다린다.
2. 백업 대상 부모 폴더를 준비한다. 아래 예시는 `private/backups`가 이미 존재한다고 가정한다.
3. 존재하지 않는 새 백업 파일명을 지정한다.

```sh
python3 -m coach_v1.backup backup --db private/reviews.sqlite --output private/backups/personal-20261005.zip
```

`--db`와 정확히 같은 이름에 `.research.sqlite`를 붙인 파일이 모두 있어야 한다.
한쪽이 없으면 `SOURCE_MISSING` 또는 `RESEARCH_MISSING`으로 중단하며 빈 DB를 만들지 않는다.
이미 있는 출력 파일은 덮어쓰지 않는다. 성공은 stdout JSON과 종료 코드 0, 실패는
stderr JSON의 `error_code`와 종료 코드 1로 확인한다. POSIX 백업 파일 권한은 0600이다.

## 복원과 재열람

부모 폴더는 존재해야 하고 `--destination` 폴더 자체는 **존재하지 않아야** 한다.
비어 있는 기존 폴더도 거부한다. 기존 개인 파일을 이동하거나 덮어쓸 필요가 없다.

```sh
python3 -m coach_v1.backup restore --archive private/backups/personal-20261005.zip --destination private/restored-20261005
```

성공하면 새 폴더에 다음 두 파일이 생기며 stdout JSON의 `db`가 서버용 경로다.

| 파일 | 보존하는 데이터 |
|---|---|
| `workbench.sqlite` | 세션, 모든 사례 revision, 작업·저장 결과, idempotency 기록, 삭제 tombstone |
| `workbench.sqlite.research.sqlite` | 자료 보고서, 전체 노트 revision 이력 |

기존 서버 명령의 `--db`를 복원된 파일로 지정한다.

```sh
python3 -m coach_v1.server --db private/restored-20261005/workbench.sqlite --token-file private/token --port 8765 --max-body-bytes 1000000 --max-observations 1000 --max-actions 24 --max-scenarios 16 --max-comparisons 512 --max-pending-jobs 8
```

세션·최신 사례·저장 결과·자료·최신 노트를 다시 열 수 있다. 과거 노트 revision도 DB에
보존되지만 과거 revision 선택 UI는 기존 R6와 같이 아직 없다. 복원 CLI는 작업 상태를
바꾸지 않는다. 이후 서버 시작 시 기존 규칙대로 RUNNING은 INTERRUPTED 실패가 되고
QUEUED 작업은 이어서 처리한다.

## 검증·일관성 범위

ZIP은 버전 1 manifest와 위 두 DB만 허용한다. 중복·추가·누락·경로 이동·심볼릭 링크
멤버, 지원하지 않는 ZIP 옵션, 잘못된 JSON/버전/크기/SHA-256을 거부한다. DB의 버전·
전체 스키마 객체와 제약·SQLite integrity·foreign key를 확인한다. 기존 `ReviewInput`
검증에 더해 TEST/SYNTHETIC·세션/패치·연속 revision·작업/결과 참조·idempotency,
자료의 정규화 ID·노트 anchor/필드/연속 이력을 확인한다. 단순히 해시를 다시 계산한
잘못된 앱 데이터도 거부한다. 해시는 오류 감지용이며 작성자의 진위를 인증하지 않는다.

두 원본에 별도 `BEGIN IMMEDIATE` 예약 잠금을 모두 확보한 상태에서 별도의 읽기
연결로 SQLite 백업을 만든다. 두 DB가 함께 쓰기 차단된 한 시점의 **커밋된 상태**를
보관하며 진행 중인 앱 작업을 하나의 트랜잭션으로 합치지는 않는다. 서버 종료는 작업을
완료시킨 뒤 보관하기 위한 권장 절차다. 활성 SQLite writer는 `SOURCE_BUSY`로 빠르게
거부한다. 읽기 연결을 먼저 고정하고 쓰기 연결을 먼저 닫아 백업 자체의 hot-journal
복구와 WAL 최종 체크포인트를 피한다. 복구가 필요한 hot journal은 자동 복구하지 않고
거부한다. 각 DB 복사의 재시도는 30초 안에 중단한다.

원본 행·스키마에는 쓰지 않고 검증은 임시 복사본에서만 수행한다. 원본 DB와 입력 백업
파일을 교체하지 않는다. WAL/SHM 잠금 bookkeeping의 바이트 동일성까지 약속하지는
않는다. 복사본만 DELETE journal 모드의 독립 DB로 만든다. DB별 최대 256,000,000바이트,
manifest 최대 16,384바이트를 지원한다. symlink 경로·부모 경로·동일 파일 별칭·DB
bookkeeping 파일과 출력의 충돌을 거부한다. 신뢰하는 개인 로컬 폴더에서 실행한다.

모든 검증을 끝낸 후 새 결과를 공개한다. 백업은 원자적 no-overwrite hard link,
복원 폴더는 Linux `renameat2(RENAME_NOREPLACE)`, Windows `os.rename`, macOS
`renamex_np(RENAME_EXCL)`를 사용한다. 지원되지 않는 OS/파일시스템은
`ATOMIC_RESTORE_UNSUPPORTED`로 중단한다. Linux에서 기존 빈 폴더가 공개 직전에
생기는 실제 경쟁도 덮어쓰지 않는 것을 검증했다. Windows·macOS 실행 검증은 이
환경에서 하지 않았다. 실패하면 임시 폴더를 정리한다.

토큰 파일, 별도 수집 원본·외부 다운로드, 영상 파일은 이 두 DB에 포함되지 않는다.
자료 생성은 기존 R6와 같이 원본 전문 대신 진단/색인 보고서를 저장한다. 해당 외부
파일이 필요하면 개인 저장 경로에서 별도로 보관한다. 백업 ZIP은 암호화되지 않는다.

## 회귀 검증

```sh
python3 -m unittest tests_mvp.test_backup -v
```

Workbench를 통한 복원 재열람, 모든 사례·노트 이력, 두 원본 보존, WAL 커밋 데이터,
실제 hot-journal 거부, writer 충돌, 제한 시간 내 CLI 완료, 변조·누락·중복·경로 이동·
비호환/잘못된 앱 데이터, 빈 폴더 공개 경쟁, 실패 정리를 확인한다.
실행 결과는 `evidence/mvp/backup-validation.json`에 기록한다.
