# Adaptive civilization music

Use this when music should respond to combat, age and civilization, or a developer requests an optional in-match custom volume panel. Read [Music and external audio](music-and-audio.md) first for the qualified loader, PCM format, session, native suppression, cook and package route. Use `aoe4-game-mode-skill` for the SCAR and UI integration.

## Contents

1. Capability and evidence
2. Rate sensor and exact intensity policy
3. Section timing and musical continuity
4. Civilization, age and variation catalog
5. Optional local volume panel
6. Implementation sequence and acceptance

## 1. Capability and evidence

The current external Garrison interface can submit or replace one looping bed and play centered one-shots. Its endpoint documents `session`, `bed`, `play`, `stopBed`, `pulse`, `stop` and symbolic `event`. The installed 0.1.4 guide rechecked on 2026-10-11 still supplies no documented crossfade, seek, start-offset, scheduled start time, completion callback, per-playing-clip gain setter or acknowledgement of audible playback. This documentation refresh does not change the older policy/sensor/transport acceptance status. Recheck the installed endpoint after a version change.

A SCAR controller can classify combat activity and request the next clip at a section boundary. This does **not** yet qualify gapless, sample-accurate transitions. Switching an existing bed starts a replacement; it does not seek to the corresponding position in another full track. True musical continuity needs prepared content plus an audible transport test. Do not promise that buying or installing Wwise adds these controls to Garrison.

Evidence recorded on 2026-10-10:

| Contract | Evidence | Qualification |
|---|---|---|
| External exploration playback | User heard the earlier probe in a native solo match | Playback confirmed; adaptive transitions are not |
| `Rule_AddGlobalEvent(f, eventType, userDataTable)` / `Rule_RemoveGlobalEvent(f)` | Official `rulesystem.scar`; complete lifecycle usage in `winconditions/conquest.scar` and `wonder.scar` | Framework wrapper; verify imports |
| `GE_DamageReceived` | Official constant and both victory-condition handlers | Damage activity route; not an all-weapons attack counter |
| Damage context fields | `attacker`, `victim`, `isRepairing` in conquest; `attackerOwner`, `victimOwner` also in wonder | Only these observed fields are qualified here |
| `Entity_IsOfType(entity, type)` | Official API; types come from `type_ext/unit_type_list` | Inspect the actual scout tag or blueprint data |
| `Player_GetCurrentAge(playerID)` | Official wrapper defined in `cardinal.scar`, used in `campaignpanel.scar` | Return 1–4; preserve defining import |
| SCAR/XAML command UI | `UI_CreateCommand(callbackName)` in `ui.scar`; official diplomacy/campaign panels | Building blocks verified; custom panel needs runtime test |
| Pure decision helper | [adaptive_music_policy.lua](../scripts/adaptive_music_policy.lua), executed with boundary/rate scenarios | Language-level policy only; no engine/transport/HUD proof |

AoE4 MCP's `api_context` returned no record for the event constants themselves; the raw official constants and extracted current handlers supplied their evidence. One search miss is not proof of absence. Conversely, a constant name is not proof of its callback payload.

## 2. Rate sensor and exact intensity policy

Record the measurement name, window length, ownership/visibility scope and scout filter alongside the thresholds. Attack orders, currently attacking units, fired attacks and damage hits are different measurements.

The user's requested policy is:

| Eligible attacks per second | State |
|---|---|
| 0, including scout-only attacks | `exploration` |
| Greater than 0 and less than 8 | `small` |
| 8 through 24 inclusive | `medium` |
| More than 24 | `large` |

Use a **trailing one-second window at each 15-second decision boundary** as the initial interpretation. Continuous observation still runs between boundaries. This responds to the fight present when the section ends, rather than averaging a large fight across the whole past section. Record any developer-selected longer smoothing window explicitly. A 15-second mean changes the meaning to counts 0, 1–119, 120–360, 361+ per section; it is not interchangeable with the initial one-second policy.

Do not add hysteresis, grace time, higher thresholds, scout damage multipliers or immediate escalation as hidden defaults. These can be separate requested settings. With the stated policy, one-second quiet at a decision can return music to exploration. Worst-case response delay is about one section plus polling/transport latency.

### Qualify actual combat sensing

