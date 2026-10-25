# Release 0.4.0 baseline and stock-building research

Captured before 0.4.0 source integration on 2026-10-17. This report records an offline inventory; it is not a Garrison cook, package import, lobby, or native-match result.

## Immutable 0.3.0 baseline

`tools/release_040/freeze_baseline.py` captured the accepted 0.3.0 release and source state in external `output/release_040/baseline/freeze-baseline.json`. It recorded 291 active Garrison source files, 484 preserved normal-edition source files, and 843 files across previous authoring/export/recipe trees. The normal edition was read and hashed only. Accepted 0.3.0 artifacts were copied to `archives/release_030_user_accepted` and checked byte-identical:

- ZIP `community_civilization_pack-0.3.0.zip`: SHA-256 `7e0ec19ed66f9bc72c35fe4f28e34113c107d70d7e841c060f960620f6dea3df`
- SGA `community_civilization_pack.sga`: SHA-256 `d83fac3eedfc5b2802fd7c8a94752238e46d1323bee52208a62330c856c519b3`

The freeze manifest includes the active project tree, accepted artifacts and receipts, preserved normal source, 0.3.0 historical baseline records, and all prior editable authoring/export/recipe trees. Keep it immutable; do not refresh it to accept later edits. `tools/release_040/freeze_baseline.py --verify-only` is the preservation check.

## Vanilla Chinese stock graphs

Inventory source was the installed game's `Attrib.sga` and `Data.sga`, read through `sga-archiver` and Garrison core `convert decode-static`, plus the current Garrison SQLite asset index. Actor and tier-list graphs include normal/default and campaign actor branches. The full machine-readable inventory is external `output/release_040/inventory/stock-chinese-buildings.json`.

All four building families have Feudal/Age II, Castle/Age III, and Imperial/Age IV variants (three distinct RGMs each). The table reports the raw sum of decoded LOD0 geometry-group triangle counts per model. It is a donor reference, not a simultaneous-visibility or finished-compound budget: the source groups include lifecycle and conditional states, and props are separately attached by stamps.

| Family | Stock logical model stems, Age II / III / IV | Raw LOD0 triangles | Median / maximum |
| --- | --- | ---: | ---: |
| Blacksmith / Military Academy | `chi_blacksmith_control_age02`, `age03`, `age04` | 24,885 / 24,427 / 35,888 | 24,885 / 35,888 |
| Archery Range | `chi_archery_range_control_age02`, `age03`, `age04` | 42,418 / 42,324 / 68,322 | 42,418 / 68,322 |
| Stable | `chi_stable_control_age02`, `age03`, `age04` | 28,767 / 28,911 / 48,276 | 28,911 / 48,276 |
| Market | `chi_market_control_age02`, `age03`, `age04` | 26,553 / 26,157 / 26,938 | 26,553 / 26,938 |

Each logical stem is located under `art/civilizations/chinese/structures/{blacksmith,archery_range,stable,market}/<stem>/<stem>.rgm`. These counts alone cannot enforce the milestone's finished-state budget. The detailed donor decode and selector records from the building-model worker are under `output/release_040/buildings/donor-decode`, with recipe `art/recipes/release_040/buildings-donors.json` and lifecycle metadata `output/release_040/buildings/donor-selectors.json`. The selector inventory records 23 lifecycle selector sets per RGM; native runtime visibility is not established here.

The exact stock Chinese actor → age list → principal stamp mapping is:

| Family | Stock actor | Age II / III / IV attachment lists | Principal age stamps |
| --- | --- | --- | --- |
| Blacksmith / Military Academy | `attrib/ebps/races/chinese/buildings/building_tech_unit_infantry_chi/building_tech_unit_infantry_control_chi.rgd` | `attrib/attachments/attachment_lists/civilizations/chinese/buildings/tech_unit_melee_chi/tier{2,3,4}_tech_unit_melee_control_chi.rgd` | `art/stamps/civ_chinese/chi_blacksmith_age_0{2,3,4}.bin` |
| Archery Range | `attrib/ebps/races/chinese/buildings/building_unit_ranged_chi/building_unit_ranged_control_chi.rgd` | `attrib/attachments/attachment_lists/civilizations/chinese/buildings/unit_ranged_chi/tier{2,3,4}_unit_ranged_control_chi.rgd` | `art/stamps/civ_chinese/chi_archery_range_age_0{2,3,4}.bin` |
| Stable | `attrib/ebps/races/chinese/buildings/building_unit_cavalry_chi/building_unit_cavalry_control_chi.rgd` | `attrib/attachments/attachment_lists/civilizations/chinese/buildings/unit_cavalry_chi/tier{2,3,4}_unit_cavalry_control_chi.rgd` | `art/stamps/civ_chinese/chi_stable_age_0{2,3,4}.bin` |
| Market | `attrib/ebps/races/chinese/buildings/building_econ_market_chi/building_econ_market_control_chi.rgd` | `attrib/attachments/attachment_lists/civilizations/chinese/buildings/econ_market_chi/tier{2,3,4}_econ_market_control_chi.rgd` | `art/stamps/civ_chinese/chi_market_age_0{2,3,4}.bin` |

