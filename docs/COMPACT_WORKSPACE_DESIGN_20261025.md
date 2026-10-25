# Compact contributor workspace: audit and proposed design

Date: 2026-10-25. This approved design is implemented in the compact candidate; see docs/compact/READINESS.md. Later owner steering explicitly permits omitting WAV masters from the upload. The sections below record the initial audit/design.
User selected a self-contained current working repository with history kept separately.

## Measured cause

The inspected folder is `F:/aoe_4_temp/community_civilization_pack_garrison_aoe4`.
Before these audit files, it contained **24,876,544,931 logical bytes** (24.88 decimal GB).
`development-data` accounts for 12,421,901,415 bytes; `.git/objects` accounts for
12,388,518,032 bytes. Everything else is roughly 66 MB. Git retaining the committed
binary packs explains the second substantial copy; this is normal Git storage,
not evidence those objects are abandoned or safe to delete. Changing `.gitignore`
or deleting tracked packs in a later commit would retain their old blobs in history.

The F: filesystem is exFAT with 262,144-byte clusters. Cluster rounding gave an
estimated 25,477,251,072 allocated file bytes at the initial scan. This estimate
excludes directory/filesystem metadata. No directory links were traversed in this
checkout. Small-file overhead is secondary to the actual binary data here.

The snapshot contains 151,548 logical files (19,771,569,771 expanded bytes).
It includes current material plus many historical deliveries, readbacks and experiments.
Examples of compressed chunk content, which overlap and must not be summed:

| Group | Compressed chunk GB |
| --- | ---: |
| Local 0.8.4 voice-production tree | 3.66 |
| Editable Blender/art masters | 2.32 |
| 0.8.0 nested recovery payload | 1.15 |
| 0.8.4 delivery tree, including intermediates/readback | 0.90 |
| 0.8.2 animation delivery history | 0.89 |
| 0.8.3 delivery history | 0.86 |
| Qualified art exports | 0.30 |

Content-addressing already deduplicates identical chunks. It does not identify
semantic duplicates such as a complete ZIP, its SGA, extracted members, earlier
versions, or float/PCM renderings of the same take.

## What currently works and what is still missing

The 15 contributor smoke tests passed in this audit. The original owner's storage
check passed for all seven links. All 9,702 spoken jobs resolve through their accepted
state to entries with matching audio SHA-256 in the snapshot index. This check
compared state/index metadata; it is not a fresh decode/hash pass over all recordings.

Existing offline restoration and exact package reproduction entrypoints are present;
this audit did not rerun full snapshot verification or archive reproduction. The
previous proof is retained, with its original scope. Root development documentation
already warns that general native builds are not portable merely by configuring
junctions. Sound installation/generation and buffalo animation helpers contain
machine-specific paths to F:, installed user software, personal extraction/skill
modules and the owner's game installation. `StateStore.ready` also reads absolute
recording paths, so moving accepted files without a verified working-state mapping
would make existing recordings appear unavailable. Frozen evidence must stay intact.

Blender and Garrison cover art work, while native attribute compilation also requires
a compatible owned AoE4 Content Editor. Existing audio must be usable without AI.
New local speech requires the pinned compatible TTS/codec/ASR software and suitable
hardware, not just any local AI model. No cloud key or paid service should be needed.
Installed tools and model weights remain dependencies, outside version control.

## Proposed layout

Create a new independent candidate at
`F:/aoe_4_temp/community_civilization_pack_garrison_aoe4_compact`.
Preserve this repository and the active E:/F: authoring workspace unchanged.
Use a fresh local Git history for the compact candidate, retaining all original Git
history in the existing repository. Do not delete, rewrite, force-push or publish.

Keep readable gameplay/localization/SCAR/RDO, recipes, tools, tests, attribution and
current guides at the root. Keep a self-contained hash-indexed lossless current-data
store in the candidate, with restore-on-demand editable assets. No essential asset
pack may require a separate service or an owner's private disk after the clone.

Retain current editable geometry, texture/media sources, rigs, the approved buffalo
r4 edit, required donors, native animation inputs, registration recipes, and accepted
sound masters and their casting/scripts/quality/provenance. Retain the current owning
SGA/package source and whatever compiled-only overlays and immediate baseline the
supported rebuild actually requires. Older version numbers alone never identify
obsolete art: active assets originate across several historical releases.

Keep rollback releases, rejected takes, failed experiments, diagnostic media and
frozen historical reports in the original preserved repository. Exclude these from
the candidate only after checking they are outside the current dependency closure.
Split coarse nested recovery bundles into required payloads if needed; preserve
original containers and hashes in the historical repository. Readbacks and packaging
intermediates can be omitted only with a demonstrated regeneration route.

A measured conservative profile selects 62,757 files and 8,533,938,911 compressed
chunk bytes before repack/index overhead. It still includes broad recovery/history
and therefore is **not the minimum or a proven complete build profile**. Copying
whole existing packs for that selection would retain 9,434,418,608 bytes because
packs mix retained and excluded chunks. Repacking is necessary. Do not promise a
final size before closure analysis and verification. A fresh Git clone will still
store both the checked-out binary data and its Git representation.

## Portability and completion criteria

1. Build an explicit dependency manifest for current gameplay, art, animation and
   accepted voices, following current recipes and final changed-member policy.
   Report every excluded category and its preserved historical location.
2. Repack required payloads losslessly; verify every retained file hash and every
   referenced dependency. Produce measured core versus history totals. Preserve
   all current required authoring sources even if they prevent a smaller target.
3. Provide supported commands using checkout-relative roots and locally configured
   executable/environment/model paths. Keep frozen evidence unchanged; use separate
   verified working copies for rebased recording state and live configuration.
   Bundle required helper source or replace personal imports with installed APIs.
4. Test from a clean isolated restore with original owner roots unavailable to the
   commands. Test source identity, missing dependency failures, edited-file
   preservation, art/texture and recipe path closure, accepted voice lookup and
   optional local-speech setup. No automatic synthesis/download/billing calls.
5. Reassemble 0.8.4 with the installed archive tool; require the original SGA SHA-256,
   namespace `b7fcea91257b408fb9e8ae4d8bc402e1`, all 11,973 member hashes/mounts,
   and the original matching ZIP. Then verify the current selective source/art
   build route independently; a package reproduction does not qualify native cook.
6. Report offline checks, Content Editor compile, Blender/Garrison cook/readback,
   TTS generation, client import, native behavior, save/load and multiplayer
   separately. Do not claim complete workstation portability from smoke tests.
7. Measure final working tree, Git objects, and restored working size separately.
   Review the candidate before deciding whether to replace the upload folder.
   Nothing is pushed, deleted or reclaimed as part of this design.

GitHub recommends keeping large generated files outside ordinary Git or using LFS;
its repository guide lists a 10 GB on-disk recommendation. A working tree plus
12.39 GB object database is unsuitable as a compact contributor handoff:
https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits
A self-contained repository can still be several GB because editable masters are
real authoring data. LFS or separately hosted packs would change the selected layout
and require a separate decision; neither is assumed here.

Machine-readable evidence: `docs/evidence/storage-audit-20261025.json`.
No existing project, pack, Git object, audio or art source was changed or deleted.
