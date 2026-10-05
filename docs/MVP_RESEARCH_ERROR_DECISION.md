# Research error ownership repair

Current source before this repair routed save and direct resource/anchor/list
UI rejections through an unscoped `rError`. A deferred old A request could reject
after B was opened and edited. Its401 cleared B's new dirty draft and source;
its409 changed B's notice. The preserved synthetic Node failures were2/4 for
save and3/6 for the actual source-created navigation callbacks. These explicit
401 inputs do not claim real HTTP token expiry.

Save now handles rejection only while its epoch, resource and note anchor still
own the request. Direct UI navigation/list calls capture the epoch immediately
after invoking their async action, then handle only a matching rejection.
Resource/anchor actions synchronously increment the epoch before their first
await; this captures their own new phase, not the previous one. The separate
file-import `rAdd` eligibility/phase guard stays intact. Current errors remain
visible and current401 still delegates authentication handling once.

Initial receipts, the first save-only repair and the final combined repair are
immutable and separately source-bound. Same case IDs, test/fixture hashes and
actual child exit codes are checked; no fixture or expected value changed.
Two actual browser tests obtain genuine409 conflicts by externally advancing
SQLite notes before a stale expected-revision PUT, hold only response delivery,
and verify B draft/notice/auth retention versus current conflict display.

No Frozen semantics, game observations, old tests, DB schema, backup format or
coaching denominator changed. Independent inspection found no material issue
in the installed async callers. Scope is epoch-changing navigation/logout;
same-epoch operations retain their current context. Rollback is a code revert
with all original observations and receipts preserved.
