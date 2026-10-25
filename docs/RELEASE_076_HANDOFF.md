# Garrison 0.7.6 asset preparation

This is an isolated art overlay, not a released mod. The selected assets are recorded explicitly in `art/recipes/release_076/selection.json`. Ten editable Blender assets provide a water buffalo, three skirmisher bodies, three held javelins and three matching projectiles. All use new visible geometry and authored texture atlases. Official rigs supply compatibility records for the four bodies. Each asset has three geometric LODs.

## Locations and evidence

- Editable sources: `art/authoring/release_076/<asset>/<revision>/model.blend`.
- Exports: `art/exports/release_076/<asset>/<revision>/` (FBX, textures, and body rig definitions).
- Recipes: `art/recipes/release_076/`; do not select files by modification time.
- Overlay manifest and gallery: `output/release_076/manifest.json` and `gallery.html` (output is the verified external-storage junction).
- Selected native art cook: `output/release_076/cooks/v5/`; logs, archive listing, extracted media and decoded proof are retained together. Earlier attempts remain diagnostic evidence, not selected deliveries.
- Source review: `source-qa.json`, `budgets.json`, per-asset `art/<asset>/<revision>/` views and receipts. References and proportions: `docs/RELEASE_076_REFERENCES.md`.
- Preservation hashes: `source-freeze.json` and `preservation.json`.

The isolated cooker produces an art-only scaffold archive as native cooking evidence. It is not the destination mod, must not be installed, and is never an assembly input in its entirety. The manifest allowlists only private `art/scenario/garrison/cc076/` member files; generated scaffold gameplay identities are excluded.

## Qualification boundaries

Source checks cover topology, UV presence, normalized weights, influence limits, stationary animation root and loop endpoints. Native readback checks all ten models, three LODs, textures, donor hierarchy and bind transforms, and skin streams. Static source and decoded previews support material review. These checks do not establish deformation across native motion clips, hand contact during throwing, player colour in game, lifecycle coverage, or gameplay acceptance.

The buffalo action `076_Supervise_SOURCE_ONLY` is editable in its blend (frames 1–121 at 30 fps). Native bovine custom-clip encoding/state selection is not qualified by the installed contract. The action is **not exported or connected**, and no SCAR orders are issued. Native bovine construction responses and supervision compatibility still require testing. Existing Worker Elephant gameplay remains unchanged.

## Reproduce preparation and checks

Run PowerShell from the Garrison root. Use the configured Python runtime:

```powershell
$py = 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B tools/verify_workspace.py --storage-only
& $py -B tools/release_076/inventory.py
# New immutable revision only; repeat for each family to revise.
& $py -B tools/release_076/blender_runner.py tools/release_076/author.py buffalo r4
# Explicitly edit selection.json only after reviewing the new revision.
& $py -B tools/release_076/blender_runner.py tools/release_076/qa_blender.py art/recipes/release_076/selection.json
& $py -B tools/release_076/test_overlay.py
# Use a fresh unique label; an existing cook is intentionally not overwritten.
& $py -B tools/release_076/cook.py --selection art/recipes/release_076/selection.json --label next-cook
& $py -B tools/release_076/decode_cook.py next-cook
& $py -B tools/release_076/blender_runner.py tools/release_076/preview_cooked.py next-cook javelin4
& $py -B tools/release_076/finalize.py next-cook
```

The six rigid r3 assets were re-exported from r2 with V flipped for the native FBX contract. Editable UVs remain unchanged. The main authoring recipe now applies this correction to future rigid exports. `reexport_rigid.py` is the historical migration, not a repeatable overwrite command. The native unit exporter already handles this flip for skinned bodies.

Blender and native cooking use the existing project lock. All Blender work runs in isolated background processes; unrelated live Blender work is not saved. Donor decode/index inputs remain in release_076. `base_cattle` is a lifecycle archetype without visible geometry, so it is inspected as an owner rather than decoded as a model.

## Future integration into a completed baseline

The overlay is ready for media conflict checking; final visual bindings are deferred. `bindings.json` is a reviewable field-level patch specification with 16 source-consumer hashes, not an applied XML patch. It covers normal/campaign unit references, age progression, weapons and buffalo presentation. Resolve actual compiled consumers in the completed baseline, including tower-trained variants and compiled-only overrides, before producing concrete private attachment/projectile patches.

1. Explicitly select the completed 0.7.5 archive and SHA256. Do not automatically use the latest file or the unfinished source freeze.
2. Run `tools/release_073/check_identity.py --archive <selected.sga>` before integration. Keep destination GUID, bundle key, mounts, archive namespace and existing compiled-only overlays.
3. Run the read-only conflict gate below. It verifies the exact archive hash, namespace, payload hashes, duplicate destinations and unexpected overwrites. Existing destination members require explicitly recorded expected hashes. No archive is assembled by this command.

```powershell
& $py -B tools/release_076/overlay.py --baseline '<completed-075.sga>' --baseline-sha256 '<exact-sha256>' --manifest output/release_076/manifest.json
```

4. Clone native visual attachments and projectile identities privately through supported tooling. Preserve the throwing owner and its held/throw/torch lifecycle; do not substitute a static held weapon for the animated owner. Never edit shared stock resources or the shared elephant attachment. Resolve all campaign/default variants and age/tower consumers. Preserve all balance, timers, trajectory and production fields.
5. For any extension addition, resolve full private/current-official inheritance for every variant; use exact native list overrides. No such extension is added by this preparation.
6. Compare the candidate changes against a narrow visual-resource allowlist and verify every other baseline member/mount unchanged. A future separately authorized assembly must run the established identity checks again against the final archive. Packaging and installation remain deferred.

The preserved completed 0.7.4 archive under release_075/baseline may be used only to exercise the media conflict gate. Passing that check is not completed-0.7.5 integration qualification.

## Native acceptance checklist for a future assembled candidate

- Train regular and tower skirmishers; upgrade II→III→IV; test campaign/default consumers and all player colours at gameplay zoom and each LOD distance.
- Walk, idle, throw repeatedly, verify hand contact, projectile silhouette/orientation, impact, torch switching, death and lifecycle transitions. Compare damage, range, timing and trajectories with the selected baseline.
- Train buffalo; walk, construct, die, assign/leave paddy, cancel work and lose target. Confirm supervision income and idle requirement without extra orders. Test save/load and multiplayer determinism.
- Custom supervision animation remains disabled unless separately encoded and qualified against active supervision state without disrupting income.

No final mod archive, release ZIP or installation is produced by this preparation.
