# 0.7.5 seven-building review candidate

The candidate is built and package-verified. It has not been installed, published or tested in game. The requested 9–10 visual target is not met. The independent review is `output/release_075/review/index.html`, with seven before/after sheets, official geometry comparisons, regional-reference links, per-criterion deductions and machine-readable scorecards/performance data.

Current provisional source-art scores are Ministry 6.94, Phổ Minh 7.68, One Pillar 7.54, Citadel 7.50, Headquarters 7.18, Garden 7.11 and Foundries 6.85. These normalize the five inspectable criteria by their 90% weight; the 10% functional owner-colour criterion remains unverified. They are not full acceptance scores. Official reference panels use neutral clay because the layered stock-material projection produced artifacts; they support geometry comparison, not native material parity.

## Delivery and rollback

- Candidate: `output/release_075/candidates/review-v1/community_civilization_pack-0.7.5.zip`
- ZIP SHA-256: `d85e81007a103729554d2d1195e6efdc18e1f084281766f0302126c4e9c92291`
- ZIP size: 155,701,952 bytes.
- Embedded SGA SHA-256: `aaca1bd8cb3d09a44cbe091816817e5bb247944f204affa5b04e6af52f56b022`
- Destination archive namespace: `b7fcea91257b408fb9e8ae4d8bc402e1`.
- Exact rollback: `output/release_075/baseline/community_civilization_pack-0.7.4.zip`, SHA-256 `6d1bdfa52b8a440848f4b6dd0acc2a45822c9480f289dac63fa630d0ad5d82d4`.

## Selected editable sources

Paths are relative to `art/authoring/release_075/`; textures are packed or retained alongside them. Matching FBX/PBR exports live under `art/exports/release_075/`. `output/release_075/final-selection.json` freezes the exact source/export hashes and cook provenance.

| Building | Editable source | Healthy body triangles | Main changes |
|---|---|---:|---|
| Economic Ministry | `ministry/r3/ministry.blend` | 19,314 | Finer roof courses, hall/storage frames and closed gables; original three static elephants preserved |
| Phổ Minh Tower | `pho_minh/r3/pho_minh.blend` | 10,548 | Masonry cornice treatment, clearer entrance and court, closed supporting shrine gable |
| One Pillar Pagoda | `one_pillar/r4/one_pillar.blend` | 15,940 | Finer tiles, lighter stair rhythm, seated arched ridge, repaired pond corners and open lotus blooms |
| Imperial Citadel | `citadel/imperial_citadel.blend` | 64,774 | Thicker walls and piers, masonry/plaster balance, improved timber UV direction, reduced repetitive roof geometry |
| Resistance Headquarters | `hq/resistance_hq.blend` | 20,346 | Continuous reed roof skins, clearer command-hall hierarchy and palisade variation |
| Imperial Garden | `garden/r4/garden.blend` | 55,840 | Layered opaque crowns, peripheral planting, repaired wall/coping/paver intersections |
| Trung Foundries | `foundry/r5/foundry.blend` | 20,192 | Open soot-darkened flues, removed intersecting stacks, seated fuel and billet rack |

These are body counts, not whole-compound budgets. The comparator evidence separately counts retained native attachments across normal/campaign branches, including conservative scaffolding and debris costs. Complete conservative mesh upper bounds, including all body states and the new flag, are 44,276 / 12,400 / 19,600 / 127,152 / 34,141 / 88,884 / 115,092 respectively. The first five fit below their qualified official reference's principal healthy lower bound. Garden and Foundries remain inconclusive: their conservative all-state upper bounds exceed the comparison lower bounds, which does not establish actual excess. Excluding inactive debris/scaffolds requires verified state propagation, not guessed numeric selector operators. See `tools/release_075/performance_refinement/result.json`. Draw calls, terrain effects, native LOD behavior and frame time are not inferred from triangle totals.

## Verified technical gates

All seven selected sources completed fresh native art cooks/readback. Ministry's inherited stock-elephant split boundaries are the sole documented preflight warning exception: the original geometry is exact and every newly added component is closed. The other selected preflights are clean. Explicit contact audits and multi-view source renders are retained with each revision.

All eight private body models (including both Citadel variants) retain exact original RGM chunks except their geometry collection, and preserve original RGO lifecycle owners, construction/health selectors and functional markers. Costs, footprints, production, research, age-up and other actor bytes are unchanged. Native animation or repair success is not inferred from this static preservation.

Seven owner flags use the genuine official rectangular flag model, native sails shader, packed mask and stock lifecycle. New stamp sources compiled through the Content Editor; typed readback verifies the exact transforms and nonselectable/nonblocking settings. The seven attachment lists cover 17 variants, retaining PBG IDs and exact original bytes when the new attachment is removed. The custom bodies remain on their existing object-PBR route. No stock model/material replacement is packaged. Actual owner tint, flag readability, wind and state propagation require the final native test.

The final SGA contains 1,295 members: 31 original visual members changed, 28 private members added, and all 1,236 unrelated original members byte-identical. Every original mount is unchanged. Identity checks pass before assembly and on the final archive. Every final member is extracted and hash-compared. ZIP readability, strict version 0.7.5 and the embedded SGA hash pass. All 2,642 frozen Garrison files and all 298 normal-edition files remain unchanged. Active 0.7.4 delivery and source metadata remain intact; no cleanup occurred.

Exact evidence is in `output/release_075/candidates/review-v1/verification.json`, `recipe-freeze.json` and `delivery-proof.json`, `output/release_075/preservation-verification.json`, and the selected cook/payload receipts. Rebuild steps are in `RELEASE_075_REBUILD.md`.

## Remaining acceptance

Use `RELEASE_075_NATIVE_ACCEPTANCE.md` on this final ZIP: import/lobby selection, ordinary zoom appearance, two player colours, construction, damage, destruction, selectable ruins, repair/rebuild, access and production, then save/load and separately multiplayer. The review candidate is not a claim that any of these passed. Retain 0.7.4 for rollback.
