# Q05 expanded source candidates → Q03 typed catalog

[executable-expanded-v1.json](../../knowledge_candidates/executable-expanded-v1.json)
adds 160 COMMON PROFILE candidates to the unchanged 17-spec
[original catalog](../../knowledge_candidates/executable-v1.json). The combined
catalog has 177 unique IDs and 173 named champion profiles. All new IDs use
`Q05-P-<champion_id>`. These are EXPLORATORY interpretations of archived official
static mechanics; they are not reviewed Knowledge heads or actual game findings.
The input is pinned to corrected source commit `261e456`, including the explicit
exclusion of Sylas's self-movement description as grab-pick evidence. The adapter
preserves that correction and binds 434 existing semantic-feature records.

The adapter maps only labels already declared in each source row:

| Source candidate | Contract enum |
| --- | --- |
| poke | POKE |
| dive | DIVE |
| grab-pick | GRAB_PICK |
| assassination | ASSASSINATION |
| protection | PEEL |
| frontline | FRONTLINE |

The adapter does not interpret descriptions or substitute new predicates.
Missing labels stay empty/UNKNOWN; they do not become NONE. Every mapped label
retains its exact semantic-feature excerpt, locator and document SHA-256 in the
[manifest](../../evidence/queue/q05-expanded-adapter/manifest.json). The spec's
sources select only those feature references. Assassin/Tank tag references are
also retained when the existing assassination/frontline interpretation depends
on that class. Entirely unclassified profiles retain their exact official
identity tag reference and make no type assertion. Unrelated spell references
are not added to those specs.

New spec counterexamples and limitations are verbatim source-row lists. As in
the original adapter, the final counterexample supplies the original PROFILE
display text, and the counterexamples supply `output.change_conditions`. These
are candidate limitations, not new tactical instructions.

All expanded profile `roles`, `strong_when`, `lane_style` and `jungle_style`
remain empty. Phase strength is still null for all 173 source profiles. Nine
expanded profiles remain entirely unclassified: Gangplank, Hwei, Kalista,
Karthus, Kindred, Quinn, Smolder, Teemo and Vladimir. Their empty profiles do not
assert the absence of any mechanic. No existing personal strategy or common
map/composition rule is expanded by this adapter.

All new `patches` and `cooldowns` are empty. Each Data Dragon `Source.patch`
preserves the archived static build 16.20.1; this does not establish an actual
match patch. Required patch input stays unknown unless supplied independently,
and an empty rule patch scope cannot execute. There are zero store/propose,
USER_WEB decision, product import, actual game validation or coaching accuracy
claims in this work.

From the repository root:

```sh
PYTHONPATH=. python3 evidence/queue/q05-expanded-adapter/build.py
PYTHONPATH=. python3 evidence/queue/q05-expanded-adapter/validate.py
```

The builder only writes the new catalog and audit manifest. The validator checks
all 160 IDs, exact label mappings and source excerpts/hashes, strict Pydantic
parsing and pure proposal hash binding, unchanged original catalog/contract,
the nine unknown profiles, and the 177-spec combined response size below 1MB using
both compact UTF-8 and the server's larger default JSON representation.
Its [validation receipt](../../evidence/queue/q05-expanded-adapter/validation.json)
records counts and the source input commit; Main owns subsequent additive loader
integration and functional HTTP/UI verification.
The builder pins audited Git history locally. The validator uses committed file
hashes and source archives only, so it also runs in a shallow CI checkout.
