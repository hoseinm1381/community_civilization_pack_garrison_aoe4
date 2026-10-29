> **Source accepted 2026-10-29:** the owner reported "it worked" and authorized
> promotion and GitHub source push without a release upload. See
> [ACCEPTANCE_110.md](ACCEPTANCE_110.md). The preparation report below retains
> its original scope and pre-acceptance status.

# Garrison 1.1.0 Korea candidate

Prepared on 2026-10-29 in `F:/aoe_4_temp/Temp_before_github_push` at the owner's
request. The permanent `F:/aoe_4_temp/community_civilization_pack_garrison_aoe4`
repository stays at accepted **1.0.6** until the owner confirms promotion.
No Korean modeling, installation, GitHub push, publication or cleanup is included.

## Gameplay and integration

- Adds **Zhu Xi's Legacy / Korea** to the existing China/Vietnam and Delhi/Persia
  shared 30-second choice. Human choices are sender-validated and resolved in
  player-index order. Timeout, AI and disconnected players retain the original.
- Imports the complete active Normal Korea roster, age progression, landmarks,
  naval mechanics, Literature, research, foreign technologies, transformations
  and information panels: **378 private tuning definitions**, **12 SCAR modules**,
  **33 icons** and **363 additional English localization rows**.
- Preserves the latest Normal fixes: normal Korean construction times; the
  Observatory's four additional distinct offers and two additional allowances;
  15% completion rebate on Literature actually paid while it functions; one-time
  cancellation refunds; reversible ruin/repair behavior; guarded Keep/Hwacha
  barrage cleanup; consistent Arrow Chutes range multiplier; Hangul gold income.
- Retains scholar proximity bonuses of 25% each, upgraded to 40%, with the same
  radii and timing. Native Literature purchases use the approved narrow Zhu Xi
  storage and race-specific book UI exception. Byzantine olive-oil data and the
  native action cap remain protected by semantic restoration checks.
- Reuses Garrison's accepted shared loader and complete Vietnam/Persia catalogs,
  including Vietnamese art/voice-private blueprints. Korean preloading is gated
  by the complete human Zhu Xi roster. Missing/incomplete rosters fall back to
  full loading; unrelated humans and AI-only slots do not load custom families.
- Preserves Vietnam presentation, voice start/restore/cleanup hooks and all
  existing art/audio/native-resource owners. Adds 43 verified Korean movers to
  Flooded Citadel's existing admission catalog, excluding 67 nonmoving Korean
  entities. No original admission entry is removed.

Fresh standard Dark Age human matches are the supported first milestone.
Korean AI, Nomad, later-age starts and save/load remain excluded. Existing
Garrison restore hooks are retained; their presence does not add Korean save
support. Credits remain **hosein81 and chilly5**.

## Identity, parity and preservation

