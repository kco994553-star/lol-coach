# Queue v2.1 — isolated read-only LCU draft adapter

`coach_v1.lcu_draft.LCUDraftAdapter` implements the authorized unofficial,
local champion-select read. It sends only `GET /lol-gameflow/v1/gameflow-phase`
and `GET /lol-champ-select/v1/session`. It has no server, daemon, game command,
identity endpoint, in-game observation, recommendation, or external API call.
Main owns launcher, authenticated server integration and browser pairing.

The capability is **DOCUMENTED_ONLY with SYNTHETIC fixture validation**. Actual
native Windows/game-client verification is **BLOCKED_EXTERNAL: game PC and
running client are unavailable in this Linux workspace**. Public documentation
and test fixtures do not establish current-client compatibility or Riot approval.

## Trusted backend interface

```python
from coach_v1.lcu_draft import LCUDraftAdapter, discover_lockfile, pair_certificate

# The public catalogue is loaded separately, never from an account endpoint.
champions = {int(row['key']): row['id'] for row in data_dragon['data'].values()}
lockfile = discover_lockfile()  # None off Windows or with no conventional install
if lockfile is not None:
    pin = pair_certificate(lockfile)
    adapter = LCUDraftAdapter(lockfile, champions, patch='16.19',
                              certificate_sha256=pin)
    sanitized = adapter.poll()
    same_snapshot = adapter.snapshot()
```

The constructor accepts an explicit lockfile path for a nonstandard install.
`champion_map` is a trusted local `dict[int, str]` of numeric public champion IDs
to catalogue IDs such as `Annie`. `patch` is optional supplied catalogue metadata;
it is **not independently observed from the client**. Unknown roster IDs fail
closed rather than guessing names. No account mapping or roster fetch occurs.
`transport` is an internal trusted test seam, never browser-configurable.

`poll()` is synchronous and serialized. A successful attempt reads phase,
session, then phase again, and checks lockfile session equality before each
request and after the final read. A changed PID/port/token invalidates the
attempt. The next attempt uses freshly read credentials. Only a SHA256 session
fingerprint survives polling; credentials and raw session bodies are not stored.
`snapshot()` returns an independent copy and makes no network request.

The caller owns a bounded polling cadence. A poll performs at most three GETs,
each with a default two-second timeout (configurable up to ten seconds), with
no redirect following or automatic retry. HTTP 429 clears the draft and applies
`Retry-After` seconds or HTTP date across later polls; an absent/invalid header
uses a conservative 60-second cooldown. Response size is capped at 512,000
bytes. Non-200 bodies are never read or emitted.

## TLS pairing and credentials

Only literal `127.0.0.1`, HTTPS, and a valid lockfile port are accepted. The
five-field lockfile accepts no host or URL and cannot override the destination.
It is a bounded regular-file read; symlink lockfiles and malformed credentials
are rejected. Credentials exist only in the backend call stack and the local
HTTPS Authorization header. Exceptions and response bodies are never logged.

`discover_lockfile()` checks conventional native-Windows Riot install locations
under the system drive and Program Files. It does not scan process command
lines or read player configuration. Its result is only a candidate path.

`pair_certificate(path)` supports a user-launched one-step local startup. Before
and after a TLS-only handshake it requires native Windows checks that the
lockfile PID runs `LeagueClient.exe` in that lockfile's directory, the process
token's user SID equals the launching process token's user SID, and the exact
IPv4 loopback listening port belongs to that PID. It checks unchanged lockfile
credentials after the handshake. It sends **no HTTP request or Authorization**,
and returns an in-memory SHA256 certificate pin; it writes no pin or secret.
Access denial, a different user, unsupported OS, a mismatched listener, or a
rotation fails closed. These Windows API checks still require a real-PC test.

This is local trust-on-first-use pairing for a trusted launch, not protection
against a compromised current-user OS or an attacker replacing the local game
installation. Never expose pairing, lockfile paths, pins, or the constructor
through a browser endpoint. A pre-established trusted pin can instead be passed
directly. Unpinned production polling returns `TLS_PIN_REQUIRED`.

The adapter creates its own TLS client context, allowing a self-signed leaf
certificate only on this fixed loopback connection. It compares the certificate
SHA256 pin **before sending credentials**. It does not change global SSL defaults,
disable verification for other clients, accept arbitrary hosts, or silently
re-pair after a pin mismatch.

## Exact sanitized snapshot schema

All keys below are always present; no additional keys are emitted:

```json
{
  "status": "CONNECTED",
  "reason": "CHAMP_SELECT_VERIFIED",
  "revision": 1,
  "phase": "ChampSelect",
  "patch": "16.19",
  "own_champion": "Annie",
  "own_position": "MID",
  "allies": [{"champion": "Annie", "position": "MID", "locked": true}],
  "enemies": [{"champion": null, "position": null, "locked": null}],
  "bans": {"allies": ["Galio", null], "enemies": ["TwistedFate", null]},
  "pick_phase": "BAN_PICK"
}
```

