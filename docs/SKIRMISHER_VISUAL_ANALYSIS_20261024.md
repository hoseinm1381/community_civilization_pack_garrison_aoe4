# Skirmisher model, weapon and owner-colour analysis

Analysis only, 2026-10-24. No model, texture, gameplay, animation or delivery package was modified. Inspection used isolated background Blender processes; the unrelated live buffalo scene was left untouched. Source masters' hashes were checked before/after inspection.

## Active resources and evidence

The 0.8.1 owning archive still consumes the release_079 r3 skirmisher II/III/IV masters through private `cc076/skirmisher2`, `skirmisher3`, `skirmisher4` media. The newer buffalo animation pilots preserve those resources byte-for-byte. Binary attachment readback confirms the private body merge meshes and private javelin parent animators; the weapon definitions reference private projectile actors. Historical source recipe names are not the only evidence of use.

Fresh offline native decode of the actual packaged age II/IV bodies and age II javelin completed with no decoder blockers. Body skeleton has 48 bones; deform layer status is ready. The unit shader and patternTex binding are present on all three decoded body material LODs. The javelin uses an object shader without patternTex. This establishes compiled structure and references, not an observed in-game colour result.

Source triangle counts:

| Asset | Near / middle / far |
| --- | --- |
| Age II | 17,444 / 8,722 / 4,360 |
| Age III | 17,434 / 8,716 / 4,358 |
| Age IV | 17,346 / 8,672 / 4,336 |
| Age II javelin | 576 / 288 / 144 |

The decoded near/middle/far geometry agrees with the selected source counts for the inspected assets. Existing movement was user-confirmed in the earlier 0.7.9 pilot, with a reversed throwing weapon reported at that time; the subsequent source uses separate throwing/projectile axes. Final held/throw/projectile appearance must still be verified together when upgrading art.

## Why the current model reads poorly

The source preview confirms rounded tube-like limbs, a narrow cylindrical neck, a smooth long tunic and a cap-like headcloth. The shoulders/sleeves have pinched transitions, while hands and facial details are built from many separate small surfaces. Extra polygons have gone into eyes, lips, fingers, sandal details and repeated rings rather than a strong readable body silhouette. About 17,000 near-LOD triangles already exist; adding density is not the primary solution.

The face needs better integrated cheek/jaw/brow planes, a more natural neck transition and less prominent separate eyeball/lip pieces. Keep Vietnamese identity and the earlier requested light/warm skin direction without caricature. Skin shade must be judged under the actual game lighting; the Workbench preview does not establish its final in-game brightness.

Clothing lacks convincing layered construction and large folds at the waist, elbow, shoulder and hem. Its UVs largely reuse material-colour tiles. The welded tunic's planar UV projection is based on y/z and collapses left/right information, limiting unique painted folds and wear. Noise/striping on repeated tiles is not an anatomical/material bake.

The elite chest armour consists of rounded, isolated oval lamellae: it reads like beads or capsules. Flatten plates into credible overlapping rows with controlled edges, continuous backing and larger readable masses. The dark palette and small trim changes make tiers weakly differentiated at normal camera distance.

