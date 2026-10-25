# Scenario tools and qualification

Use when a Garrison task needs scripted interactions, bounded effect lifetimes, UI artwork/custom font lettering, crowd-work budgets, elevated-surface experiments or cosmetic ragdoll research. These helpers supply mechanisms; the mod supplies its assets, rules, adapters and lifecycle. Use `aoe4-game-mode-skill` for actual SCAR implementation and current stock API contracts.

## Version and evidence

Historical inspection on 2026-10-10 used **0.1.3**: its release/scenario guide, installed SCAR modules and walk-surface/light panel source were read, and Blender 5.2.2 LTS exposed the UI-asset/walk-surface modules. On 2026-10-11 the installed manifest/guide reported **0.1.4**; its release/API details were reconciled without new authoring, cook or native tests. Read [Script development](script-development.md) for the new current-match runner and [Runtime contracts](runtime-contracts.md) for native orientation, Point declarations and pure helper lifecycle details.

The release guide reports general authoring/cook/readback and operator-led solo acceptance. It leaves intermittent bridge passage, collision, deck entry and latest cathedral changes pending. Do not convert that report into acceptance of a new mod's feature. The supported product route is guarded Steam `-dev`; multiplayer and automatic passenger parenting remain unqualified. Do not assume a separately distributed `garrison-play.exe` or per-frame presentation diagnostics exist.

The release describes improvements to AI, presentation, list editing, lights and ragdoll, and new commands/effects/UI/surfaces/fonts modules. Blueprint list appending was already documented in the earlier guide; avoid presenting every release-note mention as a newly introduced capability. Shared authoring and eligible add-on logic are compiled; inspect exposed contracts or installed help when Python source is unavailable.

## Commands and contextual interaction

Create one `Garrison.commands.new(protocol)` per shared input channel. `register(channel, kind, resolve, apply)` separates current actor/owner/generation resolution from payload/phase validation. Only the controlling local human encodes intent with `encode`; send it through the game's verified network event mechanism. The shared receiver supplies the **engine sender ID**, message and simulation time to `receive`, never a sender claimed in the payload.

The envelope checks ownership, generation, epoch and increasing sequence. It consumes a sequence before applying its callback, including a rejected action; it is not a reliable transport or reorder buffer. Reset only at a shared match boundary. Do not replay native Move/Stop orders already handled by the engine.

For a chest, door or lever, `commands.interaction(adapter)` owns pending approaches. `request` records actor/target IDs and generations with a timeout; `adapter.ready` returns false, `approach` or `use` after checking shared ownership, phase, range and height. `approach` sends one native order and `activate` applies the authorized scenario action. Drive `updateInteractions` from an existing simulation rule and `cancel` when another command takes over. Local picking/highlights submit intent and stay outside shared policy.

## Bounded work, effects and presentation

- `Garrison.ai.budget(rate, burst, time)`, `allow(budget, time, count)` and `visit(budget, sortedActors, limit, callback)` spread work over a bounded round-robin slice. Use simulation time, a stable ID-sorted snapshot and generation checks; shared work admission must not depend on local camera visibility or measured frame time.
- `Garrison.effects.new(adapter, capacity)` retains bounded effect/decal handles. `emit(state, event, time, lifetime, cell?, cellLimit?)`, `tick` and `clear` manage admission and expiry. The adapter supplies `create` and `destroy`; failed destruction remains accounted for and eligible for retries. The mod owns materials/textures, placement, variation and gameplay triggers. Entity carriers need shared simulation handling; genuinely local render handles may have local presentation policies.
- Existing `Garrison.presentation` snapshots/assemblies handle scripted prop transforms and visibility through adapters. They do not supply arbitrary native skeleton animation or guaranteed atomic engine writes. A body visual's lifetime must not resurrect its dead gameplay actor. Reuse audio sessions/event budgets instead of one audio process per actor.

Ability-driven animation has a separate native binding/graph gate. The 2026-10-11 Tuareg cheer fixture played but blocked movement; the stock guard selector remained true during delayed moving transitions. Successful `pcall`/forced-tree submission did not acknowledge playback. Read [Native animation research and diagnostics](animation-research.md) before using these mechanisms for uninterrupted combat motion.

## UI images, titles and bitmap fonts

**Mod Project → Icons and files → Import UI Image** validates a PNG, packages it through normal UI texture cook, and records its native Source reference in an authoring receipt. Maximum 2048 pixels per side; each dimension must be divisible by four. Invalid images are refused with required padded dimensions. Preserve an existing asset by choosing a new name for a revision. Shared API: `ui_assets.add_image`.

**Import Font** accepts a TTF/OTF the user may use:

| Mode | Output and limits |
|---|---|
| Title image | Fixed text rasterized as transparent white PNG; font-generated padding preserves lettering proportions |
| Changing text | Printable ASCII glyph images/metrics, generated SCAR import and `Garrison.mods.<key>.fonts.<name>` entry |

