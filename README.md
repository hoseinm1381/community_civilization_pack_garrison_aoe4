# Community Civilization Pack — Garrison

Current functional release: **0.9.0 — Persia and Vietnam**.

[Download 0.9.0](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/releases/download/v0.9.0/community_civilization_pack-0.9.0.zip) · [Patch notes](docs/RELEASE_090.md)

- Select China in the lobby: choose China or Vietnam at match start.
- Select Delhi Sultanate: choose Delhi or Persia.
- One shared 30-second deadline; timeout keeps the original civilization.
- Use standard Dark Age human starts. AI remains native.
- Persia currently uses its existing stock visuals. Complete Persian art is the next milestone.

Develop exclusively in `F:/aoe_4_temp/community_civilization_pack_garrison_aoe4` on `main`. Use Git for source history; keep
required art/audio/compiled-resource inputs in the existing compact store.
Do not create a workspace or full source copy for each version.

Run `python -B tools/verify_current_source.py` and
`python -B -m unittest discover -s tests/persia -p "test_*.py"`.
The Lua tests need the pinned `requirements-tests.txt` dependency. Install it
under `F:/aoe_4_temp/Temp_before_github_push/test-python` with pip `--target`,
and set `PYTHONPATH` to that directory for the test run. It is disposable after
the confirmed push; native build/package tools themselves use standard Python.
Native builds and final selective assembly are separate from source checks.
See [current implementation and evidence](docs/CURRENT_WORK.md),
[Persia delivery and acceptance](docs/PERSIA_GARRISON.md), and
[agent instructions](AGENTS.md).

Independent build: configure `workspace.local.json` from `workspace.example.json`,
then run `python -B tools/compact/github_build.py native` and
`python -B tools/compact/github_build.py package`. All scratch work uses
`F:/aoe_4_temp/Temp_before_github_push`; remove it after a confirmed push.
See [GitHub-only build proof and storage policy](docs/GITHUB_WORKSPACE_090.md).

Current local package: `output/current/community_civilization_pack-0.9.0.zip`.
A source-only burn is not the final Garrison archive: it must retain the owning
Vietnam art, voice and compiled-only resources. The compact reader reconstructs
those inputs without duplicating old media packs.

Source/static, native burn, archive/package verification and native-game
acceptance are distinct gates. Fresh-match Persian roster/landmark/repair,
save/load and multiplayer tests remain separate.

Credits: **hosein81 and chilly5**.