1. Search current official source and AoE4 MCP for an all-weapons fired-attack event and its payload. The inspected constants included projectile/accessory/artillery events, but their names do not establish coverage of ordinary melee, archers, siege, misses and attack cancellation.
2. If no exact sensor is qualified, explain the gap. An initial `GE_DamageReceived` adapter may count **eligible damage events per second**, labeled as a proxy, with the same configurable thresholds. This is not an exact implementation of attacks per second.
3. For a damage adapter, require attacker and victim; ignore `context.isRepairing`, self-damage/scuttling, world/environment damage and ineligible relationships. Validate destroyed handles before calling entity functions. Inspect the full official callbacks for lifecycle and context; do not invent `context.weapon`, `shot_id`, `damage`, or arbitrary event fields.
4. Exclude scout **attackers**, including enemy/AI scouts and all relevant age/civilization variants. A scout being attacked by a non-scout does not make that incoming attack scout-only. Use verified `type_ext` tags or an explicit resolved blueprint set, including inherited/custom scouts; display-name substring matching is insufficient.
5. For a local player's soundtrack, default to outgoing attacks by that player and incoming enemy attacks against that player. Other battles are outside this scope. Team-wide, camera-local, spectator and globally visible music are separate scope choices. Never infer hidden remote battles from a global event stream for local music. Filter visibility if expanding scope.
6. A melee miss causes no hit, an area attack can produce many hits, and damage over time may produce repeated callbacks. Do not combine projectile and damage events naively, which can double-count ranged attacks. Deduplicate into attack counts only when a verified source supplies a stable attack identity; an arbitrary attacker/time cooldown can also discard legitimate attacks.

Keep counts and presentation state separate from authoritative simulation. Local preferences must not alter combat, resources, victory, simulation RNG or synchronized game state. A bounded event queue/ring retains only the active window; avoid scanning every unit every frame just to infer attacks.

### Reusable decision helper

The pure Lua helper returns `exploration/small/medium/large`, clamps independent volume and emits one decision at each due boundary. It uses `(now-window, now]` for event timestamps. The engine adapter calls `record(now, true)` only after eligibility checks; `false` events are ignored. The helper does not detect scouts, infer owners, register events, play audio, select ages or construct UI.

Load the helper under the actual deployed project import/module convention; it returns a table. `dofile` in an authoring test is not evidence that `dofile` is the correct in-game import. At runtime, copy/adapt the table export using the project's established loader pattern and inspect the cooked import path.

```lua
-- Pure Lua illustration; Policy is the table returned by the helper.
local decision = Policy.new(startTime, 15, 1)
-- Verified engine adapter: decision.record(gameTime, isEligible)
-- Every heartbeat: local nextSection = decision.tick(gameTime)
-- A returned decision is a request, not an audio playback acknowledgement.
```

The helper advances deadlines from the original phase, not `now + 15`, and emits one current decision after a delayed tick. A late tick samples the trailing window ending at **actual tick time**, not a reconstructed past deadline; log both times and lateness. On restore/clock rewind, rebuild presentation timing deliberately rather than replaying every missed section. The helper rejects a decreasing tick clock; the controller should detect a rewind and reinitialize before calling it. An event arriving at the same timestamp as a decision is included only if its callback has already reached the queue; native event ordering needs a test.

## 3. Section timing and musical continuity

Observe events continuously, pulse every 0.25 seconds, and decide every 15 seconds from one stable start phase. At a boundary, resolve `(civilization, age, theme, intensity, section-index)` and request at most one intentional change. Do not call `session()` on each change. Native age transitions use `Player_GetCurrentAge`, sampled for the relevant local player; apply a newly observed age at the next section boundary.

Choose one transport policy:

- **Full-track baseline:** keep a full looping bed. At a decision, replace it only for a changed resolved track, age or pending gain. Same-state ticks do not restart it. This is easy to test but changing states can audibly restart unrelated songs.
- **Section sequence experiment:** prepare 15-second sections. Each boundary advances to the next indexed section, even if intensity is unchanged. Select the matching index of the next intensity arrangement instead of restarting its first section. The current bed replacement or successive one-shots has no atomic scheduling guarantee; mark gaps/overlap/drift unqualified until measured and heard.
- **Improved transport or native interactive music:** needed when strict crossfade, seek, phase alignment or scheduled playback are acceptance requirements that the above experiment cannot meet. Inspect a newer supported Garrison interface first. Native Wwise music-bank/state integration is a separate unqualified route; do not mutate game/backend binaries to manufacture an API.

Do not assume `audio.play` finishes exactly at the next SCAR timer; backend admission, latency, voice limits and clock drift can create gaps or overlap. Long one-shots cannot be individually stopped through the documented endpoint, so stop/mute policies differ from a managed bed. A pre-rendered fade/transition file is offline content, not proof of an engine crossfade.

For musically compatible sections:

