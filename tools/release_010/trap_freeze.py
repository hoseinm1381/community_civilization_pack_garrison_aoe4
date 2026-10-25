"""Freeze the trap authoring/export handoff after Blender source qualification."""
from pathlib import Path
import json, hashlib
ROOT=Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf8'))
def write(p,x): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
rows=[]
for name,blueprint,width,scale in [('stake_thicket','vn_building_bambo_outpost_chi',6.4,.75),('stake_fan','vn_building_defense_outpost_bambo_chi',20.8,.25)]:
    source=ROOT/'art/authoring/traps_010'/name; export=ROOT/'art/exports/traps_010'/name; output=ROOT/'output/release_010/traps'/name
    check=read(output/'validation.json'); manifest=read(output/'manifest.json')
    assert check['garrison_preflight']['ok'] and not check['garrison_preflight']['findings']
    assert all(c['passes'] for c in check['contacts'])
    assert len(check['geometry'])==2 and all(g['non_manifold_edges']==0 and g['degenerate_faces']==0 for g in check['geometry'])
    assert abs(check['requested_width']-width)<1e-6
    assert check['construction_stages']==[0,20]
    assert [part['first_stage'] for part in manifest['building']['parts']]==[0,20]
    correction=read(output/'stage-correction.json')
    assert correction['art_unchanged'] and correction['saved_source_verified']
    for file,expected in manifest['files'].items(): assert sha(export/file)==expected,file
    previews={}
    for label in ['game_angle','close','top','front','back','left','right','bottom']:
        p=output/(label+'.png'); assert p.is_file(); previews[str(p.relative_to(ROOT))]=sha(p)
    source_files={str(p.relative_to(ROOT)):sha(p) for p in source.iterdir() if p.suffix.lower() in ['.blend','.png']}
    rows.append({'name':name,'target_ebps':blueprint,'art_origin':'scratch','source_directory':str(source.relative_to(ROOT)),'export_directory':str(export.relative_to(ROOT)),'source_width':width,'preserved_animator_scale':scale,'expected_world_width':width*scale,'source_axis':'Z up; XY centered bounds; minimum Z=0','construction_parts':[{'name':'garrison_part_0000','content':'earth and limited folded solid foliage','first_stage':0},{'name':'garrison_part_0001','content':'irregular dark hardwood stakes','first_stage':20}],'owner_colour':'Neutral atlas; preserve native owner flags and markers in original graph. No owner colour baked.','source_files':source_files,'export_files':manifest['files'],'preview_files':previews,'validation_report':str((output/'validation.json').relative_to(ROOT)),'stage_correction_report':str((output/'stage-correction.json').relative_to(ROOT)),'triangles':sum(g['triangles'] for g in check['geometry'])})
data={'schema':'ccp.traps-art-handoff/v1','version':'0.1.0','assets':rows,'reference':{'url':'https://whc.unesco.org/document/211490','relevant_pages':'PDF pages 38-39 (printed 34-35)','interpretation':'Medieval Bach Dang hardwood stake-yard motif. These low infantry compositions are artistic extrapolations, not claimed archaeological devices.'},'rebuild':{'blender':'E:/Blender5.2/blender.exe','script':'tools/release_010/trap_build.py','runner':'tools/release_010/trap_art_runner.py','commands':['blender --background --factory-startup --python tools/release_010/trap_build.py -- stake_thicket 6.4','blender --background --factory-startup --python tools/release_010/trap_build.py -- stake_fan 20.8'],'note':'Run tools/verify_workspace.py --storage-only first. Geometry/texture recipe is deterministic. FBX/blend container bytes can carry session metadata; regenerate and re-freeze measured hashes.'},'native_cook':'Owned by release integration; this handoff proves source/export only.','gameplay_edits':False,'prohibited_changes':['No footprint or placement change','No trigger/death/lifecycle animation added','No native actor replacement','No SCAR/name/icon/age variant change']}
data['recipe_sha256']={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'tools/release_010/trap_build.py',ROOT/'tools/release_010/trap_art_runner.py',ROOT/'tools/release_010/trap_stage_fix.py']}
write(ROOT/'art/recipes/release_010/traps_010.json',data)
write(ROOT/'output/release_010/traps/final-handoff.json',data)
print(json.dumps({'assets':[{k:r[k] for k in ['name','expected_world_width','triangles','export_directory']} for r in rows],'handoff':'art/recipes/release_010/traps_010.json'},indent=2))
