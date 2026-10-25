# Custom music and external audio

Use this for background music, looping/track switching, custom gain controls, native-slider mismatch, or Garrison audio lifecycle. For one-ZIP unit responses and overlapping native speech, use [Scripted unit voices](scripted-unit-voices.md). For native SPD/WEM replacement, use [Native voices](native-voices.md).

The installed 0.1.4 audio/API guide was reconciled on 2026-10-11. New format/schema/budget details below are documentation-derived; the Berber listening/build evidence retains its original qualification. Read [Runtime contracts](runtime-contracts.md) for native transport and [Packaging/catalogs](packaging-and-catalog.md) for manifest/install rules.

For combat intensity, age/civilization catalogs, 15-second sections and optional local HUD controls, read [Adaptive music](adaptive-music.md). It separates an implementable decision policy from unqualified attack-count and seamless playback contracts.

## Qualified route and limits

The installed Garrison route plays clips through its external Windows backend. PCM WAVs are stored as `data:audio/...` in the Extension. The client detects audio members and starts its matching backend for the mod key. No native Wwise bank or private SPD is needed for this route.

On 2026-10-10 the user confirmed exploration playback and the scheduled switching of the first six-track music probe. AoE4 Music Volume changes did not control it, and gain 0.35 was too loud relative to game audio with native Master Volume at 14%. Natural uninterrupted looping, pause/resume and complete cleanup were not explicitly confirmed. A revised continuous/volume-controlled probe has code/build checks; its new audible result remains pending.

Keep source originals and produce stereo 48 kHz 16-bit PCM WAV copies as the qualified initial format. Fully decode and inspect duration, peak/full-scale samples and silence; verify waveform hashes when conversion should be lossless. A full-scale sample is not by itself proof of audible clipping. Do not trim or normalize performances without task justification. Scripted clips have a documented 64 MiB per-file limit; the automatic Sounds panel has a separate 32 MiB limit. Music can use stereo even when unit speech preparation used mono.

## Authoring and matching paths

For scripted unit responses, external playback alone does not suppress native voices. The older Berber two-unit pilot heard both; the later **0.8.1** Villager fix was operator-confirmed after the custom unit's main native speech tables and its age/gender attachment speaker overrides were addressed. Read [Scripted unit voices](scripted-unit-voices.md) for the full binding inventory, clean-stock test and acceptance limits. Use direct `audio.play()` paths for large clip sets instead of creating more than the documented 256 symbolic event kinds. Direct paths avoid that mapping limit, not playback budgets or format validation; mono 48 kHz 16-bit PCM WAV is the qualified speech starting format. Compressed external speech decoding was not established by these tests; a packaged WEM bank does not activate itself.

Selection polling must account for squads: the observed Villager selection returned zero selected entities and one selected squad. A squad-based controller can use `Misc_GetSelectedSquads` directly, as in the working 0.8.x dispatcher. If representing actors as entities, combine entity/squad selection routes and deduplicate; entity-only selection was insufficient. Reject World-owned wildlife/carcasses before querying player ownership. Inspect actual entity and squad blueprint names rather than assuming all are bare or all GUID-prefixed; admit only verified IDs/names for the intended mod. 0.8.x used `GE_SquadCommandIssued` with stock-demonstrated payload fields for supported explicit commands, plus state edges for selected activity. State edges remain inferred responses; repeated/default/queued commands still have observable-coverage limits. Keep local playback out of gameplay decisions and simulation RNG, arbitrate groups, and document unobservable triggers rather than playing unrelated dialogue.

- Use **Sounds → Playback: From a script** or the project's authored `project/source/audio/` directory. A music-only project needs no dummy mesh. File references are relative archive members such as `audio/exploration_1.wav`.
- Import the installed version's loader, usually `<mod-key>/garrison.scar` or `garrison/garrison.scar`. Use `Garrison.mods.<key>.audio` or `Garrison.audio.forMod("<key>")`. The key must match the staged Mod Project, not its human title.
- Use dot calls (`audio.bed(...)`), not colon calls. Verify current generated loaders and source before copying another guide's import paths. A separately owned Content Editor project needs deliberate runtime/audio integration.
- Cook after audio or script changes, with Live Reload off for distribution. Package uses the latest successful cook. Import/enable the new release and select its actual required Map, Game Mode and/or Tuning Pack; a Crafted-map scenario need not add a Game Mode. Fresh-process trials isolate startup/cleanup failures. The current guide reports audio in two matches of one process; historical second-match concerns are not a universal product limit. Qualify repeated matches for the actual controller rather than assuming either success or failure.

