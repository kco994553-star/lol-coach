# Collection cadence integration delta

After Main's final guard-v2 ready signal, `python -m unittest -v tests_pregame.test_recall_collection_v23` passes all11 new collection tests. Output is preserved in `collection-cadence-green.log`; exact extractor/test bytes are recorded in `collection-cadence-receipt.json`. No provider requests, Secret reads, dispatches or commits were performed.

The earlier three integration failures are preserved in Main's `cadence-integration.log`. The borrowed predecessor fixture actually had origin0 plus60000/180000 received frames; the missing120000 internal frame caused rejection. The new collection module now uses its own synthetic fixture adapter with0/60000/120000/180000 received frames, explicit empty origin events and an explicit synthetic120000 snapshot copying preceding participantFrame values with empty events. Health stays intentionally absent. This construction is test-only; production does not fill gaps. The predecessor fixture constructor remains unchanged, and no old test module was executed.

The final guard excludes the last received frame and clips event timestamps to the penultimate received time, so this fixture's effective event coverage ends at120000. These collection tests establish acquisition, privacy, deduplication, exact-patch filtering and receipt behavior. They do not require invented first-recall purchases or health values to make the data look usable; valid match observations can retain UNKNOWN details.

The added rejection test removes origin0 and verifies all relevant entrypoints fail closed: cached envelope extraction raises, the offline CLI returns BLOCKED_EXTERNAL without a public dataset or provider call, and the fresh fake transport raises after its original four requests with no retry, no retained anonymous observation and cleared pending raw match. Existing tests continue to verify malformed cache rejection, SYNTHETIC source rejection, auth stops, hard caps, safe output projection and workflow gates.

Scope: only `tests_pregame/test_recall_collection_v23.py` plus these collection cadence evidence files were changed in this follow-up. No implementation change was needed.