The saved official Malian donor in the source blend provides a useful direct comparison for game-scale silhouette, cloth layering and readable equipment. Its clothing/skin is not a Vietnamese design template. Use Chinese/light infantry as further proportion/material references before committing a redesign. The official [Malians page](https://www.ageofempires.com/games/age-of-empires-iv/civilizations/malians/) identifies Javelin Thrower as the ranged skirmisher counterpart; preserving that native animation/equipment role is appropriate.

## Player-colour diagnosis

The problem is not simply a missing pattern texture. The source creates an owner-colour mask only on atlas tile 9; compiled body materials do bind patternTex. Tile 9 is the crimson waist sash/hanging end and, on the elite, a narrow headband. Area-weighted near-LOD surface fractions mapped to that tile are:

- Age II: 6.56%.
- Age III: 4.98%.
- Age IV: 6.03%.

These are total mesh-surface proxies, not visible screen-pixel coverage. The percentage seen in a match depends on pose and camera; a narrow belt is especially weak at distance. Main tunic/sleeves are fixed tan, trousers/headwrap fixed indigo. A red-looking source preview does not prove owner-colour behaviour: Blender's preview shader does not simulate the native ownership system. The source material graph does not wire the pattern texture into its Principled preview.

Redesign the colour layout around broad tunic/shoulder panels and a visible headwrap band or sash, visible from front/back/above. A provisional goal is roughly one-quarter to one-third of the visible clothed silhouette, verified in game rather than inferred from mask texel area. Keep skin, hair, leather, metal, wood and trim independent. Use a neutral/light cloth base in masked regions after comparison with the actual native donor shader, to avoid a permanently dark red base compromising colour readability. Validate the final packed channel layout, UV correspondence and mips; test at least blue/red and a light/dark contrasting pair at normal camera and all LODs.

## Weapon redesign

The current javelin has a basic tapered dark shaft, oversized plain grip cylinder, socket and narrow leaf point. Its separate subparts and uniform surfaces read as a procedural prop. Improve the forged leaf blade's shoulders, central ridge/edge silhouette, metal-to-shaft seating, a tapered wood/bamboo shaft with restrained grain, and a compact wrapped grip. Keep ornament limited so it remains a light throwing weapon. A short cloth tie could echo team colour only if the chosen native weapon material route supports it; the current object shader does not provide that mask. Body cloth should carry ownership reliably without depending on a tiny weapon ribbon.

Author held, throwing and projectile variants from one measured weapon design while preserving each native origin, length relationship, attachment/contact and axis contract. Existing source explicitly distinguishes held native +Z, throwing -Z, projectile -Y; these are fixture-specific and must be checked against each donor. Test grip position and tip orientation through anticipation, release and flight. Do not apply one transform to all resources or change projectile gameplay to compensate for a visual issue.

## Recommended upgrade scope

1. Rebuild the visible anatomy/clothing topology around the working native 48-bone rig. Retain hierarchy, bind transforms, skeletal LOD partitions and native animations. This is a visual overhaul; new animation is not required to improve it.
2. Make a Vietnamese light-infantry silhouette: believable head/hands, articulated shoulders, short layered cross-collar tunic, cloth headwrap, practical trousers/leg wraps. Keep broad, readable shapes and restrained contrast. Treat cultural/historical details as reference-led design choices, not claims established by this audit.
3. Establish player colour on large cloth areas before detailing. Render a native decoded material control in contrasting colours; qualify real in-game ownership separately from source preview.
4. Create one proper atlas per body family with distinct skin/cloth/leather/metal response, deliberate large folds, restrained baked occlusion, normals and roughness. Do not bake directional lighting into albedo. Reallocate geometry from hidden/small repeated details to silhouette and deformation.
5. Define clear tier progression: II cloth/light kit; III restrained padded or leather protection; IV flattened layered armour and a stronger head/shoulder accent. Keep the same unit identity and broad colour layout.
6. Rebuild the matched weapon family and inspect held, release and projectile motion before final integration. Preserve damage, timing, selection, collision, production, abilities and all unrelated units.

A material-only pass could improve colour quickly but would retain the weak body and capsule armour. The recommended approach is a full visible model/weapon rebuild on the existing proven rig, using official AoE4 proportions/materials as references. Approve one finished age-II representative before expanding its accepted style to III/IV.

## Inspection artifacts

All paths below are under `output/skirmisher_analysis_20261024`:

- `source-analysis.json`: source hashes, bounds, material/image inventory, LOD counts and UV-area distribution.
- `compiled-bindings.json`: packaged body/weapon/projectile reference traces.
- `decoded/{skirmisher2,skirmisher4,javelin2}`: fresh native decoded geometry/materials/textures and manifests.
- `skirmisher2-threequarter.png`, `skirmisher4-front.png`, `javelin2-threequarter.png`: existing source previews.
- `donor-skirmisher2-threequarter.png`: saved official donor comparison.

Preview images use Workbench studio lighting and base textures, not the native game shader or player-colour simulation. They support silhouette/topology critique. No new native cook, client import, game match, save/load or multiplayer test was performed in this audit.