### Automatic entity cues

**Sounds -> Playback: Automatic entity events** observes Moves, Takes damage, Is being built and Finishes construction for the selected entity type across all players, including AI/allies/enemies. It accepts mono/stereo **16-bit PCM WAV at 22050, 44100 or 48000 Hz**, at most **32 MiB**; Listen auditions at the selected volume. Repeat is a per-entity minimum interval and Distance fades linearly around the camera target. These are polled cues, not animation markers.

Save Sound copies the source under its SHA-256 to `project/source/audio/authored/`; the eyedropper restores saved fields for edits and the cross removes a cue/its WAV. Cook regenerates `<key>/sounds.scar`, polling every 0.25 seconds. Generated Game Modes start it in OnInit and Crafted maps in Mission_Start; an edited Game Mode entry must call `mod.sounds.start()` itself. A scriptless Tuning Pack alone cannot start automatic cues.

**Playback: From a script -> Open Audio Folder** instead exposes authored archive paths under `project/source/audio/`, without adding a Game Mode or automatic events. Each scripted clip is at most 64 MiB; inspect decoder/device support for formats beyond the initial PCM WAV route. Adding the first clip/removing the last changes backend activation at the next cook. The client starts one matching backend per staged audio-bearing mod, not one process per actor. Concurrent project-record changes during cook refuse publication and preserve the prior archive/receipt.

### Symbolic events and budgets

Optional `audio/events.json` supplies top-level `pan_width` (positive world-coordinate half-width, default 60) and `events`, keyed by event kind. Each definition has `clips` (1-64 relative member paths), optional `gain` (default 1, range 0-4), `class` (default event kind; direct clips default to effect), `priority` (default 0) and `max_voices` (default 4, allowed 1-12). Unknown settings are errors. Manifest maximum is 64 KiB and 256 event kinds; paths reject absolute forms, `..`, drive/stream colons and empty components. Clips are decoded by the backend, not the settings panel.

Use `audio.event(kind, now, x, z, count, gain)` with shared simulation seconds and X/Z position. `count` is a scenario-owned positive variant ordinal, not the number of locally heard sounds; omitted count uses the endpoint's next sequence. Variant index is `(ordinal - 1) % clip_count`, independent of missed playback and simulation RNG. Optional event gain multiplies configured gain. `audio.play(path,x,z,gain)` needs no event mapping; missing symbolic mappings play nothing. Default position is `(0,0)`, default gain 1, backend output gain clamped to 0-4. Scripted positioning is external stereo positioning, not the native camera listener.

The backend admits **12 effect voices** with class caps/priorities plus one separate bed. Lower-priority effects cannot evict higher-priority voices. Its scheduler holds 256 events, adds a 20 ms presentation buffer and drops events over 250 ms behind newest observed game time. Clip cache is bounded 64 MiB/32 entries; an individual clip is at most 64 MiB. These are admission limits, not measured audiovisual latency guarantees.

## Playback contract

| Call | Purpose |
|---|---|
| `audio.session()` | Start an epoch and clear earlier playback. Initialize once per active controller; use another barrier only for an intentional reset. |
| `audio.bed(path, gain)` | Start/replace the single looping music bed. Submit on start/real transition, not every polling tick. |
| `audio.play(path, 0, 0, gain)` | Centered one-shot, useful for an audition or notification. |
| `audio.stopBed()` | Stop only the bed while cues/session continue. |
| `audio.pulse(World_GetGameTime())` | Shared-clock heartbeat, typically every 0.25 seconds. No advancing time for 0.75 seconds causes backend pause. |
| `audio.stop()` | Clear/stop the session; another session is needed before new playback. |

Methods return **submission booleans**, not audible confirmation. The endpoint is shared by scripts of the same mod; a session reset from one owner clears another owner's playback. When generated automatic Sounds are also present, coordinate session ownership and initialize them before starting music.

`session(version=1)` accepts version 1 only, advances epoch/resets sequence and enables a stopped endpoint. The agent retains the session barrier for a late/reconnected pipe; ordinary lost sounds are not replayed and repeated barriers do not restart an accepted session. Wire messages carry `m,v=1,mod,epoch,seq,t`; epoch/sequence are exact nonnegative integers up to `2^53-1`. The native bridge supplies match scope: newer-match messages clear previous playback, older-match messages are dropped. Same/older scoped epochs, repeated/lower sequences, wrong mods, stale/nonfinite events are refused. Stop/session barriers clear even a full scheduler immediately. `stop()` prevents later sends until a new session; repeated stop returns false. `stopBed()` cancels the bed and queued bed starts while preserving effects/session, but older backends may ignore it.

