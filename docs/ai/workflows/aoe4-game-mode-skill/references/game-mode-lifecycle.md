# Game-mode lifecycle and multiplayer contract

## Contents

1. Module structure
2. Lifecycle phases
3. Cleanup ledger
4. Multiplayer synchronization
5. Defensive SCAR patterns

## Module structure

Use one unique module name and prefix its globals and functions consistently. Official game modes register a module with `Core_RegisterModule("ModuleName")`, then expose callbacks named with the same prefix.

Keep import order intentional. `standard_mode.scar` registers `StandardMode` before importing `gameplay/vision.scar` so setup callback order is correct. Do not reorder imports until module registration and delegate dependencies are understood.

Separate state from behavior:

- Store module state in one prefixed table such as `_example_mode`.
- Initialize option tables to `{}` before `Setup_GetWinConditionOptions`.
- Keep temporary groups local and destroy them after use.
- Keep persistent group, timer, modifier, UI, objective, and rule handles in module state so cleanup can find them.

## Lifecycle phases

### `Module_OnGameSetup`

Use this phase for configuration that must be known before simulation initialization:

- Call `Setup_GetWinConditionOptions(state.options)`.
- Read start-condition flags such as Nomad.
- Unregister optional win-condition modules according to RDO options.
- Derive immutable settings and defaults.
- Guard every optional section and option before indexing it.

Avoid spawning, mutating player armies, or creating local UI here unless official evidence for the exact operation shows it is safe.

### `Module_PreInit`

Use only when an official analogue requires work before other module `OnInit` callbacks. It is optional.

### `Module_OnInit`

Use this phase to initialize match state before control reaches the player:

- Resolve player/team tables and validate handles.
- Register network events before any UI can call them.
- Register global events and construct persistent data contexts.
- Call framework delegates such as `DiplomacyEnabled` only when the imported modules expect them.
- Create UI only for local presentation; keep simulation state global and deterministic.

### `Module_Start`

Use this phase for gameplay that begins after initialization:

- Spawn initial mode objects.
- Create objectives.
- Start recurring or delayed rules.
- Apply start-state changes that depend on fully initialized players and entities.

Make start logic idempotent or explicitly guard it. Save/load and restore paths can re-enter parts of the lifecycle.

### `Module_OnGameRestore`

If the mode supports restore, re-register ephemeral network/UI bindings and rebuild non-serialized presentation state. Re-register a network event only when official evidence proves the registration is required and idempotent, or when a verified existence/state guard prevents duplication. Do not duplicate persistent simulation rules that were serialized.

### `Module_OnGameOver`

Remove everything the module registered or created:

- `Rule_RemoveGlobalEvent` for every global event callback.
- `Rule_Remove` or self-removal for every recurring rule.
- UI, objectives, timers, temporary markers, and persistent groups.
- Reversible modifiers when the API and design require removal.
- Simulation subsystems initialized by the mode.

`Core_OnGameOver` is the framework transition that invokes module cleanup. Do not directly bypass it when declaring a winner.

## Cleanup ledger

Maintain this table while implementing a mode:

| Resource created | Creation site | Stored handle/callback | Removal site | Re-entry guard |
| --- | --- | --- | --- | --- |
| Global event | `OnInit` | callback function | `OnGameOver` | `Rule_Exists` or state flag |
| Interval rule | `Start` | callback function | callback or `OnGameOver` | state flag |
| One-shot rule | any safe phase | callback | normally expires | prevent duplicate scheduling |
| EGroup/SGroup | helper | group id | same helper or `OnGameOver` | create unique/local |
| Timer | `Start` | timer name | `OnGameOver` | `Timer_Exists` |
| Objective/UI | `Start`/`OnInit` | handle/name | `OnGameOver` | nil/name check |
| Modifier | helper | exact modifier/target | explicit removal if temporary | applied-state table |

Do not accept a mode as complete until every row has a removal or a documented engine-owned lifetime.

## Multiplayer synchronization

- Treat UI callbacks as local. Send simulation-changing choices through a registered `Network_CallEvent` path; official `combat_mode.scar` documents this explicitly for its surrender button.
- Register the network event before the UI becomes interactive. Re-register it in restore only if official behavior requires that.
- Do not use `Game_GetLocalPlayer()` to choose a simulation owner, grant resources, spawn units, or decide victory.
- Use local-player checks only for presentation such as UI, event cues, selection, and camera behavior.
- Use deterministic engine random functions and the same call order on every peer. Do not mix local input or wall-clock state into simulation decisions.
- Validate player and entity ownership from event context before applying a mutation.

## Defensive SCAR patterns

- Check `entity ~= nil` and `Entity_IsValid(entity)` before delayed entity access.
- Resolve a player with `Core_GetPlayersTableEntry` and verify it is non-nil before reading its fields.
- Guard zero-player and empty-group cases before index access.
- Use one-based player indices; reject `World_GetPlayerAt(0)`.
- Destroy temporary EGroups/SGroups after iteration.
- Do not modify a group while iterating it unless official usage proves the operation is safe.
- Pass callback data explicitly to delayed rules; revalidate handles when the callback runs.
- Prefer a state flag over repeatedly registering the same rule from a recurring event.
- Prefer setting a modifier to a known target state over applying additive modifiers on every scan.
- Namespace all global helpers. Use `local function` for helpers that do not need framework visibility.
