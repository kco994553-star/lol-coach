# Independent loading-context implementation review

Reviewed at 2026-10-17T05:14:23.776792+00:00; branch `work/loading-context-20261017`, intake HEAD `b9cb5ed60e8cfefb743da57cdcc34d8cdca3111f`. The table below binds the actual working-tree bytes, including uncommitted repair files. Reviewer was a separate read-only AI agent; only this review record was written.

**Assessment:** no unresolved blocking finding in the reviewed engine/UI/catalog/context-test scope after three P2 repairs. This is software, source-boundary and output-semantic review. It is not expert coaching approval, player comprehension evidence, matchup validation or real-game efficacy evaluation. `real_coaching_n=0`, `accuracy=null`, expert adoption/validated coaching examples=0. Existing AUTO/HOLD/USER grades do not transfer.

## Findings and verified disposition

| Priority | Independently reproduced defect | Repair verified in actual output |
| --- | --- | --- |
| P2, resolved | With enemy Kai’Sa BOTTOM assignment cleared but Nautilus still SUPPORT, the same-position-opponent gate discarded the known assigned support from the complete lane threat set. | Assigned duo candidates are now gathered independently of the primary counterpart. The incomplete lane retains Nautilus; `lane.opponent` stays null; the representative template stays inactive. The symmetric Lux-self/enemy SUPPORT-missing case retains assigned Kai’Sa. |
| P2, resolved | Swapping Kai’Sa to SUPPORT and Nautilus to BOTTOM still activated the representative six-row template, despite its exact actor/position eligibility contract. | Exact enemy BOTTOM=Kai’Sa and SUPPORT=Nautilus checks now gate specialization. Role-swapped output retains its real duo members, selects Nautilus as counterpart and has `matchup_id=null`. |
| P2, resolved | The insufficient-binding Gangplank/Kindred/Hwei/Caitlyn/Teemo roster kept its base role and removed the follow-control action ID, but its concrete second fight action still assumed an allied control hit and proposed trap follow-up. | Concrete Caitlyn action now branches on verified control candidates. With none mapped, it names the unknown connection and compares attackable targets, E and exit space; it no longer emits the control-hit follow-up. With mapped control it names the actual control candidates. |

## Actual checks and useful meaning

- Fresh `python -m unittest tests_pregame.test_loading_context -v`: nine tests, zero failures. This includes the three findings above, source projection/locator checks and the original actor/context/permutation/support/distant-ally/missing-assignment/role invariants.
- Independent Node assertions: all 120 permutations of allies and all 120 permutations of enemies preserve the full report excluding input echo. Additional assertions passed for symmetric partial enemy assignment, a manual Zed comparison, jungle with no fixed counterpart, insufficient-control concrete action changes, actual allied map membership, and `N=0`/null output. These were focused probes, not a gameplay simulation.
- Compared against intake HEAD: the original 865 champion description facts, all 353 statistics, and all six direction presets remain identical. Independently recomputed every one of the five supplement source hashes and traversed each exact JSON locator; all raw excerpts match retained sources. Three tooltip supplements and two item-property supplements remain separately identified.
- Read actual representative summary, all six rows, roles, candidate sets and maps, plus support/enemy-support/distant-top substitutions. The milestones make distinct future decisions: receive with spacing; conditional bind follow-up; reserve escape/cover; account for targeted control/Plasma access; reassess observed purchases and return; reconsider follow-up after a core item. They include explicit unobserved skill/state assumptions, opposing responses and alternatives.
- Base classification and proposed plan are separate objects. Same Caitlyn/position retains its base ID across ally changes; verified control/cover changes the proposed conditions/action IDs. Insufficient bindings preserve the base with limits and now alter the concrete fight action as well. A classification label is not recorded as proof of optimal strategy or readiness.
- Base lane text/candidates use assigned lane actors; global Ornn/Sejuani/Zed/Fiora do not become Caitlyn’s lane actors. Jungle intervention is a separate unobserved future condition. Unknown lane assignments are not backfilled by champion style. Operations and fight retain actual roster candidates independently, including unclassified limits. No importance score, source-order top-two selection or observed arrival was found in the reviewed repair.
- Caitlyn recall maps use assigned lane partners. Fiora/Ornn postlane examples use the operations candidate set and explicit future requirements. All maps show actual allied picks, no invented enemy portraits, and explicitly hypothetical positions. They remain illustrative geometry; arrows do not prove safe paths, exact skill ranges or measured positioning quality.
- UI code renders candidate reasons, lane/jungle/operations/fight separation, base/proposed role rationale, six-row assumptions, opponent responses, alternatives and source boundaries. Text is rendered through `textContent`; source links require HTTPS. Browser/HTTP/CI/publication receipts remain Main’s integration responsibility and are not claimed by this review.