`audio.accept(event)` is the sink for the separate cooldown module `Garrison.audio.events`; the endpoint still owns wire sequence/epoch. The source's admission boolean is not playback. Keep pulse ownership singular and consume contact events before another physics advance clears them.

There is one managed looping bed per mod session. Arbitrary live gain setters, crossfade, seek, playback-completion callbacks, native music buses and settings getters are not established by this interface. Inspect current APIs before using any such capability.

The Getting Started guide's dance cue polls one private squad's alive/valid/idle gameplay state every 0.25 seconds, starts the bed on idle and stops it on work/movement/death/removal. Returning to idle restarts music. This is an example of state-driven presentation, not a frame-accurate animation-start detector or a Dance command added by an idle override. Generated Sounds keep their session/pulse; stop only the bed to leave cues active.

## Continuous playback versus audition schedules

Choose the intended policy explicitly: one full loop, complete-track playlist, or short timed auditions. A first probe deliberately switched at 30/60/90 seconds; the user experienced these as interruptions. They were authored track transitions, not a demonstrated failure of the backend's natural loop.

For a continuous loop, call `session()` once, `bed()` once, then pulse. Guard repeated Start. Do not reset a session or reissue bed from an interval rule. A gain change made by reissuing a bed can also restart it; no seamless live gain-change contract is currently documented.

```lua
-- Use the actual project key and register these with the mode's lifecycle.
local music = Garrison.audio.forMod("my_music_mod")
local running = false

function MyMusic_Tick()
    if not running then return end
    Sound_SetForceSilence(true)
    music.pulse(World_GetGameTime())
end

function MyMusic_Start()
    if running then return end
    running = true
    Sound_SetForceSilence(true)
    Sound_MusicStop()
    music.session()
    local accepted = music.bed("audio/exploration_1.wav", 0.03)
    if not accepted then
        music.stop()
        running = false
        Sound_SetForceSilence(false)
        return
    end
    Rule_AddInterval(MyMusic_Tick, 0.25)
end

function MyMusic_Stop()
    if not running then return end
    running = false
    Rule_Remove(MyMusic_Tick)
    music.stop()
    Sound_SetForceSilence(false)
end
```

This is a minimal lifecycle skeleton with a fixed track/gain, not the complete option-driven controller below. Connect its Start/Stop to the target mode's verified lifecycle. It assumes sole ownership of native music suppression; when integrating multiple controllers, coordinate ownership and restoration instead of blindly clearing another owner's silence state. False submission is an immediate transport failure, while true still does not prove backend playback. A production late-start retry policy should be bounded and presentation-only; stop/restore on exhaustion rather than leaving native music silent indefinitely.

The gain in this example is a conservative trial value, not a universal balance target. The native music APIs are documented and used in official `music.scar`; verify them through AoE4 MCP or current installed ScarDoc before adapting. Native pause/unpause code can clear the silence flag, so the controller maintains it while active. Test overlap and restoration by listening; don't mute global effects/speech to solve music balance.

## Volume controls

External playback does not automatically traverse AoE4's internal Master/Music gain stages. The user confirmed that the Music slider did not affect the first probe. The inspected backend CLI accepts archive, game PID and mod key, with no native-settings bridge option; the available SCAR evidence supplies no qualified live volume getter.

Supported fallback controls are:

1. A mod-owned numeric lobby option converted to playback gain; zero mutes custom playback. State that it applies at match setup, not immediately from the native Audio settings screen.
2. The external backend's application level in Windows Volume Mixer, where available during active playback, for independent runtime adjustment.

An optional SCAR/XAML HUD can expose local volume minus/plus and mute commands. Offer it as a developer-selected feature when authoring adaptive music; implement it when requested. The verified UI building blocks and next-section gain policy are in [Adaptive music](adaptive-music.md). HUD construction does not create a seamless live backend gain setter.

Do not hard-code another user's Master slider percentage as a gain formula. Lower native Master can make independent external music disproportionately loud; select a quiet starting gain and calibrate against speech/actions. Probe.2 uses 3%/0.03 instead of 35%/0.35, a roughly 21 dB reduction. Neither guarantees ideal balance on another device/setup.

