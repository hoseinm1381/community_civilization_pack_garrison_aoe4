# Buffalo animation replacement retry — 2026-10-24

The retry established an independent, metadata-preserving native cattle RHKA
writer round trip. It did **not** encode the authored buffalo idle/walk, create
a new-animation test ZIP, or establish native-game playback.

## Concrete result

`tools/release_081_animation/roundtrip.py` reads the native SDK 20180200 cattle
library using the retained Soulstruct-Havok runtime, generates the three missing
class definitions from the cattle file's declared type metadata, and rewrites
the library in isolated output. The original TYPE section is copied verbatim;
no ABI flags, hashes, prototype fingerprints, or admission checks are invented
or changed. Duplicate generic type names retain their original type indices.
Allocated empty annotation strings remain allocated instead of becoming null.

The first self-parser comparison passed before the independent Garrison sampler
exposed the empty-string issue. The corrected v7 output passes both checks.
Earlier failed v4 and logs remain diagnostic evidence.

- Native source SHA-256:
  `01faed8fd3db588867b8a6d9539246bf9c5ef3734d5248c32adf7a249ef48fab`
- Rewritten v7 SHA-256:
  `cc33c279fadac1d1d59270faa1e77ee01b6349145f7330ae19a917dfafa2c584`
- The independent installed Garrison sampler decoded **all 11 clips** from both
  files. Every sampled parent-local pose, frame count, duration, root-motion
  sample, and motion measurement compared exactly. The independent structural
  comparison also preserves skeletons, bindings, annotation fields and compressed
  payloads. These are offline checks, not game-engine playback.

Evidence: `output/release_081_animation/retry-1/roundtrip-result.json` and
`independent-verification.json`; the `independent-all-clips` directory retains
22 sample documents and their command logs.

## Separate supported encoder control

`human_control.py` builds an isolated, actual 48-bone English spearman control
with its unchanged native bind records and a simple authored neck rotation.
The public `mod-project unit-validate` and `unit-add` routes accepted that
supported human profile and produced a private RHKA. Garrison's readback reports
maximum error `1.209811303361924e-05`, two dynamic components, and 181 untouched
clips. This control was not cooked or packaged. Its small cube meshes are only
encoder-control geometry, not production art. No cattle Action or cattle bone
records were passed off as an admitted human prototype.

The public unit route still contains only human prototypes. Internal module
names found in the installed binary are not public callable CLI lanes: direct
`-m src.core.unit_animation_export` and `unit_animation_fullbody` returned
`unknown core module`. The animation sampler is callable, and supports reading
the corrected cattle round trip.

## Remaining encoding boundary

The authored buffalo Actions are unchanged in
`art/authoring/release_081/animation/buffalo-trial.blend`. Their animation poses
have not been converted to new predictive compressed frame packets. Rewriting
the existing packet payloads exactly does not establish an authored-motion
encoder. The installed supported human encoder control does not qualify cattle
export. A separate cattle-capable encoder still must encode those samples and
pass independent pose-error, untouched-clip, root-motion and annotation checks.
Only then should a private animator be bound to the buffalo and a diagnostic
package assembled. Shared stock cattle resources must not be overridden globally.

## Preservation and gates

All retry files live in the new `release_081_animation` family. The supported
human control uses `staging/r81-animation-control`, independently of production.
The exact delivered 0.8.1 ZIP was rehashed and remains:
`75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0`.
No normal-edition, gameplay, production animation, installed extension, or live
Blender file was changed. A separate background Blender process authored the
human control; it did not open or save the live scene. No installation occurred.

| Gate | Result |
|---|---|
| Existing buffalo source Actions | Preserved; source-only |
| Native cattle container write/read | Passed |
| Independent sampling of all 11 stock clips after rewrite | Passed, exact |
| Supported human authored-motion encoder control | Passed offline |
| Authored buffalo motion encoding | Unqualified |
| New buffalo animation native cook/package/import | Not performed |
| Native idle/move/stop/work/death | Not tested for custom motion |
| Save/load and multiplayer | Not tested |

Reproduce from the Garrison root with configured Blender Python:

```powershell
& (Get-Content .\workspace.json -Raw | ConvertFrom-Json).blender_python -B .\tools\release_081_animation\roundtrip.py
```

`verify_roundtrip.py` writes a fresh comparison directory and intentionally
refuses an existing one. Preserve the current verification evidence before
choosing a separate new output for another run. The retained runtime is a
read-only Berber research dependency; no Berber source, asset or binding was
changed, and it is not a mod runtime dependency.
