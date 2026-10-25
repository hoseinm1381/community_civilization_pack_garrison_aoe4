# 0.6.0 inventory pause checkpoint — 2026-10-18

No background job was running when paused; no decode, Blender, native cook, UI action, or source integration was started for the inherited-render-bodies continuation.

## Completed prior work retained

- Exact 19-model donor batch is complete at `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060\inventory\remaining-donors\run-004\batch-report-v2.json` and exact reference-only private index receipt is `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060\inventory\remaining-donors\run-004\batch-report-exact-index-v2.json`.
- Exact SQLite index: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060\inventory\remaining-donors\run-004\private-index-exact.sqlite3`.
- The prior remaining donor report is `tools/release_060/remaining-donors-report.md`.
- Eight villager manifests (including male/female Age IV, each 3 materials and 73 bones) and SHA-256 values were sent to `/root/ranged_production_060` before pause. No production work was started here.

## Inherited stock closure in progress

Nine reachable stock consumers from `inventory/coverage-audit-v2.json`: `unit_ram_3_chi`, `unit_siege_tower_3_chi`, `unit_monk_3_chi`, `unit_repeater_crossbowman_4_chi`, `unit_springald_3_chi`, `unit_trade_cart_chi`, `unit_trebuchet_4_cw_chi`, `unit_trebuchet_4_tr_chi`, `unit_workshop_ram_3_chi`.

- Native English render-body overrides are confirmed for ram (`eng_battering_ram`), tower (`eng_siege_tower`), springald (`eng_springald`), counterweight trebuchet (`eng_trebuchet_counterweight`), traction trebuchet (`eng_trebuchet_traction`). Tower manifest already exists in prior batch, 2 materials / 31 bones. The other four direct models have not been decoded in this continuation.
- Repeater crossbow has an active Chinese Age IV mesh list `attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_crossbowman_chi.rgd` with `animator0=chi_ranged_crossbow_age04`; existing decode manifest is under `output/release_060/qualification/ranged-rig-audit/decoded/chi_ranged_crossbow_age04/...`.
- Chinese monk and trade-cart unit EBPS files reference tier-IV attachment PBGs (`tier4_monk_chi`, `tier4_trade_cart_chi`), but those attachment RGD resources were absent from the existing 686-RGD decoded closure and were not found in the installed resolved-assets index. Plausible model assets exist (`chi_infantry_monk_age04`, Chinese trade horse Age II–IV), but the active native attachment path is not yet proven; do not report these candidates as resolved render slots.
- Trebuchet crew references core `attrib/attachments/attachment_lists/races/core/units/unit_siege_cart.rgd`; its decoded RGD has only `parent_animator=common/.../archetypes/siege_cart/siege_cart`, with no concrete mesh merge attachment established yet. Ram/workshop ram share the native body list; tower list also explicitly selects the English body model.
- Stock campaign/base variants were visible in the coverage audit; ram/tower also have XP3 variants. Keep reachability/eligibility gates unverified.

## Targeted villager Age IV check

The effective baseline VN villager actor `ebps/vietnam/vn_unit_villager_1_chi` has base and campaign `tier_group_list` entries for Chinese tier1, tier2, tier3, and tier4 villager attachment lists. The native `tier4_villager_chi.rgd` contains male and female Age IV `animator0` slots. Thus Age IV is active/reachable in the effective VN attachment selector; it is not an unused stock marker. The existing recipe covered six bodies before the prior task added the two Age IV donor manifests, bringing the available roster to eight.

## Resume target

Resume by tracing the exact native parent/attachment chain for Chinese monk and trade cart, and trebuchet crew. Only decode direct models once those paths are confirmed. Write the separate receipt under `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\output\release_060\inventory\inherited-render-bodies-v2`; do not repeat the 19-model batch or broad archive hashing.