Garrison GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`.
Archive namespace: `b7fcea91257b408fb9e8ae4d8bc402e1`.
Stable bundle: `community_civilization_pack`.

Normal source pin: `b9c504e9016d7bd355dbb0799d4e9bb827acd6ec`.
Garrison baseline: `84b0888e6d86d8782cbe195e878827a2ff40f9db` / version 1.0.6.

All 378 Korean XMLs and 33 icons are checked against the Normal snapshot after
the single namespace translation. All 12 Korean scripts are checked after
namespace/newline normalization and the binding to the existing shared loader.
No further Korean gameplay interpretation was introduced. The preserved Normal
migration ledger records the donor imports, omissions and earlier repairs;
`normal-provenance/` keeps its three reports with their original scope.

No Korean PBG collides with the existing editable source or voice identities.
The final package audit also checks all serialized PBG IDs and private references.
Editor-generated identities are retained under the destination GUID. Official
singleton inheritance is refreshed for all affected default/campaign variants.
Construction semantic receipts are rebased only for the GUID translation, with
the original Normal receipt hashes retained.

Only **five existing editable assets** change: the mode, selection core, shared
loading guard, Flooded Citadel admission list and English locale. All **746**
other baseline asset files remain byte-identical. The old 850 locale rows are
retained as an exact byte prefix. There are **425 new source assets**. See
`korea-garrison-port.json` and `tools/verify_korea_garrison.py`.

## Validation and boundaries

- Portable source check: **1,038 definitions**, **1,213 localization rows**.
- Current suite: **95 tests passed**, including the carried 81 Normal tests,
  11 Garrison movement regressions and three Garrison/Korea integration checks.
- Existing Garrison suite: **48 tests passed** against the candidate.
- Refreshed inheritance: **541 private / 5,758 official** blueprints, zero errors.
- Installed tuning validator: **zero errors**, 131 inherited corpus-version
  warnings on existing Garrison files, and the stock-reference informational
  summary. No Korean file produces a new tuning warning.
- Installed SCAR validator: zero errors. Reviewed warnings cover known engine
  wrappers/table methods, loader-owned PLAYERS and engine-owned squad groups.
  The groups must remain engine-owned; they are not leaked temporary groups.
- AoE4 MCP checks cover all 12 Korean modules, the final mode and shared loader.
  `and`/`or` reports are parser false positives. Flagged cost/group/dialogue APIs
  are documented official APIs; the index lacks usage examples for them. The
  command-availability wrapper resolves to official `player.scar`. No new engine
  API was invented. Native modified-cost/payment behavior remains a game test.
- Both installed skill self-tests passed.
- **Actual native Content Editor build passed**, validating 1,038 instances in a
  completed 661.51-second run. The correct namespace was checked before and after
  the burn. The baseline stock binary-config/schema notices are not Korean build
  failures; the completed burn has no error records.

Native-source compilation is a reference burn. The final owning package is
assembled from accepted 1.0.6 members plus only the explicit Korean/shared delta.
Its full member hashes, mounts, IDs, references, construction times and resource
caps are checked independently. `output/current/verification.json` contains the
final package result and measured budget after assembly.

Client import, latest fresh-match behavior, multiplayer, save/load and measured
VRAM/frame-time are **not tested** by these checks. No smoothness claim is made.

## Reproduce and review

Portable checks, with the pinned test dependency installed in the chosen Python:

```text
python -B tools/verify_current_source.py
python -B tools/verify_korea_garrison.py
python -B -m unittest discover -s tests/current -p "test_*.py"
python -B -m unittest discover -s tests/persia -p "test_*.py"
```

Candidate native build: `tools/build_candidate.ps1`. Its direct Content Editor
flags follow the verified Normal build contract. The Garrison core CLI refuses
run roots nested inside the mod source, so its rejected attempt is preserved in
`evidence/native-cli.log`; the successful direct burn is under `native/`.
`tools/package_korea_110.py` performs the explicit assembly and full readback.
Existing successful outputs are protected from overwrite.

Machine paths stay in ignored local configuration. Native logs, full readbacks,
cache, copied unchanged candidate build inputs and complete delivery archives
are review/build output, not another Git media bank. Promotion is limited to
the reviewed source/tool/test/documentation delta and a deduplicated immutable
compiled-resource/input delta. Keep the existing 1.0.6 art/voice packs unchanged.
The original Normal and Korea donor are not dependencies of an ordinary build.

## Native test checklist before acceptance

1. Import the candidate ZIP through Garrison and select both its Game Mode and
   Tuning Pack. Test all three human selection pairs together, original choices,
   timeout, disconnects, AI retention and command release.
2. Choose Korea as Zhu Xi. Check starting conversion, resources, sheep, Literature
   income/cost icons, research, transformations and naval production. Stock Zhu
   Xi and Byzantines must retain their own economy and purchases.
3. Check one-builder House 15s and Mill 20s, Feudal landmarks 190s, Castle 220s and
   Imperial 250s; then test multiple builders and both landmark alternatives.
4. Check both Castle landmarks without a fatal modifier error. The Observatory
   adds four distinct eligible offers and two allowances only once. With the
   initial two allowances unspent, four purchases can be pending; a fifth blocks.
   Cancellation refunds once; completion rebates only the Literature paid.
5. Ruin/repair landmarks, including the Observatory, Seowons and defense rewards.
   Ongoing effects pause/resume and initial rewards do not repeat. Check the
   25%/40% scholar bonuses, Hangul gold and simultaneous decrees.
6. Target Hwacha and Keep barrages repeatedly. Check no random later ground shot,
   target cleanup, normal firing recovery, new player orders, ruin and capture.
7. Play two Koreans alongside Vietnam, Persia, Zhu Xi and Byzantines. Test Korean
   movement near Flooded Citadel, existing art/voices and longer matches.
8. Measure frame-time/VRAM under matched settings before claiming performance
   acceptance. Korean models and their separate future asset budgets are deferred.

## Final package receipt

Verified candidate: `output/current/community_civilization_pack-1.1.0.zip`.
ZIP: **480,999,265 bytes**; incremental compressed increase over accepted 1.0.6:
**4,255,566 bytes**. SGA: **991,518,614 bytes**. The full ZIP stays below the
600,000,000-byte cap, leaving **119,000,735 bytes** for later work.

ZIP SHA-256: `f3c51cdf8060b69cb0c936703e6e8d92ec202d6e46f92918c048aa4340fcf344`.
SGA SHA-256: `80d8e008e9320232d4b8d56072c5fa6cc1040a4f3df526b63541dd4b8f60b4eb`.

Full fresh readback: **14,103 members**, **425 additions**, **five replacements**,
**13,673 byte-identical original members**, no deletions, with original mounts
preserved. All **1,337 serialized PBG identities** are collision-free and
**6,039 private references** resolve. All 27 construction repairs match native
readback; Literature storage is 100,000 and the stock action cap remains two.

Korean-exclusive native members total **12,872,448 stored/decoded archive bytes**.
All 33 icon stream tables and native mip records validate: **2,901,504 decoded
native mip payload bytes**, or **11,606,016 RGBA8-equivalent bytes** for the
recorded one-mip icons. The installed full DDS exporter rejects their UI internal
format 28; no format mapping is guessed. These byte counts are not a live VRAM
measurement. See `KOREA_110_BUDGET.json` for source bytes and complete budget limits.
No new geometry is included; existing 1.0.6 geometry/material/texture/audio member
hashes remain identical. Korean model and performance acceptance come later.

Normal and permanent Garrison source inventories, clean Git states, project
identity and the original 1.0.6 ZIP hash were rechecked after assembly. They are
unchanged. `promotion/plan.json` will identify the exact small source and immutable
input delta for owner review; no transfer is implied by preparing that packet.
