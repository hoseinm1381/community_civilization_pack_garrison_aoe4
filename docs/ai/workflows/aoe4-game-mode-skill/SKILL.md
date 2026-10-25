---
name: aoe4-game-mode-skill
description: Create, extend, debug, review, and validate Age of Empires IV match-time SCAR code, game-mode RDO configuration, and connected localization CSVs. Use when Codex needs to implement or repair .scar modules, custom game modes, win conditions, lobby options, RDO/CSV integration, rules and events, entity or squad mechanics, multiplayer network callbacks, UI data contexts, imports, cleanup, or unknown SCAR helpers. Prioritize official ScarDoc APIs and official source; treat unofficial examples as secondary evidence.
---

# AoE4 Game Mode SCAR

Produce conservative, official-first SCAR that is explicit about unresolved engine contracts. Never infer an AoE4 API from its name.

## Scope boundaries

- Match-time `.scar`, game-mode/win-condition RDO, events, networking, and simulation/UI integration belong here.
- `.aoe4mod`, `assets/attrib`, `assets/mod.rdo`, locdb, PBG IDs, and Attribute Editor data belong to `$modify-aoe4-tuning-packs`.
- Generated-map terrainlayout Lua belongs to `$create-aoe4-skirmish-map`.
- For a mixed task, assign each file to one owner skill and validate the handoff between them; do not put terrainlayout code in SCAR.

## Route generated-map starting-economy reports

When a user reports starting gold, stone, berries, wood, sheep, or straggler trees as missing, intermittent, duplicated, or too far from the Town Center, do not add a match-time SCAR workaround unless the user explicitly requests dynamic post-start spawning.

Route the terrainlayout Lua to `$create-aoe4-skirmish-map` and player-start terrain/distribution XML to `$modify-aoe4-tuning-packs`, then classify the defect before editing:

- If the entity reliably materializes but its distance varies too far, inspect the Lua candidate planner and every fallback. Give each required resource an explicit maximum TC distance, keep one selected marker for exact-one resources, and validate the joint gold/stone/berries/wood plan rather than moving one resource in isolation.
- If sheep or stragglers are defined in XML but absent in-game, verify `is_player_start`, the terrain's `local_distributions` reference, archive-GUID qualification for project-owned instances, and whether the tested SGA contains the current XML.
- If Lua writes the expected terrain marker but the entity or forest is absent, investigate local-distribution footprint clearance, TC/building overlap, map-edge clearance, neighboring reserved footprints, and stale packaging. Do not treat marker counts as proof of runtime materialization.
- Keep one owner per resource category. A proven pattern is Lua-owned exact minerals, berries, and wood combined with XML-owned sheep and stragglers; attaching a second distribution while retaining explicit Lua markers can create duplicates.
- Preserve already-approved resources and topology while tightening one resource. On a 20-meter coarse grid, a 2.5-cell maximum admits two-cell and `sqrt(5)` offsets while excluding `sqrt(8)` and three-cell fallbacks; treat this as a project example, not a universal distance.

Validate every supported size, player count, teams/FFA/random-position branch, and Classic/Nomad path. Rebuild the package, compare packaged sources with editable sources, and inspect multiple in-game seeds before declaring the issue solved.

## Command root

Set `$skillRoot` to the directory containing this installed `SKILL.md` and `$python` to an absolute, verified Python interpreter path. In Codex desktop, resolve the bundled interpreter through workspace dependencies. Do not assume `py -3` or `python` is usable until its version command succeeds.

```powershell
$skillRoot = "<path-to-aoe4-game-mode-skill>"
$python = "<absolute-path-to-working-python.exe>"
& $python "$skillRoot\scripts\validate_scar.py" path\to\mode.scar --project-root path\to\project
```

## Follow the required workflow

### 1. Establish the real integration surface

Read the target `.scar`, its `.rdo` entry/config, every imported project helper, all call sites of functions being changed, and relevant package/locdb data. Inspect current user edits before modifying anything.

