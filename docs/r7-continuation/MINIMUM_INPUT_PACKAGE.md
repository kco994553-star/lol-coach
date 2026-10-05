# 실제 State/Decision 검증에 필요한 최소 자료

**우선 한 장면이면 시작할 수 있다.** 현재 실제 동일 경기 Match·Timeline pair와 공개 정지 화면은 확보되어 있다. 부족한 것은 같은 장면에서 플레이어가 볼 수 있었던 정보와 행동 전후 순서다.

| 자료 | 최소 준비 형태 | 가능한 검증 |
|---|---|---|
| Player POV clip | MP4/WebM, 보통15–30초: 결정 전5–10초와 공격/응답/이탈. 원본 clock·minimap·HP·level·skill HUD가 읽히게 유지 | trade sequence, 스킬 대상/순서, 피해·위협 흡수, follow-up 접근, 실제 퇴로 |
| Screenshot만 있을 때 | PNG/JPEG 원본1장, 본 화면·minimap·clock·HUD 포함. 1080p 권장이나 acceptance cutoff는 아님 | 해당 시점 HP/level/CS, visible 인원, 정적 wave geometry·spacing. 동작 순서/의도/안전한 퇴로 확정 불가 |
| 짧은 sidecar 메모 | 촬영 출처/저장 경로, 자기 champion, 관점, 게임 clock·영상 내 시간, patch·matchId는 알면 기재/모르면 UNKNOWN | 시점·관점·source 연결. 닉네임/credential/API key 불필요 |
| 구조화 수집물, 있으면 | 실제 게임 PC의 기존 `scripts/collect_local.py` 원본과 receipt, 또는 동일 matchId의 Match·Timeline | Reference와 current extraction 비교. PC 간 source 관계가 있어야 해당 clip에 연결 가능 |

길이는 안내이며 새 TTL·품질 점수·정확도 목표가 아니다. 모르는 patch 때문에 HUD-only 기준 작성부터 막지 않는다. patch에 따라 달라지는 Knowledge/Decision 검토는 버전 확인이 필요하다. source 경로나 공개 링크가 있으면 기존 자료부터 검토할 수 있다.

첫 장면은 Lane/CS/trade, 다음은 정글 uncertainty/last-seen, 세 번째는 Teamfight/threat absorption/damage window를 권장한다. 숨겨진 정글 위치를 모르는 것은 유효한 UNKNOWN이며 반드시 답을 채울 필요는 없다. 다만 주 화면에 적이 없다는 것과 맵에 적이 없다는 것을 구분한다.

관전자 Replay는 별도 Ground Truth/원본 추출 비교에 사용할 수 있다. 같은 경기·시각의 player POV와 연결될 때 실제 no-hindsight 대조가 가능하다. fog 해제, 양 팀 HUD, 숨겨진 위치, 이후 승패는 Decision input에서 제외한다. 팀 fog를 켠 관전자도 player POV와 자동으로 같아지지 않는다.

텍스트 메모 예시:

```json
{
  "source_location": "공개 링크 또는 이미 보존한 원본 경로",
  "perspective": "PLAYER",
  "own_champion": "알고 있는 이름",
  "patch_version": null,
  "match_id": null,
  "clip_time_seconds_at_decision": 8,
  "game_clock_at_decision": "05:00",
  "capture_method": "플레이어 화면 녹화",
  "direct_observations": [],
  "inferences": [],
  "unknown_information": [],
  "ground_truth_source_separate": null
}
```

이 메모의 선언만으로 VERIFIED로 승격하지 않는다. 원본 hash와 실제 HUD·관점·clock을 확인한 후 operator Reference를 먼저 잠근다. 계정 비밀번호, Riot API secret, PC 원격제어 또는 유료 서비스는 이 최소 패키지에 필요하지 않다.
