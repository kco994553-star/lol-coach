# Directions prototype — official assets and policy evidence

Checked 2026-10-17T02:53:05.894460+00:00. This evidence supports static provenance and a **PRE_GAME learning / POST_GAME review** scope; it does not establish Riot approval, current game state or tactical accuracy.

## Assets

| File | Official build | Dimensions | Bytes | SHA-256 |
| --- | --- | --- | --- | --- |
| `web_r4/direction-assets/map11.png` | 16.20.1 | 512×512 | 70985 | `5b446777c3e8491c1ab1860bc8fd448ad58f46cf3630d909f74dd3dc3dda8cd1` |
| `web_r4/direction-assets/Caitlyn.png` | 16.20.1 | 128×128 | 25976 | `f7a515360f30f33dfe5ab4e8886ce59a70c2d333f924252f48f5f9a2fbc6edf4` |
| `web_r4/direction-assets/Fiora.png` | 16.20.1 | 128×128 | 28094 | `b76387ea62f007ece3e06e589ac15bc9bf5452472b70a0d847d096b06f6785b7` |
| `web_r4/direction-assets/Ornn.png` | 16.20.1 | 128×128 | 25086 | `91374f0919871a6490ac7b8ff9b073efb8b6a797f28302cc3751294c47c58d6e` |

Exact official CDN URLs, response headers and retrieval timestamps are in `config/direction_asset_sources.json` and the adjacent JSON receipt. The four PNG files are unmodified. Riot owns these assets; no MIT, CC or public-domain license is asserted. The repository software license does not relicense them.

## Map interpretation

The downloaded official `map11.png` is 512×512, with blue base lower-left and red base upper-right. It is a stylized schematic (olive paths, black jungle/background, cyan river), not a detailed current terrain model. Its 16.20.1 CDN path and Last-Modified header do not establish agreement with a running client or with current brush, objectives, spawn locations or traversability. No live or match data was retrieved.

Coordinates below use image top-left `(0,0)`, x increasing right and y increasing down. They are approximate visual display anchors chosen after inspecting the PNG, not Riot-provided coordinate metadata. Keep image and markers within the same square content box.

| Visual anchor | Normalized x | Normalized y |
| --- | --- | --- |
| 블루 진영 기지 | 0.18 | 0.81 |
| 레드 진영 기지 | 0.81 | 0.18 |
| 위쪽 라인 참고 | 0.13 | 0.14 |
| 중앙 라인 참고 | 0.5 | 0.5 |
| 아래쪽 라인 참고 | 0.86 | 0.85 |
| 상단 강가 원형 지형 | 0.332 | 0.293 |
| 하단 강가 원형 지형 | 0.67 | 0.703 |

## Official policy sources

### lol-docs

- Requested URL: https://developer.riotgames.com/docs/lol
- Resolved URL: https://developer.riotgames.com/docs/lol
- Retrieved: 2026-10-17T02:51:04.955939+00:00; HTTP 200; 99451 bytes.
- Raw response SHA-256: `27b0f04fd2fe07b1687039298937f21e8b283d088ab18f640962511275a137e2`.
- Page-displayed update: not displayed in the cited sections.

Developer API Policy / Game Integrity: “Products must not use or incorporate information not present in the game client that would give players a competitive edge”

Developer API Policy / Game Integrity: “Products should not remove game decisions, but may highlight decisions that are important and give multiple choices to help players make good decisions.”

Data Dragon: “All of which can be used by third-party developers.”

Data Dragon / Regions: “Data Dragon versions are not always equivalent to the League of Legends client version in a region.”

Data Dragon / Other / Minimaps: “The number appended to the map filename corresponds to the map id.”

### general-policy

- Requested URL: https://developer.riotgames.com/policies/general
- Resolved URL: https://developer.riotgames.com/policies/general
- Retrieved: 2026-10-17T02:51:05.014821+00:00; HTTP 200; 18909 bytes.
- Raw response SHA-256: `27c3dec47858d90693ab46e71a0152cbc8394b32a56d50ed70b3da5a2537b8a1`.
- Page-displayed update: May 29, 2025.

Core Policies: “Use the following assets in the development and marketing of your product:
Data Dragon”

