# Expert v1 clarification — 2026-10-11

Additive clarification of expert-v1.md; no original bytes rewritten.

1. independent_group_id appears in each claim only, not an additional video key.
   normalize_gemini_claims receives an already decoded dict top-level; emitted
   normalized claims omit the group until the artifact assembler adds YOUTUBE:ID.
2. Malformed top-level returns no claims and rejection FAILED_FORMAT. Empty or
   all-rejected input also returns NO_ACCEPTED_CLAIMS. Safe rejection enum is
   FAILED_FORMAT, INVALID_CLAIM, INVALID_TIMESTAMP, OUT_OF_RANGE_TIMESTAMP,
   DUPLICATE_CLAIM, NO_ACCEPTED_CLAIMS. Accepted artifact must contain at least one
   claim; failed acquisition belongs in a separate status receipt, not an empty
   expert artifact. Maximum100 claims/rejections per artifact, total<=200KB.
3. When speaker_verified=false, speaker must be UNKNOWN. A true value is the
   caller's source-identification attestation, not machine verification of the
   speech or professional credentials. Manual method requires model=UNKNOWN.
4. Timestamp is canonical two-or-more minute digits plus exactly two second
   digits0..59; timestamp_seconds equals60*minutes+seconds. Duration positive
   integer<=28800. UTC timestamps may use Z or +00:00; date fields are valid ISO.
5. New HTTP claims rows contain the immutable original artifact claim and the
   current stored proposal (which may be a later manual decision version), not
   a fabricated current approval. Comparison delegates to additive
   coach_v1/expert_measurement.py compare_claim(claim,movement_data,test_mode=False).
6. Startup expert dir file limits: max100 files, each200KB, total2MB, regular
   files only, filename11character videoID.json or safe manually named *.json;
   reject symlinks/path escapes/invalid JSON before importing any file. Directory
   optional; explicitly supplied missing directory is an error. Imported local
   source-identification assertions remain assertions; no executable rule is
   generated from prose.
