# Garrison 0.8.0 workspace consolidation

Status: approved by the user, 2026-10-24; implementation in progress.
The evidence below describes the design checkpoint. The execution ledger and
final report record subsequent operations and verification.

## Purpose and agreed scope

Create a strict `community_civilization_pack-0.8.0.zip` from the delivered
0.7.12 and reduce retained Garrison development storage to below 6,000,000,000
allocated file bytes across its E: source and owned F: external root. Count the
seven junction targets once. Also report logical bytes. This budget includes the
release, rollbacks, source, input stores, tools and evidence; it excludes the
normal edition and shared game/tool installations. Temporary restore/build
attempts may exceed the retained budget and must have an explicit owner and
retirement receipt.

The user chose to retire redundant deliveries while keeping exact independent
0.7.12 and 0.7.0 rollbacks. All 0.7.12 gameplay, visuals, UI and native animation
bindings remain unchanged. In particular, retain the authorized +2m actual
influence change, 8m footprint-edge tunnel targeting, skirmisher timing and
buffalo presentation. No new gameplay, art or voice work belongs to this release.

The result must support further editing of existing assets and authoring new
assets. Storage reduction must not depend on losing editable masters, textures,
native donors, rigs, model exports, recipes, compiled-only resource overlays or
the ability to recover required inputs.

## Current evidence

- Storage guard passes all seven configured links.
- Initial physical inventory: E: 3,703 files, 2,352,567,085 logical bytes and
  2,361,081,856 allocated bytes; F: 50,386 files, 21,762,580,904 logical bytes and
  32,698,007,552 allocated bytes. Combined: **24,115,147,989 logical /
  35,059,089,408 allocated bytes**, before the new audit evidence.
- E: uses 4,096-byte allocation units; F: uses 262,144-byte allocation units.
  Hardlinks on F: are unsuitable.
- Read-only factory-startup Blender inspection found **339 masters**, zero
  inspection errors, **1,009 unique external image files**, and zero missing
  external file images. Preserve their bytes and existing paths. Of these images,
  755 resolve outside the plain E: root, using 185,124,580 logical bytes.
- 83 JSON recipes contain 1,586 distinct absolute path strings. 701 currently
  exist; 437 absent paths resolve through `resources_071`; 448 are unresolved
  historical references, including retired previews/build products and predecessor
  names. These are an audit finding, not permission to delete further inputs.
  Four absent v1 Blend references have later editable revisions in the same asset
  families. Classify the remaining references and publish an asset readiness map.
- Existing `0.8.0/` voice research and `tools/release_080` asset preparation are
  independent prior work. Preserve them unchanged. Use
  `tools/consolidation_080`, `consolidation_080` and `resources_080` for this work.
- Full hash/compression inventory is being prepared under the owned F:
  `consolidation_080/`. No final retained-size claim is made yet.
- Both exact rollbacks have now passed fresh ZIP CRC, embedded-SGA equality and
  expected ZIP/SGA SHA-256 checks. All 300 normal-edition baseline asset hashes
  match. The initial Blender audit checks external FILE images; linked libraries
  and other external media/cache references still need a complete closure check.

0.7.1's verified method was to retain plain editable masters and their dependencies,
pack native/diagnostic inputs once by content hash with original-path indexes,
remove qualified redundant generated representations, and rebuild after removal.
Its report records a reduction from 26.56 GB logical to 2.89 GB logical / 3.10 GB
allocated. Preserve `resources_071` and `consolidation_071` as protected stores.

## Approaches considered

1. **Plain editable assets plus indexed recovery inputs (recommended).** Keep
   all editable sources and Blender-linked images at their paths. Consolidate
   repeated donor/metadata/diagnostic/native payloads into a lossless, hash-indexed
   recovery store. Retire redundant deliveries and generated containers only after
   their unique useful payloads have an explicit preservation or rebuild route.
   This extends the proven 0.7.1 approach and preserves convenient editing.
2. Keep every historical ZIP/SGA and remove only loose readbacks. This spends much
   of the budget on repeated native content and conflicts with the user's chosen
   retirement policy.
3. Archive the editable masters too. This could reduce storage further, but adds
   restoration steps to ordinary art editing and is unnecessary unless the full
   preservation set cannot meet the budget. Do not use this silently.

The user's rollback/retirement choice fits approach 1. The exact proposed design
still requires review before implementation and retirement.

## Retention rules

Keep plain and byte-identical:

- Every existing editable Blend master, original source texture/media, FBX/OBJ
  source/export, authored rig/action input, recipe and source/tool/config file.
- Every external image actually used by a retained Blend, at its existing path.
- Native unit/project templates needed for direct supported authoring, unless a
  tested preparation command materializes them before the consumer runs.
- The exact original 0.7.0 and 0.7.12 ZIPs and SGAs, their manifests, inventories
  and proof. Hashes must match the prior receipts independently.
- The protected 0.7.1 stores, shared native lock, configured junctions and active
  Garrison library/project configuration. Do not alter the normal edition.

Losslessly consolidate:

- Native donor resources, decoded geometry/metadata, earlier source snapshots,
  historical logs including failures, verification receipts and diagnostic
  payloads. Use a content-addressed ZIP/gzip store, original E:/F: path keys,
  lengths, SHA-256, ownership and restoration instructions.