| Field | Meaning |
|---|---|
| `status` | `CONNECTED`, `MANUAL_FALLBACK`, or `BLOCKED_EXTERNAL` |
| `reason` | Fixed safe machine reason; never raw exception text |
| `revision` | Nonnegative adapter-local integer; starts at 0 and increments on a changed sanitized snapshot or credential session fingerprint |
| `phase` | Recognized gameflow string or null; it alone does not authorize coaching |
| `patch` | Supplied public-catalogue patch or null; not a client observation |
| `own_champion`, `own_position` | Local selection projected using transient cell ID; null if unknown or cleared |
| `allies`, `enemies` | In client team order, at most five anonymous rows each; allies includes self |
| row `champion` | Catalogue ID or null, including visible allied hover intent, never a player name |
| row `position` | `TOP`, `JUNGLE`, `MID`, `BOTTOM`, `SUPPORT`, or null |
| row `locked` | False for an allied hover; otherwise Boolean only when a pick action and visible champion match, or null |
| `bans` | Team lists of public catalogue IDs/null, up to five entries per side |
| `pick_phase` | `PLANNING`, `BAN_PICK`, `FINALIZATION`, or null |

`middle` maps to app `MID`; `utility` maps to app `SUPPORT`; an unassigned empty
position stays null. Champion IDs 0 and -1 are unknown. For allies only, an
unknown champion may use a positive public `championPickIntent`, or a positive
champion on an explicitly allied, in-progress, uncompleted pick action; this
is an unlocked hover and can change. Absent/zero intent remains unknown.
Hidden enemies are never recovered from action IDs, pick intent, identity,
or another endpoint. Duplicate
cells, missing required projected fields, unknown fields outside explicit
allowlists, unsupported positions/actions/phases, unknown roster IDs, malformed
JSON, duplicate JSON keys, oversized responses, and contradictory pick action
sets all fail closed with `SCHEMA_UNSUPPORTED`. Ignored known client metadata
has no evidentiary meaning and is not included in snapshots.

Identity members (`summonerName`, Riot ID components, account IDs, PUUID, and
related identifiers) are dropped as JSON objects are built. Projection never
indexes their values, even when a trusted synthetic transport includes them.
There is no raw-body persistence, caching, telemetry or identity serialization.
The JSON decoder necessarily receives the local session response in transient
memory; identity fields are not interpreted or retained by the adapter.

`MANUAL_FALLBACK` clears own selection, rows, bans and pick phase on schema,
network, authentication, pin, lockfile, session or phase failure. Fixed reasons
include `NOT_POLLED`, `LOCKFILE_INVALID`, `TLS_PIN_REQUIRED`, `TLS_PIN_MISMATCH`,
`LCU_AUTH_FAILED`, `LCU_HTTP_FAILED`, `LCU_RATE_LIMITED`, `LCU_REQUEST_FAILED`,
`SCHEMA_UNSUPPORTED`, `SESSION_CHANGED`, `PHASE_CHANGED`, `PHASE_UNKNOWN`, and
`NOT_CHAMP_SELECT`. Missing lockfile is `BLOCKED_EXTERNAL/LCU_NOT_AVAILABLE`.
Only `CONNECTED` plus confirmed `ChampSelect` is eligible for a separately
authorized PRE_GAME gate. GameStart, InProgress, Reconnect, unknown phase, or a
phase change clears the draft. Prior coaching must expire on revision/status
change; the adapter does not itself render or generate coaching. Manual entry
must not bypass the app's phase/mode gate.

## Public format evidence and tests

Retrieved 2026-10-15; full-source SHA256 plus selected public excerpts are in
`evidence/queue/v21/lcu/public-format-sources.json` and `public-schema.json`.

- [Riot League Client API documentation](https://developer.riotgames.com/docs/lol#league-client-api)
  says the service is local and not officially supported for third-party use,
  with no guarantee of complete docs, uptime, or change communication. User
  authorization for this narrow read does not change that service status.
- [Community LCU OpenAPI](https://www.mingweisamuel.com/lcu-schema/lcu/openapi.json)
  documents the two GET operations, gameflow enum, and champion-select session,
  selection, action, bans and timer property formats. It is unofficial; its
  action-container schema is loose and does not prove this client's current
  nested action layout. Strict nested-array acceptance is exercised synthetically.
- [LCU connector implementation](https://github.com/Pupix/lcu-connector/blob/master/lib/index.js)
  demonstrates fixed `127.0.0.1`, `riot` Basic username and lockfile credentials;
  [lockfile parser](https://github.com/Pupix/lol-lockfile-parser/blob/master/lib/index.js)
  documents process/PID/port/password/protocol order. This module deliberately
  does not use their process-command scanning or credential-export helpers.

`python -m unittest tests_pregame.test_lcu_draft` covers projection, visible
allied hover versus hidden enemy intent, null locks/roles, identity omission and guarded identity access,
immutable snapshots, revisions, token/port rotation, mid-poll rotation, game
start/unknown/racing phase, missing/changed schemas, malformed/nonloopback
lockfiles, symlinks, network failure without secrets, mandatory pinning,
pin-before-auth, GET-only requests, redirects, JSON duplicates, 429 cooldown,
and pairing handshake/rotation boundaries. These are synthetic protocol and
fake TLS fixtures, not a real native-Windows transport success claim.
