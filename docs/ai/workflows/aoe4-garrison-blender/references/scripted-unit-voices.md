# Garrison-only unit voices and original/custom overlap

Use this when the player should **import one ZIP, enable the mod, and use normal
Garrison Play**, with no voice installer or alternate launcher. Also use it when
most units work but a Villager or another visual/gender variant still speaks its
original voice over the custom response.

This procedure is based on the **operator-confirmed Berber 0.8.1 overlap fix,
2026-10-17**, after restoring stock loose game audio. It combines embedded
scripted playback with removal of the custom units' native speech bindings.
`audio.play()` does not mute anything by itself. The confirmed result does not
establish full native-event parity, every context/age/gender, or multiplayer.

Contents: [route choice](#choose-the-product-route), [binding inventory](#inventory-every-native-speaker-consumer),
[targeted repair](#apply-only-the-admitted-speech-changes), [dispatcher](#preserve-the-working-dispatcher),
[package](#build-one-normal-import-zip), [acceptance](#verify-and-qualify-separately),
[diagnostics](#symptom-to-next-check), [fixture evidence](#berber-fixture-and-rebuild-pointers).

## Choose the product route

| User's intended product | Route | Required qualification |
|---|---|---|
| One ordinary Garrison ZIP; scripted unit replies acceptable | This guide: embedded PCM, `Garrison.audio`, presentation-only SCAR, custom native binding suppression | Correct custom reply and no native overlap in a clean game; supported triggers documented |
| Native speech scheduling/priority/context tree through private SPD/WEM | [Native voices](native-voices.md): private profiles, main and attachment bindings, separate native `audio:` deployment | Namespace, codec, all mappings and audible native routing; installer only if user accepts it |
| Experimental replacement of the game's selected native source inside PostEvent | Separate matching Garrison feature/runtime | Exact source rules, binary/build gates, selected-owner scope, media lifetime and audible one-playback acceptance |

Do not change the chosen product because a previous incomplete attempt failed.
For a Garrison-only request, a loose-file installer or bundled diagnostic runtime
does not satisfy the requested player flow. Do not infer experimental native API
support from a client version number or from packaged WEMs.

The observed normal client identified as **0.1.6**, while its session logged:

```json
{"kind":"garrison_call","m":"native_speech","note":"no handler"}
```

That session could play other units through `Garrison.audio`, but could not use
the handoff's `Garrison.speech` activation API. Remove that dependency when
deliberately converting to the scripted route. Do not silently ship a second
player executable, bypass opcode checks, or invent `Entity_SetSpeechEnabled` /
`Squad_SetSpeechEnabled`; no such mute contract was established in this work.

## Establish the actual test environment

1. Identify the user's selected mod/version, effective SGA hash, enabled bundles,
   and exact lobby selections. A source `.scar` edit is not an installed client
   update. Inspect the imported archive, not just an authoring directory.
2. Read the current session and warnings/audio logs. Distinguish audio enabled,
   a matched unit, submitted clip, backend `played`, and a user's audible result.
   A second enabled pack may be staged without being the selected tuning pack;
   investigate actual ownership/selection instead of assuming a conflict.
3. Check whether old loose private SPD/WEM files are installed. Empty directories
   named after prior speakers do not prove that their media/profiles are present.
   Hearing other units also does not prove a native pack is active: the mod can
   already contain scripted playback for those families.
4. If authorized to prepare a clean-stock test, close AoE4 first. Use saved
   installer ownership/hash evidence or the installed Steam depot file list and
   hashes to distinguish additions from stock. Back up verified additions outside
   **all game-mounted directories** before removing them; retain restore records.
   Preserve every stock-declared file. Do not delete the entire audio folder,
   shared banks, speech archives or `RelicGame.module`.
5. Recheck the clean folder against its evidence after removal. Record exactly
   which directories were verified; a `cardinal/audio` audit is not verification
   of every game archive or every audio-quality directory. If stock-declared
   files are missing/changed, stop treating the cleanup as complete and repair
   through a verified stock source/Steam route rather than guessing replacements.

For the Berber clean test, **5,283** stock loose-audio files matched installed
Steam SHA-1/size records; **1,279** old Tuareg additions were backed up/removed.
Those numbers are fixture evidence, not expected counts for another installation.
Source masters, normalized WAVs, encoded WEMs and mod recipes stayed in the project.

## Inventory every native speaker consumer

The crucial failure was stopping at `speech_ext` and `squad_speech_ext`.
Attachment entries can explicitly select original speakers independently.

| Surface | Follow/inspect | Scripted replacement fixture |
|---|---|---|
| Custom entity EBPS | `default/speech_ext`, parent, active entity variants | Main speech table absent |
| Actual squad SBPS | `default/squad_speech_ext`, loadout, training/start/spawn/upgrade routes | Main speech table absent in effective custom/canonical owners |
| Base attachments | `default/entity_blueprint_ext/animator_attachments` references | Inspect their effective lists; do not assume the base list is the only one |
| Age-tier attachments | `default/tier_ext/.../attachments/$PBGNAME` and `$PBGMAP` | Resolve every qualified custom list actually used by the unit |
| Each attachment entry | `.../attachment_speaker_code` | Clear admitted original-speaker CString overrides to `""` |
| Other native audio consumers | Action trees, foley, weapons, shared events | Separate scope; speech work does not authorize disabling them |

Trace actual references, not only filenames containing the unit's name. Include
every nested attachment entry, age, sex, appearance and embedded variant. Do not
scan only the first attachment or assume one speaker field per file. Keep stock
and custom ownership clear; changing a shared stock list could affect unrelated
units/civilizations. If a custom unit still points at a shared list that must be
changed, derive a private list and retarget only that custom consumer through the
current authoring workflow; preserve IDs, gameplay and visual data appropriately.

Also trace canonical owners. A custom `sbps/races/<race>/<mod>/...` record may not
be the one used by the Town Center, market, start units or scripted spawn. The
Berber civilian inventory previously missed canonical `sbps/races/malian/...`
owners. Confirm runtime names/PBGIDs/loadouts before creating aliases. Do not
replace an edited record with a stock donor merely to obtain a speech field.

### The exact Villager trap

The 0.8.0 Villager had no main native speech tables, but these active private
age-tier lists still assigned the original voices:

```text
attrib/attachments/attachment_lists/garrison/berber_units_050/
  bind_villager_a1_tier1_villager_mal.rgd
  bind_villager_a2_tier2_villager_mal.rgd
  bind_villager_a3_tier3_villager_mal.rgd
  bind_villager_a4_tier4_villager_mal.rgd
```

Each contained **52** speaker overrides: 26 `villagerMale` and 26
`villagerFemale`. Across four ages that was **208 fields**, 104 of each value.
Clearing only these CStrings in 0.8.1, while retaining the already-absent main
tables and the working scripted bank, resolved the overlap according to the user.
Working Scout/Archer attachment lists provided the empty-value control.

This explains why main-table removal or assigning an absent main speaker alone
did not fix earlier Villager attempts: original speakers remained explicitly
selected elsewhere. It does not prove a universal engine fallback rule. If a
different unit still overlaps after a complete inventory, continue tracing its
real consumers rather than repeatedly applying this same patch or muting all
Speech/Master audio.

## Apply only the admitted speech changes

For the scripted route, start from the accepted current archive/source, preserve
it as rollback, and isolate the candidate. Use the current structured RGD/attribute
tools; raw global byte/string replacement is unsafe and cannot prove scope.

- Inventory main speech tables and attachment speaker fields before editing.
  Removing an already absent table again is not a new repair.
- Remove the custom paired speech tables when this route and the comparison
  fixture justify that edit. If they were already removed, leave them alone.
- In the **resolved active custom attachment lists**, change only existing,
  admitted `attachment_speaker_code` CStrings from identified original speakers
  to the empty string. Do not remove attachments, gender variants, materials,
  geometry, animation actions, tier conditions, probabilities or order.
- Keep a per-member/per-field before/after ledger. Do not blindly clear every
  attachment in the mod; another unit may intentionally use native speech.
- Decode/serialize/decode with the actual current schema. Restore every edited
  field in a copy and compare complete typed structures to the original: key,
  hash, type, value and order. This semantic undo must recover the original.
- Retargeting a **native private-SPD** unit is a different operation: map its
  attachment speakers to the intended native actors, preserving requested gender
  routing. Do not clear them just because this scripted fixture used empty values.

Typed transformation for the admitted Villager field:

```text
node.key   = attachment_speaker_code       # unchanged
node.kind  = CString                       # unchanged
before     = villagerMale | villagerFemale
after      = ""
```

The older Berber main-speaker helper matched only main speaker/race/age paths.
Its success did not include these attachment nodes. Check helper coverage instead
of treating an old “speech-only patch passed” report as an exhaustive inventory.

## Reuse the recordings and validate the bank

Inventory existing accepted recordings before generating anything. Preserve
lossless masters, normalization provenance, generation receipts, actor identity
and accepted encoded assets. A WEM receipt or inventory entry is not an activated
scripted clip. Reuse the accepted PCM master/normalized WAV where available;
avoid decoding a lossy WEM merely to recreate an existing lossless source.

The qualified starting format is **mono, 48 kHz, 16-bit PCM WAV**, fully readable
by the backend. Verify source/receipt hashes, WAV channels/rate/width/compression,
duration and packaged readback hash. Do not rename WEM/Ogg to WAV. Compressed
external speech formats require separate decoder/listening qualification.

Store each unique clip once, for example `audio/voices/<sha256>.wav`. The archive
member has TOC **data** and path **audio/voices/...**; depending on the inspector,
`data` is a separate TOC field rather than a literal `data/` path prefix. Script
calls use `audio/voices/...`. Use direct `audio.play()` paths for a large bank;
do not exceed the documented 256 symbolic event-kind map merely to name clips.
Direct paths still obey decoder, clip-size, queue and voice budgets.

Record exact semantic choices. In 0.8.0/0.8.1, Villager uses one take per action
shared across ages; Tuareg uses four dialogue age banks and shared nonverbal
efforts. Move responses use existing `movegc`; attack-move uses attack dialogue.
Those are explicit adapter mappings, not a claim that native context names are
interchangeable. Pain/death require real nonverbal efforts, not command lines.

## Preserve the working dispatcher

Read [music/external audio](music-and-audio.md) for the actual audio API and
budgets, and the game-mode skill for native SCAR/event contracts. The working
Berber adapter imports `garrison/garrison.scar` and obtains:

```lua
local audio = Garrison.audio.forMod("berber_future_kingdom")
-- Controller start: audio.session() once; one named .25-second tick.
-- Tick: audio.pulse(World_GetGameTime()).
-- Response: audio.play(relativePath, x, z, gain) using dot calls.
-- Teardown: remove rules/events/groups and call audio.stop().
```

Keep the following behavior when extending a working adapter:

- Admit the intended family through verified runtime PBGIDs/names. Bare stock
  names and owner-qualified custom names can coexist in one match; do not strip
  arbitrary namespaces or assume every name is qualified.
- Use squad selection for a squad controller. Entity-only selection missed the
  observed Villager (zero entities, one squad). If converting to entity actors,
  merge/deduplicate the appropriate selection routes rather than counting twice.
- Reject `World_OwnsSquad` wildlife/carcasses **before** `Squad_GetPlayerOwner`.
  Use identity checks for recycled IDs and changed blueprints; cache family and
  position before death rather than dereferencing a killed squad.
- Detect selection-set changes; holding a selection must not repeat the line.
  Arbitrate one group responder and use duration/cooldown gating to avoid a chorus.
- Use existing `GE_SquadCommandIssued` contracts for observable explicit commands.
  In 0.8.x the demonstrated fields included `context.command` and `context.squad`.
  Observe supported activity edges for work/combat, but label them as inference.
  Do not fabricate a target discriminator for generic default/right-click orders.
- Preserve native event/command scope checks. Repeated/default/queued orders can
  still have gaps; record them rather than selecting unrelated ambient speech.
- Follow actual upgraded blueprint tiers for age dialogue. Berber matched its
  `unit_spearman_tuareg_<age>_ber` names, including an owner prefix, with an Age I
  fallback for unknown names. Do not assume sorted PBGIDs imply age order.
- Keep session, selection, variant ordinal, cooldown and camera-relative audio
  state cosmetic/local. They must not influence gameplay, simulation RNG, AI,
  damage, economy or victory. Reset them on teardown/restart.

Remove the two families' scripted exclusions when moving them off the native
experiment, populate their bank, and remove their unsupported native activation
start/pulse/stop calls. Do not fix only one of these: an empty bank, exclusion or
unsupported dependency can leave a family silent while all other units work.

## Build one normal import ZIP

For this product the ordinary package needs only:

```text
Berber-<version>.zip
  garrison.json                    # exactly one across the whole ZIP
  Berber_future_kingdom.sga         # tuning/game mode + audio + scripts
  START-HERE.txt
  VOICE_GAPS.md / coverage report  # useful compact evidence
```

No voice installer, nested companion ZIP, START-TEST command or development
runtime is required. Garrison starts its own matching backend. An unused WEM
catalog/declaration retained inside an existing archive is not proof that its
native experiment is activated; in 0.8.x the scripted adapter makes no native
speech activation call. Preserve required provenance or remove inert inputs only
through a separately validated scope, rather than confusing them with playback.

Inspect every ZIP basename, not only the root: a historical reference manifest
under `documentation/handoff/garrison.json` caused 0.7.5 to be rejected despite
having a valid root manifest. Rename reference copies to `garrison.json.txt` or
keep them outside the delivery. Read [packaging](packaging-and-catalog.md).

## Verify and qualify separately

1. **Source/typing:** accepted recordings and hashes; admitted fields only;
   unchanged main gameplay, visuals, genders and upgrade routes; semantic undo.
2. **Controller:** run the real Lua dispatcher with meaningful mocks for the
   changed behavior. The 0.8.0 tests covered both selections, commands/work,
   mixed-group arbitration, neutral/foreign rejection, efforts, reset and ages.
   The 0.8.1 regression failed against all four original attachment lists and
   passed after their 208 fields were cleared. Neither is an audible test.
3. **Archive:** validate the base hash, allowed changed-member set, current TOCs,
   unchanged-member size/CRC evidence and changed-member decoded SHA-256. Preserve
   a precise account of whether all unchanged bytes were hashed or only checked
   by CRC/size. Keep immutable source/rollback archives.
4. **ZIP:** readability/CRC, exactly one manifest, all expected members, each
   declared archive hash, no accidental executable/installer dependency. Import
   into the intended normal client to qualify actual import separately.
5. **Fresh-process listening:** close AoE4 completely, import/enable the new
   package, launch through normal Garrison Play, select the actual required lobby
   components, and test new Villagers of both appearances. Listen for **custom
   response / original overlap / silence** separately. Check selection, orders,
   work, damage/death, relevant ages, groups and a known working Spearman/control.
6. **Remaining matrix:** record which of pause/resume, menu return, second match,
   full restart, sliders, disabled-mod stock behavior, other ownership and
   multiplayer were actually exercised. A brief “it worked” confirms the reported
   symptom, not every item in the proposed test list.
7. **Cleanup/rebuild:** follow project AGENTS/STORAGE rules after verified release
   packaging. Retain source masters, profiles, receipts, scripts, current archive,
   final ZIP, required bases and compact reports. Inventory disposable extraction,
   patched payload and readback copies; verify physical paths/junctions, preserve
   regeneration routes, then remove only release-owned copies. Recheck delivery
   hashes and report reclaimed bytes. A move to another drive is not a reduction.

## Symptom to next check

| Symptom | Next evidence / action |
|---|---|
| Only Villager doubles; Spearman works | Active age/gender attachment `attachment_speaker_code` overrides; preserve the working Spearman and dispatcher |
| Main speech tables absent but original replies persist | Follow base + tier attachments, canonical spawn/loadout owners and embedded variants before proposing another mute trick |
| Villager/Tuareg silent, others work | Family bank/exclusion, actual runtime matching, `native_speech: no handler`; do not generate recordings again before checking retained sources |
| Custom voices heard without the special launcher | Could be normal scripted playback or old loose native media; inspect files/session, not the observation alone |
| Client says 0.1.6 but experimental speech fails | Read capability/handler/build evidence; version label is insufficient |
| JSON says playback accepted or backend says played | Listening still required for correct text, timing, native overlap and clean isolation |
| ZIP says exactly one garrison.json required | Count manifests recursively through ZIP names; check archived documentation copies |
| Stock sounds differ outside the mod | Audit owned loose additions safely; preserve stock files and verify disabled-mod behavior |

## Berber fixture and rebuild pointers

These optional local paths support reproduction; this guide does not depend on
their continued existence. Discover the current project/root/storage mapping.

- Project: `E:/age of empires 4 mods/AI_Assisted_modding/Berber_future_kingdom_ai`.
  `output` was a junction to
  `F:/aoe_4_temp/Berber_future_kingdom_ai_20261014/output`.
- `research/berber080`: editable dispatcher/bank, accepted-recording preparation,
  Lua tests and ordinary-client packaging. Reused 101 PCM recordings for the two
  added families; kept the other 24 banks unchanged.
- `research/berber081`: read-only investigation, attachment-speaker regression,
  typed patch/build recipe. Only the four attachment RGDs changed from 0.8.0.
- `research/stock_audio_audit.py` and
  `output/stock_audio_restore_20261017`: installed-depot comparison, quarantine
  inventory, verified restore ZIP and post-removal result. Game writes require
  authorization and a closed game; do not run the old `--quarantine` blindly.
- `output/berber_update_0_8_1`: final ZIP/SGA, `attachment-speaker-changes.json`,
  `release-validation.json`, `cleanup-report.json`; read the latest operator
  acceptance annotation as well as the as-built package notes.
- Accepted 0.8.1 ZIP SHA-256:
  `a57bf7ce3beb8614cb8df2f4ee8349ca1d02e8adeb5d6909401c39667f6fb54c`.
  SGA SHA-256:
  `c58ef43ad4b0e664609161eb35178c97500837e9a844d7583fb014a50b7cc441`.
- User evidence: after 0.8.0, “spear works great” but Villager overlapped; after
  the 0.8.1 attachment change, **“yes yes it worked.”** Record this narrow outcome
  without claiming the user individually enumerated all ages/sexes/context tests.
- Future builds must preserve **both** the 0.8.0 scripted/main-table changes and
  the 0.8.1 attachment-field changes. Rebuilding from an older source/SGA or
  regenerating bindings with the old main-field-only helper can reintroduce the
  bug. Follow the project's `REBUILD_NEXT.md` and retained base/source chain.
