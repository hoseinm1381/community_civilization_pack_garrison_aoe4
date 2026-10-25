# Garrison 0.7.12

Built 2026-10-24 from the exact delivered 0.7.11. Credits: hosein81 and chilly5.

## Delivered changes

- All three Lam Son Skirmisher weapon tiers: wind-up **0.25 -> 0.50 seconds**;
  both reload duration bounds **1.375 -> 1.125 seconds**. Their configured
  wind-up-plus-reload sum stays 1.625 seconds. Aim, wind-down, damage, projectile
  and other weapon fields are preserved. Native animation/DPS behavior still
  requires a running-match check.
- The buffalo counter publishes an explicit local click-enabled value and
  resolves the local player through stable `Player_GetID` equality. A click
  selects and focuses the camera on the next living owned buffalo, sorted by
  stable squad ID and wrapping. Zero units, replay, missing/defeated/non-Vietnam
  players remain guarded. Selection and camera focus issue no orders, including
  for working buffalo.
- Work marker: **48px outer badge / 40px icon**, previously 14px/10px. Opacity
  is 0.95. It remains steady, owner-only, hidden off camera, and removed when
  supervision ends. The tutorial arrow/clamping path remains bypassed.
- **Vietnam actual influence and display radius increase 2m**, as explicitly
  authorized after the display-only limitation was explained. This affects all
  36 positive private district-generator blueprints across 74 variant scopes.
  The scripted tunnel-network reaches also increase 2m. Other civilizations'
  native generator resources remain unchanged.
- Tunnel destination ground clicks use **8m from the building footprint edge**,
  including large Town Centers. The nearest eligible owned, completed, connected
  building is selected. A closer foundation, disconnected building or unrelated
  unknown footprint can no longer steal an otherwise valid exit. Invalid clicks
  retain feedback. Cooldown, loading/transit, unit eligibility and recovery code
  remain preserved.

## Investigation

The previous counter depended on UI-model replay bindings for button availability
and a reference-equality player lookup. A regression reproduced a valid native
player ID represented by a different wrapper: count display could continue while
the local click command was unset. Stable-ID lookup and the explicit presentation
boolean address that path. Tests also use the actual current engine `ui.scar`
command wrapper (`__Type` / `__Value`) to dispatch the global callback and verify
selection plus camera cycling.

The existing tunnel geometry already measured footprint edges rather than
centres. The user's prior match log showed nearby clicks assigned to a foundation
and rejected. The old resolver deliberately picked the closest building before
checking completion/connectivity. The new resolver filters eligibility during
the search, preserves deterministic distance/ID ordering, and accepts the 8m
boundary with a small floating-point tolerance. The native position-target
ability and COMMITTED_ABILITY handoff remain unchanged.

Current official district-generator schema exposes `range_metres` as the
confirmed control. No separate supported display offset was qualified. The user
explicitly chose the actual-reach increase as well; this release does not label
the influence change as visual-only.

## Verification results

- **17 focused tests passed**, following recorded failing regressions. They cover
  all weapon tiers and the timing sum; native player wrapper identity; actual
  command wrapper dispatch; selection/camera cycling and wrap; count/cap and
  lifecycle preservation; marker size/static state; +2m influence/network data;
  an 8m edge click on a large TC and rejection just beyond it; foundation/unknown
  neighbours; enemy/disconnected filtering and deterministic ties.
- Fresh extension inheritance: **198 local / 5,758 official** blueprints,
  **zero errors**. Exact inherited extension IDs are retained for all new range
  overrides. No new PBG identities are allocated.
- Installed tuning validator: **377 instances, zero errors**, 131 existing
  warnings and one unresolved-reference summary retained. SCAR static validation
  has zero errors: one presentation loader-contract warning and five existing
  tunnel warnings remain; generated tunnel-building data has no diagnostics.
  Loader/import paths and engine-owned squad observers were inspected.
- MCP checks: new camera API has current official documentation and matching
  official `camera.scar` usage. Four existing tunnel calls are flagged for absent
  indexed official usage; all four match exact current installed API signatures
  and remain unchanged. The prior native tunnel log demonstrates the vector,
  tick and transport path. Unknown entries are local helpers and Lua operators.
  See `mcp-check.json` and `mcp-resolution.json` for the unsuppressed results.
- **41 XML/XAML files** pass .NET XmlReader and ElementTree checks.
- Final isolated native source build **v2 passed**, validating 377 instances,
  preserving staged inputs and passing pre/post archive identity checks.
  Final SCAR members match native readback. XAML uses the qualified loose-UI
  package route; the source burner does not compile these XAML templates.
- Native attribute readback confirms every authorized timing/range scalar.
  Final integration copies only those values into exact baseline actor documents,
  retaining compiled-only overlays and KEYS order. Reversing the approved scalar
  edits reproduces the original serialized typed documents exactly.
- Final archive: **44 existing members changed, none added, 1,417 total**.
  All **1,373 untouched member hashes** and every original mount match 0.7.11.
  Models, native animation resources, textures, existing badges and cap data are
  preserved. Normal source and protected prior rebuild inputs pass their hashes.
- Final ZIP readability/CRC, exact three-file layout, strict `0.7.12` version,
  embedded SGA hash and namespace `b7fcea91257b408fb9e8ae4d8bc402e1` passed.

## Delivery and hashes

`output/release_0712/delivery/final-v1/community_civilization_pack-0.7.12.zip`

ZIP SHA-256: `b942e131a05d7d35da0251f5c53c4b1e77f89af776a14cb126051b193530437e`

SGA SHA-256: `e54fad91112350c70dab1c8cc826da26aa5c6ae9a6754244ed9141fe75d75eb1`

Complete member hashes/mounts are in `verification.json`; the strict package
receipt is `delivery-proof.json`. `art/recipes/release_0712/integration.json` pins
the member payloads, tools, tests and proof files. Exact 0.7.11 ZIP/SGA, source
snapshot and normal/prior-input hashes are frozen under `output/release_0712/baseline`.

## Reproduction and acceptance

Version-owned tools are under `tools/release_0712`. `research.py` captures current
official inheritance and baseline native ranges. `apply.py` derives all allowed
edits from the frozen source; `source_policy.py` rejects every other source change.
`native_compile.py <new-label>` runs an isolated build under the shared native
lock. Final successful native attempt is `v2`; `v1` and its logs remain preserved.

Run `tools/build_release_0712.ps1 -Label <new-delivery-label> -NativeLabel v2`
to rerun static/parse checks and assemble from the completed native attempt.
Existing labels are never overwritten. After source edits, first build a fresh
native attempt and use that label. The final assembly validates staged inputs,
copies only native-confirmed attribute scalars, compares every member/mount,
checks identity and tests the ZIP. No installation, publication or cleanup occurred.

**Fresh-match acceptance remains unverified for 0.7.12:** physical counter mouse
clicks/hover and camera cycling, the enlarged marker at HUD scales, skirmisher
release timing and motion, native influence selection/placement coverage, tunnel
ground clicks around TC edges and crowded foundations, save/load and multiplayer.
Test China and Vietnam together and retain 0.7.11 for rollback. Source/native
build/package checks are not reported as running-game validation.
