# Script development and Script Runner

Read for SCAR diagnostics, generated workspace definitions, next-match Live Reload or 0.1.4 execution inside the current solo match. Reconciled from installed guide pages on 2026-10-11; no new match was run. Use `aoe4-game-mode-skill` for stock SCAR signatures and gameplay implementation.

## Workspace and static diagnostics

**Edit Script** opens the Mod Project's `project/` folder and writes `.luarc.json`, `.zed/` and `.vscode/` settings. Definitions cover Lua 5.3 `.scar` files, installed-game APIs/constants/scripts, generated Garrison fields and typed options. Trust the folder in Zed to enable complete workspace resolution. Blender startup and Edit Script refresh definitions when the game or Garrison changes; an unchanged installation keeps its existing definitions.

The guide's contributor commands run from a Garrison source environment exposing `src.core`; they are not guaranteed importable from the compiled Blender extension alone. Verify that environment or use the installed Edit Script route instead of inventing a `garrison-core` module name:

```powershell
py -3 -m src.core.scar_workspace update
py -3 -m src.core.scar_workspace check '<asset library>/Mods/<key>/project'
```

`update` supports `--watch 300`, `--force` and repeatable `--mods <folder>`. `check` discovers Zed/VS Code's Lua language server or accepts `--language-server <path>`, defaults to Warning, supports `--level Error` and `--json`, and exits 1 when it finds problems. Text diagnostics are `file:line:column: kind: message`. Resolve unknown fields and signatures; cross-file initialization can need an explicit declaration/import. Broad `undefined-global` suppression also hides typos.

Authored logic belongs outside regenerated `scar/<key>/` and `scar/garrison/`. `options.scar` is imported separately by the Game Mode entry; `<key>/garrison.scar` loads the other present helpers. New Script enables a Normal Game Mode; **Open Map Script** creates/opens a Crafted-map script without creating a Game Mode. Loading Game Mode settings does not mutate the project; load again after changing projects. Save records visible inclusion/template/lobby/options/rules together. An edited entry survives template changes until explicit **Regenerate Script** replacement. Legacy entries can retain showcase placement code: remove it deliberately when converting to Normal rules.

Cook checks Garrison imports for missing generated helpers and local project imports for empty files, reporting file/line and preserving the previous archive on failure. Other imports may be stock game scripts, so a misspelled path can still fail only at match loading. Static diagnostics and a cook do not prove runtime behavior.

## Live Reload: next match

Enable **Game Mode -> Scripts -> Live Reload**, save and cook once. Keep `import("<key>/live_reload.scar")` first in the entry. Present authored imports load from the project's `scar/` folder once per new match under the Garrison Steam `-dev` route; editing does not rerun them in the current match. Entry scripts, generated helpers, models/textures and lobby settings still use cooked resources.

Missing/unavailable disk files fall back to cooked/game imports. A present local file with syntax/runtime errors reports the error instead of silently using its cooked copy. Inspect `GARRISON_LIVE_RELOAD`, `GARRISON_LIVE_RELOAD_MISSING` and `GARRISON_LIVE_RELOAD_OFF` markers. Turn Live Reload off and cook before distribution; Package rejects an archive cooked with it on.

## Script Runner: current match

Use matching 0.1.4 components and a freshly cooked Live Reload development archive; older cooked helpers lack the receiver. Launch/import through Garrison and select the intended Crafted Map or Game Mode plus required Tuning Pack in an unpaused solo match. A Crafted map does not require another Game Mode.

Open **Open Script Runner** in Blender or **Developer -> Script Runner** in the client. Select `mod-project.json` and a UTF-8 `.lua`/`.scar` file, which may be outside the project. **Connect to match** must report **Connected to current match** before **Run File**. **Run on Save** watches subsequent settled saves; enabling it does not execute the current file. It reruns only that file, without recursive import reload or a world reset. Scope script execution to the requested development work.

Limits: 64 KiB per file; up to eight returned scalars displayed, strings at most 384 bytes each. Tables/engine objects display by type; ordinary `print` stays in the game's SCAR log. Generated `.garrison-script-runner/` state sits outside `project/source`; exclude it from version control and deliverables.

Each execution reruns top-level code. Remove old event listeners before redefining their callback, then register the new one. Preserve needed state explicitly, such as `MyState = MyState or {}`. Align cleanup lists with periodic rules, event listeners and created resources; inspect protected cleanup failures. Garrison does not remove them automatically.

| Outcome | Required interpretation and next action |
|---|---|
| Syntax error | Whole-file compilation prevents execution, including cleanup; existing match/listeners remain. Watching turns off. Fix and run deliberately before reenabling it. |
| Runtime error | Partial changes may remain; watching turns off. Inspect/clean up the affected state before rerunning. `pcall` cannot recover native crashes or infinite loops. |
| Six-second host timeout | Outcome unknown; connection stops/mailbox clears, without automatic retry. Clearing cannot cancel executing code. Inspect before reconnecting. |
| Pause/stale heartbeat | Watching is disabled when heartbeat becomes stale. Pausing stops the game-time request deadline too. |
| New match/session | Explicit disconnect/reconnect is required. Disconnect clears the mailbox and watching, but does not undo changes. |
| Abnormal client exit | A pending request may still execute; exit the game before resuming when the outcome is uncertain. |

The guide reports two operator-started solo tests of execution, save watching, errors, periodic-rule cleanup, pause/reconnect and new-match refusal, plus a nine-second receiver-stall timeout test. Global-event cleanup has automated coverage; individual event types still require their own validation. These are guide-reported fixtures, not this skill update's runtime proof. Multiplayer is unsupported.

Sources: installed `guide/{script-runner,live-reload,check-your-scripts,write-the-logic,mod-project,lobby-option,release-0.1.4}.html`.
