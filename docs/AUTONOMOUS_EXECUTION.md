# Main Work continuation policy

2026-10-05. The user's Dynamic Workflow v1.0 and Autonomous Execution Authority
v1.0 authorize reasonable implementation, tests, publication and gated merges.
Actual payment still requires approval. Historical policy text remains intact;
it does not override this later instruction or provide missing real evidence.

The three existing Progress, CI and Evidence Watch tasks remain read-only.
Their notifications are not proof that implementation resumed. A separate
single Main executor performs continuation only after fresh repository intake,
dependency and ownership checks. No new scheduling or agent software framework
is introduced. The saved automation prompt is the operating policy.

GitHub's currently exposed webhook supports pull-request events, including
opt-in PR commit updates, reviews and comments. It does not expose arbitrary
main pushes, Actions completion or local Player-POV uploads as webhook events.
The executor therefore uses the already authorized hourly condition check for
those repository state changes. This is polling, not instant push delivery.
Do not promise that an inaccessible local file or a read-only Watch notification
automatically starts a different conversation's executor.

## One writer

Before writing, read the latest main HEAD, top current handoff, open PRs, owner
branches and any existing execution claim. Historical IN_PROGRESS paragraphs
are not current ownership. An active same-scope writer blocks new work.

The single shared coordination ref is `work/main-execution-claim`. Its
`CURRENT_HANDOFF.md` top section is the execution claim; implementation branches
are separate. Every manual/scheduled writer must acquire this same ref. A claim
on an implementation branch alone does not exclude another writer.

When work is actually executable, publish an additive top coordination handoff claim with
status RUNNING, unique run token, owner branch, task scope and exact intake HEAD.
Create it from the shared coordination ref's freshly observed parent and update that same ref without
force. Concurrent sibling updates must fail rather than overwrite. Verify the
claim/ref immediately and before each subsequent mutation. A rejected update
or changed token ends the write attempt; do not rebase an old claim over a winner.
Manual Main Work and scheduled Main execution use this same operating protocol.
If a remote claim cannot be made safely, only inspect and report.

An existing PR alone does not authorize another implementation writer. For a
terminal owner with recorded CI_PENDING, the Main executor may continue by
verifying the exact existing PR/head/run and acquiring its new claim. Unknown
or apparently abandoned RUNNING claims must not be stolen on elapsed time;
termination must be established from execution evidence or owner handoff.
Release ownership as IDLE, CI_PENDING, PARKED_EXTERNAL or FAILED when leaving.
Do not hold a RUNNING claim while waiting for external CI.
Only the currently held token may release a RUNNING claim. Do not initialize a
second coordination ref or take over an unknown RUNNING claim. If the shared
ref cannot be initialized or inspected safely, remain read-only.

## Delta and verification

Compare head, semantic input hashes, handoff, PR/review IDs, CI run/attempt and
evidence state with the last processed state in the automation's private prompt
state. Self-recording changes and already resolved failures are no new work.
No material change and no unfinished authorized task means silent no-op.
CI_PENDING remains eligible without another main commit. Preserve failed runs.

Select regression/integrity first, then the actual critical path, acceptance,
evidence, integration and usability gaps. Park only the external dependency.
Use hard gates and deterministic affected checks first; delegate independent
work when useful. Merge only after required checks, protected regression,
Frozen integrity, conflict/review checks and expected head verification pass.
Then verify resulting SHA and applicable post-merge evidence, and release claim.

Actual Player reference/state/Decision/Coach validation is currently external.
Existing public HUD frames can begin independent source-backed review without
known patch or a new clip. Another same-source AI/OCR agreement is diagnostic;
it is not independent gold. Keep real coaching N=0 and accuracy null until its
own State/Knowledge/Decision gates pass. Do not generate filler features while
waiting, turn observer/future data into player input, or relabel real as synthetic.
