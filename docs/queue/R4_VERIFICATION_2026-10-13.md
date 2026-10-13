# R4 verification — offline implementation evidence

All requests below use injected TEST transports or local bounded subprocess fixtures. Actual provider/API video calls and Actions dispatch:0. Public documentation downloads for entitlement audit are described separately in `R4_OFFICIAL_FREE_AUDIT_2026-10-13.md`.

Meaningful RED observations before implementation:

- Nine initial tests failed because paired diagnostics/model-specific proof did not exist and text still used60seconds instead of120.
- An aged charged video ID was reserved again before the permanent historical exclusion fix.
- Authentication/payment/quota failures generated four requests before terminal handling, and a forged fallback after those statuses was accepted before validator hardening.
- Corrupt recovered quota was attributed to free-entitlement failure before quota classification was corrected.
- Default fallback permission was absent before an explicit manual-only switch and receipt validation were added.

Latest GREEN targeted run: `python -m unittest tests_expert.test_v20_front tests_expert.test_collector tests_expert.test_entitlement tests_expert.test_diagnostic_cli tests_expert.test_diagnostics tests_expert.test_segments tests_expert.test_generatecontent tests_expert.test_probe_receipt_v2 -q` —109tests, zero failures/errors. The new v2.0 suite contains20tests and independently passed. Coverage includes simultaneous identical requests, wall deadline/output bound, terminal401/402/403/429, fresh exact-model proof, unsafe receipt rejection, no duplicate text, selected fallback video model, no failed-text video/reservation, six historical7396seconds conserved, no aged charged-ID retry, and disabled default fallback.

The initial complete expert discovery run had151tests and only three failures from legacy60-second assertions. Those assertions were updated to the authorized120seconds while video600seconds and metadata20seconds remain checked. A subsequent complete expert discovery run passed159tests before final explicit fallback opt-in and quota-classification additions. Final fresh `python -m unittest discover -s tests_expert -v` passed162tests with zero failures/errors. The worker's final suite log is `/tmp/r4-full-final.log`; Main's source-bound CI verification remains the publication evidence.

Workflow YAML parses; the concurrent diagnostic step passes `bash -n`; R4 Python sources compile; `git diff --check` passes. These checks establish plumbing and conservation behavior, not expert statement truth, successful provider access or coaching accuracy.
