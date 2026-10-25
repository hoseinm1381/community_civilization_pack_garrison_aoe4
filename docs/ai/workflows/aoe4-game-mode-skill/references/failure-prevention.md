# Failure-prevention and validation gates

## Contents

1. Crash and desync risks
2. Implementation gates
3. Engine test matrix
4. Completion standard

## Crash and desync risks

Audit these risks explicitly:

1. Unknown calls or guessed signatures.
2. Imported wrappers whose defining module is missing or loaded too late.
3. Nil/invalid players, entities, squads, blueprints, groups, or event fields.
4. Repeating rules registered more than once.
5. Global events, timers, UI, objectives, groups, or modifiers left alive after game over.
6. Additive modifiers applied on every scan and stacking without a cap or removal.
7. UI callbacks mutating simulation state without a registered network event.
8. Local-player state affecting spawn, resources, ownership, victory, or random order.
9. RDO option keys or enum values that do not match SCAR accesses.
10. Global helper names colliding with imports or another mode.
11. Delayed callbacks retaining an entity that has since died, packed, unpacked, or changed owner.
12. Empty groups or zero-player cases followed by index access.
13. Save/restore re-registering serialized rules or failing to rebuild local UI/network bindings.
14. Tuning/blueprint identifiers absent from the active package.
15. Temporary groups returned by `Player_GetSquads` and never destroyed.
16. `SGroup_Count` used where despawned squads must not count.

## Implementation gates

Pass these gates in order:

### Gate 1: Project and dependency inspection

- Read the target file, entry RDO, all imports, helper definitions, and call sites.
- Inspect current worktree changes and preserve unrelated user edits.
- Run `$skillRoot\scripts\analyze_scar_corpus.py` when the project has unfamiliar SCAR modules.
- Treat `--project-root` symbol discovery as existence evidence only. A definition elsewhere in the project does not prove the target imports it; verify the actual import/loader chain.

### Gate 2: Official evidence

- Select two to four official analogues.
- Confirm each engine call in the API and official usage.
- Confirm constants, event fields, and blueprint identifiers.
- Label unofficial-only dependencies in the implementation notes.

### Gate 3: Static validation

Run:

```powershell
& $python "$skillRoot\scripts\validate_scar.py" path\to\mode.scar --project-root path\to\project
& $python "$skillRoot\scripts\validate_scar.py" path\to\mode.rdo
```

Resolve errors. Investigate every warning; suppress nothing merely because an official file also contains the pattern.

### Gate 4: AoE4 MCP validation

- Run `scan_project` or `inspect_project_layout`.
- Run `check_code` with the complete final SCAR text and target path.
- Remove locally defined functions from the MCP unknown list only after matching their exact definitions; `check_code` can report draft-local functions as unknown.
- For every remaining unknown or low-confidence call, run `inspect_symbol` and `api_context`.
- Run `find_base_data` for every new hard-coded entity, squad, weapon, ability, or upgrade identifier.
- Inspect modifier property strings and wrapper implementations manually; `check_code` does not validate those contracts.
- Trace network and delegate events when touched.
- Explain RDO config/options when touched.

### Gate 5: Content Editor and package validation

- Compile/validate SCAR in the AoE4 Content Editor.
- Confirm the RDO points to the packaged SCAR entry.
- Confirm locdb and tuning dependencies.
- Verify no duplicate module/global names are loaded.

### Gate 6: Runtime validation

Static checks cannot prove engine safety. Launch real matches and inspect the game log.

## Engine test matrix

At minimum test:

| Scenario | Required checks |
| --- | --- |
| 1 human player | initialization, empty-enemy behavior, no index failures |
| 2 human players | victory path, defeat path, UI for both peers |
| Human plus AI | AI ownership, event contexts, team logic |
| Teams | ally/enemy filters, shared vision/diplomacy assumptions |
| FFA | no fixed-team assumptions |
| Nomad if supported | no early town-center/landmark assumptions |
| Save and restore | no duplicate rules/events; UI/network restored |
| Surrender/drop | cleanup and winner resolution |
| Long match | no accumulating rules, groups, UI, or modifiers |
| Every RDO option branch | valid defaults, enum handling, interaction effects |

## Completion standard

Do not say a mode "will not crash" or "always works." Report evidence precisely:

- static validator result;
- AoE4 MCP unknown/low-confidence result;
- Content Editor compile result;
- runtime scenarios actually tested;
- remaining untested engine, package, or multiplayer risks.

A robust delivery has no unknown calls, no unresolved lifecycle resources, no option mismatches, and at least one real engine smoke test. Multiplayer claims require a multiplayer test.
