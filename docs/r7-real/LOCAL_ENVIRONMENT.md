# Local LoL endpoint environment diagnosis

Observed at **2026-10-04T20:28:28.123244+09:00 KST** (2026-10-04T11:28:28.123244+00:00 UTC).

**EXTERNAL_ENVIRONMENT_BLOCKER**: this Linux Work container has no observed LoL/Riot client process or port 2999 listener. The single fixed-loopback TCP diagnostic returned `ECONNREFUSED` (`errno 111`). Its loopback is the execution container, so it cannot reach a LoL game running on a separate Windows/macOS computer. This is an environment limitation, not a request for user permission.

| Cause | Actual evidence | Conclusion |
| --- | --- | --- |
| Process absence | Read 51 `/proc/[0-9]*/comm` process names at 2026-10-04T20:29:40.060606+09:00; 0 matches for League/Riot/LoL; 0 unreadable processes | No game/client process observed. The broad League/Riot match covers ordinary truncated names; renamed processes remain a limitation, so this is combined with socket evidence. |
| Endpoint unavailable | One TCP connection to `127.0.0.1:2999`, one-second timeout, `ECONNREFUSED` | Local endpoint is unavailable in this container. |
| TLS | Existing official CA SHA-256 `da884275737f024b33c93ae5d28bdb002768a3cb73752ab40254a32218193521` matches prior official capture evidence; CA context loads with `CERT_REQUIRED` and hostname checking | TLS handshake was never reached. No TLS failure observed and verification was never disabled. |
| Permission | No process-table/socket-table permission error; connect returned connection refusal | No permission blocker observed. |
| Port/session | Zero local-port-2999 entries in `/proc/net/tcp` and `/proc/net/tcp6` | No listener/game session observed; no other port was searched. |
| Platform/environment | `Linux` / `x86_64`, `/.dockerenv` absent; Work container context supplied by session | This execution environment does not contain the local game session. |
| Implementation bug | `coach_intake/io.py` fixes the URL, requires a CA, creates a verified TLS context, disables proxy use for local data, and refuses redirects | None evidenced by this failure. TCP refusal happens before TLS/HTTP/payload handling. This is not a full implementation certification. |

No HTTP acquisition or TLS-handshake retry was made because there was no game process and the one TCP probe was refused. No credentials, payload, unrelated process names, or environment-variable dump were collected. This diagnosis changed only its new evidence and report files. Prior evidence, tests, source, and Frozen27 were not changed by it.

## Reproduce the observation

Run from this container. This prints only the platform, matched process names, fixed-port socket entries, and one loopback connection result; it does not request the game payload.

```bash
python - <<'PY'
import errno, platform, re, socket
from pathlib import Path
print('platform:', platform.system(), platform.machine())
pattern = re.compile(r'(league|riot|(^|[^a-z])lol([^a-z]|$))', re.I)
matches = []
for process in Path('/proc').iterdir():
    if process.name.isdigit():
        try:
            name = (process / 'comm').read_text().strip()
        except OSError as exc:
            print('process_read_error:', errno.errorcode.get(exc.errno))
            continue
        if pattern.search(name):
            matches.append((process.name, name))
print('game_process_matches:', matches)
for source in ('/proc/net/tcp', '/proc/net/tcp6'):
    rows = Path(source).read_text().splitlines()[1:]
    entries = [row.split()[1:4] for row in rows if int(row.split()[1].split(':')[1], 16) == 2999]
    print(source, 'port_2999_entries:', entries)
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.settimeout(1.0)
try:
    connection.connect(('127.0.0.1', 2999))
    print('TCP:', 'CONNECTED')
except OSError as exc:
    print('TCP:', errno.errorcode.get(exc.errno), exc.errno, str(exc))
finally:
    connection.close()
PY
```

The machine that actually runs an active LoL game must run the existing one-shot local collector with strict certificate verification for real payload evidence. Repeating acquisition in this unchanged container will not produce that evidence. No real gameplay coaching is enabled by this diagnosis.

Machine-readable evidence: `evidence/r7-real/local-environment.json`. Prior corroboration: `evidence/r7/local-connectivity-retry.json` and `evidence/r5/local-connectivity-status.json`.
