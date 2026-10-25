# Runtime API contracts

Read for generated SCAR helpers, MessagePack/native transport, experimental RPC, pure module adapters, rigid visual orientation and existing point lights. Reconciled from installed 0.1.4 guide on 2026-10-11; no new native test or live catalogue query was performed. Use [Scenario tools](scenario-tools.md) for commands/effects/UI/surfaces and [Music/audio](music-and-audio.md) for playback.

## Generated loader and callbacks

Import `<key>/garrison.scar` during the consumer's loading phase. Fields are conditional on project content; do not assume every mod has them. Generated files extend `Garrison.mods.<key>` without replacing one another. The loader imports present helpers **except options**, which the Game Mode entry imports separately. Keep `<key>/live_reload.scar` first when using development loading.

| Generated field | Contract |
|---|---|
| `models`, `models_all` | Model-name -> array of blueprint parts; `models_all` sorts arrays by model name. Spawn every material part together. |
| `precache(player)` | Requests all model parts during setup; missing lookup reports Tuning Pack guidance. No defined return value or visual-readiness acknowledgement. |
| `blueprints.<family>.<name>` | Owner-qualified strings for derived resources, lights and built units: `sbps`, `ebps`, `abilities`, `attachments`, `lights`, etc. Resolve with the matching `BP_Get*Blueprint`. |
| `options.load/defaults/values` | `load()` reads `Setup_GetWinConditionOptions` plus defaults and returns nested section/key values; booleans, integer numbers, dropdown keys. `values` is nil before loading. |
| `sounds.start()` | New audio session plus all-player entity polling four times per second. Repeated starts restart the session. |
| `units.precache()` | Generated loading hook requests unit entity/squad resources; later calls do nothing. Delaying a spawn is not equivalent. |
| `audio` | Same shared endpoint as `Garrison.audio.forMod(key)`; use dot calls. |

Stock `Entity_*`, `Rule_*`, `World_*` APIs retain their names. Engine module callbacks, named global Rule callbacks and Crafted-map `Mission_*` hooks remain global; do not replace a generated map wrapper's hooks when registering your own Core module. The Asset preview template places static model parts, not arbitrary units/buildings; guide showcase placement retries every 0.25 seconds at most 40 times. Those are template details, not a universal Start lifecycle.

## Transport and experimental RPC

Native bridge calls require the supported executable, guarded Steam `-dev` launch and SCAR simulation state. Use public `Garrison.*` wrappers. Missing transport, RPC replies and local presentation outcomes must not select simulation orders, RNG, resources or victory.

| API | Result and limits |
|---|---|
| `ping()` | Protected native call: 42 or nil. Registration only, not backend readiness. |
| `available` | Boolean snapshot of Send and `string.pack` availability at import; `send` checks again. |
| `encode(message)` | MessagePack for nil/boolean/finite number/string/table. Tables encode as maps, including integer-keyed tables. Reject cycles/unsupported values, strings >=64 KiB, total >64 KiB, depth >16, maps >2048 entries or traversal >4096 values. Requires Lua 5.3 `string.pack`. |
| `decode(blob)` | Requires `string.unpack`; integers/floats retain type, str/bin become strings, exact 1..n map keys become a sequence. Same limits; malformed/truncated/trailing data, extension types and nil/NaN keys raise. |
| `send(message)` | Protected encode/native call; false for absence/error. True proves local call success, not dispatcher acceptance or consumer playback. Native Send accepts one value <=64 KiB/depth <=32, with no acknowledgement. |
| `call(message)` | Experimental protected request/reply, decoded value or nil, never raises. `m="echo"` returns `payload`; `m="mod_source", mod=<key>` can return `{path=...}`. Synchronous agent handler, not backend/pipe RPC. Request/reply <=64 KiB. Guide reports no live returned-value acceptance. |

RPC installation additionally checks two native `luaS_newlstr` gates; failure can leave Ping/Send available while refusing Call. There is no inbound polling API (`Garrison_Poll`), generic light allocator or arbitrary-rig transform writer. Confirm current help/source before using a roadmap name.

Send dispatches `m="audio"`/`m="audio_session"` into a bounded **256-message** outbound queue. Each channel's consumer serves `\\.\pipe\garrison-<game pid>-<channel>`; absent consumers lose messages, with connection retry at most once per second. Logs record channel transitions/dropped counts (`no_consumer`, `queue_full`), not each message. Audio uses `audio.<key>`; runtime keys match `[a-z][a-z0-9_]*`, at most 48 characters. Unknown methods/invalid keys are diagnosed/dropped. Data is not written to disk by this transport.

## Pure helper contracts

Modules refresh on each cook for projects with scripts; scriptless tuning packs carry none. Pure helpers support Lua 5.1/5.3; the RPC encoder separately requires 5.3. Use dot calls. Invalid configuration normally asserts, stale input normally returns false/nil, and adapter errors propagate. Read installed `guide/garrison-modules.html` for full signatures before adapting a module:

