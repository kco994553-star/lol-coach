# Scoped Q15 projection optimization review

Reviewer: `/root/v23_code_review`. Read-only review of `PCPowerSnapshot`, `pc_power_response`, PC startup loading, the early `power_response` opt-in, and the new parity/isolation test. Existing baseline `power_stats.py` was inspected but not changed or rerun as a completed test suite. No provider calls, private inputs, or test executions were used by this reviewer.

## Initial finding

**P2, resolved — concurrent cache eviction can fail an HTTP request.** The local server handles requests on separate threads. At512 cached entries, one thread could hit the oldest key while another inserted a new key and evicted that entry before the first thread's final lookup. Concurrent misses could also select the same eviction key or leave the intended bound exceeded. Main corrected this with a local selected value reference and a `threading.Lock` around cache reads and insertion/eviction. A guarded while loop retains the512-entry bound. Cohort computation and deep-copying remain outside the lock, and cached values are never mutated in place. Read the final synchronization code; no unresolved concurrency finding remains.

## Reviewed behavior

- Startup snapshots are built only from REAL archived Q15 datasets after strict validation; snapshot construction validates and privately deep-copies again. No provider call or new source acceptance path is introduced.
- The fast path requires the exact `(patch,tier)` entry, no overriding `power_data`, and the same startup-owned dataset object. Missing entries, unspecified tier/patch and replacement datasets fall back to the existing selection/validation path. Thus the current explicit conflict path involving `power_data` is retained.
- The private snapshot index narrows only champion/position cohorts. Original source, sample counts/anonymous match list, uncertainty data, and full-dataset SHA256 are retained. Full validation already ensures cohorts match source patch/tier. Recomputing the subset's READY/INSUFFICIENT_DATA status satisfies the unchanged validator; BLOCKED_EXTERNAL is preserved. The unchanged selector still handles matchup/role fallback and missing points.
- Cache results are deep-copied before exposure; caller mutation cannot alter stored source/points/digest. The original startup dictionaries must continue to be treated as owned immutable inputs: object identity is an opt-in/replacement guard, not a byte-integrity check for hypothetical in-place mutation. No production HTTP path was found that mutates them in place.
- Live phase suppression remains in the existing PC preview/recall flow. The general Q15 endpoint's existing phase behavior is unchanged by this optimization.
- `actual-q15-projection-red.log` reproduces the missing snapshot feature. `actual-q15-projection-green.log` reports15 passing new PC cases, including equality with the original selector for matchup, role-population, missing champion, and input/output mutation isolation. These are new parity checks; no historical completed suite was rerun by this reviewer.

## Final affected evidence

Read the new source-bound `scripts/browser_recall_actual_v23.py` without running it. It starts an isolated local server, loads the actual anonymous archives, drives actual Chromium/manual picks, checks reference/card/source rendering and absence of unexpected writes/browser errors, and records source/dataset hashes. It performs no provider requests or actual gameplay actions.

`actual-browser-20261015T120503824437Z/runner.json` records `passed:true` and `goal_under_1000ms:true`: **868.1ms** own pick and **553.1ms** opponent pick, with both recall populations AVAILABLE. A read-only SHA256 comparison found **no mismatch** between any of that receipt's recorded source hashes and the reviewed final checkout. Final `recall_pc.py` SHA256: `604424ae36148d15a529c43c6e9f989eab0a3a8e06f0255f1336efa12266a3ad`.

The earlier multi-second actual-data results in `actual-projection-review.md` remain valid historical pre-optimization measurements. These new measurements satisfy the one-second goal for the two named cases on this environment; they do not establish a population-wide latency distribution, actual Windows/LCU behavior, or coaching accuracy. No browser or unit check was rerun by this reviewer.

## Verdict

Final scoped correctness/security verdict: **PASS; no unresolved important findings**. Final performance verdict: **PASS for the two measured actual-data Chromium input cases**. Selection/source/statistical semantics remain preserved. Final source sealing and remote CI remain Main's responsibility; acquisition source provenance remains the original trusted source and is not rebound by this projection optimization.
