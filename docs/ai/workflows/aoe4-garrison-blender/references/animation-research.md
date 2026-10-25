# Native animation research and ability diagnostics

Read for ability-driven animation, delayed moving posture, native tree inspection, forced playback or broader private clip/graph work. Search terms: Tuareg, Shrek, shield wall, accepted_call, Havok, opportunity, moving delay, phase preservation.

**Later evidence, 2026-10-24:** [Native predictive animation](native-predictive-animation.md) documents the successful metadata-preserving cattle writer, independent encoder, user-confirmed buffalo idle/full walk, and inspected Shrek private cheer replacement mechanism. The failed writer below is historical and does not remain a universal blocker. The Tuareg graph/layer/latency gaps below are not resolved by cattle playback.

## Version, evidence and separate contracts

Reconciled on 2026-10-11 from the attached discovery record, retained logs/source and Garrison extension 0.1.3 on Blender 5.2.2 LTS. Native observations below were supplied by the user; source/build checks were separate. Do not claim independent review of an entire recording from a report or log. Recheck tools, exposed contracts and resource fingerprints after updates.

An animation feature needs four independently established parts: **authoring**, **native encoding**, **graph selection/transitions/layers**, and **actual gameplay signal/lifecycle**. A Blender Action proves authoring; parsing a container proves reading; a cook proves resource generation/wiring. Lua fixtures prove tested controller policy. None substitutes for observed native playback.

The 0.1.3 public catalogue inspected in the earlier trials admitted 16 villager calm idles, six pelvis-only walks and one English spearman calm idle. The 0.1.4 guide reconciled on 2026-10-11 retains those documented slots, without a new live catalogue query or codec/graph trial; full details are in [Animation contracts](animations.md). No general running/attack/death export or interruptible arm-layer route was qualified. Do not bypass admission checks, invent fingerprints or edit shared native clips to claim a complete motion set.

## Animator owner differs from compatible skin

The English spearman build prototype owns `base_spearman`; the current Tuareg owns `base_spearshield`. The prototype build recorded 182 untouched clips, while the inspected spear/shield container had 222 entries. Rig compatibility does not make their graphs/libraries interchangeable. Querying `base_spearshield` as a build prototype returned **Unknown game prototype**, which is not a finding that the native asset is invalid.

A model-only integration can reuse compatible prototype skin while preserving the target animator, Donso statemodel and equipment. Replacing the whole animator can discard shield motions. A supported calm-idle override on the English prototype is not automatically a Q binding on Tuareg.

## Actual ability signal and owned visual state

The Tuareg fixture detects `GE_AbilityExecuted`, resolves the project-owned ability blueprint, confirms `Squad_IsAbilityActive_CS`, filters four private tiers and tracks actor/entity identity. PBG IDs identify definitions, not per-unit animation playback handles. The recorded ability PBG 1073741839 and mod GUID are project-specific; resolve the current definitions rather than copying these constants to another mod. Use `aoe4-game-mode-skill` for verified SCAR API contracts and event handling.

The verified stock selector is `spearman_shield_wall_byz`, read by `anims_spearshield`. The candidate's private schema retains Donso properties and adds the guard property. Source tracing separated its visual consumers from the Byzantine simulation `Mode_Chooser`; that simulation branch and actual Byzantine shield-wall ability were not installed. This finding is an isolated visual route, not permission to write arbitrary simulation keys.

Do not copy Byzantine shield-wall gameplay to obtain a pose: it also changes movement/attack speed. Preserve the user's ability data. Tuareg's documented values are 50% ranged-damage reduction for 15 seconds and a 90-second recharge field; actual reduction/cooldown are separate native gameplay measurements.

Own only the state/grants installed by the controller. Deduplicate event and active-edge detection; clear on actual effect end with the configured cleanup cap, death/removal, ownership/conversion, entity/tier replacement, restore and game end. Reassert only an owned selector that was cleared, rather than restarting actions each tick. The retained guard controller's 19 Lua fixtures cover logic, not engine transitions or visual acceptance.

## Delayed moving guard and stop dip

User-observed results: idle Q selects guard promptly; moving Q takes roughly 3–5 seconds; earlier stop tests briefly dipped to normal pose before returning. The user clarified that ordinary body movement/attacks work, so this is not established as a frozen skeleton.

