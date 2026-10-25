# Subscribed UGC SCAR patterns

Use this reference only for discovery when inspecting extracted subscribed mods. Official ScarDoc/API and current official source remain authoritative.

## 2026-07-17 snapshot

- 1,588 `.scar` files were read completely: 589,436 lines and 23,659,775 bytes.
- The corpus contained 1,108 unique content hashes; 480 file instances belonged to 257 duplicate-content groups.
- Files came from 74 subscription directories and 107 archive/project contexts.
- A project-isolated static audit reported 226 errors across 189 file instances and 3,264 warnings. These are review prompts, not runtime verdicts.
- By unique content, the main risks were 145 lifecycle-missing files, 38 cleanup-callback-missing files, 183 cleanup-unproven files, 74 duplicate-function files, 73 temporary-SGroup-lifetime files, and 4 unregistered-network-event files.

Do not aggregate definitions globally across this corpus. Two archives can contain the same helper name with different contracts, and one archive's wrapper cannot validate another archive's call.

## Safe discoveries

Use UGC to locate feature families worth tracing in official source: alternate win conditions, diplomacy, Nomad starts, objective presentation, observer UI, dynamic population, team rules, scenario waves, modifiers, AI hooks, and networked UI actions. Read the complete project context, including imports, data files, registration, restore, and cleanup.

Common static risk families include:

- persistent rules or events without a proven removal site;
- entity, squad, EGroup, or SGroup event registrations omitted from cleanup;
- temporary groups created inside repeated callbacks without destruction;
- UI/network registrations rebuilt on restore without duplicate guards;
- framework callbacks assumed from a different game-mode skeleton;
- copied helper names whose defining file is absent from the same archive context.

The validator recognizes rule/event families for players, entities, squads, EGroups, and SGroups. Keep a cleanup ledger for every registration, including `OnGameRestore` reconstruction and `OnGameOver` removal.

## Resolve apparent unknown calls

UGC often calls official wrapper functions that are absent from the bundled offline API index. Before labeling one invalid, query current official source or AoE4 MCP. During this snapshot, MCP resolved these examples with high confidence:

| Call | Official wrapper source |
| --- | --- |
| `Rule_AddPlayerEvent` | `rulesystem.scar` |
| `Player_GetAllEntitiesFromType` | `player.scar` |
| `Actor_PlaySpeech` | `speech.scar` |
| `Modify_AbilityRechargeTime` | `modifiers.scar` |
| `Rule_EnterProximity` | `rulesystem.scar` |
| `EGroup_CallEntityFunction` | `groups.scar` |

Do not add a call to the official allowlist merely because UGC uses it. Require an exact official definition/import or API record.

## Audit interpretation

- A delimiter/static pass can exclude obvious parse-shape failures; it does not compile SCAR in the engine.
- `lifecycle-missing` may be valid for imported libraries that are not framework entry modules.
- `cleanup-unproven` means the local static analyzer could not connect registration and removal; dynamic naming or framework-owned lifetime may explain it.
- Duplicate functions may be intentional overrides, versioned code, or an actual shadowing defect; inspect call order.
- Duplicate file instances show republishing/forking and must not inflate confidence in a pattern.

Promote a discovered pattern only after official confirmation, project-local dependency tracing, static validation, Content Editor compilation, and the relevant multiplayer/save-restore runtime tests.
