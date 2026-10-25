# Castle landmark visibility and automatic stealth — 0.5.2 diagnostics

On 2026-10-18 the user requested final **0.5.3** without another native test.
The historical diagnostic gates below no longer block delivery. The 052-C compiled
payload is finalized in `docs/RELEASE_053_REPORT.md`; no final 0.5.2 was created.

The user accepted 0.5.1 traps and monastery but reports both Castle landmarks still
invisible after completion. The two supplied screenshots and current warnings log
are preserved under `output/release_052/baseline/user-regressions`. Before the user's
Garrison import was removed, the installed archive hash was verified to match the
exact delivered 0.5.1 SGA. The immutable repair baseline is the preserved delivery.

The previous selector-name explanation did not resolve the native failure. Working
Feudal landmarks also omit those names. Physics-action names must not be treated
as proof of required render-selector names. The Castle resources contain the
authored mesh; native rendering has not been established by static truth tables,
source previews, or the previous reference cook. No further selector-name change
is authorized as an assumed fix without a discriminating result.

The user chose a diagnostic test before finalizing the repair. Diagnostic A restores
only the principal model strings in three private stamps to their original stock
Chinese models, through the same existing landmark actors, tiers and attachments.
It retains the 0.5.1 custom resources for later repair. This is a temporary comparison,
not a replacement of the final Vietnamese designs.

- ZIP: [community_civilization_pack-0.5.2-diagnostic-a.zip](F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_052/community_civilization_pack-0.5.2-diagnostic-a.zip).
- ZIP SHA-256: `b08e277d9515a3c39e2e57d747755a1debe07b0be61758600d36370cd72269de`.
- Embedded SGA SHA-256: `780306a7e7b2d5aaaaadbbf03c893c0649ff0beb14b946c5af1dcdb47f486ed8`.
- Exactly three stamp members changed; **808 members remain byte-identical** to
  0.5.1. No added/deleted members, active source changes, actor changes, or new IDs.
- Stock strings fit the verified original native allocations. Only string bytes
  and their length fields change. Native IDs, pointers, layout, transforms, visual
  membership, terrain objects and every nonmemory chunk remain unchanged.
- CRC, exact four ZIP members, manifest/SGA identity, dependency presence in the
  official catalog, complete archive comparison and preserved-input checks passed.
  Independent review confirmed the package and all three stamp changes.
- No geometry/source cook was needed for this comparison of existing stock models.
  Native visibility remains pending; offline archive verification is not a render test.

## User comparison

Close AoE4 and import this diagnostic ZIP through Garrison. Select the pack as both
Game Mode and Tuning Pack, choose China and then Vietnam. Use fresh matches.

1. Build **Resistance Headquarters** and inspect the stock model during construction
   and after reaching 5000/5000 HP.
2. In a second fresh match, do the same with **Imperial Citadel**.
3. Report whether each stock model is visible during construction and after completion.
   A selection outline or placement ghost alone does not count as normal rendering.

If stock models render after completion, continue investigating custom model loading,
collection/material rendering and the custom-resource reference contract. If a
stock control also disappears, investigate that actor's completed stamp/attachment
and state propagation before editing custom geometry. Mixed outcomes are evaluated
per landmark. Further probes must change one layer at a time.

The final repair must restore both custom designs, retain the agreed triangle cap,
native selectable/repairable ruins and victory owners, and cover all default/Cordoba/
campaign consumers. No permanently visible geometry or scripted replacement entity
may bypass lifecycle behavior. Final `community_civilization_pack-0.5.2.zip` is not
created until the custom completed models have passed the agreed native visibility
gate; destruction/ruin selection/repair, colours, access and victory checks remain
separate acceptance scenarios. Accepted trap and monastery bytes remain preserved.

Rebuild this diagnostic with the configured Blender Python and
`tools/release_052/diagnostic_a.py`, retaining completed runs rather than overwriting
them. The initial verification-only failure compared Python schema Element identities;
it was corrected to field/layout equality and is retained in `attempt-01.json`.

## Stock control result and Test C

The user confirmed both stock landmark models work in Diagnostic A. Screenshots
and the result are retained in `output/release_052/user-native-results/diagnostic-a`.
This narrows the remaining issue to custom resource rendering; it does not prove
which material setting causes the failure.

Test B changes only `options.z` from 0 to 1 in the two structure materials of each
custom landmark material resource, matching the stock building convention. The
material parameter's engine meaning is not documented, so this remains a probe.
Test C includes that same probe and the automatic-stealth candidate described below.
Use Test C instead of B for the next combined native test.

- ZIP: [community_civilization_pack-0.5.2-test-c.zip](F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_052/community_civilization_pack-0.5.2-test-c.zip).
- ZIP SHA-256: `250145a7ec9acada187dab72c1f3b64f28577fe6db552c427d353a81c744fcdd`.
- Embedded SGA SHA-256: `af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456`.
- Exactly **four of 811 archive members changed**, with 807 byte-identical to
  0.5.1 and no added or removed members: three landmark `.rrmaterial` resources
  and `attrib/abilities/vietnam/vn_activate_stealth_forvills_vit.rgd`.
- Archer activated stealth, traps, monastery, landmark stamps, geometry, native
  lifecycle owners and all other archive resources remain byte-identical to 0.5.1.
- Archive unpacking produces decoded XML sidecars. They are generated readback
  files, not additional archive members; the exact allowlist uses SGA inventory.

The user reports automatic villager stealth flickering while activated archer
stealth works correctly. The passive ability currently self-disables while active,
has a six-second recharge and queues passive casts. The isolated candidate changes
those three fields to false, zero and false respectively. It retains the native
ten-second graph, 33 m requirement, carrier roster, HQ availability rules, duration
and all IDs. The graph explicitly disables stealth at its timer boundary, so
continuous camouflage cannot be claimed from scheduling changes alone.

The isolated source cook exited normally with code 0 and validated 280 instances.
Compiled readback differs at exactly those three fields; reversing them reconstructs
the old RGD byte-for-byte. Receipts and logs are under
`output/release_052/stealth/native/rsc03`. Active source remains untouched; the
editable one-XML candidate is retained under `stealth/diagnostic-c` until acceptance.
Live Reload stayed disabled; the shared native build lock was used. No live Blender
scene was changed. Frozen prior inputs and the normal edition remain protected;
the other task's newly added `release_060` inputs are excluded and untouched.

After closing AoE4, import Test C and start fresh China → Vietnam matches:

1. Complete each Castle landmark and inspect normal rendering at 5000/5000 HP.
2. Leave a stationary villager inside HQ range for at least 45 seconds, away from
   enemy detectors. Check rapid flickering and ten-second timer boundaries.
3. Check range exit/reentry, loss of the last HQ, gathering/combat/detection, and
   the unchanged archer activated stealth as a control.
4. If the custom models render, check destruction, persistent selectable ruins,
   interrupted/resumed repair, colours, access and landmark victory separately.

Test C is an acceptance candidate, not the final 0.5.2 release. Package checks and
the native source cook passed; client import and native-match outcomes remain
pending. Retain all diagnostic inputs/readbacks until those results are known.