For a new mode, identify:

- module name and deployed SCAR path;
- RDO entry and option keys;
- required official gameplay modules;
- players, teams, FFA, AI, Nomad, save/restore, and multiplayer scope;
- simulation state versus local presentation state;
- every persistent rule, event, group, timer, objective, UI element, and modifier.

Do not implement until the lifecycle and entry path are clear.

### 2. Load only the needed references

Read [source-policy.md](references/source-policy.md) for every task.

Read these direct references as applicable:

- Game mode, win condition, persistent events, or networking: [game-mode-lifecycle.md](references/game-mode-lifecycle.md)
- RDO/options/localization/tuning: [rdo-and-options.md](references/rdo-and-options.md)
- Safe RDO/CSV editing or repair: [rdo-csv-editing-and-repair.md](references/rdo-csv-editing-and-repair.md). Read it before any direct RDO or localization CSV edit, including a one-row change.
- Official analogue selection: [pattern-catalog.md](references/pattern-catalog.md)
- Subscribed UGC discovery patterns and audit caveats: [subscribed-ugc-patterns.md](references/subscribed-ugc-patterns.md)
- Final risk audit and engine tests: [failure-prevention.md](references/failure-prevention.md)
- Full supplied-corpus coverage: [corpus-manifest.md](references/corpus-manifest.md)

Search large references instead of loading them wholesale:

```powershell
rg -n "^SymbolName\(" references/Essence_ScarFunctions.api
rg -n "\bCONSTANT_NAME\b" references/Essence_Constants.api
rg -n "^SymbolName\t" references/scar-symbol-provenance.tsv
```

### 3. Select official analogues

Choose two to four complete official files that match the requested geometry, lifecycle, event, or objective pattern. Read complete functions plus their imports and cleanup callbacks. Prefer a narrow official analogue over a broad unofficial mode.

Use unofficial code only to discover an idea or project-specific integration pattern. Trace its full dependency graph and re-prove every external call against official evidence.

### 4. Verify every engine contract

When the AoE4 MCP is available:

1. Run `doctor` when readiness is unknown.
2. Run `scan_project` or `inspect_project_layout` on the current mod.
3. Use `find_api` or `api_context` for exact signatures.
4. Use `find_usage` for official call shape and lifecycle context.
5. Use `inspect_symbol` for an unfamiliar helper.
6. Use `find_module` for imported wrapper ownership.
7. Use `trace_network_event`, `trace_delegate`, or `trace_event` when changing synchronization.
8. Use `explain_rdo_config` and `explain_rdo_options` for RDO work.

Require at least one official API/source record for each new engine call. Require the defining file and import for each Lua wrapper. If neither exists, report the symbol as unresolved rather than writing a guessed fallback.

### 5. Design lifecycle and cleanup before code

Use the registered module prefix for framework callbacks. Place work in the earliest valid phase, not simply `OnInit`:

- `OnGameSetup`: options and module selection;
- `PreInit`: only proven pre-initialization dependencies;
- `OnInit`: player/team state, event/network registration, presentation initialization;
- `Start`: objectives, spawns, and active gameplay rules;
- `OnGameRestore`: rebuild non-serialized UI/network state without duplicating simulation state;
- `OnGameOver`: remove or shut down everything registered or created.

Build a cleanup ledger using [game-mode-lifecycle.md](references/game-mode-lifecycle.md). Do not leave a persistent resource without a removal site or a documented engine-owned lifetime.

### 6. Implement the smallest complete change

For a new mode, copy [game-mode-skeleton.scar](assets/game-mode-skeleton.scar), replace both example namespaces, then add only verified imports and behavior.

Apply these constraints:

