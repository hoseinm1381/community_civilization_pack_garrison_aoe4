# Community Civilization Pack Normal

Normal edition for ordinary Age of Empires IV, with Vietnam, Persia and Korea
alongside China, Delhi Sultanate and Zhu Xi's Legacy. Garrison and Blender are
not required to play. Credits: **hosein81 and chilly5**.

## Downloads

- [Playable local ZIP](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/raw/refs/heads/normal-release/Community_Civilization_Pack_Normal-local.zip) — 12.6 MB.
- [Editable source ZIP](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/raw/refs/heads/normal-release/Community_Civilization_Pack_Normal-editable-source.zip).
- [Editable development branch](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/tree/normal).

Use **Download raw file** if GitHub opens a file preview. The green Code button's
ZIP contains this distribution branch; extract the playable ZIP inside it.

## Install locally

1. Exit AoE4. Extract `Community_Civilization_Pack_Normal-local.zip`.
2. Copy its `Community_Civilization_Pack_Normal` folder into your actual Windows
   Documents folder under `My Games\Age of Empires IV\mods\extension\local\`.
   Create missing directories if necessary. The final path is:

   ```text
   ...\mods\extension\local\Community_Civilization_Pack_Normal\Vietnam_v2.sga
   ```

3. Keep any older Normal recovery copy outside the entire game's `mods` folder
   before replacing it. The obsolete `local\Vietnam_v2\Vietnam_v2.sga` shares
   Normal's ID: do not load both. Garrison is an independent mod.
4. Restart AoE4 and enable the local mod if needed. Select **Community
   Civilization Pack Normal** for both **Game Mode** and **Tuning Pack**, using
   both from this same build.

## Play

Start a fresh standard **Dark Age** human match:

- China in the lobby: choose China or Vietnam.
- Delhi Sultanate: choose Delhi or Persia.
- Zhu Xi's Legacy: choose Zhu Xi's Legacy or Korea.

One shared 30-second choice window; timeout and AI keep the original civilization.
Korean/Persian AI, Nomad, later-age starts and save/load are outside this milestone.

## This build

Built on **29 October 2026** from source commit
[`b9c504e`](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/commit/b9c504e9016d7bd355dbb0799d4e9bb827acd6ec). Includes roster-gated loading, Literature
storage/book icons, Keep/Hwacha cleanup, normal Korean construction times, and
the Observatory's four-allowance fix without the rejected native modifier.

**81 maintained tests pass.** A fresh native Content Editor build completed.
All 1,035 SGA members pass stored-byte checks, all 44 scripts match source,
and native readback verifies the 27 construction corrections and resource caps.
The ZIP passes CRC and embedded-SGA SHA-256 checks.

The latest construction/Observatory changes still need a fresh native match.
Multiplayer, save/load and measured VRAM/frame-time acceptance are unverified.
[Detailed receipt and limits](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/blob/normal/docs/NORMAL_RELEASE_20261029.md).

The playable ZIP is **12,585,477 bytes**, an increase of **5,331,487 bytes** over
the older 26 October Normal ZIP. SGA: **12,839,445 bytes**. File-size results do not
prove runtime memory or frame-time improvements. `BUILD_INFO.json` contains the
exact hashes, native readbacks, source commit and acceptance boundaries.

## Editable source

Extract the optional source ZIP outside the game and installed-mod folders.
Open `Community_Civilization_Pack_Normal.aoe4mod` with your own AoE4 Content Editor.
Follow `CONTRIBUTING.md`; `SOURCE_SNAPSHOT.json` verifies each included source file
against the exact Git commit. Donor folders are not needed for ordinary builds.
Machine configuration, dependency installs, caches and historical packages are
excluded. The base game and Content Editor are not redistributed.
