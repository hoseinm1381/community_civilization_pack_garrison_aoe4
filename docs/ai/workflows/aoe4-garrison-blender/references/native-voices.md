# Native unit voices alongside Garrison mods

Read this for native dialogue/efforts, private `.spd` speech profiles, Wwise `.wem` media, silent custom speakers, or preserving other units' voices. For an ordinary **single-ZIP Garrison voice release** or original/custom overlap, first read [Scripted unit voices and attachment overrides](scripted-unit-voices.md). That operator-confirmed route uses embedded PCM and needs no native companion. Use the ordinary Sounds workflow for external cues/music.

## Choose the correct audio route

| Intended result | Route | Resource and runtime boundary |
|---|---|---|
| Scenario music or movement/damage/construction cues | Garrison Sounds / scripted audio | PCM WAV clips in the mod's `data:audio/` tree; Garrison's external Windows backend plays them. This does not author a native game soundbank or replace every speech trigger. |
| Garrison-only custom unit replies without a voice installer | [Scripted unit voices](scripted-unit-voices.md) | Embedded PCM, a local presentation dispatcher, and qualified suppression of the custom units' native speech bindings, including attachment overrides. Berber 0.8.1 overlap fix was operator-confirmed; full native event parity is not claimed. |
| Native selection, commands, reactions and vocal efforts for a custom unit | Private speech profile + compatible Wwise media + custom EBPS/SBPS speaker bindings | The tested native route supplies SPD/WEM files in the game's `audio:` namespace. The Extension supplies tuning and optional diagnostic SCAR. |
| Silence/replace footsteps, equipment, impacts, torch sounds or creation cues | Investigate each separate native binding | A private speech profile covers its own vocal slots. It does not establish isolated suppression of shared effects. |

The Windows native route below was qualified on **2026-10-09**, with Blender 5.2.2, Garrison extension 0.1.0/client 0.1.3, Content Editor profile 16.3.11308, and game audio metadata Wwise 2023.1.3.8471. It is an empirically tested local route alongside Garrison, not a documented Garrison native speech authoring feature. Recheck these contracts after game/tool updates and qualify other civilizations/profiles separately. Multiplayer and full-family gameplay have not been qualified by this example.

## Resource namespace: establish this before encoding a full set

### Scripted playback and native suppression are separate responsibilities

Garrison 0.1.4 supports clips inside one imported archive through its external Windows audio backend; do not tell a user that all custom audio requires a separate installation. However, embedded playback and native speech replacement are separate capabilities.

In the **2026-10-16 Berber 0.7.1 experiment**, the backend logged playback and the user heard custom Villager clips, but also heard original Malian speech overlapping. Pilot 1 removed paired `speech_ext`/`squad_speech_ext` tables; pilot 2 retained them and assigned absent private speaker codes. Both failed. Those were incomplete binding inventories, not proof that import-only scripted replacement is impossible or that a particular engine fallback caused the overlap. No per-unit SCAR speech-mute API was established.

**Superseding 2026-10-17 evidence:** in 0.8.0 the operator reported Spearman working well but Villager original/custom overlap. The four active Villager tier attachment lists still had 208 explicit `attachment_speaker_code` assignments (104 `villagerMale`, 104 `villagerFemale`). 0.8.1 cleared only those CString values to empty, matching working Scout/Archer attachment controls; the user replied **“yes yes it worked.”** The main speech tables were already absent. The game loose audio had first been verified against installed Steam depot hashes and old custom files backed up/removed. See the [complete working procedure and limits](scripted-unit-voices.md). Do not repeat main-field-only edits while overlooking these attachment-level overrides. The brief confirmation establishes the reported overlap fix, not an enumerated every-age/gender/context/multiplayer test matrix.

Before expanding an external replacement dispatcher, qualify a small audible pilot with an unchanged stock control. For a Garrison-only result, use a clean-stock-audio environment when authorized and verified; an older native companion can confound what is heard. A comparison run with an already installed companion is optional and separately labeled, not the clean scripted-only acceptance run; do not install one merely to qualify the no-installer route. Keep backend `played` evidence distinct from audible event correctness and absence of duplicate native speech. Do not mute global speech/effects to hide a custom-unit overlap. If the gate fails, report it and continue tracing the requested route; use a native companion only when the user accepts that different product layout. The user reported 0.7.0 as working; the later progress-bar screenshot proves installer validation activity, not full installation or fresh all-family gameplay.

