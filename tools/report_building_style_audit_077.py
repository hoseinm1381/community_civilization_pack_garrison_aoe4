"""Evidence-linked editorial scorecards. Scores are judgments, not test output."""
from pathlib import Path
import base64,hashlib,html,io,json,statistics
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/building_style_audit_077'
rubric=[('Art','AoE4 art direction',25,'Primary/secondary/detail hierarchy, roof language, proportions and stylized surface density.'),('Read','Role and silhouette readability',20,'Recognizable role and main mass at reduced scale; source thumbnails are only a proxy for native gameplay zoom.'),('Identity','Vietnamese visual identity',15,'Distinct, coherent regional design vocabulary within this roster; not a claim of archaeological accuracy.'),('Surface','Materials and surface craft',20,'Visible palette, UV scale, material separation, roughness/wear and detail repetition in available previews. Native shaders are not reproduced.'),('Ground','Composition and terrain transition',10,'Yard hierarchy, entrances, activity props, edges and apparent ground contact. Actual terrain decals and stamp placement are separate.'),('Age','Age and roster coherence',10,'Age-appropriate visual hierarchy and relationship to other buildings. A single shared design is not penalized merely for lacking age variants.')]
# Each row: family, name, group, category judgments /100, strengths,
# deductions, first improvement, evidence confidence.
rows=[
('house','Houses','Economy / civilian',[84,88,78,80,84,82],
 'Compact domestic silhouette; clear thatch-to-tile progression across four ages; modest timber/plaster balance.',
 'Ridge and window treatment still closely follows the Chinese donor. Age II/III differ more in palette than massing; some grain looks broad at close range.',
 'Unify timber/roof texture scale with the red-roof landmark set, then refine II/III differentiation without enlarging the house.','Medium'),
('town_center','Town Centers','Economy / civilian',[86,90,65,80,80,80],
 'Strong civic hall hierarchy, readable gates and a clear Imperial increase in roof/tower complexity.',
 'Donor silhouette and blue/red ornament remain strongly Chinese. The custom landmark set uses much quieter roof materials, so the TC does not yet anchor one consistent civilization palette.',
 'Choose a common roof/wood palette and regional gate/eave vocabulary; retain the recognizable civic mass.','Medium'),
('barracks','Barracks','Military production',[85,85,67,78,78,77],
 'Native military courtyard framing and lookout forms remain legible; age I to IV progression is clear.',
 'Very close to the stock donor in towers and roof arrangement. II/III are near twins, and the ornate late roof palette differs from the scratch landmarks.',
 'Give the compound one distinct military-yard motif and align its roof materials with the rest of Vietnam.','Medium'),
('archery_range','Archery Range','Military production',[82,80,69,76,74,75],
 'Asymmetric tower and working canopy give a recognizable production silhouette; three age bodies are represented.',
 'Large plain canopy competes with ornate native roofs. Purpose-specific archery activity is less evident than the architecture; source views omit some native props/outskirts.',
 'Make targets, bow storage and a clear practice lane the main secondary read; verify canopy placement against final native stamps.','Medium'),
('stable','Stable','Military production',[84,82,68,77,75,76],
 'Long open shed and layered roofs suit a production building; late tier gains a clear upper mass.',
 'The donor roof remains the dominant identity and the custom awning looks like an added layer. Stable-specific activity is not strong in the inspected body/detail views.',
 'Integrate the awning into the roof/column rhythm and strengthen the horse-yard entrance; preserve production access.','Medium'),
('blacksmith','Blacksmith','Military production',[86,90,68,80,78,77],
 'Chimneys and open work bays communicate the role immediately. Muted masonry and working timber fit the workshop role better than the ceremonial buildings.',
 'Still strongly donor-derived; forge-yard wear and age II/III distinction could be stronger. The tiled canopy needs the same scale/weathering as the native roofs.',
 'Add localized soot/work wear and a consistent canopy material treatment before adding more ornaments.','Medium'),
('market','Market','Economy / civilian',[82,80,72,76,74,76],
 'Open hall structure, supporting posts and layered Imperial roof preserve a familiar market mass.',
 'The large red awning is visually separate from the blue-tiled donor body. Trading activity and stall hierarchy are weak in the body-only views.',
 'Use coherent awning/roof materials and a small number of strongly readable stalls, scales and bundled goods.','Medium'),
('keep','Keep','Defense',[87,92,65,80,80,77],
 'Strong fortified mass, corner towers and entrance hierarchy; among the clearest role silhouettes in the set.',
 'Its recognizability is inherited heavily from the Chinese keep; the warm custom landmark language is less evident. Only the shared Castle body is established.',
 'Keep the fortification silhouette and develop a restrained regional masonry/eave treatment rather than another large roof overlay.','Medium'),
('monastery','Monastery','Religion / technology',[85,87,68,None,78,76],
 'The final 077 native geometry envelope preserves a clear religious hall, stairs, raised platform and smaller courtyard elements.',
 'The older editable preview is not the final 051 repaired body. Final materials and exact healthy-state/stamp assembly are not established by the diagnostic envelope, so Surface is unscored.',
 'Review the actual 077 Monastery in a fresh match beside the University and dynasty Pagoda before changing roof layers or materials.','Limited: final geometry checked; materials unscored'),
('siege_workshop','Siege Workshop','Military production',[78,84,68,72,70,75],
 'Several flues and an open workshop mass keep the industrial role recognizable.',
 'The large simple canopy and ornate donor roof have competing scale/detail languages. Back views expose a possible source-to-stamp canopy alignment issue; this is not a confirmed native defect.',
 'Verify final canopy transforms first, then make its beams, tiles and supports a continuation of the workshop structure.','Medium; final canopy alignment requires native confirmation'),
('ministry','Economic Ministry','Economy / civilian',[70,68,76,69,63,72],
 'The 077 buffalo are more coherent with the intended economy than the former elephants. Hall, lean-to and yard have a clear rural material palette.',
 'The fenced livestock yard dominates the administrative hall, making it read more as a ranch. Broad repetitive roof/plaster surfaces and clean rectangular ground panels lack the hierarchy of stock civic compounds.',
 'Strengthen the public entrance and administrative/storage role, then break up the yard surface and improve roof/timber material variation.','Higher for current source; native surroundings unverified'),
('hideout','Hideout / fortified Hideout','Defense',[80,85,68,73,72,74],
 'The combined shelter and retained lookout make the defensive function readable; wooden and fortified variants are distinguishable.',
 'The plain rectangular shelter roof/base and ornate lookout use different construction vocabularies. The fortified variant reads more as a conventional tower than a discreet shelter.',
 'Integrate the shelter-to-lookout transition and soften the box-like base. Check actual scale and native ground contact before remodeling.','Medium; supplement includes both shared-origin components'),
('one_pillar','One Pillar Pagoda','Landmarks',[76,83,84,71,72,76],
 'Single column, elevated shrine, stair and lotus basin create one of the most distinct silhouettes in the roster.',
 'Repeated timber/lattice and the small shrine roof remain heavy. Water reads as a flat basin in the source preview; native water response is not scored. The broad square apron gives a display-model impression.',
 'Refine lattice/wood variation and the basin-to-earth transition; keep the approved enlarged silhouette and footprint contract.','Higher for selected source; native materials/scale acceptance pending'),
('pho_minh','Phổ Minh Tower','Landmarks',[78,87,85,73,72,79],
 'Strong tapering vertical silhouette, legible tier rhythm and clear distinction from the other Feudal landmark.',
 'Near-identical upper modules and uniform red masonry create repetition. The base court and supporting shrine remain sparse compared with the tower.',
 'Introduce controlled masonry variation and a stronger base-to-court composition without randomizing the characteristic tower rhythm.','Higher for selected source; native scale/owner colour pending'),
('hq','Resistance Headquarters','Landmarks',[73,78,76,66,70,70],
 'Timber, thatch, watch structures and palisades communicate an organized camp and contrast with the masonry landmarks.',
 'Smooth reed roofs resemble woven sheets; palisade spacing is very regular. Several similar huts compete with the central command building, weakening landmark hierarchy.',
 'Improve thatch edges and bundles, give the central command hall more hierarchy, and organize a clear military work yard.','Higher for selected source'),
('citadel','Flooded Citadel','Landmarks',[77,83,80,72,70,78],
 'Gatehouse, central roof mass and enclosing masonry provide a convincing fortified-compound silhouette.',
 'Tiles are repetitive and strongly embossed; long walls are uniform; the clean base reads as a miniature plinth. The Flooded role is not obvious in these dry source views.',
 'Prioritize believable wall/ground transitions, restrained tile relief and a readable water-management cue if compatible with the approved visual scope.','Higher for selected source; native water/terrain context unverified'),
('garden','Imperial Garden','Landmarks',[72,76,77,66,65,74],
 'Bridge, pond, main pavilion and enclosing court clearly communicate a formal garden.',
 'Pale paving overwhelms the planting; small radial crowns and isolated trunks feel sparse. Long clean walls and repeated surfaces make the compound look assembled rather than lived in.',
 'Improve planting masses and material direction, reduce visual dominance of empty paving, and soften the court-to-terrain edge.','Higher for selected source; stock foliage/native context separate'),
('foundry','Trừng Foundries','Landmarks',[69,70,73,66,63,70],
 'Furnaces, open flues, stockpiles and cannon-related yard props establish an industrial theme.',
 'The main rectangular shed could be a generic warehouse. Clean light paving and sparse activity weaken its Imperial landmark status; soot and work wear are too evenly restrained.',
 'Build a stronger foundry silhouette and a purposeful casting/work flow, then use localized soot, heat wear and stockpile variation.','Higher for selected source'),
('wonder','Wonder — Bút Tháp Temple','Landmarks',[73,82,78,66,70,75],
 'Raised ceremonial platform, broad stair and layered hall create a clear large-scale focal point.',
 'The enormous regular red roofs and pale platform are repetitive, and side/rear areas are comparatively plain. Current UI name and the palace-style authoring interpretation communicate different identities.',
 'Resolve the intended architectural identity first, then refine roof hierarchy, ceremonial ornament and platform/ground transitions.','Higher for source geometry; native compound remains separate'),
('university','University','Religion / technology',[80,87,65,None,70,78],
 'Stock main hall preserves a strong technology-building silhouette; the scholarly courtyard additions establish a local detail layer.',
 'The main body is intentionally white/neutral in the Blender preview, so Surface cannot be scored honestly. The relatively small additions do little to transform the whole building identity.',
 'Compare the final native main-body materials with the new courtyard, then unify roof/wood treatment and scholarly activity props.','Limited: neutral stock material proxy; Surface unscored'),
('rice_paddy','Rice Paddy','Economy / civilian',[70,82,78,63,66,75],
 'Low embankment, shallow channel and sparse edge shoots add a clear agricultural cue without replacing the rice center.',
 'The isolated edge module is straight and sparse. Repeated segments may look mechanical; the central stock rice, terrain stamps and adjacency clearing are not simulated in the source image.',
 'Evaluate a contiguous group of native farms before changing the module; then vary edge wear and plant density while preserving clearable edges.','Limited: custom perimeter only; full native farm composition unscored'),
('stake_fan','Bamboo Stake Trap — fan form','Defense',[76,73,78,67,68,76],
 'Shallow irregular cover, bamboo texture and limited exposed stakes suit the intended camouflage; no broad black cavity dominates the source view.',
 'Cover and stakes are close in value and the repeated earth texture looks flat. True revealed-state readability against game terrain is unverified; camouflage itself is not treated as a defect.',
 'Test revealed/owned traps on several native terrain types; tune material value and irregular cover without making the whole trap conspicuous.','Higher for source; native visibility/context pending'),
('stake_thicket','Bamboo Stake Trap — thicket form','Defense',[75,71,78,67,68,76],
 'Dense stakes remain mostly hidden under shallow earth/leaf cover and retain an irregular edge.',
 'The denser form is hard to distinguish from the fan at reduced scale. Uniform cover colour and sparse material variation limit its natural look.',
 'Strengthen the revealed-state stake pattern and ground blending while preserving the approved shallow camouflaged design.','Higher for source; native visibility/context pending')
]
metrics=json.loads((OUT/'render-metrics.json').read_text());supp=json.loads((OUT/'supplement-metrics.json').read_text())
by={m['id']:m for m in metrics};sup={m['id']:m for m in supp};cards=[]
for key,name,group,scores,strengths,deductions,action,confidence in rows:
 known=sum(w for (_,_,w,_),v in zip(rubric,scores) if v is not None)
 subtotal=sum(w*v/100 for (_,_,w,_),v in zip(rubric,scores) if v is not None)
 total=round(subtotal*100/known)
 variants=[m for m in metrics if m['family']==key]
 assert variants,key
 cards.append(dict(key=key,name=name,group=group,category_scores={r[0]:v for r,v in zip(rubric,scores)},score=total,scored_weight=known,weighted_known_points=round(subtotal,2),full_score_interval=[round(subtotal),round(subtotal+100-known)] if known<100 else None,strengths=strengths,deductions=deductions,priority_action=action,confidence=confidence,variants=[dict(id=m['id'],variant=m['variant'],source=m['source'],source_sha256=m['source_sha256'],triangles=m['triangles'],material_slots=m['material_slots'],state_scope=m['state_scope']) for m in variants]))