The later native log recorded four starts/ends about 15 seconds apart, with `raised_selector=true` and `effect_active=true` at movement/stop edges. Useful markers are `TUAREG_Q_ART_GUARD1 START`, `MOTION_EDGE`, `GUARD_REASSERT`, and `STOP reason=effect_ended`. Distinguish actual activation time, selector-write/readback time and first visible posture frame. Record package version and actor identity alongside them.

Source inspection found six continuous opportunity checks around idle calm/tense/defensive transitions, with no equivalent moving checks found in that inventory. The **hypothesis** is that locomotion retains its selected branch until a permitted transition/clip boundary. This fits observed delays but does not prove engine reevaluation/interruption semantics or the stop dip's precise cause. A true selector during delayed playback points toward graph/playback investigation; increasing ability polling alone is not a demonstrated fix.

Stored native durations provide context, not visible timing guarantees:

| Clip | Seconds / frames |
|---|---|
| `navigation\idle_calm_basic_01` | 16.200 / 487 |
| `navigation\idle_shieldwall_01` | 3.567 / 108 |
| `navigation\idle_shieldwall_02` | 5.533 / 167 |
| `navigation\jog_shieldwall_01` | 3.067 / 93 |
| `navigation\walk_tense_f_01` | 5.500 / 166 |
| `navigation\jog_shieldwall_to_idle_quick_01` | 0.833 / 26 |
| `navigation\jog_shieldwall_to_idle_01` | 1.767 / 54 |
| `attack\stab_center_middle_01` | 1.967 / 60 |

Desired speed, play rate and blending can change observed timing. Geometry offsets or a longer spear do not create a faster graph transition.

## Native cheer and failed forced-leaf trial

The Shrek-style Tuareg fixture temporarily granted a native cheer ability when needed, issued its command through the existing Q signal, then toggled off/removed only the owned grant. **User-confirmed result:** cheer/victory motion played, movement stopped for about 15 seconds, and movement returned. It proves that full-body behavior/lifecycle for that fixture, not an upper-body overlay or arbitrary custom cheer-slot export. Use such a movement-blocking probe only when that behavior is authorized; it does not meet an uninterrupted movement/combat requirement.

The forced-leaf experiment called `StateTree_QueueGlobalStateTreeEntity(false, "anims_spearshield\\Locomotion\\Walk\\defensive\\jog_shieldwall_01", entity)`. It inspected a restoration branch and avoided forced requests during attack/charge/brace, but the user saw no useful moving improvement. **`accepted_call=true` meant a successful Lua `pcall`; no native playback handle or acknowledgement was returned.** Do not label it an accepted animation.

Priority, interruption, lifetime, cancellation and phase preservation were not qualified; forced requests were removed from the later controller. Do not repeat submissions or alter keep-alive behavior as a presumed fix. Likewise, `Entity_SetAnimatorAction/State/Event/Variable` for simple animations does not prove arbitrary `base_spearshield` clip strings are callable bindings.

## Source Actions and native codec research

A separate source-only shield Action raised the left arm over about 0.4 s, held through 15 s and lowered over about 0.4 s, preserving root/scale. It was not exported/bound as native Q motion and does not meet the later next-update/0.2 s target. Assigning it to calm idle changes calm idle, not guarded running/attacking.

The historically inspected `.rhka` is a Havok binary tagfile, SDK `20180200`, with a custom HavokAnimSet-family root and `hkaPredictiveCompressedAnimation` payloads. That investigation's Soulstruct-Havok adapter read actual skeletons, bindings, metadata and compressed payloads; Garrison's supported preview sampler provided parent-local bone samples. Those reader-only results did not establish an encoder. The later independently validated [cattle predictive encoder](native-predictive-animation.md) does.

Custom root/binding and constant-character-array adaptations were needed. A Shift-JIS reader can turn native ASCII `0x5c` separators into U+00A5; normalize lookup carefully without unnecessarily altering serialized names.

**Historical Tuareg writer gate failed:** round-trip type metadata for `hkFlags[hkUint32]` had `tag_format_flags=None`, causing TypeError during packing. No failed-codec output was accepted for delivery. The later cattle adapter retained the original TYPE section and indices, resolved source-declared custom types, encoded new predictive payloads and passed native playback; see [the proven route](native-predictive-animation.md). Do not invent ABI layouts/type flags/hashes. Preserve skeleton/binding metadata, names, durations and track-to-bone mappings; independently qualify encoding, graph consumption and runtime behavior for the actual target.

