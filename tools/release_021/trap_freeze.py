"""Freeze qualified trap exports; safe read/hash only, no native cook."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(d):return {str(p.relative_to(R)):sha(p) for p in sorted(d.rglob('*')) if p.is_file()}
assets=[]
for name,scale,target in [('stake_thicket',.75,'vn_building_bambo_outpost_chi'),('stake_fan',.25,'vn_building_defense_outpost_bambo_chi')]:
    out=R/'output/release_021/traps'/name
    check=json.loads((out/'validation.json').read_text()); manifest=json.loads((out/'manifest.json').read_text())
    assert check['garrison_preflight']['ok'] and all(c['passes'] for c in check['contacts'])
    assert check['bounds']['min'][2]>=0
    before=out/'before_010';before.mkdir(exist_ok=True)
    for p in (R/'output/release_010/traps'/name).glob('*.png'):shutil.copy2(p,before/p.name)
    assets.append({'name':name,'target_ebps':target,'art_origin':'scratch','source_directory':str(Path('art/authoring/traps_021')/name),'export_directory':str(Path('art/exports/traps_021')/name),'source_width':check['source_width'],'preserved_animator_scale':scale,'expected_world_width':check['source_width']*scale,'anatomy':['closed irregular earthen ring rising modestly above terrain','dark closed cavity floor above terrain Z=0','ten short sharp stakes seated in floor','six broken bamboo fragments']+(['woven bamboo mat crossing measured rim support','pointed solid leaf scatter','ragged large exposed opening'] if name=='stake_fan' else []),'construction_stages':[0,20],'triangles':sum(x['triangles'] for x in check['geometry']),'validation_report':str((out/'validation.json').relative_to(R)),'source_files':files(R/'art/authoring/traps_021'/name),'export_files':files(R/'art/exports/traps_021'/name),'preview_files':files(out),'owner_colour':'Opaque neutral atlas, no owner colour baked; preserve existing native flags and marker graph.','world_height':check['bounds']['max'][2]*scale,'contact_proof':check['contacts'],'uv_normals_proof':check['geometry']})
result={'schema':'ccp.traps-art-handoff/v1','version':'0.2.1','assets':assets,'gameplay_edits':False,'native_cook':'not run; parent owns integration','source_axis':'Z up, XY centered; minimum Z=0; shallow cavity floor remains above terrain','recipe_sha256':{str(p.relative_to(R)):sha(p) for p in (R/'tools/release_021').glob('trap*.py')},'rebuild':{'blender':'E:/Blender5.2/blender.exe','script':'tools/release_021/trap_build.py','commands':['Run tools/verify_workspace.py --storage-only first','blender -b --factory-startup --python tools/release_021/trap_build.py -- stake_thicket','blender -b --factory-startup --python tools/release_021/trap_build.py -- stake_fan'],'note':'Serialize Blender; machine WMI workaround remains needed via child PYTHONPATH from output/release_020/integration/wmi-probe. Geometry/texture generation deterministic; FBX/blend hashes can vary by metadata.'},'limits':['Source/export/preflight only, no native cook, integration, import or match proof','Preserve normal/campaign/upgrade bindings and existing game mechanics','Both widths already compensate for existing .75 and .25 native animator scales'],'before_after':'before_010 copied unchanged accepted previews; initial-preview retains correction comparison; final root PNGs are current.'}
for p in [R/'output/release_021/traps/handoff.json',R/'art/recipes/release_021/traps_021.json']:
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2)+'\n')
print('TRAP_HANDOFF_COMPLETE')
