# Shrek Showcase animation mechanism — inspected 2026-10-24

Found the exact screenshot's Modding Showcase 0.1.1, author overbait, installed
and enabled as bundle `modding_showcase_full`. The live public catalog lists the
same version, summary, date and author:
https://raw.githubusercontent.com/AOE-Garrison/garrison-mod-catalog/main/catalog.json

## Verified playback wiring

The packaged chain is:

```text
cow_x02_villager_squad
  → squad_ability_ext: private dance_once ability
  → ability_activate_entity_tree = cheer_toggle
  → native infantry animation state routing
  → private Shrek animator
  → cheering\idle_calm_cheering_01 ... _08
  → replacement dance motion in Shrek's private RHKA
```

The squad loads `cow_x02_villager_unit`. Both squad and entity use a `spearman`
state-model schema; the entity's `animation_action_tree_ext` opening branch is
`infantry`. The private `cow_x02_prop_visual` attachment sets `parent_animator`
to `art\scenario\a4etk_shrek_fitted_v3\a4etk_shrek_fitted_v3` in default,
campaign, cordoba and xp3 variants. The tuning archive actually contains that
stem's RGM, RGO, RHKA and rootmotion resources.

`abilities/gameplay/spearman_dance/dance_once` is self-targeted,
`can_be_interrupted=true`, and has zero recharge time. Its UI debug description
is “Dance until another order”. Its entity activation tree is `cheer_toggle`;
the squad activation/deferred tree fields and direct `entity_tree` are empty.
These are packaged settings; stop/repeat/interruption behavior was not newly
observed in a match during this inspection.

The game-mode SCAR deploys Shrek and the other demonstration units, adds starting
resources, and schedules deployment. It contains no dance-order controller,
per-frame bone animation writer, or automatic dance command. The ability and
native animation resources perform this feature.

## Confirmed replacement motion

Compared with the **matching current stock base_spearman owner**, not a different
spear/shield library:

- Shrek's library contains 210 clips; stock base_spearman contains 182.
- All eight named cheer slots, indices 160–167, contain the same replacement
  motion payload. Each uses a 48-bone skeleton, 225 frames and a duration of
  7.466666698 seconds.
- Every one of those eight payloads differs from its same-named stock clip.
  Several stock durations also differ. The sameness across all eight means the
  replacement covers whichever of these variants the native routing chooses;
  the precise selector/random-selection policy was not decoded here.
- Garrison independently sampled Shrek's `cheering\idle_calm_cheering_01` and
  the stock clip of that exact name. They are not equal. Twenty-four bones move
  in Shrek's sequence, including root, pelvis, both legs, spine, neck/head, both
  arms, palms, ankles and toes. This is whole-body motion.
- The sampled extracted reference motion reports no travel. Moving root-bone
  poses do not by themselves establish gameplay displacement.
- The native container uses predictive compressed animation data. The shipped
  compiled files do not identify the creator's Blender source, FBX take, motion
  provenance, encoder source, or export command. The differing data proves
  replacement relative to stock; it does not prove that every key was authored
  from scratch.

This establishes **private native clip replacement behind an existing native
ability trigger**. It is stronger evidence than a model using stock motion.
It does not establish arbitrary direct playback of a Blender Action from SCAR.

## Relevance to the buffalo

The reusable architecture is a private animator/library, valid motion under
names already consumed by the unit's native graph, and preserved state routing.
For ordinary buffalo idle/walk replacement the existing navigation slots are the
appropriate targets; a dance ability need not be added.

Shrek's 48-bone human motion cannot be copied directly onto the buffalo's
45-bone cattle skeleton. The compiled example demonstrates that replacement is
possible in the engine. It does not supply the still-missing cattle authored-pose
encoding implementation. The existing cattle roundtrip and this concrete native
replacement example are separate useful foundations. The installed two-prototype
public export catalogue is a tool admission boundary, not an engine limitation.

No changes were made to the installed Showcase mod, Garrison extension, normal
edition, or production 0.8.1 package. No code from the mod was executed.

## Evidence

`output/release_081_animation/showcase-inspection-20261024` retains the installed
bundle metadata, verified archive listings, selected extracted resources,
flattened compiled tuning fields, native sample results and `motion-comparison.json`.
The mode archive's two RDO-style `.rgd` resources are not attribute-RGD decoded;
their parser errors are recorded rather than interpreted as empty data. All
animation-relevant tuning resources decoded successfully.

Archive verification checked every stored member's recorded CRC/SHA1; header
signatures were not validated. Whole-file SHA-256:

- Mode: `c9e356cfeb13ef7dfd51c00dcd9f9090fa628da80647fcac6ee178d72b2c05eb`
- Tuning: `73cf2e2b4688b01f74a1b74306e36a97a17587eedcc48e2bc753dd0db06f081f`
- Shrek RHKA: `47060e3bae35ea01ab70017181c28451d5fc6f8fffa0c0600b48256140eec966`

Inspection and comparison scripts are in `tools/release_081_animation`.
Native game playback, interruption, save/load and multiplayer were not retested.
