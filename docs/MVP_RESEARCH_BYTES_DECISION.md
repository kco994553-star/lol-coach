# Research source-byte preservation — 2026-10-05

Objective: keep each Research upload's reported source hash bound to the actual
selected UTF-8 file. Risk DEEP; source integrity precedes new features. Actual
intake main `c30bb2ca553e1346e00aebd9871283101ca51950`; common coordination ref
`work/main-execution-claim`, single root writer.

Counterexample: native `File.text()` strips UTF-8 BOM bytes and silently replaces
invalid UTF-8. The server re-encodes `raw_text` and hashes those changed bytes.
Both JSON and transcript adapters accept BOM inputs directly, so browser source
hashes differ from the original file. Invalid JSON string bytes become accepted
replacement characters. The original source and immutable before receipt show
four actual failures, not a hypothetical provenance risk.

The minimal repair reads `File.arrayBuffer()` and uses
`TextDecoder('utf-8', {fatal: true, ignoreBOM: true})`. UTF-8 round trips preserve
valid bytes including BOM, multibyte text and a literal U+FFFD. Invalid encoding
is rejected with a clear message before POST or resource creation. Current-file,
read-generation and session-generation checks run before decoding. Stale read
errors and stale request errors do not alter a later selection/session. Failed
decoding preserves existing resource, note revision and unsaved text.

The server contract and adapters are unchanged. A binary/base64 HTTP extension
would add scope without improving this valid UTF-8 round trip. Falling back to
`File.text()` would restore the same corruption. No manual reference importer
is added: a new package format cannot establish independent player gold.

Nine identical synthetic cases use the same test and fixture hashes: initial
5/9, first repair9/9, final request-error ownership refinement9/9. Receipts:
`evidence/mvp/research-bytes-before.json`, `research-bytes-after.json`, and
`research-bytes-final.json`. First receipt binds the preserved R6 source; final
receipt binds the request-repair parent. A further nine-case receipt
`research-bytes-request-repair.json` binds the final current source. All versions and failure history remain.

The historical R6 Node script's stub only offers `text()`, so the new harness
reruns its exact A-first/no-A-post/only-B/display-B/no-error expectations with
ArrayBuffer-capable stubs. The original test file and expected values stay
unchanged. The scoped verifier checks all nine new cases and records that
compatibility migration explicitly. It exempts only the evidence-bound repaired
source; all other historical paths and all 27 Frozen payloads remain pinned.
The old R7 verifier remains unchanged and its old exact identity check is FAIL.

Eight new actual-browser checks extend the old38 to46. They use native File
buffers, actual HTTP responses and SQLite; only native read delivery is held.
Source hashes include Research UI, store, intake adapters and both browser
scripts. Actual browser/Actions success must be established by fresh remote
receipts before merge; Node VM success alone is insufficient.

Rollback: revert the scoped source/verification changes in a new commit while
retaining the counterexamples, receipts and this decision record. Frozen design
semantics, game engine, old fixtures and evidence gates change0. Diagnostic file
hash correctness establishes no player provenance or coaching accuracy; Player
DIRECT/DERIVED/complete/truth pair/Decision N/Coach N remain0, accuracy null.

Independent verification found an introduced current-error routing failure after rOpen advanced its own epoch. Four separate immutable request cases preserve initial2/4 (resource/note GET errors hidden) and repaired4/4. `rAdd` now tracks its own open phase and selected-file eligibility; current failures are visible and new-selection/logout failures stay suppressed. First intermediate PASS remains preserved and is not promoted to final acceptance.
