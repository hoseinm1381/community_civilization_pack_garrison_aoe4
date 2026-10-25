# Garrison 0.7.11

User request, 2026-10-24: quiet buffalo supervision feedback, correct cap display,
and replace unit/building civilization badges with the existing dragon. The user
confirmed these are civilization badges, not portrait icons. Garrison only.

## Implementation

1. Preserve exact delivered 0.7.10 ZIP/SGA, active source and normal hashes.
2. Give private supervision position tags a direct, static 14px icon branch in
   CardinalHUDPage. Bypass the tutorial TagAdorner (arrow, clamping, entrance
   animation). Use the official local `Misc_IsPosOnScreen` query only inside the
   presentation helper; remove the marker when the farm leaves the camera view.
3. Generate the cap presentation data from the existing buffalo default/campaign
   `required_squad/max_squad_cap` requirement. The medic population pool is a
   separate mechanic and returns the reported zero. Format count/cap as integers.
4. Use official `UI_OverrideUIProperty(pbg, "flag_icon", path)` at script load for
   the private Vietnamese EBPS/SBPS with UI extensions. This covers both units
   and buildings without changing shared Chinese assets or tuning extensions.
5. Run focused regressions, current official API/static validation, isolated
   native compile/readback, exact package-member comparison and identity checks.
   Deliver strict 0.7.11 ZIP with reports and reproducible inputs retained.

## Considered routes

Shrinking only the old tag icon leaves the inherited tutorial arrow/clamping
active, reproducing the reported problem. A local on-camera gate plus direct
marker template addresses both paths. Tuning overrides for every badge would
introduce many inherited-list edits; the official UI flag override API provides
the intended presentation change directly. Generated cap data reads the real
squad requirement instead of adding a second limit in UI code.

## Preservation and acceptance

All gameplay, tuning XML, models, native animations, 0.7.10 evidence and normal
edition files remain protected. No installation, publication or cleanup.
Native UI appearance, repeated camera pans, mixed China/Vietnam selection,
restore and multiplayer remain separate runtime gates until observed.
