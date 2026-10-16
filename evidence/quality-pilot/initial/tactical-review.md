# Independent tactical review

Packet SHA256: `0bf011d5641f44d6921c66f347d880c950a78980f39f8f6f32de561ace3c04d4`

HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Conditions review concerns wording only. All seven tactical verdicts remain HOLD. Historical PASS receipts cover old candidate hashes and are not votes or validation of revised actions.

## QP-20261016-KR-001-v1 — CHANGES_REQUIRED / tactical HOLD

Candidate SHA256: `d1b4eb6bbe7d12473bdb10bf732eae8870589a1893abe583e492b49cb6283f3e`

Findings:

- A1 is a positive wall-dash instruction after Riposte availability and geometry checks, but those checks are not sufficient to choose a fight: own health, visible additional threats and the purpose of committing E are absent from its choose_if. A limitation saying safety is unproved does not repair an imperative with inadequate decision conditions.
- A2 correctly distinguishes an unavailable Riposte from its animation ending. However, treating available/unknown Riposte as a universal reason to give up wall initiation is an unvalidated conservative policy; scope it to this voluntary initiation comparison, and do not extend it to urgent peel/escape decisions.
- No invented bait, successful bait, guaranteed relocation or automatic enemy-cooldown observation is claimed. Source facts describe terrain knockup and Riposte; they do not certify when E is worth using.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: Riposte is known unavailable and Fiora stands at the selected wall, while Ornn is low and a visible second enemy can punish the commitment. A1 checks can all hold although choosing the dash is harmful.
- POSSIBLE_NOT_OBSERVED: Ornn must choose an immediate defensive or ally-protection action. A rule to abandon wall E whenever Riposte is available may remove a necessary option; this review does not claim E would succeed.

What improved:

- Replaces ambiguous animation-ended check with actual current-use-availability check.
- Adds explicit geometry and movement-change stop conditions and labels the fallback unvalidated.

Needed evidence or wording change:

- Add own-state/visible-threat and chosen-fight-purpose checks or soften A1 to an option comparison.
- Keep voluntary setup separate from urgent defensive decisions; obtain known-view scenes and action comparisons before any utility claim.

## QP-20261016-KR-005-v1 — PASS / tactical HOLD

Candidate SHA256: `f8ca453683fcbc2b8f5c2e13a7fec343ff435280663d2c2899faae178f84a91f`

Findings:

- A1 asks whether available follow-up can be used at the current position; it does not turn charm hit into permission to chase. Its targetability, health, skill-readiness and reach checks are meaningful restrictions, and forward movement triggers a new decision.
- A2 cancels the charm-follow-up plan on miss/untargetability, rather than asserting all damage or defense is impossible. Comparing another target, remaining or moving is explicitly conditional and makes no safe-route claim.
- The source describes charm and Death Mark mechanics, not stationary follow-up superiority. No kill, bait, poke or fixed Zed reappearance location is invented.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: Charm lands but Ahri is in lethal visible area damage or Death Mark danger; attacking from the same spot can still lose. Health/reach checks must be used to choose, not as proof that stationary follow-up is beneficial.
- POSSIBLE_NOT_OBSERVED: One short forward move could permit a finishing attack while stationary follow-up cannot. The card should not be read as a permanent ban on a separately evaluated chase.

What improved:

- Separates hit confirmation, targetability, stationary follow-up and chase.
- Explicitly cancels the failed plan and gives several uncertain alternatives without promising safety.

Needed evidence or wording change:

- Known-view charm, targetability, own-state, other visible threats and action evidence.
- Compare stationary attack, movement and defense for the same decision conditions; retain HOLD meanwhile.

## QP-20261016-KR-008-v1 — CHANGES_REQUIRED / tactical HOLD

Candidate SHA256: `a21a3107a9e794b31a28c82715dbb396dcbc6dfc061db32fae225b05e3e07b09`

Findings:

