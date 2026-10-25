"""Freeze and verify owned house source/artifacts for integration handoff."""
import datetime, hashlib, json
from pathlib import Path
from PIL import Image, ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'output/release_010/houses';A=R/'art/authoring/houses_010'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
g=json.loads((O/'geometry-validation.json').read_text());m=json.loads((O/'materials-ready.json').read_text())
assert g['status']=='passed' and m['status']=='ready_for_serial_native_cook'
project=Path(m['project']);settings=json.loads((project/'mod-project.json').read_text())
assert settings['mod_id']=='b7fcea91-257b-408f-b9e8-ae4d8bc402e1'
assert settings['game_mode']['enabled'] is False and settings['game_mode']['live_reload'] is False
assert settings['release']['version']=='0.1.0'
models=[]
for row in g['models']:
 age=row['age'];assert sha(row['native_geometry'])==row['native_geometry_sha256'];assert row['contact_checks']['max_gap_metres']==0
 for name,resource in row['donor_resources'].items():assert sha(resource['cache_path'])==resource['sha256'],name
 row['editable_blend_sha256']=sha(row['editable_blend']);row['donor_blend_sha256']=sha(row['donor_blend'])
 previews=[]
 for state in ['before','after']:
  for view in ['game','facade']:
   p=O/f'age{age:02}-{state}-textured-{view}.png';im=Image.open(p);im.verify();previews.append({'path':str(p),'sha256':sha(p)})
 materials=next(x for x in m['models'] if x['age']==age)
 for mat in materials['materials']:
  for tex in mat['textures']:assert sha(tex['image'])==tex['sha256']
 models.append({'age':age,'geometry':row['native_geometry'],'geometry_sha256':row['native_geometry_sha256'],'donor_manifest':row['donor'],'donor_blend':row['donor_blend'],'donor_blend_sha256':row['donor_blend_sha256'],'editable_blend':row['editable_blend'],'editable_blend_sha256':row['editable_blend_sha256'],'geometry_group_count':len(row['groups']),'vertex_count':sum(x['vertex_count'] for x in row['groups']),'changed_vertex_count':sum(x['changed_vertex_count'] for x in row['groups']),'contacts':row['contact_checks'],'before_bounds':row['before_bounds'],'after_bounds':row['after_bounds'],'materials':materials['materials'],'previews':previews})
sheet=Image.new('RGB',(1200,4*516),(236,232,220));draw=ImageDraw.Draw(sheet)
for age in range(1,5):
 for col,state in enumerate(['before','after']):
  im=Image.open(O/f'age{age:02}-{state}-textured-game.png').convert('RGB');im.thumbnail((600,490));x=col*600;y=(age-1)*516+26;sheet.paste(im,(x+(600-im.width)//2,y));draw.text((x+18,y-20),f'Age {age}  |  Chinese A donor' if state=='before' else f'Age {age}  |  Vietnam remodel',fill=(35,30,20))
sheet.save(O/'houses-before-after.png')
manifest={'schema':'ccp.houses-source-handoff/v1','status':'frozen_ready_for_integration','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'project':str(project),'project_sha256':sha(project/'mod-project.json'),'settings':settings,'models':models,'comparison_sheet':str(O/'houses-before-after.png'),'comparison_sheet_sha256':sha(O/'houses-before-after.png'),'proof_scope':'Editable source, source-preserving geometry, exact interface checks, textured offline renders. No native cook, client import, or match proof by house worker.','integration_gate':'Fresh Garrison variant cook and native model bound/culling refresh, full native collection lifecycle contract validation, final changed-resource closure by integration owner.'}
(O/'house-handoff.json').write_text(json.dumps(manifest,indent=2))
(O/'geometry-validation.json').write_text(json.dumps(g,indent=2))
native_recipe=R/'art/recipes/release_010/houses-native.json';nr=json.loads(native_recipe.read_text())
for row in nr['models']:
 current=next(r for r in g['models'] if r['age']==row['age'])
 row['editable_blend_sha256']=current['editable_blend_sha256'];row['donor_blend_sha256']=current['donor_blend_sha256']
native_recipe.write_text(json.dumps(nr,indent=2))
proof=[]
for row in models:
 d=json.loads(Path(row['donor_manifest']).read_text());pts=[v for group in d['geometry']['groups'] for v in group['positions']]
 lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)];span=max(hi[0]-lo[0],hi[1]-lo[1],hi[2])
 for state in ['before','after']:
  proof.append({'age':row['age'],'state':state,'source':row['donor_blend'] if state=='before' else row['editable_blend'],'sha256':row['donor_blend_sha256'] if state=='before' else row['editable_blend_sha256'],'center':[(hi[0]+lo[0])/2,(hi[1]+lo[1])/2,hi[2]*.44],'ortho_scale':span*1.34,'ground_z':-.025,'view':'Identical donor framing and lighting before/after; presentation ground hides native buried foundation','engine':'Cycles16samples','runtime_proof':False})
(O/'textured-preview-validation.json').write_text(json.dumps(proof,indent=2))
print(json.dumps({'status':manifest['status'],'models':[(r['age'],r['vertex_count'],r['changed_vertex_count']) for r in models],'handoff_sha256':sha(O/'house-handoff.json'),'project_sha256':manifest['project_sha256']}))
