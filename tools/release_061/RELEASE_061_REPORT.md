# Community Civilization Pack 0.6.1 visibility repair

Credits: **hosein81 and chilly5**. This supersedes 0.6.0 for testing and use.

Full ZIP: `output/release_061/community_civilization_pack-0.6.1.zip`.
Its exact ZIP hash and size are recorded in `qualification/package-r1.json`.
Final SGA SHA256: `9e797ab14faf293ec1570c6dc38f1e7cab2ffda9df7d5078b7a0ecf564233c85`.
Verified ZIP SHA256: `7f20839e5a7da38619312e33992bbd029e28b9e22e0f26a68dc6e10c69374785`;
size **94,803,064 bytes**. All four package members and the embedded SGA hash passed.
The package and cleanup receipts, rather than this report alone, establish successful
delivery verification. Native acceptance remains unrun.

## Confirmed unit defect and correction

0.6.0's assembly mixed 142 native blueprints and 305 art resources in one
`set-members --alias data` operation. The archive tool retains the mount for
existing entries but assigns that alias to newly added entries. Consequently all
80 new private native RGDs were mounted in **data**, while their modified
Vietnamese consumers were correctly mounted in **attrib**. An archive byte or
path check did not catch this; the earlier release validation missed the native
mount requirement.

The working Berber 0.9.0 archive confirmed the correct split: private RGDs in
attrib, model/material/texture resources in data. 0.6.1 reconstructs the exact
0.6.0 payload from frozen final053 using separate attrib and data passes. All 80
private blueprint payloads remain byte-identical; only their TOC mounts change.
Six focused regressions now reject wrong mounts, wrong media sections, case
collisions, unexpected removals and mount changes outside the explicit list.

The unit-only repair received its own full 1,196-member readback, with **zero
payload byte changes**. It does not alone establish the exact scout/villager
fallback observed in the user's screenshots or prove actual runtime rendering.

## Castle landmark render-route repair

Both custom Castle landmark assets were inherited byte-for-byte from 0.5.3.
The earlier material-option change was unverified and the user's current match
shows it did not restore visibility. The stock-model control previously rendered
on these actors; that isolated the custom visual path, not the gameplay identity.

Inspection and isolated supported decodes found valid finite geometry/UVs, real
nonempty healthy/ruin parts, matching selector counts and present texture paths.
There was no demonstrated safe selector-name or single material-flag fix. Both
Castle models used a `structure`/`structure_collection` shader route. Berber's
working Ribat/Funduq use `object`/`object_collection`, as do the accepted custom
Feudal-building route controls.

The retained seven-part FBX and texture sources were freshly cooked through the
supported Garrison object-PBR building route, with Live Reload and generated mode
disabled. Only matched native model/geometry/material assets and their texture
dependencies were admitted. No prototype actors, blueprints, stamps or scripts
were imported. Both original custom designs and the campaign Citadel are retained.

- Fresh native cook archive SHA256:
  `c706c315ce8f208b57188278c4df5b4f8f73345675c6c36e55ad684dd7243807`.
- All three existing model stems receive an RGM/RRGeom/RRMaterial triple; six
  new textures live privately under `art/scenario/cc061/`.
- Native object geometry uses stride 20 rather than the prior structure stride
  24. Every triangle index byte and the first 16 bytes of every vertex match the
  old geometry in all groups. Position, normal/tangent/primary-UV data and the
  accepted compound geometry are retained; the extra structure channel is removed
  by the native compiler, not a guessed vertex-buffer patch.
- RGM selector and marker payloads are byte-identical. All three native RGO
  owners are unchanged. Healthy Citadel/HQ geometry remains 90,894 / 92,234
  triangles, with the original separate foundation, damage and ruin parts.
- Native cook/readback, paired object descriptors, texture dependency closure,
  source hashes and exact scoped output checks passed.

This is a controlled, reference-backed renderer replacement. **The Castle
visibility cause and success are not proven by a native match yet.** Object-PBR
may reduce full dynamic player tint; test two player colours along with completed,
damaged, ruined and repaired states. The release does not claim this as tested
in-game merely because cooking or decoding passed.

## Preservation and validation

The final SGA contains **1,202 members**: 1,187 original payloads unchanged,
nine Castle visual payloads changed, six private textures added, and no removals.
All 80 blueprint mount corrections are explicitly listed. Every native RGD,
including statistics, abilities, production, upgrade and speaker references,
remains byte-identical to 0.6.0. All other art, voices, localization, SCAR,
RDO/project identity, other civilizations and previous accepted buildings/traps
are unchanged. The three old Castle material payloads are intentionally superseded
by this repair; the protected villager-stealth payload remains unchanged.

Active editable gameplay source, the normal edition, both identity files and
all **1,870 previously retained art files** passed preservation checks. Neither
the Berber source nor its assets were modified or copied into this project.
Editable landmark sources, earlier native diagnostics and all old releases remain.
Rattan visual switching and custom worker-elephant crate geometry remain deferred
as in 0.6.0; human siege crews retain stock behavior.

