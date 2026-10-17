# Account entry / personal and pro reference dashboard v1 — 2026-10-17

User direction: Riot ID#tag + region → dashboard → primary pregame preparation → unchanged
manual/PC10pick strategy. Not login, ownership proof, LCU detection or coaching effect.
Reuse existing plain frontend, private loopback server, RiotCollector's auth/rate/redirect/
privacy safeguards and public Pages allowlist. No key/token/raw account IDs in public web,
URL, logs or repository. Private account lookup body uses POST+existing server bearer auth.
Public static hosting has no trusted backend; it returns explicit API_UNAVAILABLE and guest
entry, never forwards typed identity to GitHub/search/third-party or accepts a user API key.
No invented tier/win/KDA/progress/coaching points. Missing records are null, not zero.

## Data and status

Input exact riot_id,region; initial safe backend KR (ASIA Account/Match, KR League) only.
Other regions explicitly unsupported until allowed official routing is implemented.
Lookup uses Account-V1 → League-V4 soloqueue → recent5 Match-V5 IDs queue420 → match bodies,
never timeline/video. Filter each body queueId420 and exactly one matching PUUID; public
projection excludes PUUID/summoner IDs/raw match/opponent identities. Window min/max match
start+sampleN, omissions and fetchedAt accompany wins/KDA/champion records. Tier/LP is a
current league snapshot, separate from recent-window win rate. Zero-death KDA is undefined,
not fabricated infinity. Missing fields are excluded with reasons, not filled as0.
Partial league/match errors don't convert an account to not-found. HTTP404 account distinct;
401/403/429 latch stop (no repeated external calls in the service), time budget distinct from
expiry, missing key CONFIG_MISSING. No key present in current environment: actual API success
not claimed. No automatic live account inference or draft import.

## Pro reference boundary / periodic path

New eligible source config requires current LCK first-team verification and an independently
linked soloqueue Riot ID, both source URLs/dates plus player/team/position. Existing roster
is USER_REPORT_NOT_NETWORK_VERIFIED and contains academy/backups; preserve it but don't
promote to current confirmed LCK. Initially no eligible rows; targeted official T1 roster plus account-page player tag
confirmed one Faker account on2026-10-17. MID reuses explicit prior user-roster metadata,
not a match-position inference. Other rows remain pending.
Only exact confirmed entries + queue420 may enter new dashboard. No old89/Q15275/recall291
cohorts relabeled. Public projection may show verified pro player/team/RiotID/time and actual
period/N; user records use identical presentation but are not shared publicly. No inferred
account owner based only on Riot API account existence.
Existing pro workflow is reused for a verified-dashboard schedule/manual path and a
path-filtered main-push initial run (no duplicate workflow); unverified
legacy collection preserved as historical code and excluded from new execution scope.
Existing cross-job121-second rolling-window cooldown and Riot concurrency group are retained.
No eligible entries means no Riot call and no fake pro metrics. Active schedule configuration,
actual execution and actual populated public refresh are reported separately. The existing
workflow CAS-publishes only validated pro-dashboard.json plus its manifest hash to Pages,
with no application-code or personal-record writes; native Pages deployment remains separate. Initial run retains its safe artifact if the
new dashboard export is not deployed yet, allowing reuse without a second Riot request.

## UI / implementation / rollback

Dark navy-purple visual reference user URL; initial reference GET failed in environment,
so use specified sidebar/card/spacing/mobile direction without claiming pixel identity.
Responsive account entry and dashboard, sidebar drawer on narrow view, clear status messages,
primary preparation link loading.html, tactical practice directions.html, postgame unavailable
publicly and local authenticated link. Notes empty until actual analyzed evidence exists.
No token/identity stored in URL/localStorage; account state memory only. Abort stale lookup
on input changes and ignore older responses. Connected identity never sets ten picks.
Preserve existing loading URL via loading.html and PC /loading; root becomes dashboard.
Public export explicit allowlist expands only dashboard/assets/safe pro status, no PC service.
Rollback dashboard entry mapping/modules/routes and previous Pages; preserve all histories.

Automatic schedule/source-push refresh consults the published safe auth-stop marker. An
observed401/403 or missing key stops subsequent automatic provider attempts until explicit
manual key_renewed dispatch; rate limits remain a separate reason. A404 alone never permits first use. Only the exact pre-dashboard artifact+manifest
recorded at intake may bootstrap; other unreadable/malformed state persists a durable
AUTH_STOP_STATE_UNAVAILABLE block. Failure to read existing stop state fails closed.
