# Community Civilization Pack Normal agent instructions

This checkout is the independent Normal edition on branch `normal`. The current
user-authorized work adds Korea beside Zhu Xi's Legacy to the existing combined
game mode and tuning pack, preserving Vietnam/Persia and existing dirty source.
See `docs/KOREA_FULL_PORT.md` and `docs/korea-import.json`. Treat old stage-one
probe notes as historical evidence. Keep the
Garrison checkout and remote `main`/release branches unchanged unless a later user
request explicitly expands the scope.

The 2026-10-29 owner-approved repairs are in `docs/KOREA_REPAIR_20261029.md`.
Preserve the narrow official Zhu Xi Literature storage / race UI exceptions
constrained by `docs/korea-shared-resource.json`; do not restore the donor's global
resource UI. Preserve roster-gated prematch loading and the empty unconditional
RDO precache list. See `docs/KOREA_CONSTRUCTION_20261029.md` for the subsequent
27 private construction-time repairs and Observatory token refill fix. Preserve
the stock action cap: `resource_cap_action_player_modifier` is rejected by native
SCAR; the Korean ledger retains all four allowances. Current source tests total
81. The 2026-10-29 native build and archive/readback checks passed; the latest
native gameplay acceptance remains pending. See `docs/NORMAL_RELEASE_20261029.md`.
Publish source on `normal` and distribution ZIPs on the owner-selected
`normal-release` branch; preserve Garrison and older distribution branches.

## Identity and source

- Project: `Community_Civilization_Pack_Normal.aoe4mod`; normal identity:
  `a743d7d1-d753-4cf7-8817-e29d8ded7366`.
- Display name: `Community Civilization Pack Normal`.
- Preserve stable project/PBG/RDO/localization identities and native blueprint keys.
  The archive NiceName in `assets/_default.burnproj` must equal the project GUID
  without hyphens. Never borrow the Garrison GUID or create a shared identity.
- Normal compiles with the owned Windows AoE4 Content Editor. Do not introduce a
  Garrison, Blender, sibling-checkout, or external-cache dependency into portable
  source checks or the maintained current tests.
- Read the current README, CONTRIBUTING guide and applicable documentation first.
  Use `modify-aoe4-tuning-packs` for tuning and `aoe4-game-mode-skill` for SCAR/RDO.
  Inspect official donors/schema before altering native serialization or APIs.

## Mandatory inheritance checks

Before adding an EBPS/SBPS extension, resolve the full private and current official
parent chains for default and every affected campaign/alternate variant. Direct
child absence and generic validator success do not prove effective absence.
Override inherited singleton extensions using the exact variant's native
`List.ItemID` and matching `List.ParentItemID`; append only when the complete
chain proves absence. Preserve gameplay values for identity-only repairs.

After tuning edits, run the portable verifier, current tests,
`tools/check_extension_inheritance.py --refresh`, and the installed tuning
validator. A game update requires refreshed official archive evidence. Keep a
regression using the actual pre-repair source when repairing inherited duplicates.
If native tools/evidence are unavailable, report the affected gate as pending.

## Verification and preservation

Portable commands (Python 3.12, test dependency in `requirements-tests.txt`):

```text
python -B tools/verify_source.py
python -B -m unittest discover -s tests/current -p "test_*.py"
```

Keep source/static, native Content Editor burn, package/readback, game import,
lobby selection, fresh-match mechanics, save/load and multiplayer as separate
acceptance gates. Claim a successful burn only from a real completed burn log.
Do not promote exit code zero, mocked execution, or package hashes to native
behavior proof.

Machine-specific settings belong in ignored `workspace.local.json`; use
`workspace.example.json` as the shareable template. Do not commit credentials,
editor installs, `.aoe4`, `.tools`, cache, work/output, archives or generated files.
Preserve editable sources, owned inputs, rollbacks and failed-build evidence.
Deletion requires existing explicit authorization; Git ignore rules never authorize
deleting a local file. Keep changes limited to the authorized scope.