Tests: six new mount regressions plus the existing 93 release tests passed.
`qualification/tests-r1.json` captures exact commands, output and exit codes.
Full native archive CRC/SHA1 verification, complete extraction/hash comparisons,
TOC checks and an independent final review passed. ZIP checks require four exact
members, strict version 0.6.1, exact credits, project identity, manifest content
types, readability/CRC and an exact embedded SGA hash.

## Sources, recipes and reproducibility

Use the existing Garrison source root; all new scripts are in `tools/release_061`.
New outputs and staging are under the configured project-owned F: roots. Storage
verification must pass before generation; never replace missing junctions with
ordinary directories. No Blender scene was altered for this repair because the
exact retained FBX and textures were sufficient.

1. `freeze_061.py` pins exact060 ZIP/SGA, current source and user screenshots/log.
   `baseline/art-inputs.json` separately pins all earlier editable art.
2. `repair_archive_mounts_061.py` reconstructs the unit overlay as attrib then data.
   Its `mount-fix-r1/{attrib,data}.txt` files retain the exact pinned payload maps.
3. `cook_castle_object_061.py` creates a separate Garrison building project from
   byte-verified retained FBX/texture sources, takes the shared native-build lock,
   uses the model-enabled editor and preserves fresh logs and source hashes.
4. `assemble_castle_object_061.py` rebases only the freshly cooked native assets,
   retains the existing lifecycle/markers/RGO and emits the explicit 15-member
   payload receipt. `verify_castle_object_061.py` independently checks it.
5. `assemble_release_061.py` overlays that scoped asset payload onto the corrected
   mount candidate. `verify_candidate_061.py` fully reads back the archive, verifies
   every byte and TOC delta, source/normal/identity and prior art.
6. `package_release_061.py` consumes the passing final audit, native asset proof,
   independent review and test receipt. It verifies a staged four-member ZIP before
   promoting it to the strict final filename. Its `inspect_zip` function is the
   independent ZIP metadata/CRC/hash gate.

Existing completed build directories are immutable receipts; scripts reject their
reuse. To reproduce exact archive bytes in new output paths without recooking,
use the installed sga-archiver and the retained mapping files: `set-members`
frozen final053 with the attrib map and `--alias attrib`, then the art map and
`--alias data`, then `final-r1/members.txt` and `--alias data`. Verify the new
archive with a fresh evidence label. Keep all mapped source files and successful
cook archives/readbacks. For a new art cook, use a separate attempt label/project
and requalify the resulting native assets rather than overwriting this evidence.

Archive/asset source records:

- `output/release_061/baseline/freeze.json`
- `output/release_061/castle-object-cook-r1/`
- `output/release_061/castle-object-payload-r1/{receipt,verification}.json`
- `output/release_061/qualification/final-r1/receipt.json`
- `output/release_061/qualification/independent-final-review.json`
- `output/release_061/qualification/tests-r1.json`
- `output/release_061/qualification/package-r1.json`
- `output/release_061/qualification/cleanup-r1.json`

Prior blends/textures remain under `art/authoring/castle_next/landmarks` and
`art/authoring/release_051/landmarks`; original exports remain under
`art/exports/castle_next/landmarks`. 0.6.0 unit sources/recipes are untouched.

## Native test and rollback

Import the **full** 0.6.1 ZIP with AoE4 closed, select the pack as both Game Mode
and Tuning Pack, then start a fresh China-to-Vietnam match. Follow
`NATIVE_TEST_CHECKLIST.md` for all units/tiers/tasks, both completed Castle models,
LOD/death/deployment/ruins/repair, player colours, ordinary Chinese isolation and
multiplayer. None of these acceptance results is claimed by offline checks.

The exact failed 0.6.0 ZIP and earlier final 0.5.3 remain available as historical
rollback artifacts. 0.6.0 has the reported visibility defect; 0.5.3's custom Castle
rendering was unverified. Neither is presented as a proven visibility fallback.
No editable-source rollback is needed because this repair changes no active
gameplay XML or SCAR.

After verified packaging, remove only enumerated, fully regenerable 0.6.1 full-
archive extraction caches. Preserve all asset cook readbacks, decoded models,
source inputs, staging/config, diagnostics, private payloads, native archives,
ZIPs, recipes, scripts and reports. The cleanup receipt records reclaimed bytes
and confirms delivery/rollback hashes afterward.

Cleanup completed: the two complete 0.6.1 full-archive readback directories were
removed after exact inventory comparisons, reclaiming **337,991,399 bytes**.
Final ZIP, final SGA and retained 0.6.0 rollback hashes are unchanged. All cook
readbacks, decoded models, input/staging sources, native archives and diagnostics
remain retained; only the two regenerate-from-SGA extraction caches were removed.