- A1 makes recoil destination universally prior to net-hit angle and permits net movement only where post-recoil observation is possible. Neither priority nor future visibility is established by the quoted mechanics. In an urgent response this can encourage delaying the only available defensive input.
- Candidate visibility, anchor trajectory and terrain access are useful setup checks, but choosing a plausible destination is not observation of an actual landing. Add a deliberate-planning scope or an explicit urgent-response exception; do not infer exact recoil/collision behavior from the excerpt.
- A2 usefully rechecks actual position independently of net hit. No hidden route is declared safe, and the text does not claim net hit guarantees escape.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: An anchor is already incoming and there is no time to inspect all candidate landing threats. Waiting to satisfy the post-recoil visibility gate may be worse than choosing an uncertain immediate input; no dodge success is asserted.
- POSSIBLE_NOT_OBSERVED: Two angles have comparable recoil exposure but only one can land the slow. An absolute recoil-over-hit hierarchy can suppress relevant offensive/defensive value not evaluated by the card.

What improved:

- Breaks vague danger into observable enemy, anchor and terrain considerations.
- Separates pre-cast angle choice from post-cast actual-position reassessment.

Needed evidence or wording change:

- Narrow A1 to a comparison when time permits and remove universal priority/only-if wording for emergency responses.
- Known-view cast input, actual recoil, anchor collision and threat observations; additional mechanics evidence for geometry.

## QP-20261016-KR-015-v1 — CHANGES_REQUIRED / tactical HOLD

Candidate SHA256: `b7ab1b61724b7f7600e1a636d2d4f797dd32212f70ea9c751c71ddbadb89d926`

Findings:

- A1 preselects pausing forward attacks and comparing allied-side movement/current response while own champion and available responses are unspecified. The source grants Lee a conditional follow-up opportunity; it does not show that every forward option is inferior.
- Visible ally position is a candidate observation, not evidence of peel, consent, safety or willingness to receive Lee. The disclaimer correctly avoids claiming backward movement breaks the dash, but the action should compare forward/counterattack options when urgent rather than exclude them.
- A2 correctly requires actual follow-up use/expiry confirmation and rechecks other threats. No exact runtime, damage, successful escape or forced Lee recast is invented.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: Moving forward reaches immediately available protection while moving toward the visible ally exposes the marked player to another visible threat. A1 lacks a purpose/threat comparison that would retain that forward option.
- POSSIBLE_NOT_OBSERVED: An immediately available attack can remove a low-health Lee before a later response, whereas pausing loses that opportunity. This is a hypothetical decision alternative, not an observed kill or validated damage calculation.

What improved:

- Separates first-hit damage from the remaining follow-up opportunity.
- Requires actual use/expiry confirmation and retains uncertainty about movement breaking pursuit.

Needed evidence or wording change:

- Include urgent counterattack/forward escape in comparison or narrow A1 to nonurgent elective damage pursuit.
- Known-view own champion, available responses, Lee state, ally positions and compared chosen action.

## QP-20261016-KR-021-v1 — PASS / tactical HOLD

Candidate SHA256: `50a37a12a7f12390df6de7a1cf4dfffd68714e70452e77d47f927d8df03927de`

Findings:

- A1 applies only after observing the anchor pass and a visible terrain point while own path heads toward it. It asks to reconsider and compare, rather than declaring every movement toward terrain wrong or another route safe.
- A2 conditions its re-anchoring on actual terrain collision and actual Nautilus position. Unknown endpoints stay unknown; there is no fabricated automatic endpoint, hitbox or follow-up range.
- Comparing current position to future access is an unvalidated tactical interpretation of the terrain-pull fact. Conditions wording is bounded enough for this hypothesis, with utility still on HOLD.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: Continuing toward the terrain point is necessary to reach an ally or avoid another visible threat. Reconsideration must leave that option available rather than treating the alternative as mandatory.
- POSSIBLE_NOT_OBSERVED: A different visible movement candidate avoids Nautilus arrival but is worse against another threat. Mere nonoverlap with terrain access does not establish safety.

