# Shared web visual system v1 — presentation/state, no tactical rule changes

Authorized 2026-10-17 latest reference-system request. Reuse main9abd431/PR69–71 and prior
actual public receipts; do not collect matches/videos, rewrite advice or expand matchups.
Core surfaces: home + personal/pro dashboard, manual10pick/loading summary/detail, six-scene
practice and status snapshot. Existing PC/internal tools/launcher/private API contracts intact.

coach-theme.css owns semantic colors/type/spacing/radii and shared primary/secondary/selected/
pressed/focus/disabled/error behavior. Page CSS retains layout, artwork gradients and map
geometry but references central tokens (no per-page root color palettes). Existing map meanings
stay ally-blue/enemy-rose/own-gold/move-blue/pressure-gold/retreat-violet. Do not turn caution,
source grade or champion strength into a generic accent. Controls/rem type remain readable;
radio/checkbox sizes are separate from full-width text inputs. No new framework or graph scores.
coach-shell.js owns one fixed native menu/outline-icon component with PC sidebar and mobile
menu; actual focus/hash updates dashboard/review selection. First skip link, keyboard/touch/
Escape/outside close, visible focus, no hover-only information. Page engine state remains owner
of card/step/map/zoom selection; shared shell never touches analysis/preferences or live state.

Official decorative hero catalog hero-art.json reuses verified local Ahri/Caitlyn default
splashes with URL/hash and independent desktop/mobile crop metadata. Initial HTML has no
candidate src; read only visual ID from sessionStorage, choose random valid item once if
missing/invalid. Re-render/input/API state never reseeds. New session chooses anew; same session
reload keeps selection. Get/set storage failure falls back locally; no ID/account/picks stored.
Manual change chooses another item, preserves input/region/focus/scroll/layout. No autoplay/
background video or other-candidate preloading. Fixed local source allowlist and finite crop
validation. Art/candidate-list failure shows fallback but keeps search/guest/manual prep usable.

AI card triptych authorized by user, generated once and explicitly labeled AI illustration.
Original generated PNG preserved in workspace/generated_images. WebP encoding derivative,
1024x1536 with three equal horizontal panels, provides221432byte public asset instead of
2517785byte PNG. SVG viewboxes crop the unchanged decorative composition responsively; no
actual game screenshot/official art/tactical geometry/evidence/known enemy position claim.
Three native whole-card links and existing post-10pick fixed destinations preserved; image
choice never changes picks or account/pro records. Official sources, AI art and tactical
map/portrait explanations are separate. Old official stills/source histories remain retained.

Search retains input/loading/result/errors and explicit manual retry; public static sends no
private-account/provider request. Private backend auth/quota and first-failure stop unchanged.
Guest→dashboard→'이번 판 준비하기' preserved; no fabricated tier/win/KDA/coach scores. Retry is
user-driven, not automatic provider retry. API failure does not disable manual preparation.

Affected checks: actual PC/mobile cross-page menu/style equality, controlled fresh-session
random choices, reload preservation, single initial hero source, manual input/focus/scroll,
image failure/catalog empty/API failure/retry/guest, 10pick→phase→map zoom, keyboard/menu/
200% text/no overflow, explicit export/PC asset/auth boundaries and image source separation.
Required CI includes existing protected wave/encounter/skill/step/map regression. Functional
checks !=30second comprehension (unmeasured), strategy validation or coaching accuracy (N0).
WindowsBLOCKED_EXTERNAL and AUTO30/HOLD20/advice7/quotes/holds/failures/Gemini10/17video3/3 stay.
No Gemini/game collection/paid plan change; one authorized image-generation tool call only.
Rollback shared CSS/script/hero JSON/new AI web asset, restore old page styles/headers and
hero loader; retain receipts, generated/source originals and protected strategy/history.
