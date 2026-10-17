# Official skill display v1 — 2026-10-17 user addition

Display only: `소유자명 의 공식 스킬이름(슬롯)`; the Korean possessive is rendered without a space (`럭스의 빛의 속박(Q)`). The five champion slots are P/Q/W/E/R. Names and slots come from the retained official Data Dragon archive, not role/classification inference. No provider call or new collection is needed.

The generated public name table binds every champion's official passive and spells[0..3] to P/Q/W/E/R, checking the retained file hash and exact official name. SkillDisplay is a pure display adapter. Existing engine reports, facts, raw excerpts, source locators/hashes, saved snapshots, grades and approved/reviewed wording are unchanged. Raw-source/JSON/history views preserve original bytes; formatted display is separate from that source.

Explicit champion+key and official-name references are formatted with their owner. Ownerless repeated names (the real Anivia E/Braum Q `동상` collision) and bare keys do not default to the user's champion or first pick. Authored shorthand in the representative six rows requires explicit per-decision/per-field mention bindings. In particular the two E references in the level 3–5 alternative refer to different champions. Generic effects (`속박`, `보호막`) and shared mentions of traps do not become a particular champion ability. Summoner spells/items are not champion P/Q/W/E/R slots.

Rendering is idempotent: an existing correct `(Q)` is not duplicated. Multiple champions retain explicit owners in summary, lane, operations, fight, scenario, map step/zoom/accessibility/tooltip and existing PC reference/card/queue displays. Official headings use name(slot); raw excerpts stay raw. No change to strategy interpretation or automatic/user approval follows from display normalization.

`skillNames:true` is permitted only for a field independently verified to be an exact list of that owner's official ability names. It is never enabled for free prose. Otherwise common names such as 준비/반격/매혹/공포 remain ordinary prose unless the author explicitly identifies the owner or a bounded mention binding. Existing contradictory name/key pairs do not become verified cooldown bindings. Original source/JSON sections are explicitly separate from formatted narrative.

Expected checks: all official slot/name mappings; multi-owner equal keys; repeated names; already formatted keys; passive; unknown/invalid/mismatched locator; summoner/item exclusion; same bare E with explicit different bindings; no input mutation; raw/source/engine bytes unchanged. Browser checks cover PC and 390px loading summary/six rows/fight/scenario/map/zoom and existing PC/reference displays. Changed-only tests and required CI run; completed unrelated evidence is reused. Real coaching N=0 and Windows client BLOCKED_EXTERNAL remain.

Rollback: revert only the display adapter, generated name table, consumers, export/static additions and their bounded verification changes. Original facts/engine reports/grades are never rewritten.

2026-10-17 readability addition: when a skill label immediately follows the same explicit
champion subject (`노틸러스가 노틸러스의 닻줄 견인(Q)`), omit only the redundant display
possessive (`노틸러스가 닻줄 견인(Q)`). The adjacent subject identifies the owner. Other-owner
skills retain their possessive. Compare complete official labels, so an owner-like substring
inside `드레이븐의 리그(P)` remains intact. Raw facts/quotes/JSON remain untouched.
