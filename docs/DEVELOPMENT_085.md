# Garrison development and cold storage (current 0.8.7)

The owner continues developing in this E: workspace. Do not access or modify the
separate contributor/GitHub checkout: the owner is reducing it independently.
No synchronization or push is part of this milestone.

## Current 087 minimal fixes

087 adds Phổ Minh Tower resource drop-off and separate Skirmisher selection
grouping. Seven typed RGD overlays preserve all 086 SCAR/audio/art; four editable
XML files are updated. Read RELEASE_087_DELIVERY.md for exact rebuild inputs,
regressions and native compilation evidence. The historical 085 build recipe
does not build 087. Existing 084 rollback and compact 086 restoration evidence
remain protected.

## Minimal working release route

Current package: `output/release_085/final-v2/community_civilization_pack-0.8.7.zip`.
See `RELEASE_087_DELIVERY.md`: the delivery folder is intentionally reused, timers
are now per individual unit, and the current dispatcher is `voices_086.scar`.
The 085 build recipe and global-timer description below are historical; do not
use that recipe for the current release. Cold-storage restore commands remain
current and its package guard now recognizes 087.
Rollback: `output/release_084/delivery/final-v1`.

The accepted 084 owning archive includes compiled-only resource fixes, all custom
art and compressed spoken/effort media. 085 overlays just
`scar/vietnam/voices_084.scar` with `tools/release_085/voices.scar`; the stable
mounted filename preserves existing lifecycle imports. Do not substitute a broad
source cook, which does not reproduce that archive by itself. Keep project GUID,
burn-project NiceName, bundle key and original archive mounts.

Run from this logical Garrison root using the configured Python:

```powershell
$taskPython = (Get-Content workspace.json | ConvertFrom-Json).python
& $taskPython -B tools/verify_workspace.py --storage-only
& $taskPython -B -m unittest discover -s tools/release_084 -p 'test_*.py'
& $taskPython -B -m unittest discover -s tools/release_085 -p 'test_*.py'
& $taskPython -B tools/release_085/build.py --label review-new-label
```

Never reuse an immutable build label. Assembly validates the 084 rollback hashes,
identity before/after, every freshly extracted member, every mount, ZIP CRC and
embedded SGA. 085 permits exactly one changed SCAR; all audio, attributes, art
and gameplay member bytes must remain exact. ZIP limit is 400,000,000 bytes.
No voice generation, paid requests, downloads or game installation are required.

## Speech behavior

Successful selection/order/activity replies share one local five-second gate.
Movement, sailing and generic acknowledgements use an additional eight-second
gate. The generic acknowledgement limit conservatively covers default/right-click
commands whose target classification is unavailable in the verified callback.
Under-attack dialogue has a separate fifteen-second gate and still respects clip
occupancy. Cooldowns advance only after successful playback. They reset on local
player teardown/restart. No simulation RNG or gameplay API is introduced.

Order correlation survives travel and queues, suppressing movement on the way to
build/gather/attack and the resulting activity reply. A new command replaces that
correlation. Generic actions retain correlation through travel; attack-move
suppresses its movement/combat transitions until superseded. Pain/death media and
the existing independent effort scheduling/cooldowns are unchanged from 084.

## Independent local recovery bundles

`resources_085/*.zip` and their `.json.gz` receipts are owned recovery inputs,
not disposable caches. They retain original relative paths and SHA-256 per file.
Each bundle is fully read back before any loose original is retired. Operation
journals and allocation counts live in `consolidation_085`.

- `voice-development`: original local/cloud recordings, candidates, WAV masters,
  compressed intermediates and stock-effort development outputs. Small top-level
  voice manifests, exception reports and logs remain available for reference.
- `local-voice-tools`: the exact installed TTS/ASR Python/CUDA environment, models,
  tools, installers and incomplete downloads. The SDK checkout, recipes and lock
  files remain loose. Restoring this bundle to its original paths avoids download.
- `historical-development`, when present: older delivery readbacks and generated
  development copies. Retained release ZIP/SGA/JSON/log/text files remain loose.

Restore only what the next task needs:

```powershell
& $taskPython -B tools/release_085/cold_storage.py restore-bundle --bundle voice-development --prefix output/release_084/local/generation
& $taskPython -B tools/release_085/cold_storage.py restore-bundle --bundle voice-development --prefix output/release_084/local/compressed-v1
& $taskPython -B tools/release_085/cold_storage.py restore-runtime --prefix tool-cache/local-voices-084
& $taskPython -B tools/release_085/cold_storage.py restore-bundle --bundle historical-development --prefix output/release_083/delivery
```

Restoration verifies archive/data hashes and refuses an edited destination. It
requires enough free space for loose files. On exFAT many tiny files consume much
more allocated space than their logical sizes. Active playback media already
reside compressed inside the current SGA; keeping loose WAV copies is unnecessary
for script edits and repackaging. No additional lossy conversion was applied to
the masters. Native animation authoring tools/recovery stores remain preserved.

The interrupted indexed verification log is historical evidence only. Its
contributor-store operations are disabled at the CLI; current cleanup/restoration
depends exclusively on the independent local bundles above.

## Acceptance boundaries

Offline Lua tests and exact archive/ZIP proofs do not establish native import,
audible timing/quality, right-click command classification, save/load or
multiplayer. 084 pronunciation/acting exceptions and stock effort scheduling
approximation/female fallback remain unchanged. No fresh native compilation is
claimed for this one-SCAR presentation overlay.

## Small-file storage discoveries

On this exFAT volume the allocation unit is 262,144 bytes; tens of thousands
of small voice/state files occupy many times their logical size. Count allocated
file bytes separately from logical bytes and subtract the recovery archives when
reporting savings. Empty-directory allocation is additional and is not included
in the conservative file-allocation totals. Never infer net savings from drive
free-space movement while another project is concurrently writing to the drive.

A normal seekable ZIP writer rewrites each member header, causing many tiny
seeks/flushes on this workload. The voice bundler now uses buffered streaming ZIP
with standard data descriptors and eight bounded input reads. Runtime restoration
streams 4 MiB chunks because CUDA DLLs and the retained installer can be several
gigabytes each. Actual file hash readback, isolated restoration and edited-target
refusal remain mandatory; a smaller file alone is not recovery proof.