- Obtain aligned arrangements or stems of the same theme for exploration, small, medium and large combat. Match tempo, time signature, downbeat position, harmony/key and phrase structure across the states.
- Fifteen seconds must be an authored phrase boundary. For example, eight bars of 4/4 at 128 BPM last 15 seconds. At 120 BPM, eight such bars last 16 seconds; arbitrary 15-second cuts would land inside phrases. Ask for suitable cues or record the approved editing/time-stretch policy.
- Cut at sample boundaries: stereo 48 kHz PCM has **720,000 frames per 15-second section**. Inspect discontinuities and reverb tails. A short offline fade can reduce clicks but may create a dip, and cannot hide incompatible harmony or a scheduling gap.
- Preserve the originals. Track exact durations, frame counts, safe entry/exit cues, section index, common theme length and tail policy in the manifest. Avoid a short final remainder as if it were a complete 15-second slot; choose a prepared loop endpoint or record an explicit end/bridge policy.
- Cross-state arrangements should have corresponding section indices and cycle lengths. Do not rotate themes every 15 seconds; keep the current theme through intensity changes, rotating among alternatives at a qualified theme boundary or an explicitly chosen transition.

Test initially at normal game speed. The backend pulse reports advancing simulation time/pause state; that is not a documented time-stretch or sample-position synchronization API. Game-speed changes, pause, long stalls and restoration can break a naive SCAR-time section schedule.

