# 실제 공개 화면 — 시안 구도 맞춤

사용 URL: https://kco994553-star.github.io/lol-coach/loading.html

예시 조합 → 분석 → 라인전/운영/한타 카드. 조합 수정은 내 챔피언·포지션 버튼에서 엽니다.

| 항목 | 이전 | 이번 반영 |
|---|---|---|
| 상단 | 별도 조합 수정 행, 작은 어두운 영웅 영역 | 브랜드·내 역할·10픽·공식 일러스트·큰 두 줄 제목을 한 영역에 배치 |
| 카드 | 긴 제목과 설명, 높은 카드 | 짧은 기존 계획 이름, 번호·공통 아이콘, 낮고 넓은 카드, 보라색 선택 표시 |
| 상세 | 탭부터 표시, 작은 사각 초상화 | 큰 개념 제목, 둥근 양쪽 초상화, 실행 5항목, 금색 변경 조건, 상세 펼치기 |
| 화면 폭 | 1440 이상 2패널 | 1280 이상 2패널/작은 PC·모바일 전체 폭 상세 |

## 실제 화면과 비교
- [이전 PC](../../gameplan-layout/publication/reference-Caitlyn-1280-detail.png) → [이번 PC1280×853](reference-Caitlyn-1280-detail.png)
- [케이틀린 기본 화면](reference-Caitlyn-1280-base.png)
- [아리 기본 화면](reference-Ahri-1280-base.png) · [아리 상세](reference-Ahri-1280-detail.png)
- [모바일 기본](mobile-summary.png) · [모바일 상세](mobile-lane.png)

첨부 시안의 읽는 순서·구도·색상·제목/카드 비중을 기준으로 비교했다. 시안의 생성
그림은 복사하지 않고 기존 공식 일러스트를 사용했다. 실제 분석 문장과 전체 실행
조건을 보존하므로 이미지 픽셀이나 본문 줄 수까지 동일하다고 주장하지 않는다.

## 데이터와 기능
같은 전략 결과에서 제목·카드·상대 구도·실행 방법을 생성한다. 짧은 이름은 이미
선택된 wave/operation ID의 표시용 명칭이며 판단 규칙이 아니다. 알 수 없는 ID는
기존 결론을 유지한다. 케이틀린/BOTTOM과 아리/MID를 실제 엔진 경로로 변경하여
초상화·일러스트·상대·내용이 함께 갱신되는 것을 확인했다. 아리–제드의 지식 부족은
시안 문구로 채우지 않았다. 수치 상성비는 신규 채택하지 않았다.

5개 행동 링크, 구간/조건/리스크, 강약 표, 웨이브 도식, 미니맵·진형·확대, 근거,
이전 전체 상세 접근 유지. API·계정·원본·보류·실패·영상 호출·Windows 경로 변경0.

## 검증 구분
- 변경 단위50PASS. 실제 PR115 및 exact product-main의 pregame/regression/browser-regression3PASS.
- PC/mobile,1280/1024/768/320,200% 글자, 키보드, 직접 링크·새로고침·뒤로/앞으로,
  조합/조건 변경, 이미지/자료 실패, 진형/확대와 보호 회귀를 기존 브라우저 검사로 확인.
- 실제 공개PC1600/mobile390 기본 흐름 및1280×853 케이틀린/아리 비교 성공.
- Pages native build/deploy/report3SUCCESS. 변경 파일 HTTPS 해시, root/build-info/.nojekyll,
  pro-dashboard 보존, riot.txt 정확한 바이트 확인. deployment.json과 visual-review.json 참조.
- 이번 작업은 표현 계층 개선. 새 전략 근거 채택0, 실전 코칭N=0,30초 이해미측정,
  WindowsBLOCKED_EXTERNAL. 원본/조언7/AUTO30/HOLD20/USER0/Frozen350/호출 한도 보존.

다음 대기열: 근거 범위가 있는 상대법과 상성비 판단. 통계·전문가 판단·실전 효과를
별도로 유지하며, 시안의 숫자나 문장으로 전술 근거를 대신하지 않는다.
