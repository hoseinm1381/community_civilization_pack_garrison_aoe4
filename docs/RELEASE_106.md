# Community Civilization Pack 1.0.6

The owner reported that 1.0.6 worked on 2026-10-28 and authorized promotion,
GitHub push and publication of the import ZIP. Individual native test coverage
was not specified. Save/load, multiplayer and measured frame-time/VRAM comparisons
are not inferred from that acceptance.

## Changes since 0.9.0

- Accepted Persian building, landmark and unit art, native lifecycle bindings,
  stock-based ordinary buildings and Town Center, shared materials and textures,
  owner-colour fixes and the 1.75x Assassin Brotherhood visual scale.
- Human-roster-gated Persia/Vietnam prematch loading, retaining the native choice
  and conservative fallback. Removes the broad unconditional preload list.
- Landmark CPU geometry repair retained from 1.0.5: 116 malformed buffers in
  Gundeshapur, Grand Caravanserai, Samarkand Bazaar and Assassin Brotherhood.
  The final render geometry, owners, markers and gameplay remain preserved.
- Original UV coordinates recovered for 31 Vietnamese building models. Repairs
  the historical tangent/UV offset mix-up without changing their custom shapes.
- 432 lower-LOD normals repaired for Buffalo and Veteran/Elite Skirmishers;
  opposite-facing surfaces and skin channels are preserved.
- 180 duplicate native texture images consolidated through 303 material paths.
  Formats, sRGB, alpha, owner/skin/hair channels and every mip are exact.

## Delivery

Import the ZIP through Garrison, then select the pack as both Game Mode and
Tuning Pack. Human China/Delhi slots retain the China/Vietnam and Delhi/Persia
choice. AI remains native. Credits: **hosein81 and chilly5**.

ZIP: 476,743,699 bytes (above 400 MB; below the 600,000,000-byte cap).
SHA256: `6699db61d946c6f58119e7da365a19a79fc756b9546007f22bb4288510ca5996`.
SGA: 978,540,535 bytes.
SHA256: `9e82491506b667812daa831db8e2f4f9ab9bea79857bc60aa6911295fae2273c`.

Net compressed increase against accepted 0.9.0: 190,337,064 bytes, meeting the
preferred below-200,000,000 target. ZIP reduction versus 1.0.5: 63,174,752 bytes.
Model native compressed mip payload: 432,093,632 bytes, reduced by 196,264,232
duplicate bytes. RGBA8 mip equivalent: 2,014,751,200 bytes. These are aggregate
resource totals for both civilizations, not live VRAM measurements.

## Minimal current inputs in Git

The existing immutable baseline/media packs remain unchanged. The current index
adds deduplicated current art sources, Blender masters/rigs, texture inputs,
recipes, required native donors, compact receipts and changed compiled resources.
The full ZIP/SGA are release/build outputs, not another Git media bank. Previews,
screenshots, backup blends, stock motion clips, decoded stock projections, cooks,
readbacks and obsolete releases are excluded from the new Git delta. Original
temp inputs and prior releases are retained; this promotion performs no cleanup.

Native source compilation is a reference burn. Compiled art bindings and native
asset postprocessing are explicit immutable overlays; a source-only burn is not
the playable archive. Current source/payload pins reject stale rebuilds.

## Rebuild

Configure `workspace.local.json` from `workspace.example.json` with installed
Garrison/Content Editor/Git/Python paths, then run:

```powershell
python -B tools/compact/github_build.py native
python -B tools/compact/github_build.py package
```

Scratch stays under the existing temp root's `github106` build directory. The
builder reads promoted Git inputs, denies candidate art/research/cache input
paths, verifies the native source snapshot and completed burn, and reconstructs
the exact owning SGA/ZIP. The complete-member policy permits only the explicit
180 omissions and verifies every final member hash and mount after extraction.

To recover editable inputs with the existing portable tool:

```powershell
python -B tools/compact/portable.py restore --profile art --destination <recovery-directory> --prefix source/art/persia/
```

Restore source recipes/tools with `--prefix source/tools/` and referenced donor
images/current receipts with `--prefix source/research/`. The restore/configure workflow relocates
working paths; originals remain immutable. Standard native donors can also be
decoded again from the installed game. No new speech synthesis is required.

The release's original evidence includes 13,678 final member hashes/mounts,
3,079 checked render groups, 19,095 resolved material texture edges, all 260
original master pins and four fresh decoder controls covering the repaired unit
LODs and the formerly failing house. Full art recooking is distinct from package
reconstruction. See `BUILD_106.json` for promotion/rebuild verification.