The inspected shipping engine enumerates **`audio:*.spd`**. Its `RelicGame.module` maps `[audio:common]` to `folder = cardinal\audio` and mounts stock speech archives in that namespace. Stock `SoundSpeechMalian.sga` stores `malian_donso.spd` at the `audio` TOC root.

| Placement | Outcome in the qualified experiment |
|---|---|
| Extension archive with an extra TOC alias `audio` | Entire mod rejected: `TOC audio not permitted` / `invalid file structure`; lobby components disappeared. |
| `data:audio/malian_tuarg.spd` inside an Extension with permitted TOCs | Mode/tuning loaded and custom units spawned, but private speakers were silent. `data:audio/...` does not provide `audio:...`. |
| Private loose `cardinal/audio/malian_tuarg.spd` and referenced WEMs under that audio folder | Private selection/attack worked in both age phases; mixed selection worked; the stock control retained its original voice, confirmed by the user. |

The tested deployment therefore has two components:

```text
Garrison package:
  garrison.json
  ExistingMod.sga              # tuning + game mode; permitted Extension TOCs

Native audio companion:
  native-audio-manifest.json
  installer / verify / uninstall
  audio/malian_tuarg.spd
  audio/civ_malian/malian_tuarg/*.wem

Installed native files:
  GAME_ROOT/cardinal/audio/malian_tuarg.spd
  GAME_ROOT/cardinal/audio/civ_malian/malian_tuarg/*.wem
```

Importing/enabling the Garrison ZIP does not install the native companion. Apply the separate native installation within the user's authorized scope and tool permissions. Use the discovered game root and current module mapping; an old absolute installation path is not a portable requirement. Keep stock archives, stock loose resources, `RelicGame.module` and shared soundbanks intact. Restart the whole game process after changing native speech; returning to the menu or starting another match is insufficient evidence of reload.

## Inventory the actual unit and requested coverage

1. Identify the editable project, GUID, source owner, custom EBPS/SBPS for every age/variant, squad loadout, upgrades, and production references. Use `modify-aoe4-tuning-packs` for attributes and `aoe4-game-mode-skill` for SCAR. Voice-only work needs no mesh change or live Blender session when the chosen workflow uses files/CLI.
2. Inspect the installed stock speech archive/profile and current unit parents. Use the current Garrison archive tools or another verified reader. Inventory original context, delivery, chronology, numbered/alternate media and resource paths. Native SPD records can reference multiple media: record count is not the number of recordings required.
3. Give the user a Markdown checklist with explicit family/delivery/age rows, original take count, and requested new count. One supplied take can intentionally populate every original numbered/alternate slot of that same family/delivery. Age reuse is a mapping decision, not a filename rename of only Age 1 entries.
4. Match the supplied files to the inventory; classify missing families, deliberate substitutions and duplicate audio. Preserve originals. Distinguish named files from distinct waveforms: duplicate hashes are valid when the supplied files really contain identical audio.

**Qualified Donso coverage:** 43 families (27 dialogue + 16 effort families), 747 SPD records and 1,278 unique WEM slots. The Tuareg input had 49 named Age 1 family/delivery recordings, 48 distinct waveforms, reused across four chronological forms. Those counts describe this fixture, not every unit. Map all referenced paths, including alternate takes; filling only the visibly selected command rows can leave stock fallback or missing media.

The Donso checklist treated `cLowest`, `cLow`, `cMed`, `cHigh` as Age 1–4 planning forms **by inference** from naming and stock age mappings; the exact native suffix-to-age scheduling was not traced. All forms were populated, so the test's Age 1 reuse did not depend on proving that interpretation. Verify scheduling before assigning different performances to individual ages. Delivery labels `iNorm`, `iHigh`, `iStealth` were catalogued as normal, combat, stealth; recheck the current profile rather than applying naming universally. Effort `cNone` entries have no individual era; keep them covered. Preserve unusual entries such as `celebrate_cnone_cLowest` and map their unspecified delivery explicitly. A strict normal/combat/stealth filename filter must not discard them.

Separate dialogue, nonverbal efforts and shared effects. When the user authorizes temporary effort substitution, record the chosen dialogue explicitly and list the later nonverbal recording. Spoken commands reused as pain/death/grunts can sound unnatural; a mapped placeholder is not a final performance.