Avoid pretending a saved preferences file is a live bridge: `configuration_system.lua` contained `mastervolume=0.14` and `musicvolume=1.0` while the UI preview showed Music at 0% with Save available. Reading it would miss unsaved/live changes. Don't overwrite preferences, game binaries or backend binaries merely to connect sliders. Native Wwise music integration is a separate workflow requiring its own qualification.

## Validated Garrison lobby option schema

The current `garrison.game-mode/v1` document accepts option types `integer`, `boolean`, and `enumeration`, not the UI labels `number`, `checkbox`, `dropdown`. Integer fields are `default`, `min`, `max`, `step`. Enumeration `items` have `key`, `name`, and exactly one `default: true` entry.

Example options inside an existing section:

```json
{
  "key": "music_settings",
  "name": "Custom Music",
  "options": [
    {"key":"music_volume","type":"integer","name":"Custom music volume (%)","default":3,"min":0,"max":100,"step":1},
    {"key":"loop_track","type":"boolean","name":"Loop selected track","default":true},
    {"key":"track","type":"enumeration","name":"Music track","items":[
      {"key":"exploration_1","name":"Exploration 1","default":true},
      {"key":"combat_1","name":"Combat 1","default":false}
    ]}
  ]
}
```

Export the current game-mode document, modify it within its existing identity, validate with the installed helper, then pass the **JSON file path** to `garrison-core mod-project game-mode --project ... --set ...`. In this build `--set` reads a file; inline JSON produces a path error. Let Garrison write RDO/localization and regenerate `<key>/options.scar`.

Read typed values with the generated `Garrison.mods.<key>.options.load()` in setup. Validate selected track keys against an explicit manifest, clamp a numeric percent to the chosen range, and compute gain as percent/100. A static validator may report `options-uninitialized` because it cannot follow the imported loader; resolve that by showing the defining `options.load()` and its `Setup_GetWinConditionOptions` call. Test the actual generated loader with enum/number/boolean values, not only a handcrafted table. Preserve genuine unresolved contracts.

Define the mute policy. In the isolated probe, zero custom volume means no custom clip is submitted and native music remains suppressed: all music is intentionally silent, while speech/effects continue. A different product may restore native music when disabling custom music, but that is a separate stated choice. When looping is unchecked, submit a centered `play(path, 0, 0, gain)` once instead of a bed.

## Lifecycle and acceptance

Start after match initialization, keep one named global pulse callback, and remove it plus stop the session on game over. Maintain no playback state that affects simulation, RNG, damage or victory. Save/restore and multiplayer need separate qualification.

Ending themes deserve special handling: actual game over stops simulation time, and the backend's stalled-clock pause/normal cleanup can stop a one-shot. Audition victory/defeat tracks while the match runs to prove basic playback; that does not prove a full post-match outro. Long themes must not be treated as short stingers without inspecting duration.

Verify these gates separately:

- Original preservation, full decoding, waveform/format checks and per-file size.
- Correct archive paths/mod key, audio-enabled cook, source and every actual manifest track's readback hashes, package integrity and imported version.
- Actual controller tests: no restart across 30-second boundaries/full track, no duplicate rule/session, zero-volume mute, selected track, looping/one-shot and cleanup.
- Audible selected track, natural loop seam, comfortable balance, native music suppression, pause/resume, menu exit, fresh-process restart and unchanged speech/effects.

Retain `warnings.log`, the agent `<PID>.jsonl`, and `<PID>.audio.<key>.log` under `%LOCALAPPDATA%/Garrison/events`. Submission or a cook is not an audible pass.

## Troubleshooting

| Symptom | Inspect / correct |
|---|---|
| Track cuts every 30 seconds | Controller's audition timetable, repeat bed calls and session resets; don't diagnose the backend loop from a short preview. |
| Music is much louder than speech | Independent external gain versus native Master; lower the custom gain and calibrate by listening. |
| Native sliders do nothing | Expected for the qualified external route; expose independent controls and report the bridge as unqualified. |
| Sound stops during pause or after match end | Shared-clock stalled-time handling and session cleanup. |
| New release won't package | The packager preserves edited/unowned files in `dist/package`; back up your own prior package folder before regenerating, then add new instructions to the successful package. |
| ReflectBurner fails in a deep output path | Inspect destination length; an observed 260-character path failed while identical sources cooked from a shorter workspace path. Preserve identity/source, shorten staging and read back the new build. |

Source authority: current installed `guide/garrison-audio.html`, `guide/garrison-api.html`, endpoint `garrison.scar`, generated options loader, backend `--help`, official music APIs and the user's listening results. Optional local fixtures are in `E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\output\music_test/`; the guide does not depend on their continued existence.
