# Garrison 0.8.7 â€” Phá»• Minh drop-off and Skirmisher selection

Delivered: `output/release_085/final-v2/community_civilization_pack-0.8.7.zip`.
The existing 085 delivery folder is reused; 086 ZIP/SGA were replaced only after
complete verification. No duplicate audio bank or new release delivery folder.

- ZIP: **284,924,620 bytes**, below 400,000,000 bytes.
- ZIP SHA-256: `13911d70f58bd818699179ceb7ddf16fe46cabb401168f06542ad7bdd5cd37f1`.
- SGA SHA-256: `c910eaa6e4c1da3e18aee6fc261cd1bb173f100efe573198cfe7398765099a99`.
- Fresh extraction: all 11,973 members verified; exactly seven RGD members changed,
  11,966 members and every mount preserved exactly, zero additions/deletions.
- All audio, artwork and SCAR members are byte-identical to 086, including the
  independent-unit 5s/8s/15s cooldown dispatcher and stock effort preservation.
- Actual corrected native source compilation: **377 instances**, completed burn
  and copied native archive. Final package combines verified narrow native field
  contracts with the owning archive, preserving compiled-only resource fixes.
- Source/static: 3 source regressions (including all variant subcases), 45 chatter/
  storage tests, fresh inheritance audit and .NET XML parse passed. Final tuning
  validation: zero errors and 131 existing version-2 corpus warnings.
- Game import, drop-off/pathing and selection UI, save/load and multiplayer remain
  untested. No installation or publication was performed.

## Scope and diagnosis

Phá»• Minh Tower uses the core wonder parent and a complete extension list. Neither
its default nor campaign inheritance chain contains resource_drop_off_ext. The
working mod Hideout supplies this explicitly. 087 adds exactly that accepted
resource/drop-off contract and its resource_drop_off/economy_building tags to both
tower variants. Food, wood, gold and stone are accepted, with zero drop-off delay.
No new interactive-object entry is added: the working Hideout also uses only
repair, construct and seek_shelter_destination there. Landmark repairs, training,
art, garrison capacity, footprint and other behavior are preserved.

All three Skirmisher squad ages inherited squad_ui_ext/race_list/race_data/info/
selection_group=archer from the official core Archer. Override that one string
with vn_skirmisher for default and campaign; the tower-training aliases inherit
it. Combat classification, attack bonuses, stealth ability names and upgrades do
not change. The owning archive materializes six squad records, nine variant
selection strings in total; all must be patched because compiled inheritance
already resolved them.

## Rebuild and preservation

Editable changes: tower EBPS and three ordinary Skirmisher SBPS XMLs. Original
bytes are retained in output/release_085/087-before-source.zip; the entire assets
hash map and exact allowed changes are in 087-source-before.json and
087-source-change-policy.json. New append identities use six unused local list
IDs; no blueprint identities are created. Fresh official audit proves absence
of an inherited drop-off extension before append. Structural undo verifies every
other source value, order and identity remains unchanged.

Use tools/release_085/compile_087.py for real isolated Content Editor reference
compilation, and package_087.py for the one-time guarded owning-archive replacement.
Neither whole native source archive nor broad source cook replaces the accepted
owning archive. The package recipe requires fresh native readback agreement for
each changed property and typed exact-byte undo; all other members and mounts
must compare exactly. Codec dictionary metadata is restored during undo after
added extension keys are removed. Fresh full extraction uses temporary NTFS.

The existing final-v2 delivery folder is reused. Retain 084 independent rollback,
086-replaced-rgd-rollback.zip, compressed 086 metadata and voices_086.scar; together
with prior recipes these allow reconstructing 086. No voice generation, extra
model/tool download, game installation, publication or GitHub-folder access.

## Evidence and acceptance

Regression tests observed eight original failures (six selection variants, two
tower variants), then passed after the fix. Three source regressions now also
verify exact scoped preservation across all assets. .NET XmlReader passes all
four edited files. Fresh official inheritance: 198 local/5758 official
blueprints, zero errors. Installed tuning validator: 377 instances, zero errors,
131 pre-existing version-2 corpus warnings, plus unresolved external-reference
summary. Existing chatter/storage tests: 45 passed, including 087 package-guard
regression observed failing then passing. Native compilation and package proof
are recorded separately below when complete.

Native acceptance remains separate: import, fresh-match food/wood/gold/stone
return to Phá»• Minh Tower, villager pathing, mixed Archer/Skirmisher selection,
age upgrades, tower-trained selection, save/load and multiplayer. No in-game
acceptance is claimed by static tests, compiled data or package verification.

The initial native process was interrupted before completion. The next real
compile completed but package readback rejected two classification tags because
the authoring recipe used string rather than the donor enum scalar type. The
recipe and regressions were corrected; the fresh final compilation completed
successfully with all 377 instances validated.
Rejected inputs/logs remain in the compact native-development evidence bundle.

## Compact final handoff

The transient native runs (initial interrupted, rejected scalar-type attempt,
corrected successful run) are preserved losslessly in
`output/release_085/087-native-development.zip`; per-file SHA-256 hashes and the
retirement journal are `087-native-compaction.json.gz`. The current native
reference archive remains directly available as `087-native-reference.sga` and
is pinned by `087-native-reference.json`. Restore recorded staging prefixes from
the bundle before replaying source-native correspondence checks. Staged source
matches the active asset source in `087-native-input-freeze.json`.

The old 084 freeze remains immutable; its four expected source mismatches are
explicitly authorized by 087. Use the 087 source-policy regression to assess
those deltas, rather than weakening historical preservation checks. Current
source is four files different from the immediately prior 086 asset hash map.

The one-time scripts refuse to overwrite previous attempts. For reconstruction,
start with the preserved 084 owning archive, apply voices_086.scar at its stable
mounted path, then the seven payload files listed in 087-typed-deltas.json using
supported set-members --alias data. Compare every member/mount and final identity
against current verification.json. To reconstruct 086 instead, use the retained
086 replaced-RGD rollback ZIP and compressed 086 metadata. Cold-storage guard
recognizes the current 087 version. Keep all independent recovery bundles.
