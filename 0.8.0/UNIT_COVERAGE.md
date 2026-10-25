# Vietnamese unit coverage inventory

Generated 2026-10-17T21:15:37.571875+00:00. Static source inventory only; it establishes serialized references and selected stock data, not runtime availability, playback, build/cook/import, or native-match behavior.

## Findings

- The Vietnam army root is `assets/attrib/instances/army/vietnam/vn_normal_chinese.xml` (SHA-256 `cf78ac7c83834968d2d5997d805e587c542de2653c4d1ac14985d8c1bc0c5d53`). It starts with one private scout, six private villagers, and one private war elephant; the same composition appears in the campaign variant. Five sheep also occur in the unit list and are excluded from voice coverage. The army has an empty `production_buildings` list.
- There are 43 local Vietnamese SBPS definitions and 40 distinct squad-valued references across Vietnam EBPS. Local SBPS definitions include several upgrade, garrison, landmark, special-spawn, and free units; they are not all independently trainable.
- The local Vietnam EBPS `assets/attrib/instances/ebps/vietnam/vn_building_unit_naval_chi.xml:8` inherits the stock parent blueprint `ebps\races\chinese\buildings\building_unit_naval_chi\building_unit_naval_chi`. The Vietnamese XML provides no local ships or local train list. Selective official Attrib.sga readback found seven stock ships in the inherited Chinese dock queue.
- Do not use missing `scar_ageN` tags as proof a unit cannot be obtained. Some private SBPS rely on inherited age classification; production gates may be in building/upgrade paths. Conversely `scar_ageN` is a serialized classification tag, not proof that the unit is actually obtainable at that age. A full effective inheritance/runtime trace remains incomplete.

## Local private squad roster

Ages below are only explicit `scar_ageN` tags serialized in the local Vietnamese SBPS. “Inherited/absent” means the local file contains no such tag and source-level effective age remains unresolved; it is not a claim of unavailability. Female chance is reported only when directly serialized.

