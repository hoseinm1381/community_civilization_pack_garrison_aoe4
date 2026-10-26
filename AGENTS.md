# Community Civilization Pack: Garrison GitHub workspace

## Owner policy, 2026-10-26

The sole Garrison workspace is F:/aoe_4_temp/community_civilization_pack_garrison_aoe4.
Edit, build, commit and push here. E: holds the separate base-game/Normal edition;
read it only as reference. Do not maintain or create another Garrison source copy,
worktree, mirror or version folder. This supersedes all historical E: authority
and restore-into-another-workspace instructions.

The only scratch root is F:/aoe_4_temp/Temp_before_github_push. Native intermediate,
cache, readback and input-verification work go there. After a successful build
and confirmed successful GitHub push, preserve compact evidence and the current
SGA/ZIP in output/current, then remove that scratch root. Never delete required
uncommitted input merely because a push succeeded: Git covers tracked files only.

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
  The owner explicitly authorized updating/pushing 0.9.0 for this build test.