Each tier list also includes a shared family destruction stamp (`dest_blacksmith_stone.bin`, `dest_archery_stone.bin`, `dest_stable_stone.bin`, or `dest_market_stone.bin`). Campaign actor variants add the corresponding west scaffolding stamp (`west_blacksmith.bin`, `west_archery_range.bin`, `west_stable.bin`, or `west_market.bin`). The native stamp inventory sees 23/30/27 blacksmith, 23/28/28 archery, 32/37/37 stable, and 57/76/79 market static visual-stamp leaves by age. That count is a listed-leaf count, not proof all leaves render simultaneously.

## Vietnamese consumers and market wiring

Live source files `assets/attrib/instances/sbps/vietnam/vn_unit_villager_1_chi.xml` and `vn_unit_villager_3_chi.xml` both contain separate root and campaign build-list copies. Both currently reference private Vietnamese EBPs for blacksmith (`ebps\\vietnam\\vn_building_tech_unit_infantry_control_chi`), archery (`vn_building_unit_ranged_control_chi`), and stable (`vn_building_unit_cavalry_control_chi`). Market is the remaining stock consumer: all four copies reference `ebps\\races\\chinese_ha_01\\buildings\\building_econ_market_chi_ha_01\\building_econ_market_control_chi_ha_01`.

The compiled Chinese-HA01 Market actor was extracted from the installed `Attrib.sga` and decoded directly. Both its default and campaign tier groups point to `$PBGMAP=attachments\\attachment_lists` and `$PBGNAME=tier2_econ_market_control_chi`, tier3, and tier4, without an `_ha_01` suffix. These resolve to the standard Chinese market tier-list members shown above and use the same `chi_market_age_02/03/04.bin` stamps, shared market destruction stamp, and campaign west-market scaffold. HA01-specific market tier-list files do exist in Attrib.sga, but this actor does not select them. Therefore a Vietnamese visual replacement should isolate the owning market EBP and its visual attachment chain, then update the four Vietnamese build references; it should not assume the HA01 actor is already bound to private/HA01 age stamps.

## Historical visual research

A defensible medieval reference window for these Feudal-age structures is Northern Song, especially the Yingzao Fashi (營造法式) building code compiled by Li Jie and officially issued in 1103. The Chinese Text Project provides the digitized text and describes the 1103 official publication; use it as access to the primary text, while keeping in mind that a web transcription is not a critical edition: [Yingzao Fashi text and publication note](https://ctext.org/datawiki.pl?if=en&res=256414).

The UNESCO World Heritage nomination for Mount Songshan lists surviving timber buildings associated with Yingzao Fashi practices, including Chuzu Temple (1125), and documents their bay counts. It also identifies Chuzu Temple as the sole surviving Northern Song wooden building in its list strictly following the contemporary code. This is useful evidence for structural scale and timber construction, not for the specific plans of markets, blacksmiths, stables, or archery ranges: [Mount Songshan nomination, architectural table](https://whc.unesco.org/uploads/nominations/1305rev.pdf).

For visual direction, use measured timber bays, roof-support/bracket hierarchy, and roof massing as period-informed cues; treat workshop, market, stable, and military functions as interpretive designs unless supported by a function-specific source. Do not present decorative motifs or a particular floor plan as directly prescribed by those sources.

## Verification boundary

Storage verification passed with `tools/verify_workspace.py --storage-only` before inventory work. The freeze script completed and archived ZIP/SGA hashes match. Static inventory and model decode evidence does not establish authoring quality, Garrison cook/readback, Content Editor build, package import, lobby selection, or fresh native-match behavior.
