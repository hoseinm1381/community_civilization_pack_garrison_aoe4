# Original native trap and tunnel restoration — 2026-10-16

Revision: `20261016-native-trap-tunnel-r1`.

The user explicitly requested the original `Real_Vietnam_1` tuning-pack behavior, replacing the unsuccessful SCAR trap and tunnel implementations. This revision follows that request. The only custom trap behavior is a four-second post-attack lifetime.

## What was restored

- Both private trap buildings have their original root/campaign combat extensions, including the original weapon attachment hardpoints. Only combat extensions were replaced; construction time, cost, visuals, dynasty/influence cleanup, and unrelated building settings were preserved.
- The two active trap weapon records, alarm/projectile dependency references, and native range and Roller reload research match the original source. Existing weapon-entity and projectile dependencies were already present. Original research values and variant differences are intentionally retained, with no new balance adjustments.
- The tunnel ability matches the original native requirements, `shinobi_blink_jpn` activation, and 120-second native recharge. Its existing attachments on private units remain. `tunneling.scar`, its import, and its lifecycle hooks were removed. There is no custom tunnel network protocol, position calculation, or cooldown table.
- Copying into Vietnam v2 requires rebasing private instance references to its GUID/path and retaining its editor-generated PBG/localization identities. These identity adaptations do not change the original gameplay values. The donor project is read-only.
- Trap targeting, firing, damage, projectile/explosion effects, and research are native. The SCAR enemy-radius queries, damage writes, one-second scripted blast, construction shortcut, and diagnostic framework were removed.

## Four-second exception

The existing 0.25-second lifecycle update checks the documented `Entity_IsAttacking(entity, 0.5)` attack-history predicate for completed private traps across all player groups. On the first observation, it stores `World_GetGameTime() + 4` once. Further attacks cannot reset that deadline. `VietnamTraps_Tick(now)` runs once each lifecycle update, independently of player-alive filtering, and kills a still-valid trap at expiry. Capture does not extend its deadline. Dead/deleted entities and entities converted into another blueprint are discarded safely; game-over cleanup clears pending timers.

The API and its parameter types were verified through AoE4 MCP and official `groupcallers.scar`/`syncweapons.scar` usage. This is a native attack-history observation, not a guessed projectile-event context or damage simulator. Deadline processing is quantized to the existing 0.25-second tick; observing an actual attack on these attached-weapon buildings still needs a native check.

## Evidence

- `tests/test_legacy_trap_tunnel.py` compares the original and restored gameplay XML after identity rebasing. Both trap combat variants and five complete ability/weapon/upgrade records match. Timer tests cover both trap types, first/repeated attacks, idle/incomplete traps, capture, deletion, conversion, cleanup, and absence of scripted enemy damage.
- Nine focused tests and the full 59-test offline suite passed. Obsolete tests for the removed SCAR tunnel/blast were replaced with donor-parity and timer tests; dynasty UI and package verification coverage remain.
- Tuning validation: 237 instances, zero errors/warnings. Its informational external-reference count is 1,042, including the restored native state-tree references. SCAR validation has zero errors; remaining warnings are the existing Cardinal `PLAYERS` loader contract and imported selection-core methods. See `native-restore-validation.txt` and `native-restore-mcp.json`.
- `native-restore-audit.json` records donor hashes, affected assets, unchanged non-combat building settings, preserved PBG identity, and CSV row differences. `native-restore-baseline.json` records the rollback ZIP and pre-change hashes. The original project's files were not changed.
- No Content Editor build/package or native match was performed. Offline equality and timer tests do not establish native weapon firing, attack observation, or teleport behavior.

## User-owned build and match

1. Refresh/save and build/package `Vietnam_v2.aoe4mod` in Content Editor. Rebuild the changed weapon/ability data; do not reuse the earlier package. Preserve any Error List rows.
2. Run the existing read-only `tools/verify_runtime_package.py` command from `tools/README.md` / the historical repair report to compare installed SCAR against current source. Expect zero current-source mismatches. This does not inspect compiled tuning stats. An obsolete packaged `tunneling.scar` is unused because the new mode no longer imports it.
3. Start a fresh match, choose Vietnam, and confirm:

```text
VIETNAM_V2_SOURCE revision=20261016-native-trap-tunnel-r1 tunneling=native trap_weapons=native trap_lifetime=4
```

4. Build each trap type. Inspect its original native weapon/attack stats and let it attack an enemy. Expect `VIETNAM_V2_TRAP_DESTROY_TIMER ... seconds=4`, then `VIETNAM_V2_TRAP_AUTO_DESTROY` about four seconds later. Nearby friendly units alone must not start an attack timer. Repeated attacks must not postpone destruction.
5. Test Tunneling using the same native activation/targeting as `Real_Vietnam_1`. The ability's native 120-second recharge should apply; no SCAR tunnel-request or tunnel-movement marker is expected. Test both before/after constructing Imperial Citadel and with its original allowed targets.
6. Recheck the unchanged dynasty UI and construction-time fixes. Preserve a fresh `warnings.log` if native firing, the timer, or tunneling still fails.

No new PBG, RDO, manifest, precache, or unit-roster identity was allocated. No Git repository/commit was created; rollback remains the recorded ZIP. An independent read-only review found no confirmed Important/Critical defects. Its captured-before-observation edge was then reproduced in the actual lifecycle fixture and fixed so that all player groups receive the same private-trap lifetime; the regression failed before the correction and passed afterward.