assert len(cards)==23
assert len(metrics)==52 and len(supp)==6
for m in metrics:
 assert hashlib.sha256(Path(m['source']).read_bytes()).hexdigest()==m['source_sha256']
 assert all(t['exists'] or t['packed'] for t in m['textures'])
evidence=json.loads((ROOT/'output/asset_audit_077/assessment.json').read_text(encoding='utf-8'))['verification']
native=json.loads((OUT/'native-monastery/receipt.json').read_text())
report=dict(version='0.7.7',audit_date='2026-10-23',rubric=[dict(key=k,name=n,weight=w,scope=s) for k,n,w,s in rubric],score_method='Independent subjective source-fit judgments. Each category is /100; weighted total is rounded to an integer. Monastery and University omit Surface and normalize the remaining 80 points to /100; their possible full-score intervals are supplied. No native acceptance score is claimed.',calibration='90-100: convincing shipped-quality visual fit; 80-89: strong fit, targeted polish; 70-79: plausible fit with visible mod-specific inconsistencies; 60-69: substantial polish/redesign needed; below 60: major mismatch. These are editorial anchors, not an official AoE4 rubric.',family_average=round(statistics.mean(c['score'] for c in cards)),families=cards,package=evidence,inspection=dict(source_jobs=52,custom_source_variants=43,official_donor_jobs=9,source_renders=104,supplemental_views=12,final_monastery_geometry_envelope_views=4,total_views=120,missing_unpacked_external_texture_paths=0,sources_hash_preserved=True),runtime_checks=dict(owner_colour='Unverified in two native player colours. Stock flags on seven revised landmarks have package evidence; visible flag function is not inferred.',lifecycle='Construction, damage, destruction, selectable ruins and repair are not tested in this audit. Existing cook/package preservation evidence is a separate gate.',performance='Source triangle/material-slot counts are recorded, not scored as frame time. They can include overlapping/conditional geometry and omit stock attachments. Earlier 075 whole-compound bounds remain inconclusive for Garden/Foundries.',physical_scale='Preview framing normalizes each object separately. It is not a matched-metre comparison, native collision check or normal-game-zoom test.'),limits=['Black areas/roof artifacts in stock-derived Blender material projections also occur on stock donor controls; they are not established as native visual defects and are not used as missing-resource deductions.','Native stock outskirts, ground decals, flags, props, seasonal lighting and render state are not fully reproduced. Ground scores judge visible design intent, not tested engine blending.','Older monastery source is reference only; final 077 geometry envelope is primary structural evidence. It includes lifecycle states, uses diagnostic colours and is not a healthy-state/material reconstruction.','Rice Paddy score concerns the custom edge design; complete native center and adjacency composition remain unverified.','No history/archaeology verification is claimed. Regional identity scores describe the visual vocabulary.','No Blender masters, gameplay source, normal edition or release delivery was edited. Only audit scripts, extracted input copies, rendered evidence and this report were written.'])
(OUT/'scorecards.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def esc(x):return html.escape(str(x))
def image_data(path):
 im=Image.open(path).convert('RGB');im.thumbnail((800,640));buffer=io.BytesIO();im.save(buffer,'JPEG',quality=88)
 return 'data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode()
def picture(path,label):return '<figure><img loading="lazy" src="'+image_data(path)+'"><figcaption>'+esc(label)+'</figcaption></figure>'
css='body{font:16px/1.55 system-ui;background:#111722;color:#e8eaf0;max-width:1550px;margin:32px auto;padding:0 24px}h1,h2,h3{color:#8fdae1}table{border-collapse:collapse;width:100%;margin:20px 0 32px}td,th{border:1px solid #3e5067;padding:9px;text-align:left;vertical-align:top}th{background:#253345;position:sticky;top:0}tr:nth-child(even){background:#192331}a{color:#9ce8e5}.muted{color:#b9c4d1}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}figure{margin:0;background:#20252b}img{width:100%;display:block}figcaption{padding:8px}details{background:#192331;border:1px solid #3e5067;padding:14px;margin:14px 0}summary{font-size:20px;cursor:pointer}input{font:inherit;padding:12px;background:#253345;color:white;width:95%;border:1px solid #6a879d}.score{font-size:26px;color:#dfd490}code{overflow-wrap:anywhere}.notice{border-left:4px solid #dfd490;padding:10px 18px;background:#253345}.bars{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}progress{width:100%;accent-color:#66c4be}'
parts=['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Garrison 0.7.7 — all custom building style audit</title><style>'+css+'</style>','<h1>Garrison 0.7.7 — all custom building style audit</h1>',f'<p>23 building types · 43 custom source variants · 9 official donor controls · 120 new inspection views · {report["family_average"]}/100 unweighted mean of provisional family scores.</p>','<div class="notice"><b>These are source-based art judgments, not native-match acceptance.</b> Scores assess how the designs fit AoE4. The audit covers active Vietnamese custom and partly custom buildings, including two trap designs; it excludes stock-only buildings and inactive alternate definitions. No art or gameplay changes were made.</div>','<h2>Scoring categories</h2><table><tr><th>Category</th><th>Weight</th><th>What is judged</th></tr>']
parts.extend('<tr><td>'+esc(n)+'</td><td>'+str(w)+'</td><td>'+esc(s)+'</td></tr>' for k,n,w,s in rubric)
parts.extend(['</table><p>'+esc(report['score_method'])+'</p><p>'+esc(report['calibration'])+'</p>','<h2>All buildings</h2><input id="filter" placeholder="Filter by name, role, issue or recommendation"><table id="scores"><thead><tr><th>Building</th><th>AoE4</th><th>Read</th><th>Identity</th><th>Surface</th><th>Ground</th><th>Age</th><th>Overall /100</th></tr></thead><tbody>'])
for c in sorted(cards,key=lambda c:-c['score']):
 parts.append('<tr data-name="'+c['key']+'"><td><a href="#'+c['key']+'">'+esc(c['name'])+'</a></td>'+''.join('<td>'+('N/V' if v is None else str(v))+'</td>' for v in c['category_scores'].values())+'<td><b>'+str(c['score'])+('*' if c['scored_weight']<100 else '')+'</b></td></tr>')
parts.append('</tbody></table><p>* Surface unscored. Remaining 80 weighted points normalized to /100; confidence and possible full score range appear below. Other totals use all six source-based categories. Preview artifacts shared with stock controls do not automatically lose points.</p>')
parts.append('<h2>Main findings</h2><ul><li>The stock-derived Keep, TC, Houses and Blacksmith fit the game most naturally, although their distinct Vietnamese identity is weaker.</li><li>Phổ Minh and One Pillar have the strongest distinct landmark silhouettes. Their main remaining needs are surface variation, court composition and native context.</li><li>Ministry and Foundries need clearer role hierarchy; Garden needs fuller planting and less dominant paving; Headquarters needs better thatch and military-yard organization.</li><li>The roster has two material languages: ornate, multicoloured stock-derived roofs and relatively plain terracotta custom roofs. Consistency would improve the whole civilization more than adding uniform detail everywhere.</li></ul>')
parts.append('<h2>Individual scorecards and visual evidence</h2>')
for c in cards:
 parts.append('<details class="card" id="'+c['key']+'" open><summary>'+esc(c['name'])+' <span class="score">'+str(c['score'])+'/100'+('*' if c['scored_weight']<100 else '')+'</span> · '+esc(c['group'])+'</summary><p class="muted">Confidence: '+esc(c['confidence'])+'</p>')
 if c['full_score_interval']:parts.append('<p>Known weighted points: '+str(c['weighted_known_points'])+'/80. Unresolved Surface contributes 0–20 points; possible complete score: '+str(c['full_score_interval'][0])+'–'+str(c['full_score_interval'][1])+'/100.</p>')
 parts.append('<div class="bars">'+''.join('<div>'+esc(r[1])+' — '+('N/V' if v is None else str(v)+'/100')+('<progress max="100" value="'+str(v)+'"></progress>' if v is not None else '')+'</div>' for r,v in zip(rubric,c['category_scores'].values()))+'</div>')
 parts.append('<p><b>What works:</b> '+esc(c['strengths'])+'</p><p><b>Why it loses points / evidence limits:</b> '+esc(c['deductions'])+'</p><p><b>First improvement:</b> '+esc(c['priority_action'])+'</p>')
 for v in c['variants']:
  key=v['id'];base=OUT/('supplement' if key in sup else 'renders')/key
  if c['key']=='monastery':
   base=OUT/'native-monastery'/v['variant'];label='Final 077 native geometry envelope; diagnostic colours; all states, local coordinates; no native materials/props/stamp transform.'
  else:label='Blender source preview; '+('shared-origin shelter included; neutral ground proxy.' if c['key']=='hideout' else 'neutral ground proxy hides underground foundation.' if c['key']=='house' else 'not native shader/terrain proof.')
  parts.append('<h3>Variant '+esc(v['variant'])+'</h3><p class="muted">'+esc(label)+'</p><div class="gallery">'+picture(base/'iso.png','Isometric — '+v['id'])+picture(base/'back.png','Reverse — '+v['id'])+'</div>')
  parts.append('<p class="muted">Source mesh triangles: '+str(v['triangles'])+'; material slots: '+str(v['material_slots'])+'. Not a runtime draw/triangle total. '+esc(v['state_scope']['status'])+'</p><p><code>'+esc(v['source'])+'</code></p>')
 if c['key'] in ('barracks','town_center','archery_range','stable','blacksmith','market','keep','monastery','siege_workshop'):
  donor=next(m for m in metrics if m['family']=='stock_'+c['key']);parts.append('<details><summary>Official stock donor control</summary><p>Matched rendering setup, independently normalized apparent scale; material projection artifacts are not native defects.</p><div class="gallery">'+picture(OUT/'renders'/donor['id']/'iso.png',donor['id'])+'</div></details>')
 parts.append('</details>')
parts.append('<h2>Separate technical / native evidence categories</h2><table><tr><th>Category</th><th>Status</th></tr>'+''.join('<tr><td>'+esc(k.replace('_',' ').title())+'</td><td>'+esc(v)+'</td></tr>' for k,v in report['runtime_checks'].items())+'</table><h2>Scope and limitations</h2><ul>'+''.join('<li>'+esc(v)+'</li>' for v in report['limits'])+'</ul><h2>Package and inspection evidence</h2><pre>'+esc(json.dumps(report['inspection'],indent=2))+'</pre><p>Final 077 SGA SHA-256: <code>'+evidence['sga_sha256']+'</code>. Prior audit freshly re-extracted and matched all 1,386 members. This report rechecked all inspected source hashes and texture-path/packed-image availability.</p><p>Reproducible evidence: <code>output/building_style_audit_077/{jobs,render-metrics,supplement-metrics,scorecards}.json</code>; final Monastery geometry receipt under <code>native-monastery/receipt.json</code>. Earlier 075 comparison sheets and performance bounds support, but do not replace, the current inspection.</p><script>let q=document.getElementById("filter");q.addEventListener("input",()=>{let s=q.value.toLowerCase();document.querySelectorAll(".card").forEach(c=>{c.hidden=!c.textContent.toLowerCase().includes(s)});document.querySelectorAll("#scores tbody tr").forEach(r=>{r.hidden=document.getElementById(r.dataset.name).hidden})});</script></html>')
target=ROOT/'docs/BUILDING_STYLE_AUDIT_077.html';target.write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps(dict(report=str(target),family_count=len(cards),average=report['family_average'],scores={c['name']:c['score'] for c in cards}),ensure_ascii=False))
