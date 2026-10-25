# First runtime mechanics repair — 2026-10-15

## Native evidence and root cause

The user's fresh Vietnam match loaded the mode, completed civilization selection, and reached `VIETNAM_V2_SELECTION_COMPLETE` without a fatal SCAR error. The match then showed four inactive systems: Pho Minh gating/tower timing, traps, Rattan armor, and tunneling.

These systems shared private-blueprint detection based on `BP_GetName(...) == "vn_..."`. Private instances belong to this project's archive namespace, while those comparisons discarded that identity. The absence of all tower/trap/Rattan/tunnel runtime markers after successful lifecycle startup made the shared detection boundary the first confirmed repair point. `blueprints.scar` now resolves each private EBPS by the project GUID and compares the actual blueprint object. It also logs each first resolution for the next native run.

## Repairs

- Tower detection and Pho Minh detection now use archive-owned blueprint objects. A tower's production queue is disabled until a living, completed Pho Minh Tower exists. Regular squads remain shared with barracks/ranges, so no squad-level proximity requirement can accidentally block an ordinary military building near a tower.
- The existing `2/3` production-speed multiplier remains on towers, producing 1.5 times the normal queue duration. SCAR modifiers do not rewrite production-button tooltip times; acceptance must time an actual queue. Tower state changes now emit `VIETNAM_V2_TOWER` markers.
- Pho Minh Tower's root and campaign construction times changed from 380 to 190 seconds, matching One Pillar Pagoda's displayed 3m10s baseline requested by the user.
- Rattan Shields now applies six player-owned `MAT_EntityType` modifiers to the Vietnamese archer, crossbowman, and handcannon EBPS. This official game-mode modifier pattern follows existing units, new units, and normal age-blueprint upgrades without full-army polling or blueprint conversion. It excludes elephants and emits `VIETNAM_V2_RATTAN` when applied.
- Trap identity now uses archive-owned blueprints. Trigger and detonation behavior remains deterministic SCAR: enemies within 4.8 trigger a one-second fuse, units within 6.4 receive 30 damage, upgrades retain the approved range/damage changes, and the trap dies after detonation. Arming and detonation emit separate markers.
- Tunneling now compares the exact private ability blueprint and exact Imperial Citadel EBPS. The previous code passed a plain Lua table to `World_GetSpawnablePosition`, whose official contract requires a `Position`; it now constructs that position with `World_Pos`. The synchronized network callback still validates ownership, source proximity, destination, passability, and cooldown before moving via `Squad_SetPosition`. Request/rejection/success markers identify the next failing boundary if native behavior remains incomplete.

## Evidence boundaries

Official SCAR API/source confirmed the contracts for entity/player modifiers, per-building production queues, blueprint access, modal ability callbacks, synchronized movement, spawnable positions, health damage, relationships, and entity death. Advanced Game Settings supplied a secondary editable-mod analogue for player-owned `MAT_EntityType` ranged-armor modifiers.

The SCAR static validator reports zero errors and five existing selection-core table-method warnings. MCP code checks report no low-confidence API calls; unknown calls are locally defined/imported helpers. Tuning validation reports 235 instances, zero errors, and zero warnings, plus the expected informational count of official/external references not defined inside this pack.

No automated test suite, Content Editor build, package, or native match was run by Codex. The user owns those gates.

Rollback before this repair:

- `../../Vietnam_v2_cleanup_backups/Vietnam_runtime_before_repair_20261015-180517.zip`
- SHA-256: `ad6bb6a799053dba9c7d1ab986dbf1ac4c19c9cd3a2fc30e1c04c594facef19e`

## Next native check

Use a fresh match and preserve `warnings.log`. Confirm the log contains `VIETNAM_V2_BP` records for a built Hideout/trap/Pho Minh/Imperial Citadel. Before Pho Minh completes, the Hideout production queue must be disabled. After completion, time one 15-second regular unit in a military building and the same unit in a tower: the tower queue should take about 22.5 seconds even though its tooltip still shows the squad's base time.

Research Rattan Shields and look for `VIETNAM_V2_RATTAN ... armor=1`; inspect existing and newly trained ranged infantry before and after an age upgrade. For traps, capture whether `TRAP_ARMED` and `TRAP_DETONATED` appear. For tunneling, capture whether the last marker is `TUNNEL_REQUEST`, `TUNNEL_REJECT`, or `TUNNEL ... destination=...`.
