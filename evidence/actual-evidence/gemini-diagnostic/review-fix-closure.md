# Review fix closure

Surrogate byte count no longer throws away all diagnostics: invalid nonthought UTF8
is counted without storing text, fails TEXT_UTF8, and preserves usage/stages. HTTP200
non-object JSON is required to be a response object before the unchanged parser;
thus it records MALFORMED_RESPONSE, not a network error. Two dedicated tests failed
before correction; all46affected tests passed afterward. No provider request made.