[Audiokinetic's transition guidance](https://www.audiokinetic.com/en/library/edge/?id=setting_source_and_destination_properties&source=Help) describes exit/entry cues, beat/bar synchronization and fades in its interactive music system. These are useful content-design concepts, not capabilities automatically exposed by Garrison.

## 4. Civilization, age and variation catalog

The user confirmed the target: **three alternative tracks for each state in each age**, including exploration, small, medium and large combat. This gives `4 ages × 4 states × 3 alternatives = 48 logical music slots per civilization`. Organize corresponding alternatives into compatible theme families where possible, so intensity can change while the musical phrase continues. Independent alternatives need an authored transition/cue compatibility map. Slot counts do not require that many distinct files when reuse is authorized; duplicate aliases still do not satisfy distinct musical variation. For a future brief with ambiguous variation wording, clarify the count before preparing its catalog.

Use an explicit controller-owned manifest. Include:

- actual civilization/race key and an explicit custom-civilization override when it uses another race's stock slot;
- age 1–4, theme 1–3, state and ordered section paths;
- exact duration/frame count, source provenance, format, seam/loop status and asset size;
- metric (`attacks` or `damage_events_proxy`), rate window, decision interval and scout classification coverage;
- source gain/loudness information plus a local gain preference;
- fallback aliases with a reason and quality status for every reused or derived slot.

Do not infer the Berber soundtrack from `Player_GetRace` alone when Berbers share the Malian race key. Resolve the custom profile from the mode's explicit configuration. A local player hears that profile regardless of what music assets an AI opponent uses. A separate civilization profile does not add a lobby civilization slot.

### Missing recordings

When reuse is authorized, fill missing slots with recorded aliases: requested age/theme/state → shared recording for that same state → approved combat fallback for combat → exploration fallback. Report each substitution. Do not use victory/defeat themes as combat fallback merely because they exist. If no usable custom file resolves, stop the external controller and restore native music under the ownership policy.

The supplied Berber trial has two exploration recordings and two combat recordings, plus victory/defeat themes. A temporary catalog may reuse Age 1 in Ages 2–4, reuse exploration recordings across theme slots, and alias small/medium/large to available combat files. Such aliases provide coverage; they do **not** establish three distinct themes, three audible combat intensities or aligned arrangements. Record those deficits for later replacement.

If the developer asks to add missing music, distinguish reuse, derived edits and newly composed/generated recordings. Reuse and documented edits can fill a trial; genuine new arrangements need an available music-production workflow or supplied recordings. Do not describe pitch shifting, duplicate files or relabeling the same waveform as a new composition. Cook only actual files resolved by the manifest, not nonexistent names.

## 5. Optional local volume panel

Include this as a selectable implementation feature. When the developer has not requested an in-match panel, offer **Custom music HUD** along with lobby volume; do not inject it into unrelated mods. The current user requested that future developers be able to select this option, rather than requiring every music package to display it.

Suggested compact panel: **Custom music · 3% · [−] [+] [Mute]**, with optional developer readouts for age, state, metric/rate, selected theme/section and pending changes. Label it as the custom music control. It is independent of AoE4 Audio Settings and unit speech/effects; it is not a replacement native Master slider.

Verified UI route:

1. Read the complete creation/destruction functions and imports in official `gameplay/diplomacy.scar` or `campaignpanel.scar`. `UI_CreateCommand("PrefixedGlobalCallback")` returns a command descriptor; button `Command` bindings point to descriptors in the data context. Do not attach guessed inline Lua command strings.
2. Create an isolated `XamlPresenter` through `UI_AddChild`, a `UI_CreateDataContext` table, and simple button/text bindings. The inspected diplomacy panel attaches to `ScarNotReplay` and removes its presenter at cleanup. Verify that host and actual properties in the target mode. Keep resources before consumers and limit XAML to proven properties.
3. Store local percent, last nonzero percent, mute and pending gain. Clamp to 0–100; default 3 is a quiet starting trial, not universal balance. Small steps help fine-tuning. Keep callbacks global with a unique prefix because the command wrapper takes a function name.
4. Update the panel's data context through its verified update mechanism after each click. Use `UI_Remove` on cleanup, and remove any command/event bindings actually registered. Re-enter restore without duplicate presenters or rules.
5. Local volume affects presentation only. It needs no gameplay network event. If a control changes shared thresholds, simulation rules or other authoritative settings, that separate behavior must use the mode's registered synchronization route. Qualify actual locality in multiplayer; do not claim multiplayer support from a solo panel.

Current transport control semantics:

| Player action | Initial policy |
|---|---|
| Volume −/+ | Update local preference/readout immediately; apply gain to the next submitted section/real bed replacement. Display “applies next section” when pending. |
| Mute a managed bed | `audio.stopBed()` immediately; pulse and observe while muted, submitting no new music. Keep native music suppressed for intentional all-music mute. |
| Unmute | Resume by submitting the resolved section at the next boundary with the remembered nonzero gain. Do not pretend the previous sample offset can be recovered. |
| Volume 0 | Same mute policy. Speech/effects continue. |
| Immediate gain change requested | Reissuing `bed(path, gain)` may restart the clip. State that effect explicitly, or qualify a new supported live gain setter. |

Muting centered one-shots with `stopBed` does not stop those voices. A global `audio.stop()` clears the whole mod session, including its other custom cues. Choose a managed-bed policy when independent music mute is required and coordinate session ownership. Do not clear another controller's session merely to implement a volume button.

The optional panel is a documented integration design. Its building blocks are official; this particular adaptive HUD and backend behavior have not passed an in-game test.

## 6. Implementation sequence and acceptance

1. Confirm the controller's real module/import path, exact mod key, native silence ownership and cleanup. Preserve current voice bindings, GUID, gameplay data, victory code and unrelated units.
2. Qualify a minimal combat sensor and scout filter before audio work. Log measured metric/rate with known one-on-one, eight-attacker, large and scout-only cases. Include incoming attacks, repairs, misses, area damage and unrelated fights.
3. Prepare and validate a minimal compatible exploration/combat section pair, manifest and missing-slot report. Source copies remain outside original recordings. Audio generation/editing cannot establish engine transport timing.
4. Connect one session owner and heartbeat. The policy determines desired state; the transport adapter determines whether/when a clip is submitted. Guard duplicate Start, bounded startup failure and one transition per boundary. If readiness fails, restore native music instead of permanent silence.
5. Read local age/profile, hold the theme across intensity changes and resolve approved fallbacks. Use a presentation-only theme selector, such as round-robin; do not consume synchronized simulation RNG for soundtrack variation.
6. Add the optional HUD only when selected. Test immediate mute, next-boundary gain changes, remembered unmute and UI cleanup. Keep lobby volume as a starting preference.
7. Validate SCAR/XAML and defining imports, Content Editor cook, every actual audio member and manifest/source readback, and the packaged version independently.
8. Run a native audible matrix: thresholds 0/7/8/24/25; scout-only/incoming damage; combat ending just before/after boundaries; all ages; repeated intensity changes while the theme continues; source seams and transport gaps; 0/3/8% volume; pause/resume; menu exit; fresh process and unchanged speech/effects. Game-speed changes, restore and multiplayer are separate gates.

Logs should identify `metric`, qualifying count/window, rate, age, theme, current/pending state, section path/index, intended boundary, actual submission time, gain, mute and fallback reason. Retain game warnings plus Garrison agent/audio logs. State separate results for policy tests, sensor runtime, asset seams, package, HUD runtime and audible transitions. A passing policy helper or accepted bed request is not a successful adaptive soundtrack.
