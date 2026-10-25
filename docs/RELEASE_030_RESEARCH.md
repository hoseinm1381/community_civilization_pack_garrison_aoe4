# Release 0.3.0 reference research

## Historical architecture references

Two historical anchors are approved for the Vietnamese temple direction: a clear
historical core paired with a modest courtyard treatment. The visual treatment can
draw from the documented form of Phổ Minh and the lotus-on-pillar idea associated
with Diên Hựu / One Pillar Pagoda. They should remain distinct references rather
than being presented as one reconstructed historical complex.

Phổ Minh Pagoda's tower is a surviving, fourteen-tier monument dated to 1305. The
Vietnam News Agency's VietnamPlus feature describes it as 19.51 metres high, with
a smooth green-stone base and lower levels and thirteen upper tiers of baked red
brick. The article includes current site photographs and captions, including a
view of the tower. It describes the tower as retaining its original form, so the
reference is an extant monument rather than a modern reconstruction.
[VietnamPlus / VNA: Pho Minh Pagoda – where Tran Dynasty glory is preserved in
stone](https://en.vietnamplus.vn/pho-minh-pagoda-where-tran-dynasty-glory-preserved-in-stone-post323407.vnp)

The One Pillar Pagoda's historic foundation is dated to 1049. The Ministry of
Culture, Sports and Tourism's Vietnam Tourism Administration describes the
traditional arrangement as a square lotus tower on a stone pillar, with the
present pillar about four metres high and 1.2 metres in diameter. The Vietnam
National Museum of History records that the pagoda was destroyed in 1954 and
rebuilt in 1955. Therefore, the current visible building is a modern
reconstruction of the historical concept, not original 1049 fabric. Use its
single-pillar/lotus relationship as a form reference while keeping materials,
craft details, and historical claims grounded in the documented reconstruction.
[Vietnam Tourism Administration: One Pillar Pagoda](https://vietnamtourism.gov.vn/en/printer/18092?type=1)
[Vietnam National Museum of History: One Pillar Pagoda](https://baotanglichsu.vn/vi/Articles/3091/12748/chua-mot-cot-nhan-ky-luc-chau-a.html)

The approved “historical core plus modest court” direction is compatible with
these references: keep the core form legible and use restrained courtyard paving,
low walls, or small planted elements to frame it. These are design translations,
not claims that either historic site had the proposed game courtyard layout.

## Stock static geometry budget

Native Garrison RGMs and RGOs were matched to the installed game asset index,
then read-only selector evidence was joined to decoded LOD0 triangle records.
For the Academy, the stock lifecycle predicates mark 224 of 225 unique named
geometry selectors visible when healthy; repeated geometry records remain
separate draw instances. For Zhengyangmen and Aachen, packed collection source
object names were ordered from exact native MSCL strings and joined through the
RGM source-to-local-bone map. Every packed triangle maps to exactly one source
object and each source object maps to one local bone. The qualified completed
healthy LOD0 counts are:

| Native model resource | Raw LOD0 triangles | Completed healthy LOD0 triangles |
| --- | ---: | ---: |
| Chinese Imperial Academy, Age II | 59,652 | 59,496 |
| Chinese Zhengyangmen gate (principal gate candidate) | 98,898 | 98,762 |
| HRE Aachen Cathedral | 91,068 | 90,258 |

The three-resource median target is **90,258 triangles** and maximum cap is
**98,762 triangles**. Counts include only simultaneously selected healthy
completed LOD0 geometry; they do not add construction/damage/ruin alternatives
or alternate LOD resources. Native runtime visibility remains unverified. The
method uses `tools/release_030/stock_selector_probe.py`'s read-only evidence and
`tools/release_030/budget.py` to cross-check decoded manifest and source hashes.
Full per-slot and selector records are in
`output/release_030/inventory/stock-completed-budget.json`; the consolidated
receipt is `output/release_030/budget/stock-budget.json`. This is static source
drawgraph evidence, not GPU submission or native match proof. Separate attached
props remain outside the three principal model counts unless the exact owner
graph identifies them as part of the landmark visual.

The selected benchmarks are Chinese Imperial Academy Age II, Chinese
Zhengyangmen gate (the principal-gate candidate), and HRE Aachen Cathedral. The
preserved Vietnam Barbican EBP references the separate Chinese outskirts list
`won_zgate`; it is not included as principal geometry. Integration evidence
identifies the principal visual owner separately from that attachment.

## Baseline freeze

`output/release_030/baseline/freeze-baseline.json` captures the 0.2.1 ZIP and
packaged SGA hashes, the active Content Editor project, all 484 preserved
normal-edition files, and all 797 prior editable art, export, and recipe files
from releases 0.1.0, 0.2.0, and 0.2.1. The 0.2.1 ZIP and SGA matched their expected
SHA-256 values at capture. Use `tools/release_030/freeze_baseline.py --verify-only`
to compare current files with that immutable pre-0.3.0 manifest; never refresh it
to accept later source edits.
## Stock static geometry budget

The first decode pass produced raw totals of 17,278 Academy triangles under a
`construct_95` name filter, 98,898 Zhengyangmen triangles across six packed
collection groups, and 91,068 Aachen triangles across six packed collection
groups. Those figures are preserved in
`output/release_030/budget/stock-budget.json` as **invalid preliminary
measurements**, not as a target or cap. The Academy selection was ruin/damage
geometry; the other two totals combined packed lifecycle collections without
proving which source objects are simultaneously active in the intact completed
state. The former 91,068 median and 98,898 cap are withdrawn.

`tools/release_030/budget.py` now uses Garrison 0.1.4's supported
`convert decode-static` route and records raw resource hashes, group totals, and
collection partition metadata. It deliberately emits no median target or maximum
cap until native RGO/EBP construction and damage selectors can be resolved to
intact complete LOD0 draw sets. Collection `active_object_count` alone does not
identify the source objects or their damage/ruin status. Counts are per source
resource; no alternate LODs are summed. Separate attached props belong in a
scene budget only after the exact owning attachment graph is established.

The selected native benchmark resources are Chinese Imperial Academy Age II,
Chinese Zhengyangmen gate (the principal-gate candidate), and HRE Aachen
Cathedral. The preserved Vietnam Barbican EBP references the Chinese outskirts
list `won_zgate`, while integration evidence identifies its principal visual
owner separately from the outskirts attachment. `won_zgate` must not be counted
as principal geometry. Installed native owner lifecycle selectors and packed
collection source-object names remain the missing evidence needed to finish the
budget. This is static decoder work only: no Blender scene, native cook, GPU
capture, or match runtime was used.