The font file stays outside the archive and is not installed in Windows. This route does not register a native font family; the toolkit does not supply a license. Dynamic Arabic, Tamazight/Tifinagh or other unsupported text needs the normal native label fallback. The guide states these operations use the bundled core, without a separate Python installation. The receipt records the selected font hash.

For a verified contributor source environment, the fixed-title command is `py -3 -m src.core.ui_assets <project> <name> <font.ttf> --text "Chapter One" --size 96`. Changing-text mode substitutes `--font --size 32` for the text/size arguments and calls `ui_assets.add_font`; fixed text uses `raster_title`. Treat sizes/text as example choices and inspect current CLI help. Do not assume `src.core` is importable from the compiled extension alone; ordinary panel import needs no contributor checkout.

For dynamic text, import the normal project loader and receipt-specified metrics (for example `ui_fonts/<key>/<name>.scar`), then construct `Garrison.fonts.new(Garrison.mods.<key>.fonts.<name>)`. `fonts.show(label, existingContainer, text, maxWidth)` returns false when it cannot show the label; show native fallback then. The container must already exist. Display truncates to at most 64 characters, adding an ellipsis when needed; identical text avoids repeated native work. `fonts.clear` retains failed removals for retry. Do not tie shared game outcomes to local UI success.

`Garrison.ui.new(adapter)` owns one local root. `play(state, spec, time, duration)` replaces its predecessor and returns a generation; bind image sources before the adapter triggers native animation. `tick` expires the root, protects replacements from stale generations, and retries retained removal failures; `dispose` tears it down. The mod must call these methods from its own UI lifecycle. This is not an automatically installed victory/title system.

## Walk-surface experiments

**Map → Walk surfaces** creates an editable ordinary mesh that may be parented to a prop in Blender. **Export Surface Recipe** reads evaluated triangles/placement into a new JSON recipe, preserves the scene, and refuses to overwrite a recipe. `walk_surfaces.add_to_project(project, name, recipe)` builds an experimental static probe using the existing cook.

Blender parenting does not create native passenger attachment, collision or traversable decks. For moving-surface work, use `Garrison.surfaces` local frames/exclusive passenger leases and `surface_routes.create(mesh)` path/step/exit operations. One graph represents a single local height layer; move its frame instead of rebuilding it each tick. Local `surfaces.pick` returns a point; validate surface generation/local position through shared intent before passenger movement. Native movement, clearance, entry/exit transfers and combat remain the adapter's responsibility. Qualify a static probe before claiming moving-platform behavior.

## Ragdoll and light qualifications

The release says the player includes a **Jolt physics backend** for prepared-rig cosmetic ragdolls, with stock-animation fallback. The 0.1.4 release adds requests for bounded launched-ragdoll simulation duration and travel distance, retaining existing defaults. It does not enable physics for ordinary stock units automatically or document a general new bone/clip export route. Inspect the current prepared-rig/native request schema before choosing parameter names or ranges; the release note alone supplies neither.

The earlier 0.1.3 `ragdoll.scar` inspection exposed `Garrison.ragdoll.direction(event)` only: it chooses direction from projectile velocity, blade velocity, supplied direction, attacker-to-victim vector, then facing. That historical helper inspection does not establish the entire 0.1.4 backend surface. It did not qualify activation, skeleton binding or a death callback; the installed guide update also supplies no new general end-to-end acceptance.

Before authoring a ragdoll probe, inspect the actual player feature gates, prepared rig/body recipe and native adapter contract. If those cannot be established, report the specific gap and preserve stock death animation. Treat cosmetic playback and gameplay death independently. Backend availability does not broaden the two Build Unit prototypes or add authored attack/death clip replacements; see [Animation contracts and qualification](animations.md).

The release mentions light softness/flicker and scripted on/off. The inspected light panel source exposes radius, intensity, flicker and colour; no softness field was found there. Inspect the relevant shared schema/operator before prescribing a softness control. Keep the existing distinction between authored effect-light resources, follower movement and a bounded native adapter for existing point lights. This update does not establish arbitrary runtime colour/intensity changes.

## Build and native qualification

Import the generated loader to expose helpers; importing it installs no scenario policy or timer. Validate authored receipts/references, cook and read back resources, then package/import/select the intended version. In a fresh solo match, separately verify rendering, interaction cancellation/generation handling, effect/UI cleanup and relevant collision/transfer behavior. Report document/source, build/readback and native evidence separately. Update only guidance supported by the exact tested fixture; keep pending surfaces, ragdoll and multiplayer cases explicit.

Sources: installed `guide/release-0.1.4.html`, `guide/release-0.1.3.html`, `guide/scenario-contracts.html`, `guide/mod-project.html`, `guide/play.html`, `guide/point-lights.html` and `guide/garrison-modules.html`; historical `garrison_shared/scar_modules/{commands,effects,ui,fonts,ai,ragdoll}.scar`, `walk_surface_panel.py`, `light_panel.py` and exposed compiled `ui_assets`/`walk_surfaces` inspection. Use the current installation instead of assuming paths/private repository examples are available. Font contributor CLI forms are documented in scenario-contracts; ordinary Import Font/UI Image uses the installed bundled core.