Product Registration: “All products must be registered in, and audited by Riot Games through the Developer Portal”

Product Registration: “Any new features or changes to a product must be audited through the product’s page in the Developer Portal”

Core Policies / legal boilerplate: “[Your product] isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.”

### third-party-applications

- Requested URL: https://support-leagueoflegends.riotgames.com/hc/en-us/articles/225266848-Third-Party-Applications
- Resolved URL: https://support.riotgames.com/en-us/riot/events/third-party-applications
- Retrieved: 2026-10-17T02:51:05.033495+00:00; HTTP 200; 155454 bytes.
- Raw response SHA-256: `a5349d22c07cbc218b502393ebf5886ad6b5d53a829ca1dbc0816c5d9fe28a56`.
- Page-displayed update: February 10, 2025 at 4:52 PM.

Riot's Stance: “Exposing information that's intentionally obfuscated”

Riot's Stance: “Taking actions on your behalf (botting or scripting)”

Riot's Stance: “Drawing conclusions for you during gameplay (ie we want to see you play the game first, then analyze and reflect later!)”

### legal-jibber-jabber

- Requested URL: https://www.riotgames.com/en/legal
- Resolved URL: https://www.riotgames.com/en/legal
- Retrieved: 2026-10-17T02:51:05.057588+00:00; HTTP 200; 79271 bytes.
- Raw response SHA-256: `04b2f929aa0af0a00e1e9e743bd6e61d24b198570974e5caad1b5ee15376d1fd`.
- Page-displayed update: August 2018.

1. What can I develop with Riot’s IP?: “personal, non-exclusive, non-sublicenseable, non-transferable, revocable, limited license”

1. What can I develop with Riot’s IP?: “strictly for noncommercial (except as specifically provided below) community use”

3. No unauthorized games or apps.: “We prohibit the use of our IP in games and apps.”

6. Can I share my Project with the community?: “[The title of your Project] was created under Riot Games' "Legal Jibber Jabber" policy using assets owned by Riot Games. Riot Games does not endorse or sponsor this project.”

## Prototype boundary

- Official Data Dragon assets may be used under Riot policy conditions; this does not establish registration, audit, endorsement or blanket permission for every product feature.
- The support page separately prohibits drawing conclusions during gameplay and acting on a player's behalf. Merely labelling a feature static, manual or reference does not establish permission for live tactical recommendations.
- This prototype is scoped to pre-game learning and post-game review; new live automation or real-time decision features are outside this evidence.
- Developer Portal registration and feature audit are Riot requirements. Their completion for this product is not established by these source GETs.
- IP remains Riot's. A software repository license does not relicense these assets. Legal Jibber Jabber contains revocable conditional permissions and restrictions; Developer/API policies must also be considered.

- No live game collection, game-input automation, enemy hidden-state access, cooldown tracking, or live tactical commands. Scenario arrows and tokens are hypothetical learning illustrations.
- Static/manual/reference labels do not prove a live feature is permissible. The product must not claim registration, audit or Riot endorsement from these GETs.
- Existing official Korean champion excerpts were reused from the 16.20.1 archive with manifest SHA-256 checks; exact field locators are in the JSON. These are official static facts, not approved tactical interpretations.

Visible scope note: 경기 전 학습 · 경기 후 복기용. 실제 경기 중 전술 지시나 자동 조작을 제공하지 않습니다.

Visible asset attribution: 지도·챔피언 초상화: Riot Games Data Dragon 16.20.1. 화면의 위치·동선은 학습용 예시이며 실시간 관측이 아닙니다.

Required visible developer-policy disclaimer:

LoL Coach isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

## Bounded collection and checks

Eight requested public GET resources succeeded (four small official PNG assets and four official policy/documentation pages; the support URL redirected to the current official support page). No API key, paid service, Gemini, YouTube API, Riot Match API, new game, video, audio or transcript original was used. October 17 KST video usage remains 3/3. HTML originals remain temporary outside the repository; bounded exact policy excerpts, dates and response/text/quote hashes are preserved.

PNG signatures, dimensions, local SHA-256 values, exact excerpt inclusion and champion archive hashes were checked. The map was visually inspected. No old full test discovery, install or baseline run was performed.
