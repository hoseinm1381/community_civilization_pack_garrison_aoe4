# Korea construction and Observatory repair — 2026-10-29

Updated Normal in place following the owner's native test. The screenshots and
current `warnings.log` confirm inflated private building times and an Observatory
SCAR failure. Literature generation is visible in the owner's screenshots.
These new repairs have source validation; rebuild and native retest are pending.

## Construction

Changed only existing `cost_ext/time_cost/time_seconds` scalars in 27 private
Korean buildings. Current installed `ReferenceAttributes.sga` provides the normal
core building times. Landmark times follow the Korean gameplay age rather than
the age in the visual donor's filename. No global build-rate multiplier was added.

| Building | Before | After |
| --- | ---: | ---: |
| House | 30 s | 15 s |
| Mill, lumber camp, mining camp | 40 s | 20 s |
| Barracks, range, stable, dock | 60 s | 30 s |
| Farm | 12 s | 6 s |
| Blacksmith, monastery | 50 s | 25 s |
| Siege workshop | 90 s | 45 s |
| University | 120 s | 60 s |
| Town Center and capital | 300 s | 150 s |
| Outpost | 120 s | 60 s |
| Mountain Fortress | 360 s | 180 s |
| Palisade / gate | 12 / 15 s | 8 / 10 s |
| Stone wall / gate / tower | 24 / 45 / 135 s | 16 / 30 / 90 s |
| Stone Pagoda | 6 m 20 s | 3 m 10 s |
| Gate of Reverence, Seon_deok Observatory | 7 m 20 s | 3 m 40 s |
| Gyeongbok Palace, Hall of Worthies | 8 m 20 s | 4 m 10 s |

Bulguksa Temple already has 190 seconds and remains so. The two private academy
definitions retain their custom 30-second times. The market already inherits
20 seconds. Costs, stats, lifecycle, list identities, build menus and stock Zhu Xi
definitions are preserved. Actual elapsed time depends on builder count and
active game effects; the table describes the normal blueprint time.

`korea-construction.json` records every changed file, exact XPath, before/after
value, official owner and original semantic hash. Tests restore only that scalar
in memory and require the entire remaining definition to match the original hash.
The donor parity audit explicitly allows these 27 intended corrections.

## Observatory crash

Native log at 11:24:35 reports:

```text
Modifier resource_cap_action_player_modifier could not be created.
Could not find modifier in code.
core.scar:62 -> research.scar:65 -> KoreaResearch_Observatory
```

The previous repair incorrectly treated a tuning modifier identifier as a valid
SCAR `Modifier_Create` string. Static API checks do not validate that string;
the old test also incorrectly accepted it. The exact previous function is now
a failing native-contract regression fixture with that property rejected.

Removed that modifier call. The existing per-player Korean ledger holds all
research entitlements: two initially, plus two from the Observatory once. The
native `RT_Action` channel keeps its stock cap of two and receives
`min(2, remaining allowances)` at initialization, Observatory grant, accepted or
rejected purchase, and cancellation/completion settlement. Refill after payment
allows all four purchases, even while they are pending together. Exhausting the
ledger leaves zero native payment tokens. Cancellation returns its allowance
once. Repairing or snapshotting the Observatory does not repeat its reward.

No shared army cap change or new native modifier is needed. This continues to use
the documented `Player_SetResource` API, and all simulation updates are selected
Korea player state. Ordinary Zhu Xi and other civilizations are unaffected.

## Evidence and validation

- Official/editor: current installed core cost fields; refreshed complete
  EBPS/SBPS parent audit: 524 local, 5,758 official, zero errors.
- Portable verifier: passes, 910 instances and 1,213 localization rows.
- Maintained tests: **81 pass**, including the exact old Observatory failure,
  all 27 scalar-only repairs, four pending purchases, exhausted allowances,
  cancellation, repeated Observatory invocation, and independent Korean players.
- Installed tuning validator: zero errors/warnings, one informational summary of
  5,907 stock references outside the local pack. Changed references: none.
- Installed SCAR validator on `research.scar`: no diagnostics.
- AoE4 MCP: `syncAllowances` resolves to the local definition; no new unknown
  engine API. Existing documented `Player_GetAbilityBPCost` has sparse usage
  evidence and remains a native payment-verification gate.
- Donor translation audit: 378 definitions, 127,446 compared values, 91 research
  routes; zero unexplained discrepancies after the 27 explicit time repairs.
- All 104 original Persia dirty files and all 463 donor asset files match their
  preserved hashes. Only 27 Korean XML files and Korean `research.scar` changed
  under `assets` in this request. Garrison is unchanged.
- Both skill self-tests and Git whitespace check pass.

Reproducible evidence is under ignored `work/korea_construction_20261029`: initial
hashes and dirty diff, compressed original changed XML/SCAR, pre-repair native log,
current official XML evidence, validator outputs and final receipt. One-time
recipe: `tools/inspect_korea_construction.py`, then
`tools/repair_korea_construction.py`. Ordinary builds use the edited source and
do not depend on the donor or these work files.

Additional Korean source is 14,079,795 bytes; source deflate estimate is
5,400,749 bytes. No new art is added. Final package/ZIP contribution, runtime
residency and frame-time measurements remain pending; see `korea-budget.json`.

## Native retest after rebuilding Normal

1. Confirm House 15 s and Mill 20 s in a fresh Korea match. Time single-builder
   construction and verify multiple builders still accelerate normally.
2. Test Stone Pagoda and Bulguksa separately at 3:10; both Castle landmarks at
   3:40; both Imperial landmarks at 4:10. Verify completion and age progression.
3. Build the Observatory with both initial allowances unspent: no SCAR error;
   four distinct additional offers and four total purchases remain available.
   Try four purchases together and verify a fifth is unavailable. Cancel one,
   retry it, and confirm only one allowance/payment refund.
4. Ruin/repair the Observatory: no repeated offers or allowances, ongoing rebate
   behavior resumes. Repeat with two Korean players and a stock Zhu Xi player.

No Content Editor burn, new package, installation or native match was performed
for this repair. Existing installed/built copies require a rebuild to include it.
