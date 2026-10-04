# R7 검증 이력 — 과거 PASS와 최종 PASS 분리

- Baseline: main 884a435e52fa20e21971269dd52e30239fc4f8ff, remote124/local124 Git blob 일치. workflow API 조회400은 connector endpoint 제한; tree에 workflow 없음.
- Fresh R6: 2026-10-04T11:01:47Z 96/96, 보호9/9, UI race/file race. 11:01:49Z browser/390px mobile PASS. 기존 evidence/r6는 수정하지 않음.
- REPAIR(문서): 공식 웹 예제의 MIDDLE을 보존 raw의 position으로 잘못 기재한 초안을 raw/hash 확인 후 빈 문자열로 정정. 초기 L2 설명도 전략 판단 계층으로 정합화. Frozen 변경 없음.
- RETRY(수집): 11:08:07Z 공식 인증서 다운로드 timeout. 11:10:07Z 기존 공식 CA 해시/TLS context 검증 후 loopback 재시도; Connection refused. TLS 검증 해제나 타 PC endpoint 추정 없음.
- Initial R7: 20261004T111120744873Z — 110/110 + 보호9/9 PASS. 이 테스트 범위는 이후 independent challenger가 발견한 두 참조 비교 결함을 검출하지 못했다. 따라서 최종 R7 근거로 단독 사용하지 않는다.
- Independent adversarial finding: (1) caller의 ESTABLISHED 선언 + arbitrary observer ref가 MATCH 분모1을 만들 수 있었음. (2) expected 1과 actual True가 Python equality로 일치. engine activation은 둘 다 false였으나 정확도 보고 잠재 오류.
- REPAIR: 선언 참조 비교를 diagnostic으로 분리하고, 실제 reference provenance importer가 없으므로 real denominator0/BLOCKED 유지. canonical JSON 비교로 boolean/number 구분. 반례 테스트 추가.
- Final R7: 20261004T111536178607Z — 111/111 (기존96 + 신규15), skipped0/failure0/error0, 보호9/9 PASS. source hashes는 해당 verification.json. Fresh baseline의 UI 코드는 최종에서도 byte-identical.
- Independent fix check: 두 반례2/2 재현 PASS; 최종 보고/Reference protocol에서 실제 N0·슬롯≠사례·문서≠실경기 경계 확인. 추가 material blocker는 실제 프레임/Reference 부재.
- No real case, no real coaching score, no Golden promotion, no Frozen change. Risk DEEP, D3 불필요. R7 acceptance의 BLOCKED/PARTIAL 항목은 docs/r7/R7_REPORT.md에 보존.
