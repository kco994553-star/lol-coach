# R7 공개 플레이어 POV 취득 감사

2026-10-05 UTC. **새 원 게시자 Vimeo 플레이어 POV 15초 sequence를 실제 취득하고 decode 가능성을 확인했다.** Reference 선동결 및 State/Decision 추출은 root operator의 별도 단계다. 이번 discovery agent는 OCR·Vision·State 추출을 실행하지 않았으며, 완전한 실제 Reference나 coaching accuracy를 주장하지 않는다. R8 작업은 하지 않았다.

## 취득한 새 source

[원 게시자 canonical video](https://vimeo.com/651298214)의 제목은 `League of Legends 2021.11.29 - 21.58.38.07.DVR_Trim.mp4`다. 원 page JSON-LD는 [동일 uploader profile](https://vimeo.com/user158549888), uploadDate `2021-11-29T21:25:45+00:00`, 15초·1920×1080 영상을 연결한다. 게시 계정은 확인했지만 uploader와 실제 gameplay controller의 동일인 여부, 정확한 match ID·patch는 독립 인증하지 않았다.

canonical page와 page가 직접 광고한 embed를 HTTP200으로 받았다. embed가 광고한 HLS master 및 1080p variant와 native init·3개 ordered video fragment도 HTTP200이다. native fragment bytes를 순서대로 합쳐 video-only 파일을 만들었으며, pixel 수정이나 재인코딩 없이 FFprobe가 H.264·1920×1080·30fps·15.033333초를 확인했다. 총 native media는 **10,777,539 bytes**로 설정한 16MB 상한 안이다. Audio는 취득하지 않았다. 만료형 media URL·원 page 내용·게임 화면·player name을 공개 evidence에 재게시하지 않는다.

| 항목 | 취득 결과 |
|---|---|
| 공개 thumbnail | 334,881 bytes; SHA256 `95049a513dd2a8f673c10a5a262aeae09ff0c4be6ba703cb91c162ca7669dd47` |
| native sequence | 10,777,539 bytes; SHA256 `94ee285b5270ea0157170645d4a8d845b9e14205fbc55b0a11d393d7210f4372` |
| acquisition-quality view | 주 화면·minimap·clock·own HUD 표시. replay timeline 없는 player-style 화면 |
| thumbnail 시계 | 16:49. decoded frame별 clock은 operator Reference 단계에서 확인 |
| decode-only PNG | clip offset 0.1·5·10·14초. crop·overlay·OCR 없음; discovery agent는 이 PNG를 보지 않음 |
| 외부 overlay | 오른쪽 외부 통계 overlay 존재. 해당 수치를 원 게임 HUD 또는 player-known 사실로 취급하지 않음 |

원본과 decode-only frame, page·segment receipts는 Git 밖 `private-r7-player-grounded/`에 두었다. 공개 감사 JSON에는 정확한 filename·size·hash 및 clip offset을 기록했다. 취득 성공 notice와 playable-video notice를 감사 종료 전에 root에 전달하여 operator Reference lock을 먼저 수행할 수 있게 했다.

## 서로 다른 공개 경로와 정확한 blocker

| 경로 | 실제 결과 | 처리 |
|---|---|---|
| 특정 Medal clip | search index에 신규 clip shell. 직접 unauthenticated page HTTP403 | 해당 URL 1회 후 중단, 플랫폼 전체 unavailable 주장 없음 |
| Reddit 원 POV post | poster의 자기 POV 설명은 검색됨. search-service source fetch `DisabledError` | direct HTTP request는 하지 않았고 HTTP403으로 바꾸어 보고하지 않음 |
| 원 poster가 연결한 Streamable | GameFAQs의 자기 경기 설명·clip URL. exact clip 직접 HTTP404 | 1회 후 중단 |
| 원 research/developer project | CSCI599 primary report의 own screenshot·custom testing 설명 확인 | 해당 project에서 신규 연속 sequence 취득은 없음 |
| GitHub 원 developer demo | 고정 revision asset 15,119,287 bytes HTTP200, Git blob hash 일치 | practice-tool·debug overlay·일반 clock 가독성 부족. player scenario Reference에서 제외하고 reserve 취득만 보존 |
| 별도 Vimeo660 | page·thumbnail 취득 성공. 양팀 sidebar·replay timeline이 보이는 observer view | full clip 취득 안 함, player Reference에서 제외 |
| Vimeo651 | primary page·advertised HLS의 플레이어 POV sequence 실제 취득 | 이번 새 usable source 1개. root operator Reference lock 필요 |

세 search round로 materially different route를 검토했고, playable primary uploader sequence 성공 후 추가 discovery를 중단했다. 이전 원본5·GameStar gallery·실패했던 YouTube `CejHqSces8Q`·동일 HF pair를 재취득하거나 새 source로 재계수하지 않았다. pay·credential·bot bypass·대규모 전체 dataset 취득·외부 사용자 메시지는 없었다.

## 정보 경계

이 sequence와 보존된 HF `EUW1_7095952008` pair는 **join하지 않는다**. 같은 match ID가 없으며 새 POV의 제목·게시일은2021, HF pair는2024다. page의 capture filename이나 uploader 존재를 exact patch 인증으로 바꾸지 않는다. fragment 관계는 동일 advertised rendition의 순서로 확인했지만, 게임 시계와 POV 연속성은 root operator가 원 pixels를 확인하여 Reference에 선확정한다.

discovery agent의 actual state extraction·OCR·Vision은0이다. 완전한 actual State/Decision Reference 수·Decision validity·coaching N·accuracy는 이번 취득 감사에서 산출하지 않았다. 공개 POV를 전혀 구할 수 없다는 전체환경 결론도 내리지 않는다. 상세 receipt와 blocker는 [public-pov-audit.json](../../evidence/r7-player-grounded/public-pov-audit.json)에 있다.


## 추가 독립 감사: 동일 capture의 전후 구간과 identity

2026-10-05 UTC. 최초 취득·제한·hash 결과를 위에 그대로 보존하고, root 요청에 따라 공개 primary 경로를 추가 확인했다. **원15초 capture의 더 긴 전후 구간·결정 전5–10초·독립 같은시각 truth는 직접 연결되지 않았다.** 이 결론은 아래 확인 범위이며 전체 인터넷의 획득 불가를 뜻하지 않는다.

[원 uploader profile](https://vimeo.com/user158549888), [public videos list](https://vimeo.com/user158549888/videos), [anonymous public list metadata](https://vimeo.com/api/v2/user158549888/videos.json), page가 광고한 [RSS](https://vimeo.com/user158549888/videos/rss)는 모두 직접 HTTP200이다. HTML·list API·RSS는 각각 동일6개 video를 제공했다. 원 filename 일치 항목은651298214 한 개이고, 원 metadata의 duration은15초·description과 tags는 비어 있다. 공개 list page2는 HTTP400으로1회 후 종료했다. 해당 응답을 private/unlisted 계정 내용의 부재 인증으로 해석하지 않는다.

보존된 원 page/embed의 공개 metadata에는 matchId·gameId·patch가 없고 available version은 current1개다. 기존 클립을 다시 받지 않았다. 두 search engine에서 exact filename·uploader/profile·원 video ID를 좁게 검색했지만 결과는 기존15초 원 video뿐이며, full original·earlier interval을 직접 연결하는 신규 source는 찾지 못했다.

### 같은 uploader의 인접34초 capture

public list와 RSS가 [별도34초 원 upload651298774](https://vimeo.com/651298774)를 직접 연결한다. 제목은 `League of Legends 2021.11.29 - 22.01.37.08.DVR_Trim.mp4`, 원 page JSON-LD uploadDate는 `2021-11-29T21:27:29+00:00`다. canonical page와 page가 직접 광고한 original thumbnail만 HTTP200으로 취득했고 full media는 받지 않았다.

original thumbnail은 주 화면·minimap·own Tristana HUD·**19:00 clock**을 보인다. 같은 uploader, 같은 champion, 같은 visible controller identifier text는 연관성 hint다. 원15초와 filename 시간이 다르고 clock overlap·명시 matchID·patch가 없으므로 same-game/session 인증, 원15초의 pre-context 또는 independent same-time truth로 바꾸지 않았다. 원본 Reference 수정·match join·추가 denominator 기여는 모두0이다. thumbnail의 external stats overlay 수치도 근거로 승격하지 않았다.

### 최초 NOT_RUN 후보의 직접 요청 판정

위 최초 표의 `direct_request NOT_RUN`은 최초 시점의 기록으로 유지한다. 이번 추가 요청으로 해당 후보의 pending은 제거했다.

| 최초 후보 | 추가 실제 판정 | bounded blocker |
|---|---|---|
| Medal second exactURL | 공개 unauthenticated direct read1회, HTTP403 | 이 URL의403. retry·다른 사용자·bot 우회 없음 |
| Reddit 원 POV exactURL | 공개 unauthenticated direct read1회, HTTP200·8,431bytes | 실제post/media 대신 automatic JavaScript challenge form. post title/caption/media URL 없음. challenge 실행·submit하지 않고 종료 |

Reddit HTTP200을 원post 취득 성공으로 표시하지 않으며, 이전 search-service `DisabledError`와 이번 direct-read challenge를 구분한다. 이번에 확인한 candidate direct route에 남은 미시도는0이다. 원 클립/HF/옛5화면 재취득·재계수나 신규 Reference 생성은 하지 않았다.

남은 자료는 **동일 capture의 시작 전 실제 구간**, capture에 직접 연결된 **정확한 match/session ID·patch**, 그리고 **독립 동일 경기·동일 clock truth 또는 시야 기록**이다. 공개 primary profile·목록·metadata·RSS와 두 exact search 경로를 확인한 뒤 이 좁은 누락을 기록하고 종료했다. 관련 원본 metadata·thumbnail은 Git 밖에 보관하며, 상세 additive receipts는 `public-pov-audit.json`의 `followup_primary_context_audit`에 있다.
