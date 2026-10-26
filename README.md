# Community Civilization Pack Normal

Editable Age of Empires IV combined game mode and tuning pack, with Vietnam and
Persia alongside their original civilizations.

- Select China: choose **China or Vietnam** at match start.
- Select Delhi Sultanate: choose **Delhi or Persia** at match start.
- One shared 30-second choice window; timeout keeps the original civilization.
- AI retains its original civilization.

Use fresh standard Dark Age matches. Persian AI, Nomad, later-age starts and
save/load are outside the current supported milestone.

## Develop and verify

This is the independent `normal` branch for
[hoseinm1381/community_civilization_pack_garrison_aoe4](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4).
It contains the complete editable gameplay source and custom icons. No Garrison,
Blender, sibling project, historical archive or external asset store is needed.

```text
python -m pip install -r requirements-tests.txt
python -B tools/verify_source.py
python -B -m unittest discover -s tests/current -p "test_*.py"
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for local setup and the owned Windows
Content Editor build. Open `Community_Civilization_Pack_Normal.aoe4mod`. Configure
machine paths in ignored `workspace.local.json` from `workspace.example.json`.
Native inheritance refresh additionally uses `requirements-native.txt`.

The Normal GUID is `a743d7d1-d753-4cf7-8817-e29d8ded7366`; Garrison has an
independent identity and build pipeline. Do not copy GUIDs between editions.

## Current evidence

The opening selection was user-tested. The full Persian roster is imported in
editable source, with a functioning-Gundeshapur eligibility gate. Read the
[full import report and native test checklist](docs/PERSIA_FULL_PORT.md).

Source checks and mocked mechanics tests do not establish native compilation,
import, roster gameplay or multiplayer acceptance. Native landmark donor-effect
teardown on ruin/repair remains an explicit test gate; no speculative scripted
bonus was added. Historical tests and reports describe older snapshots and are
not the maintained test-discovery entrypoint.

Credits: **hosein81 and chilly5**. Original Persia source also credits Hossein
and ChillyEmpire. Source visuals and author attribution are retained.
