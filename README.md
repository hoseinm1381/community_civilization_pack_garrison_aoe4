# Community Civilization Pack Normal — local base-game build

This branch distributes the Normal edition for ordinary Age of Empires IV on Windows. It combines a Tuning Pack and Game Mode, adding Vietnam and Persia alongside China and Delhi. **Garrison and Blender are not required to play.**

Credits: **hosein81 and chilly5**. Original Persia source credits Hossein and ChillyEmpire.

## Downloads

- **[Download the playable local mod ZIP](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/raw/refs/heads/base_game_release/Community_Civilization_Pack_Normal-local.zip)** — use this to play; no Content Editor build is needed.
- [Download the editable source ZIP](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/raw/refs/heads/base_game_release/Community_Civilization_Pack_Normal-editable-source.zip) — optional, for modifying/rebuilding the mod.
- [Editable development branch](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/tree/normal).

Click a ZIP above, or open its file on GitHub and choose **Download raw file**. GitHub's green **Code → Download ZIP** downloads this distribution branch, containing both ZIPs; extract the playable ZIP inside it.

## Install locally

1. Exit Age of Empires IV completely.
2. Extract `Community_Civilization_Pack_Normal-local.zip`. It contains:

   ```text
   Community_Civilization_Pack_Normal/
     Vietnam_v2.sga
   ```

3. Open your Windows **Documents** folder, then:

   ```text
   My Games\Age of Empires IV\mods\extension\local\
   ```

   The usual full path is `%USERPROFILE%\Documents\My Games\Age of Empires IV\mods\extension\local\`. If Documents is redirected to OneDrive or another drive, use that actual Documents location. Create missing `extension` or `local` directories if needed.

4. Copy the extracted `Community_Civilization_Pack_Normal` folder into `local`. The final path must be:

   ```text
   ...\mods\extension\local\Community_Civilization_Pack_Normal\Vietnam_v2.sga
   ```

   Avoid an extra nested `Community_Civilization_Pack_Normal` directory. Keep the SGA filename as supplied.

5. If an older Normal copy is already installed, keep a recovery copy **outside the game's entire `mods` folder** before replacing it. In particular, the old `local\Vietnam_v2\Vietnam_v2.sga` build shares this mod's ID and display name: move its `Vietnam_v2` folder out of `mods` so it cannot load alongside this build. This instruction concerns the obsolete Normal copy; other mods and the independent Garrison edition have separate identities.
6. Start AoE4 again. Enable the local mod in the game's mod manager if necessary.

## Play

Create a fresh standard **Dark Age** skirmish/custom match. Select both:

- **Game Mode:** **Community Civilization Pack Normal**.
- **Tuning Pack:** **Community Civilization Pack Normal**.

Use the Game Mode and Tuning Pack from this same installed build. Selecting only one does not load the complete mod.

As a human player, choose:

- **China** in the lobby → choose **China or Vietnam** at match start.
- **Delhi Sultanate** in the lobby → choose **Delhi or Persia** at match start.

The shared choice window lasts 30 seconds. Timeout keeps the original civilization. AI retains its original civilization.

## Troubleshooting

**Two entries with the same name:** an old Normal build is still installed. Exit the game, move the obsolete copy outside `mods`, and restart. Do not choose by row position; identical labels can hide different builds.

**No Delhi/Persia popup, or “No eligible Chinese or Delhi human…”:** confirm that you selected Delhi as a human, started in Dark Age, and chose both the custom mode and tuning pack from this ZIP. Fully restart after removing duplicates; already loaded scripts can survive a lobby change. The previously diagnosed conflict combined the old six-unit Persia probe helper with the newer full-Persia tuning data.

**The ZIP does not appear in-game:** AoE4 loads the extracted `.sga` under the path above, not the ZIP or the editable `.aoe4mod` source project.

If the issue persists, retain `warnings.log` from the game's Documents folder and describe the lobby selections and observed result. Keep full Persian gameplay, save/load and multiplayer acceptance separate from installation checks.

## Editable source

Extract the optional source ZIP into a development folder **outside the game installation and active local-mod folders**. Open `Community_Civilization_Pack_Normal.aoe4mod` using the AoE4 Content Editor installed through your own game/Steam setup. The included `CONTRIBUTING.md` explains local build prerequisites, and `SOURCE_SNAPSHOT.json` records every packaged source hash.

The source snapshot includes the current editor-saved working files, including 104 modified files relative to its recorded Git base. It excludes `.git`, editor caches, local machine configuration, installed tools, work folders and old releases. This does not commit those edits to `normal`. The original source documentation records historical validation milestones; use this branch's `BUILD_INFO.json` for this distribution's measured evidence.

## Build status

This is the existing local compiled build, packaged on **26 October 2026**; no new native compilation was performed for this branch. Its archive namespace, stored-byte checks, full private Persia roster, and absence of old `ps_probe_*` members were verified. The source snapshot passed the portable verifier and all **29 current tests**.

Earlier opening selection was user-tested. A fresh native match after the duplicate-install repair, the complete Persian roster/landmark effects, save/load and multiplayer remain unverified. Nomad, later-age starts and Persian AI are outside the current supported milestone. Some native landmark effects on ruin/repair remain an explicit test gate.

`BUILD_INFO.json` and `SHA256SUMS.txt` identify the exact payloads. This is a mod-only distribution; the base game and Content Editor are not included. Preserve the Normal GUID `a743d7d1-d753-4cf7-8817-e29d8ded7366`; Garrison uses an independent identity.
