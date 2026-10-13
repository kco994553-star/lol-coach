# R3 selected pro reference roster — preparation ready

`config/pro_reference_players.json` is the user's exact 2026-10-13 KR roster: 25 primary players (five per role), nine backups, and ShowMaker's alternate account. The supplied names, teams, Riot IDs, observed ranks/activity and OP.GG Pro-badge claims are `USER_REPORT_NOT_NETWORK_VERIFIED`. ADC maps to canonical BOTTOM. The selected individuals are a separate reference population; they are not a verified current CHALLENGER/GM League seed cohort. Tier stays UNKNOWN.

No actual Riot calls were made. Actual collection and pro overlays remain blocked on U3, the renewed Riot key. Main's authenticated `/dev/v1/postgame/reference-roster` uses `prepare_pro_reference(config)` to show the exact public roster and instructions; saving the roster is preparation, not evidence of collected matches.

## Local commands

Zero-network preparation:

```text
python scripts/collect_pro_reference.py --config config/pro_reference_players.json --prepare-only
```

After the renewed key is available, collect locally using the existing `RIOT_API_KEY` environment configuration:

```text
python scripts/collect_pro_reference.py --config config/pro_reference_players.json --private-directory private/pro-reference --matches-per-account 3 --position-share-threshold 0.5
```

Do not put credentials on the command line. Never collect personal/pro raw data in Actions or upload caches/originals as artifacts. Default limits are three recent matches per account, 250 requests, 100 unique fetched matches and a 300-second deadline, with no automatic retry. The default three-match sample reaches all 25 healthy primary players/five roles within those budgets, including the alternate account. Raising the per-account sample without raising budgets can exhaust the run before later roles; the receipt records literal coverage and stopping reason. The existing Riot transport enforces its local 20/second and 100/120-second windows, response-header bounds and immediate first-401/403 stopping. Limits are explicit CLI options; a budget-blocked receipt records the literal reason and any completed selections.

## Account and replacement behavior

Account-V1 by-riot-id preserves exact Unicode, spacing and case before URL quoting, including `오 너#111`, `JUGKlNG#kr`, `강 철#샤 넬` and `DNS Quantum#KR 1`. Successful PUUIDs are cached once under stable player-name/account-slot keys, independently of later Riot ID nickname changes. Player names and alternate-account slot ordering define cache identity; changing the roster's actual account owner requires deliberate local cache maintenance. A nickname edit alone does not trigger another Account lookup.

Primary and alternate accounts are one player. Equal PUUIDs are queried once, games are deduplicated, and requested match IDs must match the actual returned metadata before storing or counting a sample. Account 404 skips that account and records its stable public player/account key. A 401/403 aborts the whole collection immediately; it never causes a backup-account attempt.

Backups are considered, in the configured role order, only for the user's three authorized triggers:

1. No usable account lookup succeeds for the player.
2. No verified ranked-solo queue-420 game falls within the last 30 days.
3. The observed role share is below the operational configurable threshold (default **less than 50%**).

Unknown position assignment stays UNKNOWN, with no fabricated low-share value or backup replacement. A valid recent player whose timeline is missing stays skipped with `NO_USABLE_ROLE_TIMELINES`; missing timelines do not add a fourth replacement trigger. Backup exhaustion and every actual replacement are recorded. Role share uses a bounded recent sample per account, not an exhaustive 30-day census; its threshold is a collection policy, not tactical accuracy or a gameplay recommendation.

## Private outputs and honest overlays

All output paths must remain inside an effective dedicated `private/` directory; `..` components and symlink ancestors/files are rejected. Outputs are:

- `accounts.json`: private stable-key PUUID cache.
- `private/matches/*.json`: private original match/timeline pairs selected for the reference role.
- `collection-receipt.json`: safe current-run selection, replacement, failure and budget receipt.
- `reference-data.json`: validated anonymous `postgame.pro-reference.v1` resource aggregate.

POSIX folders use 0700 and files 0600. Native Windows chmod is best effort; the user must configure an owner-only dedicated folder's NTFS ACL, which the app does not verify. WSL provides the POSIX permission checks. PUUIDs and raw match IDs never appear in collection receipts or reference datasets; only anonymous match hashes are retained in aggregate lineage.

The new reference schema is separate from existing League tier deltas. It groups selected recorded **absolute total** gold, XP and CS by champion, canonical role, exact patch and elapsed-minute bin. Games are counted once per champion/role cohort and clustered by anonymous match identity. Student-t 95% CI and the existing CI-width-versus-sample-spread omission policy are reused; n<2 remains hidden. Patch cohorts are never pooled across patches.

`validate_pro_reference(data)` enforces a strict aggregate allowlist. `attach_pro_reference(detail,data,test_mode=False)` returns an independent copy with a separate `detail.pro_reference` panel. It filters exact champion/role/patch, leaves the existing `detail.reference` League resource-delta comparisons intact, exposes true absolute-total units, and overlays personal absolute totals against selected-pro means/CI. Synthetic references require internal test mode. Missing matching or eligible samples stay UNKNOWN. Pro status, historical rank, coordination and causality remain unverified. When loading a reference alongside a changed roster, compare its `roster_sha256` to the current config before attaching it.

## Verification

`python -m unittest tests_pregame.test_pro_reference tests_pregame.test_v20_postgame` exercises exact Riot ID quoting, cache stability across nickname changes/restart, alias/game deduplication, private modes and path/symlink rejection, strict roster counts, same-role backup rules, unknown/missing-data behavior, immediate auth stopping, request budgets, requested/returned match identity, anonymous aggregate validation, same-champion/role/patch overlay gating and synthetic isolation. All transport inputs are SYNTHETIC; no real Riot/provider requests are involved. Main owns the final source-bound HTTP/browser integration proof and current deployment evidence.
