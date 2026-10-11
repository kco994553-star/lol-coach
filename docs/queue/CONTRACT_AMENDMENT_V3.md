# Adapter lineage amendment for additive PRE_GAME v2/v3

Authority: USER_QUEUE_V1.3_2026-10-11 and USER_QUEUE_V1.4_2026-10-11.
The user authorized additive versions while preserving frozen originals and
their evidence. This amendment changes verification of an intentionally
extended contract module; it does not rewrite a historical assertion or source.

Frozen source commit: `708dc737ca4cd70eff86e6a4c6a2ceba039430f3`.

| Historical file | Frozen SHA-256 |
| --- | --- |
| `coach_v1/pregame_contract.py` | `23c9d0fd4a90f968c71d9e425bdd51ac56b8d0fdd9f7e7a9253aae4c1b9c9761` |
| `evidence/queue/q05-expanded-adapter/validate.py` | `e13717b145254ca42026715459f03c47763fbd7b58358f19267c5353d0ca2660` |
| `evidence/queue/q05-expanded-adapter/manifest.json` | `03c69af2497c5fc2c435a4852da11c7b80b24207e06349ee0a512cf1f351fe63` |

The historical preservation test asserts byte equality of the original catalog,
roster and whole `pregame_contract.py` module against its manifest. That module
now dispatches separately versioned schemas. Running the unchanged validator
directly against the current extended module therefore fails its historical
whole-module hash assertion. A direct-current 5/6 result remains a 5/6 result.
Neither the validator, manifest, original catalogs nor original receipts is
edited to make that result appear to pass.

[verify_queue_extensions.py](../../scripts/verify_queue_extensions.py) executes
the following distinct suites and records their full test IDs and logs in a
fresh `evidence/queue/adapter-v3-*` directory:

1. **Historical frozen v1: six original assertions, unchanged.** The original
   validator is loaded from verified frozen bytes. Its contract dependency is
   the exact frozen module; its canonical/digest dependency is also checked
   against the frozen commit. A temporary source view supplies those frozen
   contract bytes while the original assertions inspect the current preserved
   catalogs, roster and source archives. Every original test method executes,
   including the original whole-module byte assertion. There are no skips.
2. **Current additive amendment: six semantic assertions.** Five inherited
   assertions run verbatim against the current parser. The preservation
   assertion explicitly replaces whole-*current*-module byte equality with
   verified frozen contract bytes, unchanged validator/manifest/catalog/roster
   bytes, identical schemas for every original v1 strict model, and exact v1
   parsing, serialization, canonical JSON, digests and proposal payloads for all
   177 original specs. Valid binding and changed-claim rejection are checked
   against both versions. Original input serialization and rejected hidden
   coordinates are checked across all five selected positions. The fresh
   receipt names this suite as amended; it does not claim that the direct
   historical validator passed against the extended module.
3. **Versioned extensions: separate v2/v3 assertions.** The unchanged 13-profile
   v2 catalog retains its exact frozen payload hash, round trips through v2,
   keeps unknown gameplay patch scope and uses `EXECUTABLE_V2_SHA256`. Derived
   in-memory v3 PROFILE test specs use an explicit schema version and movement
   field, round trip independently and bind only to `EXECUTABLE_V3_SHA256`.
   V2 proposals cannot bind to v3 specs; hidden runtime extras are rejected.
   These derived test specs are neither source candidates nor saved proposals.

The original 177-spec catalog is checked in full. Empty gameplay patch scopes
remain UNKNOWN. Exact mechanics, source hashes, sparse unknown classifications,
labels, output text, combined response size and absence of actual approvals
remain covered by the six adapter assertions. The original v2 initiative
catalog hash is
`986c1740df77c3af4c0d1b81297bf2bc72a959579f4e4616b1b20785cccc4627`.

CI checks out full history (`fetch-depth: 0`) so the frozen commit is available;
missing history or changed frozen/current source bytes fail the verifier.
It retains the expanded source validator, fresh unified pregame tests, original
browser and pending-save race checks, and adds the extension verifier plus the
fresh v1.3/v1.4 browser flow. New model/data/movement/HTTP tests belong in the
unified pregame verifier. No synthetic dataset or approval enters actual views,
and these checks make no real-match coaching accuracy claim.
