# Community Civilization Pack: Garrison GitHub workspace

## Accepted current release: 1.0.6 (2026-10-28)

The owner confirmed "version 1.0.6 worked ok" and authorized minimal current
editable/rebuild promotion, main push and a GitHub release containing the ZIP.
Follow docs/RELEASE_106.md and development.json. These current pointers supersede
the historical 0.9.0 build pointers below. Future art still follows the temp
review/acceptance workflow. Preserve existing immutable packs and original temp
inputs. This publication performs no cleanup or deletion.

Run tools/compact/github_build.py native then package. Complete-member assembly
is required for the explicit duplicate-texture omissions. Verify the exact
accepted ZIP/SGA hashes from promoted inputs before publishing. A broad native
source burn does not replace compiled art bindings and owning-resource overlays.

## Owner requirement: asset optimization and 1.0.0 corrections (2026-10-27)

Optimization is a release acceptance requirement for every added civilization.
The owner reports severe lag and maximum GPU load on an RTX 5050 with the 1.0.0
Persia candidate. Do not treat a successful cook or ZIP as performance acceptance.

- Budget each civilization's additional packaged assets to at most 300,000,000
  bytes; prefer below 200,000,000, with 250,000,000 an intermediate target.
  Keep the complete current mod import ZIP below 600,000,000 bytes. Record the
  actual final ZIP size and incremental compressed contribution against the
  accepted baseline; also report archive bytes and decoded texture memory.
  ZIP compression alone is not runtime optimization.
- Prefer installed stock resources by reference. Ordinary buildings should keep
  recognizable AoE4 silhouettes with only restrained Persian modifications.
  Unique buildings, landmarks and wonders retain their distinct identities.
  Restore the Town Center to a recognizable stock-based Town Center.
- Deduplicate textures and materials across ages, states and families. Use shared
  atlases, measured texture resolutions, mipmaps and appropriate native compressed
  formats. Preserve dynamic owner, skin and hair masks; never bake team colour.
- Require active, verified runtime LODs, not merely packaged lower-detail files.
  Measure simultaneously visible geometry, material/draw groups, texture residency
  and redundant/overlapping geometry against equivalent complete stock assemblies.
  Target stock median costs and do not exceed measured stock maximum without a
  recorded reason and owner acceptance.
- The owner permits simplifying intermediate damage appearances for ordinary
  buildings if useful. Preserve construction, ruins, repair, targeting, selection,
  gameplay and native lifecycle owners. Keep damage appearances for landmarks
  and wonders. Do not strip stock damage resources that are referenced in-game
  merely to remove archive bytes.
- Correct the lumber-camp missing-asset placeholder; enlarge Assassin Brotherhood
  visuals uniformly to 1.75 times their current size, preserving gameplay footprint;
  investigate yellow cavalry cloth and restore intended dynamic team colour.
- Maintain an issue ledger, reproducible optimization recipes and before/after
  budget receipts. Native frame-time/VRAM comparisons under matching settings are
  a separate acceptance gate; no smoothness claim from file-size reduction alone.
- Keep development and candidate builds under
  F:/aoe_4_temp/Temp_before_github_push. Preserve current packages, art masters,
  rebuild inputs and unrelated work. No pushing, deletion or installation is
  authorized by this optimization request. Permanent workflow documentation may
  be updated now; permanent gameplay/art stays unchanged until acceptance.


## Owner policy, 2026-10-26: assets in temp, accepted work into GitHub

The permanent Garrison GitHub repository is
F:/aoe_4_temp/community_civilization_pack_garrison_aoe4. Develop and review new
Persian assets in F:/aoe_4_temp/Temp_before_github_push, the owner's reusable dirty
workspace. Keep experimental art, candidate integration edits, exports, cooks,
readbacks and previews there until the owner accepts the result. This explicit
instruction supersedes the earlier policy to edit new assets directly in main.
See docs/PERSIA_ASSET_WORKFLOW.md for the acceptance, promotion and cleanup gates.

Gundeshapur is the first Persian Feudal landmark asset. Preserve existing gameplay,
footprint, identity and native construction/ruin/repair behavior. Visual direction
must be established before modeling. Normal and the original Persia donor remain
read-only. Do not create further workspace/version copies or duplicate media banks.

After explicit owner acceptance, transfer only accepted changes and their complete
editable/rebuild inputs into the permanent repository, document and verify them,
then commit and push to main. The owner authorizes that push after acceptance;
do not push asset work before acceptance. Minimize storage by retaining unique
important inputs and compact evidence while excluding regenerable caches.
Delete the temporary root only after the push is confirmed and every important
editable/ignored input has a verified durable home. Git covers tracked files only.

Current release: 0.9.0, functional Persia plus Vietnam; new Persian art is the
next milestone. Read docs/GITHUB_WORKSPACE_090.md and docs/PERSIA_GARRISON.md.
Use tools/compact/github_build.py native followed by package, configured through
ignored workspace.local.json (see workspace.example.json). This compiles tracked
source and checks the stored current delta; it refuses stale source/payload pairs.
Changed gameplay/art requires a new explicit delta, not bypassing that check.
Old tools/current_persia.py and current_sync.py document the one-time E: port;
they are not the F: build or milestone-sync entrypoints. Historical freezes and
receipts remain immutable evidence, not current path configuration.

## Preservation and verification

- Keep GUID b7fcea91-257b-408f-b9e8-ae4d8bc402e1, bundle community_civilization_pack
  and archive namespace b7fcea91257b408fb9e8ae4d8bc402e1. Check .aoe4mod, manifest,
  SCAR/RDO and assets/_default.burnproj NiceName before/after assembly.
- development.json selects index-current.json.gz layered on index.json.gz.
  Preserve every referenced immutable pack. They contain editable art, rigs,
  textures, recipes, shipped Oggs, compiled-only resources and recovery inputs.
  Never replace them with only a playable SGA or delete packs as caches.
- Broad native source builds are reference archives, not the final owning archive.
  Preserve Vietnam custom art, voices, owning-resource fixes and mount aliases.
  Integrate only an explicit changed-resource map and compare all untouched bytes.
- Resolve full current private and official inheritance before adding singleton
  extensions. Use inherited variant IDs; refresh inheritance, run tuning/source
  checks and confirm a real completed Content Editor burn.
- Installed Garrison/Blender and Content Editor are external tools. Use current
  aoe4-garrison-blender, modify-aoe4-tuning-packs and aoe4-game-mode-skill guidance.
  Do not touch live Blender work or regenerate voices as part of a release rebuild.
- Existing speech is complete; shipped Oggs rebuild from Git. Local AI environments,
  model weights, omitted WAV masters and voice-production history are separate.
  Inventory any such unique inputs before retiring old storage. A successful
  package build alone does not prove full art recooking or speech regeneration.
- Keep source/static, native burn, art cook, archive/package, client import,
  fresh-match behavior, audible playback, save/load and multiplayer gates distinct.
- No automatic history rewriting, force pushes, paid requests or scheduled sync.
  The prior 0.9.0 build-test authorization is historical. New asset pushes follow
  the explicit owner-acceptance gate above.