## Retained-source and confidence limits

Independently read the retained four-champion P/Q/W/E/R descriptions, the Kai’Sa R/Lux W/Lux E tooltip fields used by the repair, and boots/longsword item properties. The source supports Plasma-gated Kai’Sa access, wand-contact shielding, Lux E area reveal, Caitlyn recoil/trap activation and Nautilus’s described control mechanisms. No numeric template values were evaluated. The review found no claim that a Lux bind guarantees a trap chain, an early level proves learned/ready skills, minions guarantee safety from Nautilus Q/R, Caitlyn E cancels Nautilus R, a core item proves Kai’Sa evolution, or an item purchase proves matchup superiority.

The official text supports mechanisms. Spacing, timing, target choice, follow-up and fallback remain `DESIGN_HYPOTHESIS`; assumptions are `NOT_OBSERVED`. Detailed six-row knowledge is bounded to the correctly assigned representative duo. Other rosters use a limited conditional framework and partial function bindings; this review does not establish complete champion coverage, matchup quality or teaching usefulness. No provider/network/game/video call, old full test suite, protected issue mutation, expert/POV adoption, real player trial or live-game validation was performed by this reviewer. Historical findings and Main’s pending integration work are preserved rather than converted into successful receipts.

## Reviewed byte bindings

| Path | SHA-256 |
| --- | --- |
| `AGENTS.md` | `8a3991710fc377a3d5d6b634635fdb513e248731045d2b2385c4dd356a268450` |
| `CURRENT_HANDOFF.md` | `9f798d0f8fe56a04d6a8abca130bee48636fc27aadd92164871c8946f9a96b62` |
| `contracts/loading-strategy-v1.md` | `3c16cca8ca673c2307659ee6c63395b7530a8dea3a30b08828341ce8034f24ab` |
| `contracts/loading-context-v2.md` | `8ababd873cec08294d04a1fbde7005a055d94969983d5e8f6e89501056924435` |
| `web_r4/loading-engine.js` | `47acf437b202a447f023c97c58a029de928a9e16bdf0d7d75e57c632607353dc` |
| `web_r4/loading.js` | `283cf590047c4b2e253b89f75fb48c24d641686b73e97ec12f7478824a88daba` |
| `web_r4/loading-data.json` | `afed16abf57639b0c748c1c3fa711703d0ec97d595f58356c419322ac8fdd562` |
| `web_r4/loading-map.js` | `7555f5c879f590f18f647d320deeec7ce563b2f13f611c4a25ab290e5052062d` |
| `web_r4/directions-engine.js` | `86236dff0e2f0e44b5e230e20a9a745e833625d55b8858298d3eea9ed15bae26` |
| `web_r4/directions-data.json` | `c4560f2602295fb689bfe29f901babb78afeaece1fae04b60277b00bce8d4920` |
| `scripts/build_loading_catalog.py` | `993aa93cd96747868e80d4578b7622fc37125affc46ad02dc7c06b7a2c616367` |
| `tests_pregame/test_loading_context.py` | `cc9c9ae823f0fbfc5a0c0b003cfdc555a6ab0ea404d5008c2b415bd579095599` |
| `evidence/actual-evidence/loading-context/baseline-projection.json` | `40d29ebf7e4243718dd989b19e7ac2ed46bf4ec2100b68d11c763c966381420b` |
| `evidence/actual-evidence/loading-context/mechanism-audit.md` | `70863cd07f78b9d59eab51d7fa54f49de6cd2f8998017fcfe8f86a1740f7f584` |
| `evidence/actual-evidence/loading-context/mechanism-audit.json` | `f5e8b0c0fe053d2c29cd3d60c4266cf549a9cf499406f9249a13c0d1834aea79` |
| `data/official_catalog/versions/16.20.1/Caitlyn-16.20.1.ko_KR.json` | `d3215fc64246d7014dbd924cf1b76620756f84184c01191f0f6ffa65c3625029` |
| `data/official_catalog/versions/16.20.1/Lux-16.20.1.ko_KR.json` | `93a8e2062496941166b55bea23541f428ac6f1511c8c15c2eb2a8efcc5f93d9b` |
| `data/official_catalog/versions/16.20.1/Kaisa-16.20.1.ko_KR.json` | `98544004fbc81a31b38a8856c301b5434e7881bb05fd4ec708dabb0827214ed3` |
| `data/official_catalog/versions/16.20.1/Nautilus-16.20.1.ko_KR.json` | `87cf8bdca7e108fc7214c921715298e04a350bca1d619a8aa8c0ab0450e7ce32` |
| `data/official_items/versions/16.20.1/item.ko_KR.json` | `8fd60c77bddc212fd1550850f0db01caa68c05c9f11e377d52df03a9627f8085` |
