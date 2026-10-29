# Normal loading and Korea repairs — 2026-10-29

Updated the existing Normal source. Garrison, the donor, all 104 existing Persia
edits, package identities and protected build inputs are preserved. No build,
installation, publication, push or deletion was performed.

## Loading from Prepare Persia 1.0.5

Read that chat and the accepted Garrison 1.0.6 source retaining its loading fix,
`assets/scar/ccp/loading_103.scar`. Normal now imports `ccp/loading.scar` before
its three prematch callbacks. Every client checks the complete human lobby roster:
China permits Vietnam, Delhi permits Persia, and Zhu Xi permits Korea. AI alone
does not load a custom family. A missing/incomplete roster conservatively loads
all families and logs the fallback. Selection follows loading, so choosing the
original civilization cannot unload a family already needed for that choice.

Removed 761 unconditional RDO precache entries: 693 entities and 68 squads,
including 583 stock entries and duplicates of Vietnam's private roster. The
PrecacheList wrapper identity, mode entry, options and localization identities
remain. Fifteen shared stock dependencies load once when any family is needed.
Private rosters remain complete. No asset files were deleted. The generator now
reads editable Vietnam definitions rather than recreating an unconditional RDO list.

| Human slots permitting a custom choice | Private requests | Shared requests |
| --- | ---: | ---: |
| None | 0 | 0 |
| China only | 178 | 15 |
| Delhi only | 192 | 15 |
| Zhu Xi only | 151 | 15 |
| All three | 521 | 15 |

These are explicit calls, not transitive native asset loads or resident memory.
`loading-policy.json` retains the original item inventory and identities. Actual
VRAM and frame-time savings require a matching-settings native comparison.

## Literature and native costs

The current official Zhu Xi army stores zero `merc_byz`; the donor stored 100000.
The previous port omitted that required storage change. Native costs still used
the same channel's olive-oil presentation. The owner approved these narrow exceptions:

- Preserve the current official Zhu Xi army except `resource_max_cap/merc_byz`
  becomes 100000. Starting resources and income cap stay unchanged. Ordinary Zhu Xi
  receives no Korean income or purchases.
- Preserve the current official resource definition and its Byzantine variant,
  adding only a `racebps/chinese_ha_01` override for **Literature**, its description
  and book cost icons. Byzantines retain their olive-oil UI and mechanics.
- Use an unused identity already allocated by the installed Content Editor for
  the new UI item. No donor identity is reused.

`korea-shared-resource.json` pins the official structures. Portable checks remove
only the exceptions and verify exact semantic hashes. Income and native costs
use the same resource channel; Hwarang's existing 200 Literature cost is preserved.

The Observatory also grants selected Korean players one reversible +2 action-cap
modifier before its reward. Previously its extra choices could be clamped by
stock Zhu Xi's cap of two. Repair does not repeat the grant. Literature settlement
and the agreed Seowon/Hangul values remain.

## Keep and Hwacha

The donor and initial port deliberately issued a random forced attack six seconds
after Keep activation. Its point was 44–60m away, inside the boosted weapon range.
This directly explains the reported random retarget instruction.

The Keep now uses native Stop at six seconds; both barrage types release their
exact temporary handles at seven seconds. Hwacha uses Stop instead of fake
movement. Per-entity records preserve simultaneous activations. Death, ruin and
ownership changes release their records; the former owner never commands a captured
entity. A new movement order is preserved. Original burst/range values, upgrades
and tuning remain. Stop cannot cancel projectiles already in flight; native final
volleys and restored automatic targeting still need the acceptance test below.

## Translation and source checks

`korea-script-map.json` traces all 32 imported donor scripts, including called
helpers marked old and reasons for omissions. `audit_korea_translation.py` checks
all 378 private definitions, 127446 serialized values and all 91 research routes.
No unexplained differences remain. It separately classifies editor modernization
already present before this repair: 105 redundant legacy tier-requirement lists,
1101 current official defaults, 29 obsolete false fields, and four redundant damage
values inherited from private archer parents. Valid editor changes are preserved.

- Portable verifier: 910 instances, 1213 locale rows, correct Normal GUID.
- **75 maintained tests pass**, including roster gating/fallback, Literature
  storage emulation, Seowon ruin/repair, Observatory capacity, simultaneous barrages,
  death/capture cleanup and movement-order preservation.
- Installed tuning validator: **0 errors / 0 warnings**. Its stock-reference
  summary is informational. Changed direct official references resolve separately.
- Refreshed inheritance: 524 local / 5758 current official, **0 errors**.
- Installed SCAR validator: 17 files, **0 errors / 11 reviewed warnings** concerning
  borrowed engine groups, loader-provided PLAYERS, existing selection aliases and
  an older source index missing official wrapper evidence.
- AoE4 MCP has no unresolved new engine calls after project definitions and
  official usages are resolved. `Player_GetAbilityBPCost` is documented with sparse
  usage evidence; native payment behavior remains an acceptance gate.
- All 104 existing dirty Persia files and all 463 donor assets match their protected
  hashes. Receipts are in ignored `work/korea_repair_20261029`.

The exact donor fixture still exercises the real identity-only repair without
changing numeric gameplay. Live editor schema changes are audited separately.
The asset receipt remains source-only: final SGA/ZIP contribution and measured
runtime residency are unset. No custom 3D assets were added by this repair.

## Native evidence and acceptance — pending

The screenshot and latest warnings log confirm Korea selection and initialization.
That log later reports failure to allocate **7415838759 bytes**, followed by a fatal
exit. It contains no Korean Lua error. A compressed unchanged diagnostic copy is
preserved. This proves a memory failure; it does not establish its cause or prove
that the loading change resolves it.

After rebuilding Normal, use a fresh standard Dark Age match:

1. Check loading with Zhu Xi only, no eligible humans, AI-only eligible civs and
   all three pairs. Verify private models appear after selection.
2. Build a Seowon near resources, wait 15 seconds, and verify Literature rises.
   Check +25%/+40% scholar bonuses, book cost icons, native research payments and
   the 200-Literature Hwarang purchase. Exercise cancel/completion rebates.
3. Keep both initial research choices, build the Observatory and verify four usable
   choices remain stored. Research, ruin and repair without duplicate grants.
4. Activate two Keeps and two Hwachas at different targets/times. Watch all seven
   seconds: no random secondary attack, no lingering boosted range/rate, independent
   reset, normal Keep targeting afterward and new movement orders retained. Repeat
   with a destroyed, ruined or captured caster.
5. Include original Zhu Xi and Byzantines; verify stock resources, production and
   olive-oil UI. Repeat Vietnam/Persia selection and multiplayer.
6. Compare peak/steady VRAM, RAM and frame times under identical settings. Preserve
   fresh logs for any further allocation failure.

No new build, package, native gameplay or performance acceptance is claimed here.
Credits: **hosein81 and chilly5**.
