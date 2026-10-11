# Q10 — actual Windows game-PC capture preparation

2026-10-11 UTC. **BLOCKED_EXTERNAL: real game PC/package absent.** Preparation is
ready; Q10 collection completion requires the exact real package described below.
No endpoint attempt was made here and no fresh sample was acquired. Existing
R5 documentation samples are structural references only, not real observations.
No collector, live feature or automatic inspector is added in this change.

## Minimal reuse on the Windows PC

Use the existing `collect_windows.cmd` → `scripts/collect_local.py` →
`coach_intake.__main__.acquire` path, documented in `docs/R5_DATA_ACCESS.md`.
It needs Python3.10+, no pip packages, Riot account credentials, API key or payment.
Run it on the computer actually running LoL; cloud localhost is not that PC.
Windows execution against a real LoL client remains unverified.

1. Use a checkout containing the existing scripts; record its commit SHA in your
   separate operator context. Keep the checkout and its `private/` directory in
   a local location with access limited to you. Avoid shared/synchronized folders
   for raw payloads; Windows access control is provided by the chosen directory,
   not a permission guarantee from this Python tool.
2. In a controlled practice/custom session, record visible phase/mode, own
   position/champion and known patch with their basis in `operator-context.json`
   inside the eventual private package. The metadata are MANUAL/UNVERIFIED;
   unknowns remain null. Do not put this context into or edit the original raw JSON.
3. While the game client is running, double-click `collect_windows.cmd` once.
   Alternatively, from the repository root use `py -3 scripts\collect_local.py`
   once. These are alternatives, not a loop. The wrapper prints the result
   directory, `private/capture-<UTC timestamp>/`, and success/failure.
4. Inspect `status.json`: `passed=true`, `stage=DONE` means acquisition and audit
   only. It does not verify patch, source semantics, viewpoint, match end or
   coaching accuracy. On failure retain the directory and its exact error/stage.
   Retry only as a separate manually initiated run with a new generated directory
   after the external problem is resolved; never replace the failed record.
5. Copy the blank template from `evidence/queue/q10/field-availability-template.json`
   into the **private** package as `field-availability.json`. Populate metadata
   only from the received artifacts and mark each actual path present/missing;
   materialize participant indices from the returned array. Retain the blank
   committed template as a template. Do not fill it with guessed observations.

The script downloads Riot's official CA, validates TLS, and requests exactly
`https://127.0.0.1:2999/liveclientdata/allgamedata`, once, directly without a proxy.
Public CA download may use the normal public HTTPS proxy. Redirects are refused;
response limit is2,000,000 bytes and per-request timeout10 seconds. CA and payload
requests are separate, so10 seconds is not a total-run duration guarantee.
Do not disable TLS verification or change the endpoint to a remote/private host.
No polling, game manipulation, upload or gameplay advice is performed.

The Game Client endpoint is **in-game**, not champion select. A successful capture
cannot demonstrate PRE_GAME automatic pick-window availability. Pregame phase,
visible draft and own selections must remain separate manual records until a
validated, policy-disclosed League Client adapter exists. Do not repeatedly query
this endpoint in champion select hoping to create a draft source.

## Exact package for resumption

Keep all originals together under `private/capture-<timestamp>/`; `private/` is
already ignored by Git. Never commit or publicly upload raw identities/payloads.

| Artifact | Expected acquisition artifact and integrity requirement |
|---|---|
| `raw.json` | Exact original response bytes, not reformatted. Contains names/identifiers; keep private. SHA256 must match `receipt.json.raw_sha256` and `audit.json.raw_sha256` |
| `receipt.json` | Exact collector source URL, retrieval time, raw hash, byte count and `UNVERIFIED_LOCAL_CAPTURE` declaration. Documentation sample kind is ineligible as a real sample |
| `audit.json` | Original existing identifier-excluding diagnostic. Its sections/facts/issues stay unmodified; hash integrity is not source authentication |
| `status.json` | Original acquisition status, stage and CA hash/source. `passed=true` is transport/audit success only. Failure may leave only status and CA or a partial package; preserve it and report missing artifacts |
| `riotgames.pem` | Downloaded official certificate; retained hash must match status. This is a public CA artifact, not account credentials |
| `operator-context.json` | Separate MANUAL record: author/time, checkout commit, PC collection context, visible phase/mode/viewpoint and their basis, selected `my_position`/`my_champion`, own binding if known, patch/region and basis. Unknowns null; game-end claim remains manual |
| `field-availability.json` | Private copy of the blank Q10 template, completed offline from this exact raw hash; includes actual paths/types, null/missing reasons, source time and separate manual context. No raw identifiers or speculative cooldown values need be exported |