What improved:

- Turns a generic path reminder into a specific currently chosen movement comparison.
- Uses actual post-collision position and stops on changed collision/visibility.

Needed evidence or wording change:

- Known-view trajectory, actual collision, own alternatives and other visible threats.
- Independent observed action and conditional comparisons; no scene-derived effect is established.

## QP-20261016-KR-022-v1 — CHANGES_REQUIRED / tactical HOLD

Candidate SHA256: `795e39bd60803bdbd6b83c934bb403d01001cb96be89ef3dd4c884756c2bc63e`

Findings:

- A1 commands changing overlapping ally-follow movement before establishing whether staying close serves a chosen mitigation or whether changing movement is feasible. Path knockup risk alone does not establish a universal separation policy.
- The stop_if that rejects a candidate when any enemy is visible conflates visibility with actual threat. A visible distant/unavailable enemy can coexist with the best candidate. Require assessment of observed threat and own response instead of mere enemy presence.
- Updating direction after target movement is good, and A2 does not claim that withholding join handles other threats. No fixed sidestep, guaranteed dodge or extra blast radius is fabricated.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: The chosen defensive action requires remaining within reach of the targeted ally, and separation would prevent that mitigation. The excerpt cannot rank spreading over that plan.
- POSSIBLE_NOT_OBSERVED: The only traversable candidate contains a visible distant enemy unable to threaten during the movement, while remaining overlaps the shockwave. Rejecting the candidate solely because an enemy is visible can be harmful.

What improved:

- Tracks a moving target and current shockwave rather than assuming a fixed line.
- Separates known target/path from uncertain join and disclaims definite avoidance direction.

Needed evidence or wording change:

- Replace mere-visible-enemy disqualification with explicit candidate threat/own-state comparison.
- Scope separation to optional overlap without a deliberate mitigation purpose; known-view movement and target/path receipts.

## QP-20261016-KR-026-v1 — CHANGES_REQUIRED / tactical HOLD

Candidate SHA256: `7112a2f3cf9fd46b3ad3af8a068d5ad3753b19f878d606e8aa03fcaa97547685`

Findings:

- A1 usefully binds scouting to the immediate decision segment, actual revealed area and loss of information. It does not invent ward coverage, invisibility detection, empty-path certainty or a guaranteed alternative route.
- A2 text has an OR trigger (unavailable OR unsuitable observation), while its two choose_if items read as an AND (unavailable/unknown AND older information insufficient). Clarify whether either trigger suffices, including a failed current cast observation or no prior observation.
- Fallback chooses path change or movement hold, and can become an overly passive exhaustive menu during immediate danger. Narrow this to elective segment entry or leave immediate movement under explicitly unknown risk available when remaining is known dangerous. Source scouting mechanics do not prove hold is preferable.
- HOLD: No matching player-known POV/known-view receipt or independently observed action was supplied for this review. Counterexamples below are POSSIBLE_NOT_OBSERVED. Literal mechanics do not establish action utility, expert agreement, real-game accuracy, or USER approval.

Possible counterexamples:

- POSSIBLE_NOT_OBSERVED: Hawkshot is available but its actual revealed area fails to cover the segment; A2 text applies, but the unavailable/unknown choose_if does not. The list semantics create an uncovered branch.
- POSSIBLE_NOT_OBSERVED: Ashe must leave an immediately dangerous current position through an uncertain segment and no visible alternative exists. Deferring all passage can be worse, although no uncertain route becomes safe by necessity.

What improved:

- Connects scouting target to a concrete current movement purpose.
- Separates actual revealed area, stale information, unavailability and Lee follow-up; no arbitrary safety time.

Needed evidence or wording change:

- Make A2 trigger semantics explicit and bound hold to elective entry or add urgent-threat comparison.
- Known-view scouting purpose, actual reveal/loss, current threat and observed decision evidence; official coverage/duration evidence before precise claims.
