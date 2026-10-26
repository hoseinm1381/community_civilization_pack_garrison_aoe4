# Trap construction followed by passable conversion

Updated 2026-10-17 to the user's approved two-stage design. This supersedes the
earlier direct pass-through attempts, which failed native construction testing.
Only the normal edition is changed. Build and native testing belong to the user;
no build or package was run for this revision. Earlier native build outputs predate
this revision and must not be used as evidence for it.

## Behaviour

The villager menus still offer the original `vn_building_bambo_outpost_chi` and
`vn_building_defense_outpost_bambo_chi`. Both source actors are byte-identical to
the originals saved before either walkability attempt. They keep their original
infantry/vehicle blockers and simulation boxes during placement and construction.
No villager menus or production references were edited.

On the existing 0.25-second lifecycle tick, a living trap that is no longer under
construction is converted in place with `Entity_ConvertBlueprint` to its matching
`_passable` child. No entity is killed/recreated or force-constructed. Conversion
is attempted only for the original building forms; completed passable forms are
recognised without repeated conversion. Captured private traps use the same scan.

Each passable child inherits the corresponding original actor under this mod's
GUID. Its only gameplay overrides are an empty `impass_ext/block_path` list and
`impass_ext/impass_simboxes/default_simbox=False`, in normal and campaign variants.
Costs, construction time, health, requirements, native targeting/weapons/damage,
research, visuals, selection and Delete are inherited. No copied parallel combat
or art definition can drift independently from the original actor.

The four-second destruction timer recognises both forms. Attack history is sampled
before conversion so an attack observed on the completion tick is not lost if the
conversion clears that native history. Later attacks do not extend the timer.

## Integration and identity

Two passable EBPS children were added under `assets/attrib/instances/ebps/vietnam`.
`assets/scar/vietnam/traps.scar` handles conversion and the existing timer.
`VietnamMode.rdo` adds the two child EBPS precache entries; its existing entries
and object identities remain unchanged. `prematch_precache.scar` was regenerated
from the RDO: 95 private entities and 43 squads. New PBG and RDO IDs came from the
installed editor's headless identity generators with live/historical IDs reserved.
No editor process or native build was required for that allocation. The receipt is
`docs/trap-completion-identity.json`.

## Offline verification

- Tuning validator: 239 instances, zero errors and warnings. External reference
  values remain informational; no unknown engine APIs were introduced.
- SCAR and RDO static checks passed. Both skill fixture self-tests passed.
- Five new completion/lifetime tests failed against the old implementation and
  passed after this change. These use the existing Lua engine fixture and do not
  simulate or prove native collision/construction behaviour.
- Full suite: 64 tests, the same six pre-existing missing-donor-path errors in
  legacy parity tests. No new failures/errors. Those tests were not rewritten.
- Original builder actor byte identity, child-only passage overrides, exact source
  change allowlist, unchanged RDO entries and protected Garrison hashes passed.

Evidence: `output/trap-completion-switch-20261017T113717Z/verification.json` and
adjacent validation/test logs. Source rollback:
`archives/before_trap_completion_switch_20261017T113717Z.zip`. Earlier baselines,
failed candidates and their diagnostic evidence remain retained.

## User-owned native check

Build the normal `Vietnam_v2.aoe4mod` with its current source, then use a fresh match.
For both traps, verify placement, one/multiple villagers building, interruption and
resumption, then movement across the completed trap by friendly/enemy infantry,
cavalry, elephants and siege. Expect `VIETNAM_V2_TRAP_PASSABLE` after completion,
followed by the existing timer/destruction markers only after an attack.
Check conversion preserves current health, ownership, position, selection and
upgrade effects; check Delete and the four-second lifetime. Campaign and multiplayer
behaviour remain native gates. Conversion is documented and used by official SCAR,
but its exact trap collision update and state preservation require this game test.
