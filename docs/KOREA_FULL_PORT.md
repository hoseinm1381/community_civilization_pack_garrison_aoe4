# Korea source port — 2026-10-29

This records the initial import. The later native feedback and owner-approved
resource exceptions are documented in [the repair report](KOREA_REPAIR_20261029.md).
That report supersedes this document's zero-cap resource caveat and unconditional
prematch loading policy; its current validation count is 75 maintained tests.

Korea joins the existing Normal game mode and tuning pack as a human
**Zhu Xi's Legacy / Korea** opening choice. China/Vietnam and Delhi/Persia use
the same shared 30-second window. Timeout and AI retain the original civilization.
The Normal GUID and archive NiceName remain
`a743d7d1d7534cf78817e29d8ded7366`.

This delivery is editable source plus validation. No Content Editor burn, new SGA,
import ZIP, game installation, multiplayer acceptance or performance acceptance is
claimed. Native checks below remain required.

## Imported behavior and preservation

- 378 private `kr_` tuning definitions, 33 source icons, 91 research routes and
  124 active donor weapon effects. `korea-import.json` records source hashes,
  destination PBG IDs, reference translations and 523 extension identity repairs.
- All new PBG IDs come from the installed Content Editor's UniqueIDGenerator,
  reserving existing destination, donor and current official identities first.
  The donor's 92 colliding PBG values are not reused as destination identities.
- The standalone Korean StandardMode, stock DynastyUI replacement, global
  `merc_byz` resource override and shared Zhu Xi army override are omitted.
  Six unimported historical SCAR files are listed in the migration ledger.
  Helpers labelled “old” that still implemented active research are represented
  in the consolidated routing table.
- Current official Zhu Xi starts with five villagers and an Official. Korea
  converts those six workers into six private Korean villagers; the existing
  scout, sheep and lobby food/wood/gold/stone remain. The legacy six-villager start
  is accepted too. No replacement starting army or duplicate sheep is spawned.
- The donor's capacity of 99 scholars and first-free-scholar token transfer only
  to selected Korean players. Research allowances use a per-player ledger.
  Literature uses the existing per-player `RT_Merc_Byz` channel with a Korean
  display; the global Byzantine resource definition remains stock.
- The 104 pre-existing dirty Persia files and all 463 donor asset files compare
  byte-for-byte with the pre-port hashes. The original binary Git diff is kept in
  ignored `work/korea_port/preexisting.patch`. Garrison was not edited. No
  deliverables, masters, donor files, caches or rollback evidence were deleted.

## Agreed corrections and implementation cleanup

- Seowons retain natural-resource snapshots within 32m, scholars within 16m and
  defense checks within 34m. Every 15 seconds, base Literature gains +25% per
  eligible nearby scholar, or +40% after the corresponding upgrade. Outposts add
  0.75 and keeps 2.5 each per tick. Descriptions now say proximity.
- Initial foreign exchange supplies four unique offers and two research choices.
  A functioning Observatory grants four further unique offers and two further
  choices once. Repair never repeats that grant.
- Native abilities pay Literature. The research ledger records the effective
  paid ability cost, makes only the corresponding queued upgrade free, refunds
  canceled/failed queued research once, and rebates 15% of paid Literature on
  completion while the Observatory functions. Free grants have no rebate.
  The donor's inappropriate food/gold “refund” top-ups were not carried over.
- Arrow Chutes consistently multiplies ordinary archer range by 1.4, including
  Castle Age. Hangul retains its active 2 gold per 6 seconds per nearby scholar.
  The missing naval Extended Lines queue call is repaired.
- Ongoing landmark income, guard spawning/patrol and decree bonuses pause while
  ruined. Completed research, accumulated kills, palace health gains and initial
  reward receipts persist. The active donor's first-eight Stone Pagoda research
  rewards and Jinju's initial eight guards / 12–24 guard limits are retained.
- Temporary effects use exact modifier handles and independent records instead
  of rounded inverse multipliers and shared FIFO callbacks. Decrees retain their
  60-second game-time expiry while a ruin pauses their effect. A repair resumes
  only an unexpired effect. Trident retains its 0.9 movement/acceleration factor
  for six seconds, refreshing one debuff instead of compounding it on every hit.
- One interval services selected Korean players. Lookups and research routes are
  cached; engine-owned squad observers are never filtered or destroyed. Only
  spawned squads are enumerated. Rules, global events, temporary groups, UI and
  stored modifier handles have explicit cleanup.
- A stale guard self-heal reference is updated to the exact current official
  `abilities/always_on_abilities/chinese_ha_01/shaolin_monk_passive_heal_self`.

## Validation and evidence

Run portable checks from Normal:

```text
python -B tools/verify_source.py
python -B tools/check_korea_port.py
python -B -m unittest discover -s tests/current -p "test_*.py"
```

