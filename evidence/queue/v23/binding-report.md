# Queue v2.3 preservation and delta CI

This change reuses completed Queue v2.1 verification. It does not execute or claim a new pass for any completed v2.1 verifier, old unit suite, or old browser flow.

## Trusted historical inputs

- Base commit: `fedc30060259b5eeac4ab2ca096daa6259e354b6` (merged PR #35).
- [MVP regression checks, run 38722880438](https://github.com/kco994553-star/lol-coach/actions/runs/38722880438): first-attempt push at the exact base; GitHub API reports completed/success.
- [Pregame queue checks, run 38722880374](https://github.com/kco994553-star/lol-coach/actions/runs/38722880374): first-attempt push at the exact base; GitHub API reports completed/success.
- Raw read-only GitHub API receipts, a 3,936-file SHA256 base manifest, and the original bytes of all ten bounded existing paths are archived in `parent/`. The parent receipt SHA256 is pinned directly in the new verifier: `684093a61590aff3fa41d8ff853f5501ca0361d476b20bbe5fe5b8e9ae76594d`.

No old verifier, amendment, manifest, old test, candidate packet, USER schema, decision issue configuration, or completed receipt was rewritten. Every existing base path outside the explicit ten-file successor list remains byte-bound to the base. This includes all previous 350 candidates, 30 automatic review packets, USER boundaries, frozen contracts, and historical evidence. Original changed-path bytes remain recoverable under `parent/`.

## New checker and workflow semantics

`python scripts/verify_mvp_v23.py` requires the separately sealed child amendment, verifies its exact source list/current hashes, preserves every protected base hash, checks the parent receipt and archives, compares the saved full-tree manifest with Git objects at the exact base, proves base ancestry, and validates the original successful CI receipts. Only explicit new JSON data paths and v2.3 evidence artifacts can be added outside the exact source list; undeclared code and changes to old protected files fail. Parent archives cannot gain arbitrary files. The checker executes no predecessor Python verifier or predecessor assertions.

`--prepare` prints an `UNSEALED_CANDIDATE` and never writes authority. `--tests` additionally runs exactly these new modules: `test_v23_binding`, `test_recall_stats_v23`, `test_recall_collection_v23`, `test_official_items_v23`, `test_recall_candidates_v23`, and `test_recall_pc_v23`.

Both original CI workflow names and jobs are retained. A checkout containing the v2.3 contract or amendment selects the v2.3 path. Missing or invalid seals fail. On that path, historical unit/verifier/browser steps are skipped, the new source checker and explicitly listed affected tests run, and actual Chromium runs only `scripts/browser_recall_v23.py`. Historical commands remain present with a historical-scope guard. Arbitrary future branches cannot receive a broader changed-source allowance merely by inheriting the v2.3 amendment: unknown sources and changes to protected files fail the same exact binding.

The pregame receipt explicitly distinguishes fresh v2.3 work from reused base CI and records `prior_completed_verification_rerun: false`. No test count or synthetic browser receipt establishes coaching accuracy or actual Windows/LCU behavior.

The previous hard-gate entrypoint recursively executed completed historical assertions. Reusing that entrypoint would conflict with the user's explicit instruction and `contracts/queue-v23.md` to avoid revalidation. The additive delta entrypoint resolves that conflict by preserving the old assertions verbatim as history, proving their exact trusted source and successful base-CI provenance, and running only the new scope. This is a change of verification scope, not a fresh old-suite pass or a relaxation of old assertions.

## Local evidence and final seal

- `binding-red.log`: ten new checks initially fail because the successor verifier is absent.
- `binding-green.log`: 13 new binding/tamper tests pass. They cover frozen files, USER storage schema, protected issue configuration, original candidates/packets/evidence, predecessor verifier, new source/data bytes, authority promotion, altered CI provenance, and undeclared source/archive paths.
- Both workflow YAML files parse; `git diff --check` is clean for the owned changes.
- No completed old test was executed, and no full historical suite was run.

The initial handoff left the child amendment unsealed while implementation workers were editing sources. Main subsequently sealed it at commit `626a277ecd1c180be29033d93e88755226cdd6f2`. The initial integration attempt failed only `bounded_changes`: the provenance generator `evidence/queue/v23/candidate-author-build.py` was omitted from the exact source list. The historical `integration-delta-green.log` filename is misleading; its recorded result is FAIL and that original evidence remains unchanged.

After Main authorized the final-source correction, the exact generator path was added to `CURRENT_PATHS`; no generic Python evidence allowance was added. `binding-generator-red.log` records the new declaration regression failing before the correction. Two new regressions check that the generator's exact bytes are sealed and that other executable evidence remains rejected. The amendment was resealed with 31 current source paths, 3,926 preserved base paths, and five new JSON data paths.

`python scripts/verify_mvp_v23.py --tests` then exited **0**: all **74 new v2.3 tests**, including **15 binding tests**, passed in 28.576 seconds, and all **22 binding checks** passed. The complete output is `integration-delta-after.log`. No completed v2.1 verifier, test, or browser flow was executed. The uncommitted correction consists only of the verifier, its regression tests, the resealed amendment, this report, and the two new evidence logs; whitespace checks pass. Main must reseal after any later changes to bound status documents or collected data. This local result does not claim a completed remote v2.3 CI run or coaching accuracy.