The installed CLI probe `garrison-core -m src.core.state_tree_authoring --help` returned **unknown core module**. Internal manifest/module names are not proof of a callable public interface. This identifies a missing installed route, not an engine impossibility.

## Reflected tree inventory and coverage

The corrected `anims_spearshield` inventory had 2,978 owned objects and 206 animation-related tracks: 202 ordinary, three synchronized non-entity-weapon and one matrix track. It exposed 163 distinct named clip candidates, plus unresolved constituent expansion for `strafe_tense_jog`. This is not a complete reachable-motion manifest for a particular unit/equipment configuration.

Validate type checksums, ranges and reflected layouts. Reference-wrapper targets use the reflected `m_objectID` field, not necessarily the first word. In this inspected build its offset was eight; preceding data could be a placeholder. Resolve it from reflection on another build instead of hard-coding that offset.

For full custom motion, resolve conditions and matrix constituents into a coverage manifest. Review ordinary/guarded idle, directional movement, starts/turns/stops, spear attacks, charge, brace, torch/equipment transitions, reactions and death. A list of names is neither a reachability proof nor tested replacement coverage.

## Broader route qualification

Possible research directions are a private arm/shield layer, or ordinary/guarded pairs with phase-preserving transitions. Both require a verified native encoding and graph route. Stop commands, a permanent raised idle, equipment swaps and whole-body restarts do not satisfy uninterrupted motion.

Use the user's actual timing/behavior target. For this Tuareg request it is visible activation and expiry within 0.2 seconds of confirmed signal while preserving gait phase, attack progress/hit timing, root travel, audio/equipment events and queued orders. Test every reachable state, all four ages, repeated/mixed activation, training/upgrades, ownership/conversion, removal, death, restore and game end. Compare travel speed, cadence, responsiveness and actual damage reduction against the working baseline.

If no private route is qualified, retain the working fallback and identify the missing encoding, binding, interruption or phase contract. Do not silently shrink a complete-motion request to one idle or declare the overhaul complete. Presentation adapters are not a native bone-pose channel; the Jolt cosmetic ragdoll facility does not broaden clip export. Solo acceptance does not imply multiplayer acceptance.

## Local evidence index

Source discovery record: `research/tuareg_complete_overhaul/GARRISON_CUSTOM_ANIMATION_DISCOVERIES_2026-10-11.md` in the Berber workspace `E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai`. The guidance above is self-contained; these optional local artifacts support exact continuation:

- Public catalogue/slot probes: `output/tuareg_complete_overhaul/{installed-contracts.json,native-slot-export-probes.json}`.
- Tree/coverage: same directory's `native-graph-summary.json`, `motion-coverage-candidates.json`; parser/layout tests: `research/tuareg_shield_posture/read_native_tree.py`, `research/tuareg_complete_overhaul/test_native_reference_layout.py`.
- Clip catalogue/timings: `output/tuareg_force_trial/native-animation-catalog.json`; sampled clips under `output/tuareg_refined_trial/clips/`.
- Source-only Action: `art/tuareg_shield/Tuareg_Shield_Q_RaiseHold_SOURCE_ONLY.blend`, `prepare_ability_pose_source.py`.
- Cheer: `art/tuareg_shield/tuareg_q_cheer_trial.scar`; retained user-native evidence under `output/tuareg_shield_posture_test/native-cheer-pass/`.
- Failed force: `art/tuareg_shield/tuareg_q_force_trial.scar`; `output/tuareg_art_guard_trial/native-force-failed/warnings.log`.
- Current guard: `art/tuareg_overhaul/{tuareg_q_art_guard_trial.scar,test_art_guard_trial.py}`; fixture result `output/tuareg_art_guard_trial/controller-green.log`; native feedback `output/tuareg_refined_trial/native-original-art-feedback.log`.
- Havok adapter/tests: `research/tuareg_complete_overhaul/{native_havok_codec.py,test_native_havok_codec.py}`; failed writer/type logs: `output/tuareg_force_trial/{native-codec-roundtrip.log,codec-typeflags.log}`.
- Private graph CLI probe: `output/tuareg_refined_trial/private-graph-interface-probe.log`.
