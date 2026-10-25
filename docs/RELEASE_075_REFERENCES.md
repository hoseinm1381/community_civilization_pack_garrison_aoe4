# Reference basis and qualification boundaries

## Regional references

- [Thang Long archaeological site](https://hoangthanhthanglong.com/di-tich/di-tich-khao-co-hoc/?lang=en): stone column foundations, brick courts, lotus bases and ceramic roof ornament. Ministry, Citadel and Garden superstructures are interpretations, not surviving medieval buildings.
- [National tourism authority: One Pillar Pagoda](https://vietnamtourism.gov.vn/en/printer/18092?type=1): single column, timber beam/platform support, square shrine and pond. The current building was restored in 1955; its photograph is a structural reference, not proof of the complete 1049 design. Preserve approved in-game scale.
- [Vietnam News Agency: Pho Minh](https://en.vietnamplus.vn/pho-minh-pagoda-where-tran-dynasty-glory-preserved-in-stone-post323407.vnp): tapering stone/brick tower, 1305 construction and fourteen levels. Material transitions and tier cadence inform refinement without arbitrary asymmetry.
- Resistance Headquarters and Foundry remain functional reconstructions. No claim of an excavated resistance-camp/foundry plan. Exclude modern machinery and nineteenth-century ceremonial cannon designs.

## Official reference evidence recovered

Hash-checked retained measurements are under `output/release_075/references/retained`.
These are historical measurements, not a refreshed complete-compound budget:

- Imperial Academy and Barbican/Chinese principal gate provide civic hierarchy, masonry, roof and Feudal visual comparisons.
- Daming Palace provides imperial garden/hall material and compositional comparison.
- Forbidden Palace provides Imperial landmark scale/hierarchy reference; it is not a functional foundry donor.
- Existing Castle budget used an older 50-percent-overstock allowance. **Do not use that allowance for 0.7.5.**

Before final art acceptance, refresh selected official resources, account for simultaneously visible stamp submodels/outskirts, and compare materials, texture memory and triangle counts separately. Pending visual comparison sheets cannot be represented as completed.

## Owner-colour pilot

Independent review found the current stock Chinese and Delhi town-centre stamps use `art/civilizations/common/flags/flag_rectangle/flag_rectangle`. Its native `sails` material has `g_masksTex` and `options` [1,0,0.5,8]; it does not use the ram's `maskTex5` contract.

Preserve this stock model/material family for a separate stamp submodel pilot. Do not convert object-PBR building bodies to structure materials or bake a fixed colour. Which mask channel/option drives owner tint, destination ownership propagation, alpha/wind and lifecycle behavior still require qualification. Final native two-colour testing remains mandatory for a functional claim.
