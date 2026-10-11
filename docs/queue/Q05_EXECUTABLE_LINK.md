# Q05 → Q03 executable candidate link

[executable-v1.json](../../knowledge_candidates/executable-v1.json) is a bare list
of **17 valid `pregame.rule.v1` specs** against the Q03 contract originating at
`627c77a`. It adapts committed content `501255d9ac4aef689b6831adcdbdba93bb3bc4e9`:
13 named COMMON PROFILE candidates, two general COMMON type rules, and two
POSITION ROLE rules. This is an EXPLORATORY catalog. There are no saved proposals,
USER_WEB approvals, product imports, live observations, cooldowns or production runs.

The source roster still has 173 rows; only the 13 detailed source-backed profiles
enter the executable catalog. Their declared golden lane positions are context,
not official lane claims. Profile `roles`, `strong_when` and `jungle_style` remain
empty/unknown. Official combat-class tags cannot be translated into Position
enums. Existing threat/protection/lane candidate labels map to the contract enums;
empty lists mean unknown, not NONE. Profile mechanic features that the contract
cannot express remain source evidence and never become predicate fields.

All **`patches: []`** are intentional. The archived static build is **16.20.1**,
and each Data Dragon `Source.patch` preserves that exact revision. Unversioned
official guide references keep `Source.patch: null`. No source establishes a
confirmed actual gameplay applicability patch, so there is no assumed `16.20`
scope. The golden/user runtime patch remains null. Official developer docs say
Data Dragon builds can differ from regional client versions; the NA realm reports
16.20.1 but does not authenticate a match patch. A direct official 26.20 patch-notes
request returned404; that failure is retained as a bounded lookup, not converted
to evidence of another patch.

Empty patch scopes block approval for execution. A user may explicitly edit the
structured scope and propose a new exact EXPLORATORY spec through the UI after
confirming its source applicability. A user approval does not authenticate the
actual game patch. Neither this adapter nor the static source pin fills the
draft's missing manual patch.

## Preserved and omitted rules

| Original | Executable mapping |
| --- | --- |
| Q05-J02 | COMMON/JUNGLE: allied GRAB_PICK presence; declared jungle identity required |
| Q05-O01 | COMMON/COMPOSITION: allied GRAB_PICK or DIVE presence |
| Q05-R-TOP | POSITION/ROLE: selected TOP plus allied TOP FRONTLINE |
| Q05-R-SUPPORT | POSITION/ROLE: selected SUPPORT plus allied SUPPORT PEEL and GRAB_PICK |

All mapped output claims are verbatim original candidate claims. Original
counterexamples become verbatim `output.change_conditions`; the adapter does
not claim that wave/readiness/hp/location/objective prerequisites were achieved.
Those live observations are outside InputDraft and cannot be executable fields.
Counterconditions/stop conditions remain empty because no compatible exclusion
predicate is supported by the original source. Cooldowns remain empty without
two exact-patch sources and rank-semantics cross-checking.

Twelve original rules cannot preserve their exact applicability under the current
whitelist: terrain knockup, duelist Vitals/parry, delayed marks, movement-stopping
charm, hit-gated dash and teleport escape have no feature predicate. Marksman is
an official combat class, not a predicate field; BOTTOM or POKE does not establish
that class. The adapter does not silently replace those guards with broader types.
The [manifest](../../evidence/queue/q05-adapter/manifest.json) identifies each
omitted rule and reason, plus exact original source file/spec hashes and excerpts.

Consequently MAP/lane outlooks and FIGHT outputs are unsupported in this adapted
catalog. ROLE has sourced TOP and SUPPORT views; JUNGLE/MID/BOTTOM ROLE and all
five LANE/FIGHT views remain unfilled. The original common/profile sources still
cover all ten golden champions and the three frequent picks. Missing personal
cells must show 미확인; original role prose is not duplicated across sections to
fill the UI. Further views require a compatible source-backed candidate or a
versioned contract extension under the existing queue authorization, not a fabricated condition.

## Review binding and local verification

Each spec's sources preserve the original URL, document SHA-256 and source
locator. The manifest retains excerpts and archived source paths that Source's
strict schema does not carry. New source-audit receipts are under
`evidence/queue/q05-adapter`; original sources/candidates are unchanged.

Main can use the existing immutable source report / exact proposal hash binding.
Only the real user browser review can create USER_WEB decisions. The catalog is
not an approved Knowledge head and cannot activate coaching itself.

From the repository root:

```sh
PYTHONPATH=. python evidence/queue/q05-adapter/build.py
PYTHONPATH=. python evidence/queue/q05-adapter/validate.py
```

Validation parses every exact RuleSpec, checks original claim/limits preservation,
source hashes and locator/excerpt content, the empty gameplay patch scopes and
cooldown lists, and named-champion-free strategic predicates. The pure
`proposal_rule` helper verifies that each binding would say patch UNKNOWN; it
does not call a store/propose/review/run endpoint. Receipt:
[validation.json](../../evidence/queue/q05-adapter/validation.json).
