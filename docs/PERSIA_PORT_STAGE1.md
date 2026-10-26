# Persia port: stage 1 native conversion test

This is the first handoff in the approved staged port. The shared selection and
conversion test are implemented in editable Normal source. **The complete Persian
civilization is not installed yet.** Full roster integration, Persian economic
and military effects, Gundeshapur and landmark lifecycle fixes follow successful
native acceptance of this test.

## What this test establishes

- Chinese humans choose China/Vietnam and Delhi humans choose Delhi/Persia
  (conversion test). Each player has one irreversible choice during one shared
  30-second window. Unanswered and disconnected slots keep their original choice;
  AI keeps its original civilization. Selection closes early when everyone answers.
- The probe converts one native Delhi capital, six villagers and one scout to
  six private current-official child definitions. Both entity and squad
  blueprints are converted and checked. Future Town Center villagers/scouts and
  Town Centers built by private villagers use the private definitions too.
- Native Delhi builder menus, research, abilities, art and voices are inherited.
  Their retention after conversion is an engine test, not established by Lua mocks.
- Default and campaign extension overrides use the exact current native item
  identities. The Content Editor DLL allocated six new collision-free PBG IDs.
- Startup resources match both source Persia and current official Delhi:
  200 food, 200 wood, 100 gold, 0 stone. No resource grant/reset or sheep spawn
  occurs, so lobby resource settings and ordinary map sheep remain intact.
- Conversion is preflighted before mutation. A rejected preflight leaves Delhi;
  a partial conversion is logged and displayed as a failure, never represented
  as untouched Delhi. The shared command hold and temporarily disabled AI are
  released. Lua errors are handled; native engine crashes cannot be caught here.

## Build and native acceptance

Use standard fresh Dark Age matches with the normal resource preset. Nomad,
later-age starts, save/load and Persian AI are deferred. This probe is for
qualification; choose ordinary Delhi for ordinary Delhi play.

1. Reload `Vietnam_v2.aoe4mod` in Content Editor so it notices the six new
   instances and three SCAR modules. Build through the existing supported
   `tools/build.ps1` helper, or the editor's normal workflow. Keep the full burn
   log and verify actual completed compilation. No build has been run by Codex.
2. Check that the resulting SGA's archive name is
   `a743d7d1d7534cf78817e29d8ded7366`. The existing project, burn project, mode
   RDO, tuning linkage and all opaque RDO IDs remain unchanged. Source identity
   validation is not compiled-archive proof.
3. Select this combined game mode and its matching tuning pack. Put Chinese
   and Delhi humans together, with ordinary AI opponents. Choose Vietnam for
   the Chinese player and Persia (conversion test) for the Delhi player.
4. Confirm the common countdown, early completion and release of commands/AI.
   Repeat choosing China/Delhi, letting both slots time out, and with multiple
   Delhi humans choosing different options. Exercise teams, FFA and a multiplayer
   client as well as host. A disconnect must not hold everyone indefinitely.
5. For the Persia test, inspect the starting capital, six villagers and scout;
   retain `warnings.log` containing `PERSIA_PROBE_INIT_APPLIED` and
   `PERSIA_PROBE_ACTIVE`. Train a new villager and scout. Check that both old
   and new villagers can gather, construct the same native buildings, and use
   the same menus. In a subsequent age, build another Town Center and train units.
6. Check Town Bell/garrison/return-to-work and native research such as
   Wheelbarrow, including units already present and units trained afterward.
   Compare native Delhi research prices/times and Scholar influence with an
   unconverted Delhi player. This deliberately tests inherited Delhi behavior;
   it does not yet test Persian dynasty or Divan effects.
7. Verify China/Vietnam selection and existing Vietnam mechanics remain intact.
   Ordinary Delhi and AI Delhi must receive no probe units or changes. Confirm
   sheep are not duplicated and starting resources do not change when choosing.
8. On any failure, retain the completed burn log, tested SGA hash and
   `warnings.log`. `CIV_SELECTION_INIT_FAILED ... partial=true` means restart
   that test; the partially changed army is not a valid fallback civilization.

The next stage starts only after these native results are accepted. It ports the
real Persian roster and its dependency closure, preserves source values, applies
the two approved fixes, and presents other tooltip/data conflicts individually.

## Evidence and repeatable source checks

From the Normal root, using the verified bundled Python executable:

```powershell
$python = 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $python -B -m unittest discover -s tests -p 'test_persia_*.py' -v
& $python -B -m unittest discover -s tests -p 'test_selection.py' -v
& $python -B tools/persia_port/verify.py
& $python -B tools/check_extension_inheritance.py --refresh --official-cache work/persia_port_20261026/official-extensions.json --output work/persia_port_20261026/inheritance-after.json
& $python -B 'C:\Users\RS\.codex\skills\modify-aoe4-tuning-packs\scripts\validate_tuning_pack.py' .
```

`work/persia_port_20261026` contains the verified source rollback ZIP, baseline
hashes, editor identity receipt, pinned current official XML and archive hash,
the complete 281-file source dependency/identity inventory, source-check results
and progress ledger. `tools/persia_port/prepare_probe.py` reproduces the probe
from these pinned donors and the preserved identity receipt. It does not perform
the full migration. Do not rerun the identity allocator over an existing receipt.
Requalify the official donors after a game update rather than relying on stale XML.

Current source verification: **40 focused tests passed**, the tuning validator
reported zero errors/warnings, .NET XmlReader parsed all 255 active attribute
files, and refreshed inheritance resolution against 5,758 official blueprints
reported zero errors. Both installed skill self-tests passed. A fresh reviewer
found no important defects in the staged probe.

The historical suite is not green: the diagnostic frozen-source overlay and
current run each executed 856 existing tests with 97 failures, 359 errors and
9 skips. No newly failing test IDs remain after adapting the engine fixture to
load the new modules and scoping the Rice Paddy assertion to Vietnamese farms.
The overlay changes Python source reads/enumeration; subprocesses/native APIs
still see current files. Preserve these diagnostics rather than treating this
comparison as native or complete regression proof.

SCAR static validation reported zero errors and eight reviewed warnings: five
calls through the locally defined selection-table alias, two startup squad
observer/count diagnostics, and one loader-provided `PLAYERS` diagnostic. The
observer is engine-owned and must not be destroyed; starting entities are
validated before conversion. The loader imports `cardinal.scar` first. MCP
reported no missing localization IDs; its unknown names resolve to project
helpers, Lua string operations or comment/parser artifacts. Its low-confidence
entries for entity enumeration and existing message-box calls have exact
official API signatures. These checks do not establish native conversion.

No existing Vietnam attribute instance or Vietnam gameplay module other than the
shared selection policy was changed. The original Persia project and Garrison
were read-only references. Original Persia credits remain Hossein and ChillyEmpire;
their source localization and visuals remain untouched for the later full port.

## Rollback

`work/persia_port_20261026/normal-before.zip` contains the original editable assets,
project, README, tools and tests. Its SHA-256 and each original source hash are in
`baseline.json`. Restore the three changed original asset files and README from
this ZIP, and remove only the six generated `ps_probe_` XML files and the three
new `assets/scar/persia` files listed in `migration-map.json`/`preservation.json`.
Reload the source in the editor before rebuilding. Keep this evidence and the
original package; no cleanup or deletion is part of this handoff.
