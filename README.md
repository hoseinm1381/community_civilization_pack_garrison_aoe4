# Community Civilization Pack — Garrison

Current release: **1.0.6 — Persia and Vietnam**, accepted by the owner on 2026-10-28.

[Download 1.0.6](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/releases/download/v1.0.6/community_civilization_pack-1.0.6.zip) · [Patch notes and rebuild guide](docs/RELEASE_106.md)

- Select China in the lobby: choose China or Vietnam at match start.
- Select Delhi Sultanate: choose Delhi or Persia.
- One shared 30-second deadline; timeout keeps the original civilization.
- Use standard Dark Age human starts. AI remains native.
- Persian buildings, landmarks and units now use the accepted custom visuals.

Develop and review new Persian assets in `F:/aoe_4_temp/Temp_before_github_push`.
After owner acceptance, transfer the accepted changes and all important editable
inputs into `F:/aoe_4_temp/community_civilization_pack_garrison_aoe4`, document and
verify, then commit/push `main`. Delete temp only after verified preservation and
confirmed push. Keep storage compact without losing editable sources. The accepted
1.0.6 inputs are promoted; future art follows [Persia asset workflow](docs/PERSIA_ASSET_WORKFLOW.md).

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

Current local package: `output/current/1.0.6/community_civilization_pack-1.0.6.zip`.
A source-only burn is not the final Garrison archive: it must retain the owning
Vietnam art, voice and compiled-only resources. The compact reader reconstructs
those inputs without duplicating old media packs.

Source/static, native burn, archive/package verification and native-game
acceptance are distinct gates. Fresh-match Persian roster/landmark/repair,
save/load, matched performance and multiplayer coverage remain separate. The owner
confirmed 1.0.6 worked; individual test coverage was not specified.

Credits: **hosein81 and chilly5**.