- Deduplicate only identical verified bytes. Preserve predecessor directory
  hierarchy, including ranged-unit v4/v5b/v5c inputs. Do not rewrite frozen
  historical recipes or their expected hashes to conceal missing inputs.
- Before retiring an old SGA, account for its unique useful members, TOC mounts
  and archive provenance. Preserve compiled-only or experimental resources in
  recovery storage if they are absent from the current pack and loose inputs.
  Exact old container bytes are required for designated rollbacks only.
- Extract unique source/evidence from an old ZIP before retiring its redundant
  delivery container. Unknown or unclassified material remains protected.

Retire only on an exact path-and-hash allowlist after qualification:

- Redundant old deliveries and intermediate assembled archives.
- Verified generated cook/readback/staging representations with retained
  source/rebuild or recovery proof.
- Recreated previews, bytecode and empty ordinary directories where safe.

Moving data between E: and F: does not count as reducing total storage. No blanket
recursive cleanup of a junction, no source compression to hide allocation, and no
deletion based on directory names alone.

## Release and development workflow

Freeze current active sources, the normal edition hashes, editable inputs and the
exact delivered 0.7.12 before preparing candidates. The expected 0.7.12 hashes are:

- ZIP: `b942e131a05d7d35da0251f5c53c4b1e77f89af776a14cb126051b193530437e`
- SGA: `e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1`

0.8.0 is a metadata-only preservation release. The embedded SGA must remain exact
0.7.12, including all 1,417 member bytes and mounts. Preserve Garrison GUID,
bundle key, archive namespace, original credits and normal/Garrison isolation.
Run `tools/release_073/check_identity.py --archive <final.sga>` before compilation
and against the final assembly. Validate strict version, ZIP CRC/readability,
member layout and embedded SGA hash. No installation or publication.

Provide a new supported entrypoint and `docs/DEVELOPMENT_080.md`. Explain how to:

- inspect and restore a named input or asset family to original paths without
  overwriting edited files;
- prepare/cook/read back an existing building and animated unit using retained
  inputs, including the recent skirmisher/buffalo/Hideout assets;
- start a new asset and integrate it through an explicit changed-member policy;
- make later SCAR/tuning/UI changes using fresh validation and native compilation;
- carry compiled-only owning-resource overlays when replacing affected actors.

The 0.8.0 preservation builder may be frozen for reproducibility, but it must not
be advertised as a universal future-edit builder. Future releases need their own
approved changed-member policy; preparation helpers and recovery storage must
remain usable without relying on retired historical delivery containers.

## Verification and retirement sequence

1. Finish the canonical inventory, hashes, dependency closure and classifications.
   Save one retention/retirement manifest with resolved physical paths, owners,
   restoration/rebuild routes and exact expected hashes. Reject source drift.
   Normalize extended Windows path prefixes, case and junction targets before
   matching dependencies. Inspect linked Blend libraries and other external
   media/cache references as well as FILE images. Map every current released
   asset family to its masters, textures, rigs, exports, recipes, native donors
   and compiled-only overlays; a missing required current dependency blocks the
   claim that development can resume across all assets.
2. Create and fully read/verify recovery bundles before removing any original.
   Test safe restoration, aliases, predecessor hierarchy, corrupt data, stale
   hashes, traversal, edited destination refusal and missing storage links.
   Keep the restoration tool, index and bundle checksums available outside their
   own archive. Test clean recovery without reading retirement candidates.
3. Calculate projected retained logical and allocated bytes, including all stores,
   rollbacks, 0.8.0 delivery and evidence. Target a projected ceiling of
   **5,700,000,000 allocated bytes** to leave margin below the final 6 GB cap.
   Do not discard editable inputs if the projection fails. Report the shortfall
   instead. Report temporary restore/build headroom separately.
4. Qualify the current source with fresh inheritance/validators, an isolated real
   native source build, and representative native building/animated-unit asset
   rebuilds. Include a recent asset and the older packed-input path. Serialize
   Blender/cooks and preserve unrelated unsaved Blender work and failure logs.
5. Verify the 0.8.0 ZIP, exact current archive, source/input closure and rollbacks.
   Review the exact retirement manifest against all preservation gates.
6. Refresh hashes immediately before each approved deletion. Operate only inside
   checked owned roots, skip junctions, stop on unknown/new/edited content, and
   retain a compact operation ledger. No unrelated directories are moved/deleted.
7. Rebuild/restore again after retirement from the retained inputs, verify package
   equality and all protected source/normal/rollback hashes, recheck junctions,
   and independently measure final retained allocation across both roots.
   Use empty staging and retained inputs only for post-retirement qualification.
8. Publish exact before/after bytes, reclaimed bytes, artifact hashes, recovery
   commands, asset readiness results and any limitations. Refresh the development
   handoff and storage policy without weakening earlier frozen release evidence.

Source/static checks, native source compilation, asset cook/readback, package
verification, import, fresh-match behavior, save/load and multiplayer remain
separate gates. Unobserved game behavior stays explicitly unverified. No claims
that every historical recipe already works: resolve required readiness gaps or
list the specific blocked asset before reporting development readiness.

## Approval boundary

The user has authorized the goal and the rollback/retirement approach. This design
defines the concrete preservation and destructive scope for review. Implementation
and retirement begin after design approval; any larger deletion scope or loss of
editable inputs requires a new decision. No additional per-file approval is needed
for operations that satisfy this approved design and its verified allowlist.
