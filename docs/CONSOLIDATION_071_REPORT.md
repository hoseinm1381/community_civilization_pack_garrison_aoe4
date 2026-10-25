# 0.7.1 consolidation completed — 2026-10-19

The Garrison workspace now retains approximately **2.89 GB of file data**, using
**3.10 GB of allocated file storage** across E: and F:. This meets the 3 GB
file-data target and the user's revised 6 GB allocation allowance for exFAT.

| Owned Garrison storage | Before: file data | After: file data | Allocated file storage |
|---|---:|---:|---:|
| E: active source | 2.84 GB | 1.57 GB | 1.58 GB |
| F: external inputs/output | 23.72 GB | 1.32 GB | 1.52 GB |
| **Combined** | **26.56 GB** | **2.89 GB** | **3.10 GB** |

Reduction: approximately **23.66 GB of file data**. Values use decimal GB.
Allocation is measured using Win32 compressed-file size and filesystem cluster
rounding, separately from file length. F: uses 262144-byte exFAT allocation units;
E: uses 4096-byte NTFS units. Directory metadata and unrelated mods/tool/game
installations are outside these file totals. Exact final counts are recorded in
`F:/aoe_4_temp/Community_civilization_pack_garrison_temp/consolidation_071/final-storage.json`.

## What was retained

- All **265 original Blender masters**, with unchanged bytes and paths, and all
  **965 unique external images** they reference. No Blender resaves, image-path
  changes, filesystem compression or hardlinks were used.
- Editable gameplay/localization/SCAR/project files, every FBX/OBJ mesh source,
  authoring recipes, source textures, native unit rig/material/burner templates,
  scripts/configuration and future voice preparation.
- Exact independent original **0.7.0 ZIP and SGA** in
  `archives/release_070_rollback/`.
- Current **0.7.1 ZIP and SGA** in `output/release_071/delivery/`.
- All required native/decoded rebuild inputs and historical diagnostics, including
  the 1752 audited log files and failed-build evidence, preserved as plain required
  files or lossless indexed input bundles. Reports and hash evidence remain.
- The normal edition remains unchanged: **545 files** verified against its
  pre-consolidation snapshot. The active gameplay/project snapshot contains
  **404 unchanged files**.

## What was retired or consolidated

Obsolete release archives, regenerable native cook/readback/staging/prototype
outputs, preview galleries, `.blend1` backup files and Python bytecode caches were
retired only after rebuild, retention and independent-review gates passed.
The final successful rebuild's temporary outputs were retired separately after
its package hashes reproduced exactly. **24076 empty plain directories** were
removed while preserving every configured junction and target container.

The protected `resources_071` store holds **9649 original-path resource keys**.
Large numeric JSON uses lossless gzip; the native/diagnostic ZIP stores **6019
distinct payloads for 9493 original paths**, occupying 238687521 bytes. Every key
was decompressed/read and checked against its original length and SHA-256.
Required Blender images and unit templates stay plain at their existing paths.
Restoration creates independent files and refuses to overwrite edited inputs.

See [the development guide](DEVELOPMENT_071.md) for input restoration and current
build commands. Historical release tools may refer to retired caches; the current
entrypoint is `tools/build_release_071.ps1`. Future gameplay edits require a new
release policy and explicit changed-resource overlay, rather than bypassing the
0.7.1 frozen-source preservation check.

## Rebuild and preservation evidence

1. Fresh native source compilation passed before retirement and again afterward:
   **369 instances validated**, no reported build errors, source unchanged.
   Both compiles produced source-validation SGA SHA-256
   `d319188a01a2faf192c25927b3585814a4d60fe1ce4bc8c2f3f6848859e307ca`.
2. Fresh Garden native cook/readback and weighted archer2/archer4 three-LOD native
   geometry comparisons passed. The archer4 compressed-input rebuild exercised
   the corrected-normal and predecessor-snapshot validation branches.
3. The 0.7.1 owning archive was assembled and independently extracted/read back:
   **all 1243 native member hashes and TOC mounts match exact 0.7.0**. This preserves
   compiled-only lifecycle/selector/producer fixes that source-only compilation
   could otherwise lose.
4. Strict four-member ZIP verified: manifest/version/identity/credits, ZIP CRC,
   and embedded SGA SHA. The complete rebuild after old files were removed
   reproduced the exact 0.7.1 SGA and ZIP hashes.
5. Independent reviews checked the exact retirement allowlists, protected sources,
   image/template closure, resource-store integrity, rollback, package and budget.
   Final protected-input verification and all seven junction checks passed after
   cleanup. **12 focused integrity/path/bundle tests passed**.

Current package: **131964386 bytes** (about **132 MB**).

| Artifact | SHA-256 |
|---|---|
| 0.7.1 ZIP | `6782ab9af99aad362b3bf14b6af09cb6ba9224fbea961597aa92d7383d521d8f` |
| 0.7.1 SGA | `d622e6e1b045d595a059f48646b32a0303ea66bb1631eca96ab4baa4e8290f0c` |
| Original 0.7.0 ZIP | `d44688715b6116e4cb0d4e1527dc01837d2e13f0dbd4655460d8e62c93a9faeb` |
| Original 0.7.0 SGA | `63e148ab21f0f2e157bee99a414b39c53284ceb9584812026cadfa47cc5accd2` |

Compact operation ledgers, independent reviews, stop/correction evidence, retained
input hashes, baseline snapshots and exact post-cleanup proofs are protected in
`consolidation_071/`. Main and final operation ledgers are lossless gzip files.
`output/release_071/package-post1.json` and `native-source-post1.json` record the
successful rebuild after retirement.

Client import, lobby selection and native match/appearance testing were not run.
Native resource equality and cook/package proof are separate from those user gates.