| Module | Non-obvious operating boundary |
|---|---|
| `scene` | Adapter owns spawn/visibility/destruction. Delayed work uses `{id,generation,epoch}` tokens, not reused engine IDs. Clear destroys in sorted ID order and invalidates old tokens; adapter failure can leave partial cleanup. |
| `ai` | Stores actor references; caller updates alive/generation/route lease. Decide uses sorted actors, increasing tick and excludes manual control/leases; commit revalidates authority and consumes an issued intent before execution. No engine order policy is installed. |
| `physics` | Isolated fixed-step sphere solver, Y-up metres/seconds; no engine bodies or automatic scene link. `advance` requires 0 < dt <=0.5; configured step <=0.05. Consume contact events before the next advance clears them. Saturated collision work discards remaining travel rather than unchecked tunnelling. No public impulse method. |
| `presentation` | Live scene tokens plus copied/normalized pose snapshots. Interpolation is shortest-path **nlerp**, not constant-speed slerp; cut marks discontinuity. A renderer adapter must apply samples. |
| `presentation` assemblies | Borrow 1-128 distinct prewarmed handles; do not spawn/destroy them. Validate all parts before ordered pose/visibility writes. Failed submission tries to hide parts and permits same-revision retry; rollback is not atomic. Close cannot transfer entity ownership. |
| `lights` | Pure `new/spawn/set/clear` operates on adapter-owned handles; partial failures retain state for retry. Followers use precached colour variants, owner/target generation and increasing epoch/revision. Off destroys the effect carrier, not just its visible mesh; clear closes the follower. |
| `audio.events` | Separate cooldown/timing admission source. Starts stopped, configured finite cooldowns, rejects backwards time. True means source admission only. Sink can be endpoint `accept`; scenario owns pulse and contact callbacks. |

`examples/runtime_modules/kinetic_scene.scar` is an optional contributor composition, not automatically deployed `Garrison.KineticExample`. Copy/import an available example explicitly and supply its scenario adapters; no new fixture acceptance follows from pure-Lua tests.

## Opt-in rigid visual orientation

`Garrison.presentation.nativeState(time, rotation, cut, state, neutral)` serializes a quaternion for `Entity_SetAnimatorState(entity, "garrison_pose", payload)`. Cook detects explicitly named authored use of this native-state route and adds `garrison/runtime/visual-presentation.json`; comments, the shipped module and local-alias calls do not request it. Do not infer that an unrelated AnimatorState selector requests visual orientation. Only an enabled requesting archive activates presenter hooks at guarded launch; restart without it to remove those hooks.

The scenario owns the animator's neutral pose/physics. Send position through normal SCAR; this native route replaces rigid visual orientation while retaining engine interpolation, with `cut=true` for resets/teleports. It does not write arbitrary bones. The guide leaves new Football runtime acceptance pending; other objects need neutral-pose and native checks too.

## Existing Point lights

This separate opt-in adapter does not depend on visual orientation. Package data member `garrison/runtime/point-lights.json` with schema `garrison.point-lights/v1` and `groups[]`: each group has `id` and ordered `points[]`; each point has exact cooked `position` [x,y,z], `color` [r,g,b,a], `attenuation` array values and `initial_on` boolean. The guide shows a two-value attenuation array `[1.5,25]`; substitute the actual cooked descriptor rather than guessing meanings or values. The library supplies mod key; declarations cannot supply code/addresses. Validate executable/native instruction gates. Disabled archives do not activate it; capability changes apply on the next game process.

Limits: **1-48 points per group, up to 16 groups per mod, 256 points total per launch**. Conflicting enabled inventories are refused. Use full descriptors from the actual cooked inventory; the guide's sample is not a stock-light identity.

Import the light helper; `nativeMask(states,count)` requires explicit booleans in point order and builds an exact integer by doubling/addition. `nativeState(modKey,group,revision,mask)` produces the payload for `Entity_SetAnimatorState(controller, "garrison_lights", payload)`. The controller entity carries intent, not the light render handle.

Revisions are integers 1-4294967295 and increase when the target changes. Same revision/mask retries unfinished delivery; older revisions or changed masks under the same revision are refused. Retransmit latest target about every 0.5 seconds for late-created sources. Off zeros RGB; on restores original RGB while preserving alpha/position/attenuation/handles. Initial state applies on source creation; scene clear resets targets/revisions and removed handles are forgotten.

Descriptor matching does not authenticate mod ownership. Unrelated sources with identical descriptors are unsafe: live duplicates stop control of that slot but cannot reverse an initial state already applied. The guide's accepted inventory is Football's 33 prepared sources; other inventories, source types, continuous colour/intensity changes and multiplayer remain unqualified. Emission, atmosphere and actual point illumination are separate mechanisms.

Sources: installed `guide/{garrison-api,garrison-modules,point-lights,scenario-contracts,new-units-and-maps}.html`. Live helper/source contracts take precedence after updates; do not treat internal implementation gates as instructions to patch game binaries.
