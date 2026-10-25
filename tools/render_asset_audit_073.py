"""Render the evidence-backed 0.7.3 asset inventory as a self-contained report."""
from pathlib import Path
import hashlib,html,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/asset_audit_073'
def load(n):return json.loads((OUT/n).read_text(encoding='utf-8'))
actors=load('actors.json');squads=load('squads.json');inputs=load('audit-inputs.json')
drift=[]
for key,value in inputs['source_assets'].items():
    data=(ROOT/key).read_bytes();current=hashlib.sha256(data).hexdigest()
    if current==value:continue
    old=(Path(json.loads((ROOT/'workspace.json').read_text())['external_root'])/'staging/r73/v1/src'/key).read_bytes()
    assert hashlib.sha256(old).hexdigest()==value
    assert Path(key).stem in ('vn_building_defense_outpost_chi','vn_building_defense_outpost_2_chi')
    assert data==old.replace(b'name="time_seconds" value="60"',b'name="time_seconds" value="30"'), 'Concurrent rendering/source change requires reaudit'
    drift.append(dict(file=key,before_sha256=value,current_sha256=current,change='Separate concurrent edit: build time 60 to 30 in default/campaign. No model/attachment/source rendering field changed.'))
(OUT/'concurrent-source-drift.json').write_text(json.dumps(drift,indent=2)+'\n',encoding='utf-8')
buildings=[
 ('Town Centers, including capital/secondary variants','Custom geometry','I–IV','Four remodeled age bodies.'),
 ('Houses, including faster-build variant','Custom geometry','I–IV','Four custom age bodies; original outskirts/scaffolding can remain.'),
 ('Barracks','Custom geometry','I–IV','Four remodeled bodies.'),
 ('Archery Range','Custom geometry','II–IV','Three remodeled bodies plus authored detail compounds.'),
 ('Stable','Custom geometry','II–IV','Three remodeled bodies plus authored detail compounds.'),
 ('Blacksmith','Custom geometry','II–IV','Three remodeled bodies plus authored detail compounds.'),
 ('Market','Custom geometry','II–IV','Private market actor and three custom visual tiers.'),
 ('Keep','Custom geometry','III, shared thereafter','Custom Castle body/detail; no separate new Imperial keep body was found.'),
 ('Monastery','Custom geometry','III–IV','Custom main monastery bodies and details. Distinct from the stock dynasty Pagoda.'),
 ('Siege Workshop','Custom geometry','III–IV','Custom main bodies and details.'),
 ('Economic Ministry','Custom geometry','Shared','Custom hall/yard compound; stock elephant decorations are retained components.'),
 ('Hideout, including fortified/passable-related forms','Custom geometry','Shared states','Custom low outpost/shelter models; default/stone variants.'),
 ('One Pillar Pagoda','Custom geometry','Feudal landmark','Private custom compound, enlarged visual and ruin geometry.'),
 ('Phổ Minh Tower','Custom geometry','Feudal landmark','Private custom tower compound and ruin geometry.'),
 ('Resistance Headquarters','Custom geometry','Castle landmark','Custom landmark body/outskirts.'),
 ('The Flooded Citadel','Custom geometry','Castle landmark','Custom citadel compound/outskirts.'),
 ('The Imperial Garden','Custom geometry','Imperial landmark','Custom 070 Garden compound.'),
 ('Trừng Foundries','Custom geometry','Imperial landmark','Custom 070 Foundry compound.'),
 ('Wonder — current UI name Bút Tháp Temple','Custom geometry','IV','Custom 070 wonder; authoring research calls the interpreted palace Kính Thiên.'),
 ('Both Bamboo Stake Trap forms','Custom geometry','Shared','Custom pit/stake/camouflage visuals; passable children share them.'),
 ('University','Partial custom geometry','IV','Stock main building retained with custom scholarly courtyard/detail additions.'),
 ('Rice Paddy, both farm definitions','Partial custom geometry','Shared','Custom perimeter/edge model; the central rice/farm layer still uses the stock Chinese farm tier.'),
 ('Dock','Stock','Current tiers','No private dock model selected. Needs a custom asset for a Vietnamese redesign.'),
 ('Granary','Stock','Shared','Stock Chinese granary; the second local granary definition is an alternate/source-present record.'),
 ('Dynasty Pagoda','Stock','III–IV','Stock Chinese religious tiers. It does not select the private custom Monastery art.'),
 ('Palisades, palisade gates/bastions, stone walls/gates/bastions and wall tower','Stock','Native tiers','Inherited Chinese construction entries. No private wall-system assets selected.'),
]
units=[
 ('Villagers — main vn_unit_villager_1_chi','Custom geometry','I–IV, male/female','Eight authored body variants. Stock work tools/cargo/archetypes remain where retained.'),
 ('Spearmen','Custom geometry','I–IV','Four authored body variants; fire variants point to the same family. Equipment is separately material-remixed/stock.'),
 ('Archers','Custom geometry','II–IV','Three authored body variants.'),
 ('Crossbowmen','Custom geometry','III–IV','Two authored body variants.'),
 ('Giao Chỉ Heavy Arquebusier, including Serpentine variant','Custom geometry','IV','Authored handcannoneer body; its separate native gun/weapon donor is not proof of a newly modeled arquebus.'),
 ('Men-at-Arms — active Mongol-derived Vietnam family','Custom geometry','III–IV, male/female','Four authored bodies, including lobed variants. Older Chinese-derived MAA definitions remain stock.'),
 ('Repeater Crossbowman','Custom geometry','IV','Private actor v6i26e2e88 selects the authored repeater4 body.'),
 ('Monk — active private production family','Custom geometry','III–IV','Private actor v6icf9e7cc selects two authored bodies; staff III is a material remix and staff IV remains stock.'),
 ('Royal Elephant attached arquebusier','Custom geometry','IV','The separate attached handcannoneer actor selects the authored handcannon4 body.'),
 ('Scout','Material remix only','I–IV, male/female','Eight selected stock-geometry rider/body material variations; no newly modeled horse anatomy.'),
 ('Horsemen','Material remix only','II–IV','Stock mounted geometry with private material variants.'),
 ('Knights/Lancers','Material remix only','III–IV','Stock armored-cavalry geometry with private material variants.'),
 ('Trader','Material remix only','II–IV','Active private actor v6iffd591f selects three material-remixed stock trade-cart bodies.'),
 ('Royal Elephant body, paid/free and upgraded forms','Material remix only','IV','Two stock elephant body material remixes. Distinct from the custom attached arquebusier.'),
 ('Water Buffalo','Visual mismatch','Shared','Active vn_unit_water_buffalo_vit selects v6iea653a7 -> v60b03/m024, whose proven donor is a Sultanate armored elephant. No dedicated buffalo-shaped asset is selected.'),
 ('Counterweight Trebuchet and siege cart','Material remix only','IV / cart III','Private selected stock-geometry material variants; no resolved custom human-crew redesign.'),
 ('Siege Tower','Material remix only','III','Private selected stock-geometry material variation.'),
 ('Lam Sơn Skirmisher','Stock','II–IV','Native Malian javelin-unit attachments/body tiers. Needs distinct Vietnamese body/equipment assets.'),
 ('Nỏ thần and Reinforced Nỏ thần','Stock','Current variants','No private body model selected; native donor body retained. Needs a distinctive siege model if desired.'),
 ('Culverin, including discounted form','Stock','IV','Current squad loadout selects official unit_culverin_4_chi.'),
 ('Mangonel','Stock main body + remixed cart','III','Official unit_mangonel_3_chi main actor plus private remixed siege cart. Main machine has no custom model.'),
 ('Battering Ram','Stock; retained remix is unselected','Current private ram actors','Private identities v6ia182e18/v6i10f848c still select native ram art; packaged m016 remix is not selected in the inspected graph.'),
 ('Fishing Boat, Transport Ship, Trade Ship, early combat ship, War Galley, heavy Warship, Fire Ship','Stock','Seven Dock production families','All seven inherit official Chinese naval squads/actors; no private ship models.'),
]
legacy=[
 ('Trap Planter and vn_unit_villager_3_chi','Stock bodies','Source-present; no incoming main private production edge found. Check intended availability before commissioning new art.'),
 ('Imperial Official','Stock','Source-present; not counted as a confirmed current production family.'),
 ('Legacy Worker Elephant vn_unit_war_elephant_2_vit','Material remix only','Tughlaq worker-elephant material variant; no riderless crate/three-stick model activated. No incoming main private production edge found.'),
 ('Legacy Water Buffalo vn_unit_war_elephant_1_vit','Elephant material remix','Older alias/source-present; shares the elephant body also selected by the active Buffalo child.'),
 ('Bombard and Ribauldequin','Stock main machines','Source-present native loadouts; no incoming main private production edge found for the direct local squads. Bombard can share the remixed siege cart.'),
 ('Traction Trebuchet','Material remix only','Retained private actor; no incoming main private production edge found.'),
 ('Old private Springald/Scorpion','Stock; remix unselected','Retained actor v6i7e003d7 uses native Springald art. Its m017 custom material variant is packaged but not selected in the inspected graph.'),
 ('Older Chinese-derived Men-at-Arms, monk and trade-cart records','Stock','Retained definitions coexist with the custom/remixed private production families; do not classify by filename alone.'),
 ('Lumber Camp, Mongol Ger, alternate Minh Pagoda landmark and alternate new Imperial Garden','Stock','Retained/alternate source records. Main initial-villager construction does not select these specific records.'),
 ('Second Granary, alternate capital TC and older farm/landmark representations','Mixed shared assets','Inspect per-blueprint appendix; duplicate source identities do not imply additional art families.'),
]
notes=[
 'Rattan research has no qualified activated woven-armor/back-shield visual. Retained authored experiments do not count as active custom assets.',
 'Six older equipment material selections exist, but only five are selected by the inspected local actor/equipment graph: recurve bow, crossbow, arbalest, basic spear, monk staff III. The ji-spear remix is retained without a selected edge.',
 'Ram m016, Springald m017 and ji-spear m023 are retained model selections without a selected edge in the inspected default local actor/equipment graph. Fixing such bindings may avoid creating replacement assets from scratch.',
 'Horse anatomy, elephant anatomy, stock work tools/cargo, many weapons, siege mechanisms and unresolved human siege crews remain native or material-only. A custom unit body does not mean every component is bespoke.',
 'A missing custom design is not a missing game resource: stock fallback assets can work normally. This report does not authorize gameplay/art changes.',
 'Static production/construction edges are candidates; requirements, civilization branches and SCAR conversions can change actual availability. Sparse campaign/expansion records may inherit default visual fields.',
 'Source and package graphs do not prove in-game appearance, animation, lifecycle behavior, save/load or multiplayer.',
]
assessment=dict(version='0.7.3',buildings=buildings,units=units,source_present_or_alternate=legacy,notes=notes,concurrent_nonvisual_source_changes=drift,static_checks=dict(tuning=load('tuning-validation.json')['summary'],inheritance=load('inheritance.json'),model_provenance=load('model-provenance.json'),xmlreader_files=381))
(OUT/'assessment.json').write_text(json.dumps(assessment,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def esc(s):return html.escape(str(s))
def table(head,rows):return '<table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
parts=['<!doctype html><meta charset="utf-8"><title>Garrison 0.7.3 asset audit</title><style>body{font:15px/1.55 system-ui;max-width:1400px;margin:36px auto;padding:0 24px;color:#e8eaf0;background:#111722}h1,h2{color:#8fdae1}table{border-collapse:collapse;width:100%;margin:16px 0 32px}th,td{text-align:left;border:1px solid #344052;padding:9px;vertical-align:top}th{background:#253345;position:sticky;top:0}tr:nth-child(even){background:#192331}code{word-break:break-all}summary{cursor:pointer;font-weight:600;padding:12px;background:#253345}details{margin:8px 0}input{width:95%;padding:12px;font:inherit;background:#253345;color:white;border:1px solid #789}small{color:#b8c2d0}</style>',
 '<h1>Garrison 0.7.3 — buildings and unit model audit</h1>',
 '<p>Checked editable source, compiled private records, inherited official attachments, private model/stamp selections, age tiers and equipment. All 1,267 verified package member hashes were rechecked. This audit changed no gameplay, art, normal-edition source or delivery.</p><p>Concurrent source drift: two Hideout files separately changed build time 60 to 30 seconds during the audit. Exact byte comparisons confirm no rendering fields changed. See concurrent-source-drift.json. The package comparison remains against verified 0.7.3.</p>',
 '<p><b>Custom geometry</b> = authored/remodeled meshes. <b>Material remix</b> = stock geometry with changed materials. <b>Partial</b> = custom additions with a stock main component. <b>Stock</b> = no selected private replacement. An asset existing in the archive does not establish that a consumer selects it.</p>',
 '<h2>Important finding</h2><p>The active Water Buffalo selects the private material-remixed <b>Sultanate armored elephant</b> model. It does not select a dedicated buffalo-shaped model. This is a static binding finding; native appearance was not tested.</p>',
 '<h2>Buildings</h2>',table(['Family','Status','Ages / variants','Evidence and remaining work'],buildings),
 '<h2>Units</h2>',table(['Family','Status','Ages / variants','Evidence and remaining work'],units),
 '<h2>Source-present / alternate records</h2><p>These are included for completeness; no new asset backlog is inferred solely from their presence.</p>',table(['Record/family','Status','Availability/evidence limit'],legacy),
 '<h2>Components and limits</h2><ul>'+''.join('<li>'+esc(n)+'</li>' for n in notes)+'</ul>',
 '<h2>Verification</h2><p>376 tuning instances: 0 errors, 130 pre-existing warnings. Current official inheritance: 198 local / 5,758 official blueprints, 0 errors. .NET XmlReader parsed 381 source files. All 305 historical unit payload hashes match the current package, confirming the geometry-versus-material provenance for 57 retained model selections. The audit includes 102 local non-projectile/non-weapon actors, 77 private squads, and 267 inspected official records.</p>',
 '<h2>Every private actor — searchable evidence appendix</h2><input id="filter" placeholder="Filter by actor name, asset name or source path">']
for row in actors:
    selected=', '.join(m['key'] if m['key']!='building-or-trap' else m['path'] for m in row['body_models']) or 'Stock / no private body selected'
    equipment=sorted({m for e in row['equipment'] for m in e['custom_models']})
    parts.append('<details class="actor"><summary>'+esc(row['name'])+' — '+esc(selected)+'</summary><p><code>'+esc(row['source'])+'</code></p><p>Packaged: <code>'+esc(row['member'])+'</code></p><h3>Default body/tier selections</h3>'+table(['Path','Attachment','Private'],[(a['path'],a['name'],a['private']) for a in row['attachments']])+'<p>Custom equipment: '+esc(', '.join(equipment) or 'None found')+'</p><details><summary>All raw visual evidence, including variants</summary><pre>'+esc(json.dumps(row,ensure_ascii=False,indent=2))+'</pre></details></details>')
parts.append('<h2>All private squads and actual loadouts</h2>'+table(['Squad','Localized name or official localization key','Loadout actors'],[(s['name'],s['label'],', '.join(x['name'] for x in s['loadout'])) for s in squads]))
parts.append('<p><small>Evidence: output/asset_audit_073/{actors,squads,production-edges,inherited-production,unit-model-selection,model-provenance,audit-inputs,assessment}.json. Raw variant absence is not an inheritance failure. This is an offline asset audit, not native acceptance.</small></p><script>document.getElementById("filter").addEventListener("input",e=>{let q=e.target.value.toLowerCase();document.querySelectorAll(".actor").forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(q))})</script>')
target=ROOT/'docs/ASSET_AUDIT_073.html';target.write_text('\n'.join(parts),encoding='utf-8')
print('Rendered',target,'with',len(actors),'actor evidence panels and',len(squads),'squad loadouts;',len(drift),'separately changed nonvisual source files recorded')
