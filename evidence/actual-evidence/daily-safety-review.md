# Independent daily Gemini safety review — 2026-10-16

Reviewed the working tree against `contracts/actual-evidence-v1.md`, base `103b8b80`, and root `AGENTS.md`. Scope: `coach_v1/gemini_daily.py`, `scripts/run_gemini_daily.py`, `.github/workflows/expert-video-collection.yml`, the three retired legacy CLI guards, and `tests_expert/test_gemini_daily.py`. This review does not authorize collection or relax the contract.

## Findings

### P2 — Numeric ACKs are not bound to the uploaded reservation, and replay protection is local

`coach_v1/gemini_daily.py:173` accepts any positive integer as the durable upload ACK. It neither verifies the artifact exists nor binds its contents/name/run/attempt to this reservation. The exclusive claim at lines 177–179 only protects a particular local directory; `scripts/run_gemini_daily.py:157` derives that directory from mutable `RUNNER_TEMP` and the supplied run ID. The CLI checks run/attempt environment strings but does not authenticate them against Actions.

Synthetic reproduction: reserve one TEXT once, call `dispatch` twice with the identical pending state, run ID `42`, arbitrary artifact ID `999999999`, and two temporary claim directories. Both reach the injected transport: **2 calls for the same reservation/day**. No artifact was uploaded. The production workflow does supply the actual upload step output at workflow lines 62–67; this finding concerns the independently callable live CLI / restored-local-state path, not a claim that the normal successful workflow itself dispatches twice.

Fix expectation: validate the durable artifact identity and exact reservation-state binding before dispatch; fence the executable live CLI to the trusted workflow context. Ensure replay of a pending reservation from another local claim directory cannot authorize a second dispatch. Add isolated tests for nonexistent/wrong-run/wrong-reservation ACKs and replay across claim directories. Preserve cancellation/unknown-outcome consumption and the first-attempt restriction.

### P2 — Empty or malformed VIDEO extraction is reported as valid

`coach_v1/gemini_daily.py:155` discards `normalize_gemini_claims` rejection reasons. That normalizer returns an empty accepted list for both `{"claims":[]}` and a wrong-shaped object such as `{"not_claims":"arbitrary"}`. Lines 160–161 return a successful-looking output in both cases. Dispatch then records `VIDEO_SUCCESS_UNREVIEWED`; `scripts/run_gemini_daily.py:164–167` writes extraction and unconditionally sets `valid_extraction=true`. POV similarly accepts an empty `observations` list at daily lines 162–169.

Synthetic reproduction confirmed both EXPERT objects return `accepted_claims=0` without a parsing failure. The new CLI integration test itself returns `{"claims":[]}` for VIDEO, so it currently blesses the behavior. This conflates VIDEO HTTP200 with parsed nonempty extraction, which the contract explicitly separates.

Fix expectation: retain HTTP200 as transport evidence, distinguish malformed structure from a valid empty result, expose whether a nonempty extraction exists, and keep review status independent. Set `valid_extraction` only for a validated nonempty extraction. Add isolated empty/wrong-schema/all-rejected/out-of-interval and empty-POV cases. Keep all such results exploratory and blind evaluation disabled.

### P2 — Persistent source-metadata errors are discarded, allowing unchanged daily TEXT loops

`scripts/run_gemini_daily.py:173–188`, performs metadata verification/discovery after the successful TEXT but before any VIDEO reservation. A YouTube 401/403/402 or persistent argument/configuration error raises out of that phase. Lines 194–199 replace the typed error with `INVALID_OR_UNAVAILABLE_DAILY_STATE` and persist only the unchanged successful TEXT state. Consequently `coach_v1/gemini_daily.py:99–102` sees no persistent error and permits a new TEXT the next Seoul day under the same configuration.

Synthetic reproduction: inject a collector whose `_youtube` raises `_External('PROVIDER_HTTP_FAILURE', http_status=403)` in `verify_source_metadata`. `preparevideo` exits 1; the receipt loses HTTP403/classification; the daily state stays at two events (TEXT reservation/success). `reserve_text` the next day succeeds with the identical public configuration. An invalid YouTube credential or permission can therefore cause a new Gemini TEXT every day indefinitely. Similar pre-reservation `_gate` configuration failures are not durably classified either.

Fix expectation: retain bounded typed persistent-stop evidence outside the request-result schema, including metadata/gate errors, and check it before future requests until the public configuration/credential revision changes. Preserve 429 versus network/server/auth/permission/argument distinctions. Do not hash or store credential values. Add an isolated two-day metadata401/403/402/configuration test, with429 separately remaining a quota/rate result.

## Checked properties and limits

The workflow uses one schedule at `0 9 * * *`, one shared manual/scheduled concurrency group, trusted main, and first attempts only. Legacy live CLI phases are fenced before networking while legacy recovery remains callable. Normal reservation functions share Seoul-day TEXT/VIDEO slots across purposes, require same-run TEXT success before VIDEO, charge full original duration, reject any previously charged video ID, and preserve quota/state prefixes. Explicit POV source plans use the separate POV channel list; discovery remains EXPERT-only. URL/interval metadata bounds are validated. Both output purposes retain API-offset isolation as unproven, disable blind evaluation, and avoid claiming coaching accuracy.

These observations are code inspection, not provider-isolation evidence, actual availability proof, credential/project linkage proof, or validation of same-game/scene gates. No historical full suite was rerun; no real provider, secret, collection, old evidence mutation, commit, or external publication was used. The in-flight migration/zero-job recovery change was intentionally left to its implementer and is not duplicated here.

Counterexample script: `/tmp/daily-safety-counterexamples.py` (outside the repository); executed using `PYTHONPATH=. python /tmp/daily-safety-counterexamples.py`, exit0. Its transports and metadata failure are synthetic, and all state is temporary. Only this review file was written inside the repository.


## Implementer disposition — Main

All three P2 findings were addressed before provider execution. New review fixtures
showed RED then34 daily/CLI tests GREEN. No thresholds or historical records changed.

- CLI now checks the actual Actions run/path/main/attempt and artifact ID/name/run,
  downloads the paired reservation state and requires exact logical byte content
  equality before dispatch. The claim directory is fixed to this checkout's git
  directory; changing output directory/RUNNER_TEMP cannot replay a request. Pure
  injected-transport library helpers are not separately authorized live entrypoints.
- Wrong extraction shape is malformed; empty/fully rejected/out-of-interval output
  has valid_extraction=false and its own extraction status. HTTP200, nonempty
  extraction and review remain independent.
- Typed pre-reservation failures are append-only PREPARATION_FAILURE events;
  authentication/permission/payment/argument failures stop unchanged configuration
  on later dates.429 remains separately classified. Secret values are never hashed.

Verification: tests_expert.test_daily_review_fixes (six new counterexample groups)
and the28 new daily tests; logs daily-review-red.log/daily-review-green.log. Existing
predecessor suites were not executed. No deferred minor findings.
