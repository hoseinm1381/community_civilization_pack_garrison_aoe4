# Community Civilization Pack

## Current package: 0.7.12 — timing, buffalo controls, influence and tunnel exits

Use [the 0.7.12 report](docs/RELEASE_0712_REPORT.md). The verified ZIP is in
`output/release_0712/delivery/final-v1`. It transfers 0.25s from skirmisher reload
to wind-up, enables counter selection/camera cycling, enlarges the work icon,
increases Vietnam influence/network reach 2m, and accepts eligible tunnel exits
within 8m of building edges. Native match/save-load/multiplayer acceptance is
pending. Exact 0.7.11 is retained in `output/release_0712/baseline`.

## Previous package: 0.7.11 — quiet markers, buffalo cap and Vietnam badges

Use [the 0.7.11 report](docs/RELEASE_0711_REPORT.md). The verified ZIP is in
`output/release_0711/delivery/final-v1`. This fixes the off-screen farm notifier
and buffalo cap text, and applies the dragon civilization badge to private
Vietnamese units/buildings. Native UI/save-load/multiplayer acceptance is pending.
Exact 0.7.10 is retained under `output/release_0711/baseline`.

## Previous package: 0.7.10 — Vietnam visuals and HUD

See [the 0.7.10 report](docs/RELEASE_0710_REPORT.md) and
[implementation ledger](docs/RELEASE_0710_PROGRESS.md). The accepted rollback is
`output/release_079/delivery/final-v1`. New source, art, cooks and verification
use `release_0710`; the guarded assembly entrypoint is
`tools/build_release_0710.ps1`. Native gameplay acceptance remains separate
from build/package verification. The verified ZIP is in
`output/release_0710/delivery/final-v1`. No installation, publication or cleanup.

## Historical 0.7.2 — normal v12 gameplay with existing custom art

Use [the current development guide](docs/DEVELOPMENT_072.md) and
`tools/build_release_072.ps1`. Current player files are in
`output/release_072/delivery`; preserved 0.7.1 remains in
`output/release_071/delivery`, and exact 0.7.0 rollback is in
`archives/release_070_rollback`. Historical instructions below are retained as
project history and may refer to retired caches or releases.

## Historical preparation notes

Independent **Garrison edition**, containing the existing Vietnam tuning pack and
game mode. The 0.1.0 houses/traps release is preserved and was reported tested and
good by the user. The current 0.2.0 milestone adds barracks, town-center, rice-paddy
boundary, Hideout and Economy Ministry visuals while preserving gameplay.

- Editable project: `community_civilization_pack.aoe4mod`.
- GUID: `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`.
- Garrison key: `community_civilization_pack`; current test release version: `0.2.0`.
- Preserved normal edition: `../Community_civilization_pack_normal`.
- Agent rules: `../AGENTS.md`; link ownership/recovery: `STORAGE.md`.
- Preparation result: `docs/PREPARATION_REPORT.md`.
- Asset/build/package route: `docs/GARRISON_WORKFLOW.md`.
- Current release scope and progress: `docs/RELEASE_020_PLAN.md` and
  `docs/RELEASE_020_LEDGER.md`.
- Release delivery/checks: `docs/RELEASE_020_REPORT.md` (generated on success),
  `output/release_020/package-verification.json` and
  `output/release_020/community_civilization_pack-0.2.0.zip`.
- Accepted 0.1.0 rollback: `archives/release_010_user_accepted`.

Current release commands (from this directory):

```powershell
& .\tools\build_release_020.ps1 -VerifyOnly
& .\tools\build_release_020.ps1
```

Full builds use a new label and fresh native cooks; verification-only uses the
current 0.2.0 candidate. The older 0.1.0 build tools/receipts remain historical.

The Content Editor source owns gameplay. Separate Garrison family projects own
art; generated game-mode ownership and Live Reload are disabled. Garrison does
not automatically import or synchronize the existing Content Editor project.

Keep **F:** connected. `art/garrison_library` contains persistent project recipes
despite the external parent's `temp` name. Active editable art belongs on E: in
`art/authoring`, retained exports in `art/exports`, and recipes in `art/recipes`.

From this directory, check storage and identity:

```powershell
& .\tools\prepare_garrison.ps1 -CheckOnly
& .\tools\build.ps1 -ValidateOnly
$workspace = Get-Content .\workspace.json -Raw | ConvertFrom-Json
& $workspace.python -B -m unittest discover -s tests -q
```

The historical `verify_workspace.py --preservation` checks the preparation-only
milestone and deliberately rejects subsequent visual additions. Release-specific
checks in `tools/release_020` compare against accepted 0.1.0 with an explicit
ten-actor visual allowlist and eleven private visual identities. The test
suite retains the normal baseline's two failing weapon donor-comparison subcases
after correcting its donor path; the full raw suite is not claimed green.

Run `tools/build_release_020.ps1` for the current Garrison release pipeline or add
`-VerifyOnly` to check the current ZIP/source/archive without a new cook. Family
projects and their required source inputs are mapped in `art/GARRISON_PROJECTS.json`.

Gameplay remains the existing Chinese-human China/Vietnam opening choice; AI and
all Vietnam mechanics are preserved. Internal Vietnam blueprint/module names and
diagnostic markers deliberately remain. No generic civilization-selection system
has been introduced.

Copied historical documents retain their original GUIDs, paths, Vietnam v2 names,
and build evidence. They are historical records, not active regeneration inputs.
Use this README, `workspace.json`, `docs/editor-identity.json`, and
`docs/migration-provenance.json` for current identity. The unchanged original
README is retained in `docs/preparation/NORMAL_README.md`.

Native Garrison cook/readback and package evidence is recorded separately in
`output/release_020`. These checks do not establish native appearance, lifecycle,
or multiplayer behavior. Client installation/import and native matches remain
user-run gates. Publication requires a separate request.