The maintained suite has 64 passing tests, including three-pair selection,
timeouts, wrong choices, AI exclusion, disconnects, missing blueprints, conversion
failure, worker conversion, payment/queue/cancellation handling, two Korean
research states, unique foreign offers, Seowon income, overlapping decrees,
landmark ruin/repair and lifecycle cleanup. An exact 11,565-byte donor fixture
reproduces 11 inherited-extension failures before repair; its repaired counterpart
passes and preserves all numeric gameplay values and enums. Lua 5.1 parses every
Korean module.

The installed tuning validator reports 908 instances, **0 errors / 0 warnings**.
Its informational stock-reference summary is not an error. The separate current
official direct-reference audit resolves every external `instance_reference` in
the imported definitions after the Shaolin path correction. Refreshed inheritance
validation covers 524 local EBPS/SBPS and 5,758 current official records with no
errors, including default/campaign/alternate extension identities.

The installed SCAR validator reports 0 errors and 9 reviewed heuristic warnings
across 14 files. AoE4 MCP checks have no unresolved new engine calls after resolving
project definitions and parser false positives. These are separate evidence. Review
their detailed receipts in ignored `work/korea_port`: pure table-method aliases,
engine-owned group lifetimes, loader-provided `PLAYERS`, and the existing shared
selection wrapper can produce heuristic warnings. Project helpers are resolved
against their definitions/imports, not treated as undocumented engine calls.

Official evidence includes the installed ReferenceAttributes archive (hash in
the migration ledger), official `gameplay/chatcheats.scar` entity-then-squad
conversion, `player.scar` vehicle-cap modifiers, `gameplay/score.scar` upgrade
event ownership, `ai/army.scar` spawned-squad enumeration, and the documented
queue/modifier/UI APIs. MCP's older index supplies API/source corroboration;
current installed archive XML controls native identifiers and inheritance.

`Player_GetAbilityBPCost` and `Player_GetEntitiesEGroup` are documented official
APIs with sparse usage evidence in the bundled index. Their actual engine
behavior is explicitly part of the native checklist, not proven by mocks.

## Asset budget and reproducible migration

`korea-budget.json` records exact source bytes, a source compression proxy and
RGBA8 decoded icon estimates. No custom 3D geometry or textures beyond the PNG
icons are copied; existing stock models remain references. Source compression
does not establish native package size, runtime texture residency or smoothness.
Final SGA bytes, ZIP bytes, incremental compressed contribution, measured VRAM and
frame-time remain unset until an actual build and matching-settings comparison.

The guarded one-time recipes are `tools/import_korea.py`,
`tools/allocate_korea_ids.ps1` and `tools/migrate_korea_behaviors.py`. Ordinary
builds use the imported source and require no Korea donor or migration cache.
The original migration's identity receipt and official snapshot are protected
under ignored `work/korea_port`; do not rerun allocation or the importer over an
already imported project. All used IDs and source hashes also live in the
portable ledger. Refresh the budget with `tools/check_korea_port.py --update-budget`.

## Native acceptance checklist — pending

1. Run the normal build entrypoint with the configured owned Content Editor.
   Retain a completed burn log; then inspect the final SGA namespace, member
   contents and packaged SCAR. A successful source check or process exit is not
   a completed burn. Do not install or publish as part of this source milestone.
2. Import the new candidate when authorized and use Community Civilization Pack
   Normal for both game mode and tuning pack in a fresh standard Dark Age match.
   Select Zhu Xi, test both choices and timeout, and verify AI remains Zhu Xi.
   Repeat China/Vietnam and Delhi/Persia together with the new pair.
3. First Korean smoke: correct TC, six villagers, original scout/sheep and lobby
   resources; construction and age-up menus; ordinary Zhu Xi unaffected. Verify
   Literature is stored despite the stock army's zero `merc_byz` cap, native
   ability costs are paid, and the Korean counter matches the usable amount.
   The donor global resource/army override is deliberately not reinstated as a
   workaround. A carrier/cap mismatch must be investigated from native evidence.
4. Exercise Seowons, the first free scholar, scholar capacity above the original
   limit, proximity income, upgrades, supervision/drop-off behavior, fishing and
   military-ship Literature, research success/failure/cancellation/death, effective
   discounts, and exactly-once completion rebates. Check that Byzantines retain
   their olive-oil resource and UI. The retained 0.84 drop-off adjustment needs a
   native check against current supervision bonuses.
5. Test all land/naval production and age tiers, private weapons, Tiger Hunters,
   Hwarang transformations with health/kill continuity, Trident, Hwacha and keep
   barrages, decrees, markets, foreign technologies and public information panels.
6. Destroy and repair each landmark repeatedly. Verify income/spawns/bonuses pause,
   earned progress persists, grants do not duplicate, and timed effects on two
   Korean players remain independent. Observe native donor aura teardown too.
7. Test two Korean humans plus original Zhu Xi/China/Delhi/Byzantines and Vietnam/
   Persia, observer/local-player UI switching and multiplayer synchronization.
   Measure matching-settings frame-time/VRAM separately. Save/load, Korean AI,
   Nomad and later-age support are outside this milestone.

Credits: **hosein81 and chilly5**. Original Korean author attribution and source
visuals are preserved; the donor remains unchanged.