| Private SBPS | Explicit age tag | Local sex/speaker metadata | Notes |
|---|---:|---|---|
| `vn_unit_archer_2_chi` | scar_age2 | female chance 0.0 |  |
| `vn_unit_archer_2_vit` | scar_age2 | female chance 0.0 |  |
| `vn_unit_archer_3_chi` | scar_age3 | female chance 0.0 |  |
| `vn_unit_archer_3_vit` | scar_age3 | female chance 0.0 |  |
| `vn_unit_archer_4_chi` | scar_age4 | female chance 0.0 |  |
| `vn_unit_archer_4_vit` | scar_age4 | female chance 0.0 |  |
| `vn_unit_bombard_4_chi` | inherited/absent | female chance 0.0 |  |
| `vn_unit_bombard_4_chi_cheap` | inherited/absent | female chance 0.0 | special/free variant |
| `vn_unit_crossbowman_3_chi` | scar_age3 | female chance 0.0 |  |
| `vn_unit_crossbowman_4_chi` | scar_age4 | female chance 0.0 |  |
| `vn_unit_culverin_4_chi` | inherited/absent | inherited/unset; name=culverin |  |
| `vn_unit_culverin_4_chi_cheap` | inherited/absent | inherited/unset; name=culverin | special/free variant |
| `vn_unit_handcannon_4_chi` | scar_age4 | inherited/unset |  |
| `vn_unit_handcannon_4_chi_cheap` | scar_age4 | inherited/unset | special/free variant |
| `vn_unit_horseman_2_chi` | inherited/absent | female chance 0.0 |  |
| `vn_unit_horseman_3_chi` | inherited/absent | female chance 0.0 |  |
| `vn_unit_horseman_4_chi` | inherited/absent | female chance 0.0 |  |
| `vn_unit_knight_3_chi` | scar_age3 | female chance 0.0 |  |
| `vn_unit_knight_4_chi` | inherited/absent | inherited/unset |  |
| `vn_unit_manatarms_3_chi` | inherited/absent | inherited/unset |  |
| `vn_unit_manatarms_3_mon_for_vit` | inherited/absent | inherited/unset | special/free variant |
| `vn_unit_manatarms_4_chi` | scar_age4 | inherited/unset |  |
| `vn_unit_manatarms_4_mon_for_vit` | inherited/absent | inherited/unset | special/free variant |
| `vn_unit_mangonel_3_chi` | inherited/absent | female chance 0.0 |  |
| `vn_unit_monk_3_chi` | scar_age3 | female chance 0.0; speaker=monk, name=monk, race=no_race |  |
| `vn_unit_official_1_chi` | scar_age1 | female chance 0.0; speaker=villagerMale, name=official, race=no_race |  |
| `vn_unit_ribauldequin_4_chi` | inherited/absent | inherited/unset; name=ribauldequin |  |
| `vn_unit_scout_1_chi` | inherited/absent | inherited/unset | female chance not locally serialized; stock scoutfemale profile alone does not establish effective female use |
| `vn_unit_spearman_1_chi` | scar_age1 | female chance 0.0 |  |
| `vn_unit_spearman_2_chi` | scar_age2 | female chance 0.0 |  |
| `vn_unit_spearman_3_chi` | scar_age3 | female chance 0.0 |  |
| `vn_unit_spearman_4_chi` | scar_age4 | female chance 0.0 |  |
| `vn_unit_spearman_fire_1_chi` | scar_age1 | female chance 0.0 |  |
| `vn_unit_spearman_fire_2_chi` | scar_age2 | female chance 0.0 |  |
| `vn_unit_spearman_fire_3_chi` | scar_age3 | female chance 0.0 |  |
| `vn_unit_spearman_fire_4_chi` | scar_age4 | female chance 0.0 |  |
| `vn_unit_villager_1_chi` | scar_age1 | inherited/unset; race=chinese |  |
| `vn_unit_villager_3_chi` | scar_age1 | inherited/unset |  |
| `vn_unit_villager_bambo_chi` | scar_age1 | inherited/unset |  |
| `vn_unit_war_elephant_1_vit` | inherited/absent | female chance 0.0; speaker=warelephant, name=war_elephant, race=no_race |  |
| `vn_unit_war_elephant_2_vit` | inherited/absent | female chance 0.0; speaker=warelephant, name=war_elephant, race=no_race |  |
| `vn_unit_war_elephant_handcannon_4_vit` | inherited/absent | female chance 0.0; speaker=warelephant, name=war_elephant, race=no_race |  |
| `vn_unit_war_elephant_handcannon_4_vit_free` | inherited/absent | female chance 0.0; speaker=warelephant, name=war_elephant, race=no_race | special/free variant |

## Inherited naval production

The official names below were read from extracted official Chinese Dock and ship SBPS RGD files under `research_tools/official_attrib/`; Vietnamese dock inheritance is confirmed at `assets/attrib/instances/ebps/vietnam/vn_building_unit_naval_chi.xml:8`. The table keeps age tags distinct from real availability gates.

| Stock squad | Class | SBPS age tag | Planned speech role | Evidence |
|---|---|---:|---|---|
| `unit_naval_fireship_3_chi` | fireship | scar_age3 | `NAVAL_FIRE` | `research_tools/official_attrib/unit_naval_fireship_3_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_fishing_boat_2_chi` | fishing boat | scar_age2 | `NAVAL_FISH` | `research_tools/official_attrib/unit_naval_fishing_boat_2_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_transport_ship_2_chi` | transport ship | scar_age2 | `NAVAL_TRANSPORT` | `research_tools/official_attrib/unit_naval_transport_ship_2_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_combat_ship_2_chi` | combat ship | scar_age2 | `NAVAL_MILITARY` | `research_tools/official_attrib/unit_naval_combat_ship_2_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_combat_warship_4_chi` | combat warship | scar_age4 | `NAVAL_MILITARY` | `research_tools/official_attrib/unit_naval_combat_warship_4_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_war_galley_3_chi` | war galley | scar_age3 | `NAVAL_MILITARY` | `research_tools/official_attrib/unit_naval_war_galley_3_chi.xml`; decoded official source, see JSON hashes |
| `unit_naval_trade_ship_3_chi` | trade ship | scar_age3 | `NAVAL_TRADE` | `research_tools/official_attrib/unit_naval_trade_ship_3_chi.xml`; decoded official source, see JSON hashes |

