# R3 personal postgame review — ready, real account pending

The authenticated local page `/postgame` imports a Match-V5 match/timeline pair and an explicitly selected own participant. It lists local matches and displays one recorded match. No Riot API or provider call was made during implementation. Actual one-match completion remains `BLOCKED_EXTERNAL`: U1 (Riot ID and server) and U3 (renewed Riot key) are pending.

## HTTP / Python contract

Main owns authenticated route integration, sharing the existing bearer token:

- `GET /dev/v1/postgame/matches` → `{matches:[summary],privacy:"LOCAL_PRIVATE"}`.
- `POST /dev/v1/postgame/import` → summary. Body: `{match,timeline,participant_id,source?}`. `source` defaults `REAL`; `SYNTHETIC` requires the server's internal test-mode flag. No HTTP body can enable test mode.
- `GET /dev/v1/postgame/matches/<64hex-id>` → private detail, with aggregate references injected server-side.
- `POST /dev/v1/postgame/analyze` → detail. Exact body `{match_id,plan_id}`; null plan ID clears association. A saved plan is selected manually, never matched automatically.

`PostgameStore(private_directory,test_mode=False)` exposes `list_matches()`, `import_match(body)`, and `get_match(id,power_data=None,movement_data=None,plan=None)`. Summary fields are `id`, `champion`, `role`, `patch`, `duration_seconds`, `source`. Invalid input raises `ValueError`; absent valid match ID raises `KeyError`. Main maps those to authenticated HTTP errors. Default body limit remains unchanged; a full raw pair may require restarting the local server with `--max-body-bytes 12000000`. The store independently caps each pair at 12 MB.

Optional private `phase_annotations` use the existing movement annotation schema: match SHA256, exact received timestamp, stage, explicit stage conditions, source SHA256/pointer and `VERIFIED` or `MANUAL_UNVERIFIED` provenance. Only explicitly verified annotations with exact timestamp binding can select a matching validated stage reference. Importing a timeline alone never establishes stage from elapsed minute. API structure validates consistency; local import is not cryptographic proof of a Riot response or of ownership.

## Resource and movement semantics

The first three graphs show personal cumulative gold, XP and CS (minions plus jungle minions). Missing resources stay null and missing minutes remain gaps. Level lines mark the first recorded frame at that level; item lines mark actual purchases, with no completed-build assertion.

Reference graphs overlay personal differences on validated same-champion/role/patch statistics:

- `MATCHUP`: personal total minus the opposing same-role total, in gold/XP/CS units. Only the corresponding opponent champion cohort is used.
- `ROLE_POPULATION`: personal total divided by the **exact received elapsed minute**, minus the reference point's overall role-population rate. Reference mean is champion cohort rate minus that same role-population rate; units are gold/minute, XP/minute or CS/minute differences. This is not a personal matchup delta. CI belongs only to the validated reference delta, never to an invented absolute champion mean or the personal observation.

Visible reference means retain their existing 95% Student-t CI and omission rules. Each cohort has `personal_points` and a human-readable `units` field; no raw account data enters those references. Synthetic reference data is withheld outside internal test mode.

Position graphs show recorded distance to the median of all five allied coordinates, requiring all five coordinates. That is a coordinate proxy, not the actual main body. Comparison requires the person's explicitly verified stage/conditions and an eligible same-champion/role/patch/stage/conditions/minute reference; absent proof or missing phase samples stays `UNKNOWN`. No position is labelled wrongdoing.

Context cards use only own death, recorded objective events, allied ward events and preceding recorded own/allied jungle/support positions. A sample recorded later in the same minute cannot explain an earlier event. Cards display sample age and `SUSPECTED_CONTEXT_ONLY`. Dependency samples display all allied champions’ recorded movement, with ambiguous declared roles UNKNOWN. A saved plan’s dependency allies are matched by a unique champion/role tuple; missing or mismatched target movement stays UNKNOWN. The UI exposes each named target’s movement with coordination unknown. Wave, unseen enemies, skill state and video remain unverified/unknown.

A manually linked saved plan must be `CURRENT` and match champion, position and patch. Expired or mismatched plans are withheld. Only REVIEWED/APPLIED rules contributing to displayed saved cards supply premise conditions, carrying rule ID and version. Rejected, exploratory, excluded and conflicting rules are withheld from this premise list. Its premises, execution and effect are separate; even an applicable recorded plan's execution and causal effect remain `UNKNOWN`. No win/loss judgment is returned.

## Privacy and local collection

Raw originals remain under a dedicated local `private/postgame/` directory (already ignored by Git). POSIX directories are 0700 and raw files 0600, atomic exclusive publication preserves conflicting originals, traversal and symlinks are rejected, and reads verify regular-file identity before reading. No raw account, match ID or PUUID appears in list/detail responses, receipts or browser artifacts.

Windows permission handling is best effort: native chmod does **not** verify owner-only NTFS ACLs. The user must set their dedicated private folder to their own user only; the UI explicitly says that NTFS ACL isolation is unverified. WSL provides the POSIX mode checks. Native Windows capture originals must also stay local; see R5's procedure.

After U1/U3 are provided, invoke locally (current collector supports KR):

```text
python scripts/collect_personal_matches.py --riot-id "GameName#TagLine" --server KR --private-directory private/postgame --count 1
```

The key comes from the existing `RIOT_API_KEY` environment configuration; do not put it on the command line. Account lookup → own match IDs → match and timeline uses the existing bounded official transport. Missing/malformed keys cause zero requests; the first 401/403 stops collection. The CLI emits only safe summaries and fixed failure reasons. Do not run personal collection in Actions and do not upload personal originals as artifacts.

## Verification

`python -m unittest tests_pregame.test_v20_postgame` covers private roundtrip/modes, server test gating, malformed/mismatched pairs/owner roster, missing values/gaps, noncausal contexts, missing allies, traversal/symlinks, expired/mismatched plans, verified phase references, exact elapsed normalization, conflicting reimport, portable chmod fallback, credential/401/403 stopping behavior, rejected-plan premise exclusion, duplicate-role ambiguity, and named dependency target matching/missing movement. All fixtures are SYNTHETIC.

`python scripts/browser_postgame_v20.py --output evidence/queue/v20/postgame-synthetic` starts an isolated 12 MB test server and checks import/list/detail, graphs 1–3, resource gaps, level/item markers, personal/reference overlays, death/objective/ward contexts, verified/unknown/missing positioning, explicit saved-plan ID, separate premises/execution/effect, 390px mobile layout, logout, no external requests and no approval operations. Raw fixtures and disposable token are removed with the temporary directory; only synthetic screenshots and receipts are retained. Actual account acquisition remains pending U1/U3.
