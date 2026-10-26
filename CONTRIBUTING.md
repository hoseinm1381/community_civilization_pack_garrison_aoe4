# Contributing to Community Civilization Pack Normal

The `normal` branch contains the editable Content Editor source for Community
Civilization Pack Normal. Work from this checkout. The repository's Garrison
edition has an independent identity and build pipeline.

## Check a clean clone

Python 3.12 is the CI reference version. The source verifier uses only the Python
standard library. Lua-backed regression tests additionally use `lupa`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-tests.txt
.\.venv\Scripts\python.exe -B tools/verify_source.py
.\.venv\Scripts\python.exe -B -m unittest discover -s tests/current -p "test_*.py"
```

On Linux or macOS, use `.venv/bin/python` instead. GitHub Actions runs these same
source and current-test commands on Python 3.12. Historical tests under
`tests/legacy/` preserve earlier mechanics and may require archived evidence or describe
superseded behavior; the maintained portable gate is `tests/current/`. Stage-one
helpers in `tools/persia_port/` are historical migration tools, not current build
or validation entrypoints.

These checks validate editable source and simulated SCAR behavior. A passing run
provides no evidence of Content Editor burn, game import, fresh-match behavior,
save/load, or multiplayer acceptance.

## Build with the owned Windows editor

Install Age of Empires IV and its Content Editor through your own Steam setup.
A clean source clone does not include the game, official archives, editor,
third-party tool installations, or compiled output. Normal requires no Garrison
or Blender installation.

Copy `workspace.example.json` to the ignored `workspace.local.json` and set the
local `editor_root` and `python_path`. Read `tools/build.ps1` for its supported
configuration and parameter overrides. Run it from this checkout, for example:

```powershell
powershell -ExecutionPolicy Bypass -File tools/build.ps1 `
  -EditorRoot "D:\SteamLibrary\steamapps\common\Age of Empires IV" `
  -PythonPath ".\.venv\Scripts\python.exe"
```

The native inheritance preflight must resolve current official parents before a
build. Install its optional decoder using `python -m pip install -r
requirements-native.txt`. After a game update, refresh that evidence with
`python -B tools/check_extension_inheritance.py --refresh`, using the configured
Python and the included read-only archive reader. Record any missing local tool
as a prerequisite failure; do not weaken or bypass the check. The installed
tuning-pack validator is a separate source gate. A native build is confirmed by a
completed burn log, then package/import and native matches are checked separately.

## Make a scoped change

- Preserve the normal project GUID, PBG IDs, RDO IDs, blueprint keys, localization
  IDs and native inheritance unless the task explicitly requires a change.
- Follow effective inheritance through the full private and current official
  parent chains for default and every affected campaign/alternate variant.
- When overriding an inherited singleton extension, retain that variant's native
  `List.ItemID` with matching `List.ParentItemID`. Append only after proving the
  extension absent from the complete effective chain.
- Keep source, current tests, tools and concise documentation together. Add
  meaningful regression coverage for changed behavior and keep historical evidence
  identifiable. Do not edit historical reports to imply current acceptance.
- Keep native editor state, archives, work/output caches, local configuration and
  credentials out of Git. Ignore rules preserve those files locally. Do not force
  add ignored content or delete rollback material as routine cleanup.
- Describe the concrete behavior change, source checks performed, completed native
  gates, and any remaining gates in the pull request.

This repository does not grant redistribution rights for Age of Empires IV or
stock assets. Contributors must use their own required game/editor installation.
