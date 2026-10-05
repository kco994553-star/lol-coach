# Current MVP validation

`scripts/verify_mvp.py` checks the current local MVP while keeping the historical
verifiers, frozen contracts, fixtures, expected values, and evidence intact.

```sh
python3 -m pip install -r requirements-r3.txt
python3 scripts/verify_mvp.py
```

Python 3.12, the pinned Pydantic dependency, Node.js, and OpenSSL are required.
The synthetic transport tests use the fixed loopback port 2999. A missing
OpenSSL executable or occupied port causes an actual unittest skip, which fails
the required regression check instead of becoming a pass.

Each invocation creates a unique `evidence/mvp/<UTC>-<random>/` directory. Its
`verification.json` binds the checked sources by SHA-256, records subprocess
exit codes and logs, and reports the scoped result. Previously recorded evidence
outside `evidence/mvp/` is hashed before and after the run; any changed bytes fail
the run. The frozen legacy validator runs in a temporary copy because its own
implementation writes `evidence/validation.json` and validation history.

The required scope is:

| Check | Required result |
| --- | --- |
| Frozen contract payload | All 27 manifest hashes match |
| Historical R0–R6 protected bytes | Match the preserved baseline, except the evidence-bound UI repairs, versioned read-only note-history addition and strictly bound source-proposal UI/API addition, plus the baseline's handoff exemption |
| Preserved R7 sources and old test file sets | Match the preserved historical receipt and baseline |
| Protected legacy validator | Nine checks pass in an isolated copy |
| Unchanged `tests_r3` through `tests_r7` | Exactly 111 tests run, with zero skips, failures, errors, or expected failures |
| Backup and restore | All current `tests_mvp/test_backup.py` tests pass, with zero skips |
| Save acknowledgement and draft retention | Seven synthetic Node VM cases pass |
| Existing delete/import and research-file races | Two original cases plus the original Research A-first expectations in the current nine-case harness pass |
| Latest synthetic import selection and stale errors | Seven new Node VM cases pass |
| Research UTF-8 provenance | Nine synthetic codec/adapter/read-order cases pass; preserved 5/9→9/9→9/9 history binds old/current source |
| Research current/stale API errors | Four separate Node cases pass; actual introduced 2/4 failure and repaired 4/4 preserved |
| Research navigation/deletion | Four cases pass; first1/4 failure and first/final4/4 receipts preserve exact old/current source chain |
| Stored note history | Exactly 19 storage and five real HTTP tests pass; explicit UTF-8 response cap, auth/Host/Origin, original rows/schema/CAS unchanged |
| Research current/stale save and navigation errors | Four save +six actual-callback Node cases pass; preserved2/4→4/4→4/4 and3/6→6/6 source-bound failure history; current401 remains handled, stale401 remains explicitly synthetic |
| Source-bound Knowledge proposal | New storage, authenticated HTTP and schema2 backup tests all pass with zero skips; actual source revision/hash, EXPLORATORY-only immutable versions/CAS, pre-migration recovery and rollback, physical PK/FK cascade and count-only deletion receipts |
| Postgame schema mechanics | Thirteen synthetic schema tests pass |

The historical `scripts/verify_r7.py` hard gate still requires the original web
app's exact bytes. The authorized repair changes that file, so its historical
identity check is expected to fail. The new verifier explicitly records that
identity difference; it does not modify the historical baseline or claim a
fresh historical-verifier pass. The Research byte repair additionally requires its strict before/first/final receipt binding. Read-only note history additionally authorizes only the exact versioned `web_r4/index.html`, `web_r4/research.js` and `coach_v1/server.py` hashes; unchanged ResearchStore schema/storage and old guards remain required. Any other protected historical difference fails
the new verifier. Frozen design and legacy engine bytes remain protected.

The before/after save receipts are preserved separately at
`evidence/mvp/save-race-before.json` and `evidence/mvp/save-race-after.json`.
The new verifier checks their fixture and source binding, compares the seven
case identities, checks the initial 3/7 and repaired 7/7 results and exit codes,
and reruns the current-source cases into its own new evidence directory. These
tests use deterministic HTTP replies and a DOM stub, not a browser.

The later import repair keeps those save receipts unchanged. Its separate
`import-race-before.json` and `import-race-after.json` bind the saved repair's
source hash to the import repair's parent and current source. The same seven
case IDs, fixture hash and test-script hash must match. The initial import run
has three passes and four actual failures; the repaired run has seven passes.
The current verifier reruns both save and import cases. It does not rewrite the
old save receipt to pretend that it tested the new app bytes.

The actual browser suite retains the previous 32 checks and adds six import
checks using native browser File objects with delayed `File.text()` completion.
Both A/B read orders and clearing the newest selection are exercised. This is
38 historical checks against a synthetic backend. Eight further actual Research file-byte, invalid-input, dirty-note and stale-read checks bring the byte-repair count to46. Four current navigation/deletion checks extend the required browser count to50. Native File bytes must match the persisted adapter hash. These are never real-match coaching accuracy.

## Optional preserved-source integration

The four existing pinned-source tests require private, exact-byte `match.json`
and `timeline.json` inputs. Supply their directory explicitly:

```sh
python3 scripts/verify_mvp.py --postgame-raw-dir /path/to/preserved/raw
```