## Prepare WAVs and encode genuine Wwise media

Convert copies to mono 48 kHz 16-bit PCM WAV as the qualified starting format. Decode each source fully; check channels/rate/sample width, nonzero duration, clipping and near-silence. Preserve source hashes and record output hashes and durations. Do not silently normalize, trim, stretch or otherwise change the performance unless requested or justified to the user.

Discover native requirements from the **installed** game:

- `cardinal/audio/PlatformInfo.xml`: generator/platform metadata.
- `SoundbanksInfo.xml`: bank/schema metadata.
- `audio/wwiseconfig.lua` in the current data archive: selected platform SpeechCodec.
- One actual stock WEM: RIFF size/chunks, codec/channel/rate and format compatibility.

In the qualified Windows build, generator **2023.1.3.8471**, soundbank version **150**, and **SpeechCodec 4 (Vorbis)** matched Wwise Authoring 2023.1.3.8471. Its `Authoring/x64/Release/bin/WwiseConsole.exe` performed conversion; Authoring alone supplied it. SDK, Unity/Unreal integrations, and every deployment platform were not needed. A newer beta was not the chosen compatibility target. Recheck requirements rather than installing this version blindly for another build. Account login/downloads remain the user's account interaction; never ask for credentials in chat.

Use a disposable Wwise project and a WSOURCES list. Audiokinetic documents external source input lists, conversion settings and output locations in [External Sources settings](https://www.audiokinetic.com/en/library/edge/?id=specifying_input_output_locations_for_external_sources&source=Help). The following syntax was executed with the matching installed console; check its help after version changes:

```xml
<ExternalSourcesList SchemaVersion="1" Root="E:\VoiceWork\wav">
  <Source Path="selection.wav" Conversion="Vorbis Quality High" Destination="selection" />
  <Source Path="attack.wav" Conversion="Vorbis Quality High" Destination="attack" />
</ExternalSourcesList>
```

```powershell
# Resolve these verified paths for the current machine first.
& $voiceConsole convert-external-source $voiceProject `
    --source-file $voiceSourceList --platform Windows `
    --output $voiceOutput --verbose --no-wwise-dat
```

The tested console adds a `Windows/` output folder and emits `.wem`. When creating a new Wwise project, the containing folder must share the `.wproj` stem (for example `TuaregVoices/TuaregVoices.wproj`); reuse an appropriate existing project when available. Check the console exit code, conversion log and actual outputs. Native Vorbis WEMs in this fixture have valid RIFF/WAVE lengths, format tag `0xFFFF`, mono 48 kHz, and `fmt ` / `hash` / `data` chunks. Compare to the current stock sample; these checks are structural, not audible acceptance. WAV or Ogg renamed to `.wem` is not native encoding.

## Clone a qualified private speech profile

Use a mod-owned speaker and mod-owned media paths; changing stock Donso resources would affect other consumers. The tested private code was **`tuarg`**, chosen because it has the same five-byte length as **`donso`**. This is a constraint of the bounded memory-image clone, not an engine-wide five-character naming rule. Choose a distinct unused identity for another mod; simultaneous mods sharing `tuarg` would share that native profile and media. Keep one deployment manifest as owner.

The inspected SPD is Relic Chunky v4 with `RFCI`, `RFUP`, `RNEW`, `RSHI`, `ROBJ`, `RERF` DATA chunks and reflected version `4131415`. The qualified Donso file is 313,216 bytes, SHA-256 `e37eafc275b19db533b03b00658d32c677b21134467fca5d34de82ca21686b76`. It contains relative string/media pointers; arbitrary global text replacement or changing string lengths can invalidate them.

Use [the bounded helper](../scripts/donso_speech_profile.py) for this exact source fixture:

```powershell
& $voicePython "$voiceSkillRoot/scripts/donso_speech_profile.py" inspect $voiceSourceSpd
& $voicePython "$voiceSkillRoot/scripts/donso_speech_profile.py" inspect $voiceSourceSpd --records
& $voicePython "$voiceSkillRoot/scripts/donso_speech_profile.py" clone $voiceSourceSpd $voicePrivateSpd --speaker tuarg
& $voicePython "$voiceSkillRoot/scripts/donso_speech_profile.py" verify-media $voicePrivateSpd $voiceNativeAudioRoot
```

It qualifies the source digest, parses records, changes only parsed speaker/media strings, preserves length/offsets and all other bytes, rejects the stock identity and conflicting output, and checks referenced media containers. It does not redistribute stock SPD/media, implement a general SPD compiler, install game files, or prove playback. A changed fixture or another civilization requires reinspection and a new native probe; do not force the helper past its guard.

Create the authoring output directory before `clone`; the helper does not create parent directories. `inspect --records` exports every raw context/race/speaker and media path as JSON for inventory/mapping without guessing family semantics. `qualified_stock_source=false` on a private clone is expected: that flag qualifies only the unchanged original stock source. `verify-media` proves reference containment, existence and RIFF/header compatibility; it does not decode the Vorbis payload, check the chosen dialogue assignment, or establish playback. Use encoder logs, assignment hashes and the audible test for those separate gates.

For each SPD media reference, stage the mapped encoded source under its exact private path. Preserve native context strings, record ordering and opaque metadata. Read the output SPD back and verify every reference against the staged/installed files and the assignment manifest. A path-existence test alone cannot detect a wrong recording: compare assigned source hashes too. Reusing a source is allowed; count coverage and distinct sources separately.

## Bind only the custom unit

The qualified attribute properties are:

| Blueprint owner | Field | Native private value in the example |
|---|---|---|
| Custom EBPS | `speech_ext/speaker_code` | `tuarg` |
| Custom SBPS | `squad_speech_ext/squad_speaker_code` | `tuarg` |
| Active custom attachment lists, when nonempty | `attachment_speaker_code` on every age/gender/visual entry | Map to the intended private native speaker, preserving the requested voice/gender routing; do not leave unintended stock speaker overrides. |

Retarget both owners across every custom age/variant. Confirm the custom squad actually loads the custom entity and its upgrade/production chain uses these records. The Tuareg case changed eight fields across four ages. Keep the existing `squad_name_code`, `squad_race_code`, class/unit codes, gameplay stats, IDs, GUID, production and upgrade links unless current official evidence requires a change. Stock Donso `squad_name_code=donso` and `squad_race_code=no_race` remained valid in the successful private-speaker probe; renaming every related field was unnecessary.

Trace canonical training/start-unit paths as well as custom subfolders. Berber's initial Villager/Trader speech edits were only under `sbps/races/malian/berbers/`; effective stock production used canonical `sbps/races/malian/` owners. The 0.6.1 patch added canonical aliases using the existing custom same-PBGID bytes with speech-only edits. This is a source-routing diagnosis, not permission to replace custom gameplay with stock records or proof of every civilian response. Inspect actual PBGIDs, loadouts and references before adding aliases.

The two main fields are not an exhaustive inventory. Follow entity base attachments and `tier_ext/.../attachments` references into their actual lists. The older Berber `bindings.patch` helper admitted main speaker/race/age fields only; it did not retarget `attachment_speaker_code`. A helper success therefore cannot prove all effective speakers were changed. For the scripted route, clear the admitted custom attachment overrides instead of binding them to an installed private SPD; for native playback, preserve/map the intended actor identities. These are different product choices.

### Portable native installer lessons

- A sharing ZIP can contain a Garrison ZIP and a separately extracted native installer; explain which ZIP to import. An installer payload is not itself a Garrison mod. One observed attempt to import a many-file voice package was rejected as `ZIP contains too many files`; this does not establish a numerical client limit. Deduplicate recordings in the download and expand required aliases during installation.
- A Steam-aware picker can accept the Steam folder, a library, `steamapps`, the game root, or a deeper game folder. Walk ancestors, inspect known `steamapps/common` paths and Steam's `libraryfolders.vdf`/AoE4 `appmanifest_1466860.acf`; validate `RelicCardinal.exe`, `RelicGame.module` and the current audio directory. If multiple installations match, request a more specific folder. Avoid an unbounded disk search. Discover the actual namespace mapping rather than assuming every distribution is identical.
- The tested companion deliberately rejects reparse points anywhere in source/destination ancestry. Running it through the project's E: `output` junction failed before installation; opening the same extracted package through its real F: directory allowed validation to proceed. This is the companion's safety policy, not a Garrison import restriction. Recommend extraction into an ordinary local directory or the verified physical target; do not disable destination-containment checks to bypass it.
- Thousands of native aliases can take minutes to validate. Show component, stage, processed/total files and percentage from the start, including validation, conflict checks, install/adoption, verify and uninstall. The 0.7.3 wrapper used `Write-Progress` plus throttled persistent status lines (about once per second) for hosts that do not render a bar. Percentages restart per stage. Progress goes to host/stderr so machine-readable JSON remains clean. An apparently idle console is not proof of a hang; sample process CPU/I/O without interrupting it.
- Preserve private ownership state across compatible installer versions; verify the whole package before writes, refuse foreign collisions, roll back newly created files on failure, and uninstall only unchanged owned files. Test fixtures independently of the game. Private hardlinks are an optimization: use verified copies where unsupported, including exFAT; do not require NTFS for a portable package.

## Prove routing with a small isolated native test

Start with selection and attack only. It is acceptable for a routing fixture to fill every private WEM slot with those two clips so unknown contexts cannot silently refer to missing files. Label it clearly as a two-recording probe: hearing only two lines is expected, and success does not mean the final family mapping is installed.

Include an unchanged stock control and private age variants. Request prematch resources using the current documented API when the scenario spawns new blueprints. Use `aoe4-game-mode-skill` and AoE4 MCP/installed ScarDoc for exact spawn contracts. In the observed fatal error, `Squad_CreateAndSpawnToward` parameter 4 expected `ScarPosition` but received a Lua table. Construct **both** spawn and facing arguments with the verified `World_Pos` wrapper:

```lua
-- custom_sbp is the verified, qualified custom squad reference.
-- Import the wrapper's defining official module (ScarUtil.scar in this build).
local origin = Player_GetStartingPosition(player)
local position = World_Pos(origin.x + 8, origin.y, origin.z + 6)
local toward = World_Pos(origin.x, origin.y, origin.z)
local squad = Squad_CreateAndSpawnToward(
    BP_GetSquadBlueprint(custom_sbp), player, 0, position, toward)
```

A literal `{x=..., y=..., z=...}` is not that engine position type. Use a fresh match after a fatal startup error; resuming partially registered startup can generate duplicate rule errors unrelated to the first defect.

Require audible private selection/attack in the early and late age phase, an unchanged stock control, and mixed selection without missing audio or duplicated responses before retargeting production. The engine may choose a stock member's voice in a mixed group; test individual private units separately. Record both log/lifecycle evidence and the listening result. No missing-WEM message in `warnings.log` does not establish that a private profile loaded.

## Integrate, install, package and verify

- Expand the qualified mapping to the complete provided set, reuse authorized age/take recordings, and document every temporary substitute.
- Preserve the existing mod identity and retarget only its custom speaker fields. A game-mode voice manifest and one startup diagnostic are useful; name the **expected** profile, speaker, mapping revision and coverage counts. Logging the manifest does not assert that playback succeeded. Native speech owns selection/order timing; invent no SCAR speech callbacks. Treat an external polling dispatcher as a separate experimental presentation route subject to the audible suppression gate above.
- Build the actual existing Extension through current Content Editor. A Garrison project cook does not automatically rebuild a separately owned source project. Read back all age speaker fields, imported SCAR and mode/tuning content; check archive CRC/SHA blocks and package manifest hashes. Keep authoring tools, caches and original game binaries outside distributables.
- Supply an explicit native companion manifest with private relative paths, bytes and SHA-256. The installer checks containment and private identity, rejects conflicting/redirected destinations, verifies all payloads before changing files, and removes only matching owned files. Perform upgrades while AoE4 is closed: validate the old manifest, remove only its matching private files, then install/read back the new mapping. Preserve the old private release for rollback. Another project's profile collision needs resolution, not a forced overwrite.
- State Garrison enablement **and** exact lobby selections. Existing mod localization can give the mode and tuning pack different titles. In the Berber example these are **Berber Civilization** (Game Mode), **The Berber Dynasties** (Tuning Pack), and **Malians** (civilization). Treat those as example names and discover the target mod's current ones.
- Restart AoE4 completely and test selection, movement, attack, attack-move, stop, hold, formations, garrison/ungarrison, brace, combat, damage, healing/death and upgrades through affected ages. Exercise individuals, groups, mixed groups, AI ownership and unrelated units. Check timing/truncation, original voice fallback, duplicates, missing media and scope isolation.

Report separate results for **conversion**, **profile/mapping readback**, **tuning/SCAR validation**, **Content Editor build**, **package integrity**, **native installation**, **audible routing probe**, and **full-family gameplay**. Leave unexercised families unverified. The successful Tuareg evidence qualifies selection/attack routing in both age phases and stock isolation; the full 49-recording package is built/installed/read back, while the full production matrix and shared-effect suppression remain unverified.

### Companion manifest contract

The tested installer used schema `tuareg-native-audio-sidecar/v1`, `speaker`, `profile`, and a complete `files` array. An abbreviated shape is shown below; fill **every** actual referenced media row with its measured byte count and real SHA-256 before installing:

```json
{
  "schema": "tuareg-native-audio-sidecar/v1",
  "speaker": "tuarg",
  "profile": "malian_tuarg.spd",
  "files": [
    {"path": "malian_tuarg.spd", "bytes": 313216, "sha256": "measured_profile_digest"},
    {"path": "civ_malian/malian_tuarg/malian_tuarg_select_inorm_clowest_01.wem", "bytes": 0, "sha256": "measured_encoded_digest"}
  ]
}
```

This is a manifest structure example, not an installable payload. Counts and identity guards in the original Tuareg installer are fixed to its 1,279 files/`tuarg` identity; adapt and validate them for another qualified private identity. No general native installer is bundled with this skill. Author one using the contract above, or adapt the optional locally qualified `tools/Install-TuaregNativeAudio.ps1` and `Upgrade-ToFullTuaregAudio.ps1`. They require the corresponding complete manifests and are not generic cross-unit installers.

## Troubleshooting

| Symptom | First evidence to inspect | Action / limit |
|---|---|---|
| Mod missing from lobby | Fresh `warnings.log`, archive TOCs, client enabled state | Resolve forbidden `audio` TOC rejection; retain permitted Extension structure. |
| Stock control speaks, private units silent | Cooked speaker fields, SBPS→EBPS, SPD native namespace, complete restart, installed hashes | Correct native deployment before recoding all clips. `data:audio/` is not native `audio:`. Then probe SPD/codec acceptance; silent logs are not proof. |
| Only two recordings heard | Installed sidecar revision and each media assignment hash | Expected for the two-clip fixture; install the complete mapping after the native gate. Updating only the tuning ZIP cannot change an independently installed sidecar. |
| Same line repeats for one order | Supplied per-family take count and mapped variants | Expected when one provided take is reused across five or more native slots. Different commands should use their mapped families. |
| Some actions speak the wrong/new line | Family/delivery/age map, placeholder table, installed source hashes | Resolve the exact assignment; effort placeholders are intentional only when authorized/documented. |
| Custom Age 1 works, upgraded unit does not | Every EBPS/SBPS age binding and inherited replacements | Retarget missing custom variants and cover every chronology/take path; preserve upgrade links. |
| Fatal SCAR position-type error | API signature, wrapper import and both position arguments | Use the current typed position constructor; rebuild and start a fresh match. |
| Footsteps/impacts/creation still original | Separate action trees, foley switches, weapon/shared events | Private speech does not replace them. Qualify a per-unit route; preserve shared stock consumers. |

## Source and qualification pointers

- Installed Garrison `guide/garrison-audio.html` and `guide/garrison-api.html`: external backend and runtime scope.
- Installed game `RelicGame.module`, stock speech archive/profile, `PlatformInfo.xml`, `SoundbanksInfo.xml`, and platform configuration: native namespace/format evidence.
- Audiokinetic [External Sources settings](https://www.audiokinetic.com/en/library/edge/?id=specifying_input_output_locations_for_external_sources&source=Help): conversion list and output concepts; it does not define AoE4 mounting.
- Optional local qualification artifacts, if this workspace still exists: `E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\output\TUAREG_VOICE_VALIDATION.md`, `tuareg_voice_test/full-delivery-verification.json`, `routing-diagnosis/evidence.json`, `mcp-spawn-contract-evidence.json`, `mcp-full-voice-evidence.json`, and `tools/`. Read current status rather than treating old probe filenames as the final release. This reference and its helper remain usable without that workspace.
