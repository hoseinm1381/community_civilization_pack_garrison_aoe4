# Second user-operated run: entity ID contract repair

2026-10-14. User reported a clean Content Editor error list (zero errors, zero warnings) followed by a fatal SCAR pause at match start. Codex inspected the log and edited source only; no builds or tests were executed.

## Exact failure

Game warnings.log at 20:10:15:

```text
Invalid parameter 1 (type expected=unsigned int, received=table) in function Entity_IsValid
Lua VietnamMode.scar Ln 52 (holdMatch)
Lua VietnamMode.scar Ln 188 (func)
Lua Core.scar Ln 153
```

The stack establishes that initialization ran, a Chinese human was eligible, and the four qualified private-blueprint checks passed. The failure occurs in the opening hold before popup presentation. The earlier namespace repair therefore advanced the runtime path; it does not establish successful selection or conversion.

## Root cause and source repair

`EGroup_GetEntityAt` supplies a SCAR entity handle. `Entity_IsValid(Integer id)` accepts the numeric world ID instead. Our opening hold, conversion checks, and cleanup incorrectly treated these as the same representation.

- Obtain IDs through documented `Entity_GetID(entity)` before immediate validity calls in the hold and initializer.
- Store `entityID` with the original health cap for delayed cleanup. Validate that ID, then resolve `Entity_FromID(entityID)` before restoring the cap. Destroyed entities are skipped without dereferencing a stored handle.
- Preserve handles for APIs whose signatures actually require entities, including blueprint conversion and health-cap changes.
- Focused read-only review also identified the adjacent ownership precondition: `Entity_GetPlayerOwner` must not be called for World-owned entities. The hold now enumerates each player's entities directly through `Player_GetEntitiesEGroup`, avoiding the global scan and unsafe ownership query. Each temporary group is destroyed within its iteration.
- Correct the mock's previously permissive validity function to reject non-numeric IDs. Add a source regression case for an entity destroyed before cleanup. Neither updated tests nor gameplay were executed by Codex.

Official evidence: installed ScarDoc `Entity_GetID(EntityID entity)`, `Entity_IsValid(Integer id)`, `Entity_FromID(Integer id)`; AoE4 MCP official `entity.scar` stores `Entity_GetID` and validates the stored numeric ID, and `core_objectives.scar` validates an ID before `Entity_FromID`. Berber source also uses `Entity_IsValid(Entity_GetID(entity))`; it remains unchanged.

## User verification

Reopen, save, and build the edited source. Repeat the same China-human match with the matching mode and tuning. Confirm whether the match now reaches the popup/countdown without a fatal pause, then choose Vietnam and check unlock and villager production. Send the new warnings.log if a runtime error remains. Popup behavior, conversion, independent production, and multiplayer coexistence remain pending.