The equivalent environment variable is `R7_POSTGAME_RAW_DIR`. With that input,
all 17 existing postgame tests must pass with zero skips. The verifier writes
input hashes, not raw game bytes, into the new receipt. An explicit directory
with missing or wrong bytes fails; it is not silently treated as unavailable.

Without that input, the 13 synthetic tests still run. The four pinned-source
tests receive a separate `NOT_RUN` result with their reason and zero executed
tests. They are not counted as passes or artificial unittest skips.
`full_postgame_17_passed` remains false. A scoped MVP pass never certifies live
game capture, player information, coaching accuracy, or production readiness.

## GitHub Actions

`.github/workflows/private-mvp-ci.yml` runs the default scope on pushes to
`main`, pull requests, and manual dispatch. Its filename is historical naming
for this local MVP work; it does not make the GitHub repository private. The
repository was observed as public (`private: false`) on 2026-10-05.

The workflow uses standard `ubuntu-latest`, a ten-minute job limit, cancellation
of superseded runs, `contents: read`, and commit-pinned official checkout and
Python setup actions. Node and OpenSSL come from the hosted runner image. It
does not require private game data, secrets, cloud accounts, a self-hosted or
larger runner, browser downloads, artifact uploads, or repository writes. It
prints the private-source `NOT_RUN` status alongside the scoped result.

A separate browser job installs the exact `playwright@1.62.1` automation library
in the runner's temporary directory with browser downloads disabled. It runs
`scripts/browser_mvp.py` against the runner's preinstalled Google Chrome and an
isolated synthetic backend. It prints the current commit and full child and
launcher receipts into job logs and the job summary, with no artifact upload.
A missing browser or failed scenario fails that job. The local scoped verifier
continues to report that it did not itself execute browser E2E.

The [official Playwright v1.62.1 release](https://github.com/microsoft/playwright/releases/tag/v1.62.1)
and [official Ubuntu runner image software list](https://github.com/actions/runner-images/blob/main/images/ubuntu/Ubuntu2404-Readme.md)
were checked on 2026-10-05. That image lists Google Chrome, Node, npm, and OpenSSL.

[GitHub's official runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
states that standard hosted runners are free and unlimited for public
repositories. This basis, checked on 2026-10-05, and the official release pin
sources are recorded in `evidence/mvp/ci-cost-basis.json`. The free-runner basis
depends on the repository remaining public. The job only starts when GitHub's
event metadata says `repository.private == false`; a later private repository
state skips the job and does not count as a CI pass. No paid runner configuration
is introduced here.

A local run cannot prove that GitHub Actions executed. Until an actual workflow
run is observed, the Actions result remains unverified; a passing local receipt
does not substitute for an Actions run URL and conclusion.

Research source-byte repair and preserved failure details: `docs/MVP_RESEARCH_BYTES_DECISION.md`. The old text-only Research test stub is preserved; `R6-LATEST-FILE-A-FIRST` reruns its unchanged ordering expectations in the ArrayBuffer-capable harness.

Navigation response identity repair adds a further strict source-chain gate with unchanged previous byte/request repair receipts, then reruns all prior9+4 guards. Exact original expected4 navigation cases and first1/4 failures are preserved; no stale deletion result may clear a different resource and draft. Current gaps: `docs/MVP_EXECUTABLE_GAPS.md`.

Stored note history reuses existing immutable personal note rows. The web path is documented in `docs/MVP_NOTE_HISTORY.md`; prior versions are previewed/downloaded separately and never become the editable latest note or game evidence. No timestamp/author is inferred. The source-version record preserves exact pre-change and current hashes. Eleven actual browser history checks extend the prior50 to61, including exact download, preserved latest draft/CAS, genuine delayed success/error/index replies, navigation and deletion. Fresh Actions must establish this result before completion is claimed.

Two genuine delayed/current HTTP409 browser checks retain all prior61 and bring the current required browser count to63. They prove current conflicts stay visible and old conflicts cannot alter another resource draft/notice/auth. They do not claim real401 credential expiry. The error repair extends exact source-chain binding through separate immutable before/intermediate/final receipts; history-version record bytes remain untouched.

The source-bound proposal slice preserves all earlier source records and their
failure history. `knowledge-baseline.json` binds the exact merged PR5 intake;
`knowledge-source-version.json` binds the actual new server/index/research/backup
and new Knowledge module bytes. Legacy ResearchStore code stays unchanged;
current startup uses an additive schema2 store with physical source and version
foreign keys. This is implementation of the Frozen persistence contract, not a
contract change. Backup v1 archive format remains two databases, admits actual
research schema1/2 and checks manifest/actual schema agreement before restore.

Sixteen additional native-browser Knowledge lifecycle cases retain the preceding63,
so the required current count is79. Eight fixed Node VM deletion/response cases
are rerun separately, with the original failing and intermediate passing receipts
preserved. Explicit Node401 inputs are not actual authentication-expiry evidence.
They exercise real HTTP/SQLite data with held response delivery for race cases;
they do not prove the operator claim, actual player state, patch applicability,
decision validity or coaching accuracy. `EXPLORATORY` is fixed; coaching stays
disabled, PLAYER and real Decision/Coaching N remain0, accuracy null. Unsupported
multi-source rules and reviewed-rule activation remain outside this slice.