Dock unit role splits: fishing boat `NAVAL_FISH` binds to stock `tradeShip`; transport `NAVAL_TRANSPORT` binds to `scoutShip`; trade ship `NAVAL_TRADE` binds to `tradeShip`; fireship `NAVAL_FIRE` binds to `fireShip`; combat ship and war galley bind to `ship`; combat warship binds to `warShip` (both under `NAVAL_MILITARY`). These role assignments are grounded in explicit official SBPS speaker fields. Fish and cargo vessels share `tradeShip`; NAVAL_MILITARY spans two separate stock speakers (`ship` and `warShip`) with similar broad combat contexts. Role/action routing is not confirmed by this static inspection.

## Starting, production, and inherited consumers

- Default and campaign starting forces are directly referenced by the army XML at lines 314–324 and 680–690; starting force unit names/counts are listed above. `initialization.scar:66` also creates/spawns the war elephant via `Squad_CreateAndSpawnToward`; targeted search found no other SCAR squad creation API call for this family.
- The 40 `ebps_squad_consumers` entries in `UNIT_INVENTORY.json` retain every source EBPS path and line for squad references. They include queues, building garrisons, starting-force structures, special landmark outputs and duplicated default/campaign branches. A reference is not automatically proof of player production.
- Private Vietnam outpost/landmark defensive garrison entries include private archers, crossbowmen, handcannons, spearmen and fire-spearmen. Treat these as garrison unlocks/contents, not separately buildable consumers unless a production queue is independently shown.
- Special consumers include elephants in the Economy Ministry and landmark start/bonus consumers; the free elephant handcannoneer variant is not ordinary production. See source paths/lines in JSON for each direct squad reference.
- Official stock inherited consumers identified during survey include Chinese repeater crossbowman, springald, trebuchet variants and workshop ram, plus English Abbey King; these rely on inherited/foreign blueprint consumers. Their effective acquisition requirements remain unresolved in this inventory.

## Speech metadata and bank applicability

The planned script bank has 18 role keys: the user’s 16 roles plus `NAVAL_TRANSPORT` and `NAVAL_FIRE`. `SCOUT_F` is recorded as a stock-only unresolved profile, not a planned key. It should carry four chronological writing banks across all profiles, but an authored bank being present does not mean an actor exists in that age. Age-gated actor availability and dormant creative bank content are separate. The ordering/meaning of `cLowest/cLow/cMed/cHigh/cNone` and `iNorm/iHigh/iStealth` has not been established from the inspected SPD serialization, so no chronology or delivery semantics are assigned to those suffixes.

