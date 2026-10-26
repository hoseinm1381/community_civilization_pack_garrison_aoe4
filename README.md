# Community Civilization Pack — Garrison

Current functional release: **0.9.0 — Persia and Vietnam**.

- Select China in the lobby: choose China or Vietnam at match start.
- Select Delhi Sultanate: choose Delhi or Persia.
- One shared 30-second deadline; timeout keeps the original civilization.
- Use standard Dark Age human starts. AI remains native.
- Persia currently uses its existing stock visuals. Complete Persian art is the next milestone.

Develop directly in this folder on `main`. Use Git for source history; keep
required art/audio/compiled-resource inputs in the existing compact store.
Do not create a workspace or full source copy for each version.

Run `python -B tools/verify_current_source.py` and
`python -B -m unittest discover -s tests/persia -p "test_*.py"`.
Native builds and final selective assembly are separate from source checks.
See [current implementation and evidence](docs/CURRENT_WORK.md),
[Persia delivery and acceptance](docs/PERSIA_GARRISON.md), and
[agent instructions](AGENTS.md).

Current local package: `output/current/community_civilization_pack-0.9.0.zip`.
A source-only burn is not the final Garrison archive: it must retain the owning
Vietnam art, voice and compiled-only resources. The compact reader reconstructs
those inputs without duplicating old media packs.

Source/static, native burn, archive/package verification and native-game
acceptance are distinct gates. Fresh-match Persian roster/landmark/repair,
save/load and multiplayer tests remain separate.

Credits: **hosein81 and chilly5**.
