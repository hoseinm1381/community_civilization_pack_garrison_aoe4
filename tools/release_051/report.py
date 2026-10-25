"""Human-readable report from current 051 delivery receipts."""
import re
from common import *
def main():
    guarded();p=read(OUT/'package-verification.json');a=read(OUT/'archive-verification.json');c=read(OUT/'checks.json');cleanup=read(OUT/'cleanup-verification.json')
    assert p['status']==a['status']==cleanup['status']=='passed'
    assert sha(p['zip'])==p['zip_sha256'] and sha(p['sga'])==p['sga_sha256']==a['sga_sha256']
    pointer=read(OUT/'native-source/current.json');native=read(pointer['file']);reference=read(OUT/'reference/receipt.json')
    text=f'''# Community Civilization Pack 0.5.1

Built from verified 0.5.0. The normal edition was used only as the trap-port donor
and remains unchanged since the 0.5.1 freeze. Broader siege/keep/earlier-art redesign
was deferred by user choice. The user will test the delivered ZIP in game.

## Delivery

- [0.5.1 ZIP]({Path(p['zip']).as_posix()}) ({p['bytes']:,} bytes).
- ZIP SHA-256: `{p['zip_sha256']}`.
- SGA SHA-256: `{p['sga_sha256']}`.
- Frozen 0.5.0 SGA: `{SGA050_SHA}`; ZIP: `{ZIP050_SHA}`.
- GUID `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`; credits **hosein81 and chilly5**.
- {len(a['changed'])} changed, {len(a['added'])} added, {a['untouched_members']} untouched members;
  all untouched members are byte-identical to 0.5.0. Final {a['final_members']} resource paths are unique.

## Changes

Trap construction retains the existing blocking actor and custom Garrison visuals.
The normal edition's completion handler converts completed traps in place to two
private passable children on the existing 0.25-second scan. The four-second timer
observes attacks before conversion and does not restart on later attacks. Native
PBG/Reflect identity allocation, two added precache entries and existing RDO-object
preservation were checked. The compiled blocking parents exactly match 0.5.0;
child restoration permits only PBG/parent/component identity and the intended
block_path/default_simbox differences. The native KEYS dictionary's removed unused
path_type entry is restored with those block-path nodes for the byte comparison.
No unrelated trap combat, placement footprint, cost or production data changed.

The two Castle landmark RGMs now expose explicit healthy, damaged and ruin selectors
compatible with their retained native owners. Geometry, materials, owner colour,
markers and native persistent selectable/repairable entities remain unchanged.
The missing named healthy selector is a strong cause inference for the reported
post-completion disappearance; the user's native test remains the acceptance gate.
Unsupported predicate operators/properties/states now fail the offline checker.
The existing full-compound healthy bounds remain 110,488 Citadel / 103,505 HQ,
including all retained debris, both below the agreed 120,779.25 cap.

Both monastery tiers restore the coherent donor-shaped tiled roofs and remove
the oversized added canopy and its tall frame. The original donor deformation
and smaller Vietnamese bell/shrine/lotus/courtyard details remain. Each tier removes
784 canopy/frame triangles and retains 684 detail triangles, with physically
compacted indices, no invalid indices and no newly degenerate faces. Native body
geometry, materials, owner masks, markers, footprints and outskirts remain unchanged.
Restored selector membership covers every source object. Detail stamps share their
base transform for default, Cordoba and campaign; projections account for game Y-up.
The raw game-Z offset is a horizontal offset, not a vertical displacement.

## Assets, evidence and verification

- [Editable assets]({(ROOT/'art/authoring/release_051').as_posix()}).
- [Native exports and texture references]({(ROOT/'art/exports/release_051').as_posix()}).
- [Rebuild recipes]({(ROOT/'art/recipes/release_051').as_posix()}).
- [Monastery complete-compound geometry previews]({(OUT/'monastery/previews').as_posix()}).
- [Landmark healthy/damaged/ruin previews]({(OUT/'landmarks/previews').as_posix()}).
- [Detailed receipts]({OUT.as_posix()}), including original screenshots and warnings under baseline/user-regressions.

Native source compile validated {native['validated_instances']} instances; the new
trap children passed compiled inheritance checks. A fresh native reference cook
and readback passed for {len(reference['model_references'])} model references using
the exact final candidate resources. This is reference validation of already-cooked
native geometry; it is not a fresh FBX model recook or an in-game rendering test.
The regression suite ran {c['tests']['tests']} tests with exactly the same two inherited
weapon-parity failures, no new failures/errors/skips. The five completion tests
passed; asset regressions, source/static SCAR checks and archive/ZIP integrity passed.
The tuning validator reports zero errors, 41 warnings and one informational unresolved
external-reference summary. Official engine dependencies remain external. The final
dependency-delta receipt resolves both new child/parent/precache chains and all seven
model resource quartets; art dependency fields remain identical to frozen 0.5.0.
This preserves the baseline closure without claiming an exhaustive engine-resource audit.

Background Blender startup timed out while preserving the unrelated open scene.
Corrected monastery details are supplied as editable UV-mapped OBJ plus deterministic
native reconstruction recipes. The .blend and original FBX copies are explicitly
reference assets, not freshly saved corrected scenes. Monastery previews are geometry
projections with stamped surroundings, not native material renders. The native
decode-static route also rejected the unchanged 0.5.0 private model with non-finite
UV diagnostics; control/failure logs are retained, and installed native chunk/index
readback separately verified the corrected mesh buffers.

## Native acceptance and rollback

Import/lobby and native match tests are pending user testing. Verify both landmarks
at placement, construction completion, damage, destruction, after collapse cleanup,
selectable persistent ruins, interrupted/resumed repair and second destruction;
check landmark victory accounting. Inspect both monastery tiers in two player colours,
at different distances, with adjacency and production access. Test trap construction
with one/multiple villagers, interruption/resume, friendly/enemy infantry/cavalry/
elephant/siege passage after completion, conversion state/health/ownership/selection,
attack on the completion tick and the non-resetting four-second lifetime.

Preserved 0.5.0 is the exact diagnostic baseline; 0.4.0 remains the earlier rollback.
No client import or multiplayer success is claimed. The guarded entrypoint is
`tools/build_release_051.ps1`; old 0.5.0 checks are historical and must not be run
against the newly edited active source. Finalization removed only inventoried,
regenerable full-archive readback caches: {cleanup['reclaimed_bytes']:,} bytes.
Source, recipes, native inputs/readback, failure diagnostics and deliveries remain;
delivery hashes were checked again afterward.
'''
    text=re.sub(r'\]\(([EF]:/[^)\n]+)\)',r'](<\1>)',text)
    target=ROOT/'docs/RELEASE_051_REPORT.md';target.write_text(text,encoding='utf-8');print('REPORT051',target)
if __name__=='__main__':main()
