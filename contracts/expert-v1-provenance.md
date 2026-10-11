# Expert v1 provenance and quota safety — 2026-10-11

This additive correction follows independent source review; earlier bytes stay
unchanged. YouTube uploader/channel identification does not identify a speaker
in a particular clip. Config speaker/speaker_verified describe an allowlist
label only. Automatic Gemini artifacts therefore always keep video.speaker=
UNKNOWN and speaker_verified=false until a user supplies video-specific source
identification. Manual true remains an explicit caller assertion, not factual
machine verification. Channel names are displayed separately from speaker names.

Reservation recovery must include failed/cancelled runs, not only successful runs.
Missing/corrupt/ambiguous state fails closed. The selected reservation snapshot
must be the newest durable ledger produced by the serialized collection workflow;
receipt says which run/artifact supplied it. Later processing outputs cannot
replace earlier reservations with a less complete state. Missing history may be
initialized only with INITIAL_ZERO_USAGE_CONFIRMED=true and project usage bound
to this collector (GEMINI_QUOTA_EXCLUSIVE_CONFIRMED=true). If project usage is
shared/unknown and external consumption cannot be measured, actual dispatch is
BLOCKED_EXTERNAL. Failure/cancellation after reservation does not refund quota.
Rolling24h is a conservative operational window, not an assertion about the
undocumented YouTube-duration reset timezone. No service limit or paid fallback
is bypassed. Workflow retention must cover this window; per-run reservation
artifact is persisted successfully before any Gemini dispatch. Do not infer
processed success or release a reservation from a successful workflow exit.