- Prefix global state and framework-visible functions with the unique module name.
- Use `local function` for private helpers.
- Guard optional RDO sections, enum items, player records, and delayed entity handles.
- Keep simulation changes deterministic and independent of `Game_GetLocalPlayer()`.
- Route local UI actions through registered network events before changing simulation state.
- Prevent duplicate rule/event registration with a state flag or proven existence check.
- Avoid repeated additive modifiers; track application state and reversal explicitly.
- Destroy temporary EGroups/SGroups and clean persistent ones.
- Preserve current project behavior and user changes outside the requested scope.
- Keep terrain-layout Lua separate from match-time SCAR.

Do not hand-write opaque RDO object IDs. Prefer Content Editor output and patch only understood fields.

When an RDO or localization CSV is malformed, do not patch symptoms in SCAR. Follow [rdo-csv-editing-and-repair.md](references/rdo-csv-editing-and-repair.md), establish a parseable baseline, repair localization before references, preserve editor-generated identity, and validate the RDO/CSV/SCAR contract together.

### 7. Validate in layers

Run the bundled static validator on each edited file:

```powershell
$skillRoot = "<path-to-aoe4-game-mode-skill>"
& $python "$skillRoot\scripts\validate_scar.py" path\to\mode.scar --project-root path\to\project
& $python "$skillRoot\scripts\validate_scar.py" path\to\mode.rdo
```

For an unfamiliar corpus, build a provenance digest:

```powershell
$skillRoot = "<path-to-aoe4-game-mode-skill>"
& $python "$skillRoot\scripts\analyze_scar_corpus.py" path\to\corpus --json report.json --markdown corpus-manifest.md --symbols symbols.tsv
```

Confirm the generated UTC timestamp, source root, file counts, and hashes before relying on a cached manifest or symbol index.

For a UGC or multi-project corpus, audit each archive/project context separately so one mod's definitions and imports cannot satisfy another mod's calls or lifecycle:

```powershell
& $python "$skillRoot\scripts\audit_scar_corpus.py" path\to\corpus `
  --symbol-index "$skillRoot\references\scar-symbol-provenance.tsv" `
  --json scar-audit.json
```

Deduplicate findings by content hash when estimating distinct defects, but preserve every file instance for provenance. Treat lifecycle and cleanup diagnostics as static risks until the target framework's entry contract is confirmed.

Then run AoE4 MCP `check_code` with the complete final SCAR text and target file. Investigate every unknown or low-confidence result. Run Content Editor compile/package validation and a real match smoke test when the environment permits.

Run the bundled smoke test before delivery:

```powershell
& $python "$skillRoot\scripts\self_test.py"
```

Compare MCP unknown calls with exact local function definitions before treating them as missing APIs; draft-local functions can be reported as unknown. Validate hard-coded blueprint/weapon/upgrade names separately with `find_base_data`, and inspect modifier property strings manually because `check_code` does not prove either contract.

Static validation and MCP evidence do not prove engine or multiplayer behavior. Follow the runtime matrix in [failure-prevention.md](references/failure-prevention.md).

## Use source confidence explicitly

Classify important decisions in working notes:

- **High**: official API plus compatible official usage.
- **Medium**: official source wrapper with verified definition/import but no API entry.
- **Low**: unofficial implementation or usage-only record.
- **Unresolved**: no exact definition/signature/contract.

Do not ship unresolved calls. Do not silently upgrade low-confidence evidence.

## Deliver with evidence

Report:

1. files changed and integration points;
2. official analogues used;
3. APIs/wrappers verified and any low-confidence dependency retained;
4. cleanup and multiplayer strategy;
5. static, MCP, Content Editor, and runtime results separately;
6. untested engine scenarios or project-data dependencies.

Use this evidence ledger for every delivery: `official/API`, `official usage`, `project definitions/imports`, `unofficial evidence`, `unresolved contracts`, `static result`, `MCP result`, `Content Editor result`, and `runtime scenarios`.

Never promise that SCAR "cannot crash" or "always works." State exactly which gates passed and what still requires in-engine proof.