| Profile key | Source metadata / assignment | Evidence confidence |
|---|---|---|
| `CIV_M` | Vietnam villager SBPS sets race_code=chinese, inherits speaker/gender attachment metadata; direct effective speaker unresolved | structural/source metadata only; no runtime or audible proof |
| `CIV_F` | same as CIV_M; female stock branch is inherited, not confirmed effective Vietnamese runtime selection | structural/source metadata only; no runtime or audible proof |
| `SCOUT` | Vietnam private scout is a Chinese stock donor child; stock Chinese male scout SPD decoded as `scout`. Female chance not locally serialized; availability of SCOUT_F branch unresolved. | structural/source metadata only; no runtime or audible proof |
| `SCOUT_F` (stock-only, not planned) | Stock Chinese female scout SPD decoded as `scoutFemale`; whether Vietnamese scout can select/use it remains unresolved, so no separate script bank is proposed. | raw stock profile only; no reachability/runtime/audible proof |
| `INFANTRY` | No custom speaker metadata found on local line squads; inherits Chinese donor speech metadata; effective per-unit resolution untraced | structural/source metadata only; no runtime or audible proof |
| `ARCHER` | No custom speaker metadata found on local archer squads; inherits Chinese donor speech metadata; effective resolution untraced | structural/source metadata only; no runtime or audible proof |
| `CROSSBOW` | No custom speaker metadata found; inherits donor or local parent; effective resolution untraced | structural/source metadata only; no runtime or audible proof |
| `GUNNER` | No custom speaker metadata found on local gunner squads; inherited effective speaker unresolved | structural/source metadata only; no runtime or audible proof |
| `CAVALRY` | No custom speaker metadata found on local cavalry squads; inherited effective speaker unresolved | structural/source metadata only; no runtime or audible proof |
| `MONK` | local vn_unit_monk_3_chi sets squad_speaker_code=monk, squad_name_code=monk; female branch and SPD not inspected | structural/source metadata only; no runtime or audible proof |
| `OFFICIAL` | vn_unit_official_1_chi sets male speaker villagerMale and female speaker villagerFemale; distinct OFFICIAL voice not serialized | structural/source metadata only; no runtime or audible proof |
| `TRADER` | local trader profile effective fields not confirmed; profile key is role-bank assignment pending source resolution | structural/source metadata only; no runtime or audible proof |
| `ELEPHANT` | private war elephants and elephant handcannon set speaker warelephant, name war_elephant, race no_race; crew dialogue is not evidenced | structural/source metadata only; no runtime or audible proof |
| `SIEGE` | local private siege squads primarily inherit; physical crew presence and crew dialogue inference excluded unless explicit | structural/source metadata only; no runtime or audible proof |
| `NAVAL_FISH` | Fishing boat SBPS explicitly selects `tradeShip`; binds to `chinese_tradeship.spd` (includes resourceFish). | Serialized speaker binding and structural SPD only; no runtime or audible proof |
| `NAVAL_TRANSPORT` | Official transport SBPS explicitly selects `scoutShip`; SPD has enemySpotted/structureRepair, no weapon contexts. | Serialized speaker binding and structural SPD only; no runtime/audible proof |
| `NAVAL_TRADE` | speaker `tradeShip` in `chinese_tradeship.spd`; structural SPD summary only | structural/source metadata only; no runtime or audible proof |
| `NAVAL_MILITARY` | Combat ship/war galley explicitly select `ship`; combat warship selects `warShip`. | Two separate stock speakers; structural only; no runtime or audible proof |
| `NAVAL_FIRE` | Fireship SBPS explicitly selects `fireShip`; decoded SPD includes detonate. | Serialized speaker binding and structural SPD only; no runtime or audible proof |

Decoded speech files: selective SPD extraction only (nine SPD members, no broad audio extraction). The installed helper reports structural readback only and `qualified_stock_source=false`; decoded records/media refs do not prove playback. The Chinese villager SPD parser failed with `Invalid media list`; its raw SPD is preserved with hash. The `scoutShip` SPD was also selectively extracted and decoded (323 records, 584 media references). The Chinese warship SPD was decoded (173 records, 301 references); its combat contexts broadly match `ship`, while remaining a separate stock speaker bank. Physical crew on ships/siege weapons and any crew-dialogue inference are unresolved; all ship voice-role assignments above refer to squad/ship speakers, not inferred visible crews.

## Exclusions, unresolved inheritance, and source hashes

- Inherited speaker, gender-attachment, and age values are unresolved where the private XML does not override the field. Local villagers set `squad_race_code=chinese`, but effective male/female attachment speaker selection is inherited. Local official explicitly uses `villagerMale`/`villagerFemale` speaker codes; it does not establish a unique official-only voice profile.
- Monk and elephant profiles have direct local speaker metadata (`monk`; `warelephant`) but corresponding custom pronunciation or Vietnamese-specific SPD was not established.
- No local ship EBPS/SBPS definitions exist in the local Vietnam family; naval roster is inherited stock Chinese content.
- For trade ship, decoded SPD lists `structureRepair`, `garrisonUnits`, and `unloadUnits`; transport uses `scoutShip`, and combat ship/war galley vs combat warship use `ship` and `warShip` respectively; do not infer shared event routing. SPD context labels do not establish availability or action routing for a particular ship.
- `UNIT_INVENTORY.json` includes SHA-256 values for all local Vietnam SBPS definitions, relevant EBPS consumers, army root, SCAR entry, Vietnamese dock, selectively extracted official Attrib sources, and extracted stock SPD files. Each local SBPS record includes its evidence lines for parent, age, female chance and direct speaker/name metadata.
- The first-pass inventory scripts under `research_tools/` are analysis aids; final coverage and speaker-binding corrections were reviewed into these files, so the Markdown is not claimed as a deterministic regeneration of the JSON.
- Official MCP base-data searches returned empty results and are recorded as lookup misses, not invalid-data findings. No runtime proof is claimed.