For the earlier `coach_v1/capture.py` route, the original artifact is a
`lol-coach-raw-capture-v1` **envelope**, not plain Live Client JSON. Preserve that
file intact, including `raw_base64`, `raw_sha256`, `received_at`, endpoint and
unverified flags. Record a separate envelope-file SHA256; if an offline reviewer
strictly decodes the payload, its decoded-byte SHA256 must match the original
`raw_sha256`. The envelope hash and decoded payload hash are different quantities.
Never run the plain-JSON audit directly on the envelope and call its missing
`activePlayer` fields a source failure. This alternative lacks the wrapper's
status/receipt/audit package; identify missing artifacts explicitly rather than
fabricating them. The wrapper is the recommended minimal procedure.

To re-run the existing diagnostic on a plain raw package offline, use a **new**
output path from the repo root (replace the example directory with the actual one):

```powershell
py -3 -m coach_intake inspect private/capture-REAL_TIMESTAMP/raw.json --out private/capture-REAL_TIMESTAMP/audit-recheck-001.json --max-bytes 2000000
```

The standalone `inspect` CLI reports `UNVERIFIED_IMPORT` and does not load a
receipt or expected hash; `integrity_hash_matched=false` is therefore expected.
It does not replace the original acquisition audit. Original package hash checks
must separately compare receipt/audit against the exact raw bytes, for example
using PowerShell `Get-FileHash -Algorithm SHA256` locally. Case of hex digest is
irrelevant. Never hash parsed/re-serialized JSON in place of original bytes.

## Phase/mode/field availability and cooldown boundary

The existing diagnostic covers four sections, player/event counts and five raw
facts: game time, active health/max health, gold and level. It can identify missing,
null, wrong type and selected semantic issues. It does not inventory every role,
rune, summoner or ability subfield; this task uses the template for that bounded
manual offline inventory instead of adding duplicate inspector software.

- Source pointers in the template come from the existing R5 documentation sample
  or the official active-player example checked in Q01. They are **candidate
  paths**, not claims that a real client supplied them. Before receiving raw bytes
  every row is `NOT_INSPECTED`; later `PRESENT` proves structure only. Omitted
  keys are `MISSING`, present nulls are `NULL`, invalid expected type is
  `WRONG_TYPE`; no zero/false/default values substitute for absent fields.
- `/gameData/gameMode`, `/gameData/gameTime`, map fields, active ability/rune
  structure and returned participant champion/team/position/rune/summoner
  structure may be inventoried. Actual player count is whatever the array
  contains; do not require ten by silently generating missing players. Per-player
  index/template paths are expanded only from actual entries. In-game `position`
  does not automatically confirm the selected role or own-player binding.
- `phase`, `my_position`, `my_champion`, own slot, perspective and session patch
  are separate operator metadata unless a verified original source explicitly
  supplies them. No `/gameData/gameVersion`, phase or other guessed raw field is
  added to this template. `gameTime=0` is not PRE_GAME proof; game-mode text is
  not player viewpoint or policy authorization. A postgame label is not an
  independently verified game-end gate.
- `/activePlayer/abilities/{Q,W,E,R}/abilityLevel` is a rank candidate. Official
  examples expose IDs/descriptions/ranks, not a verified remaining-cooldown
  field. `/activePlayer/championStats/abilityHaste` and `cooldownReduction` are
  documented stat candidates only; presence does not prove effective cooldown.
- If additional cooldown-like **keys actually occur**, an offline reviewer may
  record their exact original JSON pointer, key/type, presence and source hash
  under `cooldown_candidates.discovered_fields`. Do not invent path names such
  as `cooldownRemaining`, reinterpret descriptive text as a timer, assume enemy
  visibility, or compute cast/reuse times. Absence of discovered keys means only
  none recorded under the inspected scope; it is not a universal API guarantee.
- Every remaining-cooldown field is `NOT_AVAILABLE` here. No timers, estimates,
  OCR, cast history, enemy event synthesis, current-ready claims, live enemy
  tracking, or own/allied live feature. This is one-shot private collection for
  offline availability research; it generates no actionable live output.

Policy/source boundaries remain those in `Q01_PRE_GAME_DATA.md` and DESIGN.
Static Data Dragon builds do not establish runtime patch; Q01's candidate
cooldowns and conditional mechanics remain independently source/review gated.

## Resume gates and current evidence

Q10 is **BLOCKED_EXTERNAL** solely on an actual game PC and eligible local raw
package. Preparation is READY: receipt plus exact immutable original bytes,
status/audit/CA and separate manual context allow an offline reviewer to establish
field availability without altering the source tool. If a package is incomplete,
resume artifact diagnosis with explicit missing reasons; do not mark collection
complete. Keep coaching disabled and unknown semantics unresolved.

Q11 requires real samples for its actual-data checks; this template is not a
sample. Q12 requires accessible actual video/frames; JSON cannot substitute for
screen evidence. Q13/Q14 require independent reference and the relevant patch,
perspective, state/knowledge/decision/coach gates; neither collector success nor
AI agreement satisfies them. Real Player/Decision/Coach N=0; accuracy=null.

Documentation/template verification: JSON parses, every candidate path was
cross-checked against its stated historical documentation source, unknown
placeholders are preserved, and the existing collector/capture source files are
unchanged. No Windows/LoL endpoint run, fresh sample, code change, generated event
or runtime test result is claimed.
