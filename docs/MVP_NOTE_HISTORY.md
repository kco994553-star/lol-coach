# Saved Research note history

Open a saved resource in **자료 살펴보기**, then **저장된 노트 이력**.
Load the saved-version list and select a version. Its original four note fields
appear as read-only JSON, with the resource, anchor, requested revision and
latest revision observed by that read. **조회한 버전 내려받기** downloads that
exact preview. A separate current-note download keeps its original behavior.

The preview does not replace the editable current note, clear a dirty draft,
change the expected save revision or create another saved version. There is no
restore action in this slice. Saving the current editable note still appends a
new revision through the existing conflict check. Navigation, logout and a
successful save clear the preview and invalidate pending history requests.
Notes remain manual personal records; reading a version does not validate the
game observation, intent, strategy or coaching. Existing rows do not contain
author or saved timestamps, so those values are not generated.

Authenticated GET routes:

| Route suffix after `/dev/v1/research/{id}/notes/{anchor}` | Result |
| --- | --- |
| `/history` | Actual saved IDs descending, current revision and count; an unsaved note has revision0, count0 and an empty list |
| `/revisions/{positive canonical integer}` | Exact stored four-field payload and identity, requested revision, current revision and read_only flag |

Existing resource/VIDEO cue-anchor rules, loopback Host/Origin checks and token
authentication apply. Missing resources or saved revisions return404; invalid
revision spelling/anchor returns422. A missing revision is never generated.
The response's actual UTF-8 byte size is limited by the explicitly configured
`body_bytes`; oversized history returns413 without truncation or mutation.
Invalid stored payloads return409 rather than invented note values.

The original ResearchStore, schema version1, latest-note API, CAS and complete
two-database backup/restore format remain unchanged. New helpers only select
existing rows in the existing transaction boundary. Original old tests,
Frozen payloads and earlier failed UI repair receipts remain intact. The
historical exact-byte gate's deliberate differences are recorded through the
separate current source-version binding, not by replacing historical hashes.
