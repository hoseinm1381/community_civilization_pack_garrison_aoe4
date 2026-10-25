"""Hash the 030 concealed trap inputs and retain prior-release comparisons."""
from pathlib import Path
import shutil
from common import ROOT, OUT, guarded, read, write, sha
guarded()
rows=[]
for name,scale,actor in [('stake_thicket',.75,'vn_building_bambo_outpost_chi'),('stake_fan',.25,'vn_building_defense_outpost_bambo_chi')]:
    out=OUT/'traps'/name
    v=read(out/'validation.json')
    assert v['garrison_preflight']['ok'] and v['no_black_rim'] and v['no_black_cavity']
    assert all(c['passes'] for c in v['contacts']) and v['world_height']<.2
    before=out/'before_021'; before.mkdir(exist_ok=True)
    for p in (OUT.parent/'release_021/traps'/name).glob('*.png'): shutil.copy2(p,before/p.name)
    inputs={}
    for folder in (ROOT/'art/authoring/traps_030'/name,ROOT/'art/exports/traps_030'/name):
        for p in folder.rglob('*'):
            if p.is_file(): inputs[p.relative_to(ROOT).as_posix()]=sha(p)
    rows.append({'name':name,'actor':actor,'native_scale':scale,'world_width':v['source_width']*scale,'world_height':v['world_height'],'triangles':sum(g['triangles'] for g in v['geometry']),'source_export_sha256':inputs,'validation':str(out/'validation.json'),'construction_stages':[0,20],'design':'shallow mottled earth, woven bamboo and leaf cover; small interrupted openings; no black surrounding or broad black cavity'})
record={'version':'0.3.0','assets':rows,'limits':['Static authoring/export checks; native appearance needs user match review','Opaque earth/leaf cover, no terrain sampling or invisibility mechanic'],'recipe_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'tools/release_030').glob('trap*.py')}}
write(OUT/'traps/handoff.json',record)
write(ROOT/'art/recipes/release_030/traps.json',record)
print('TRAP030_HANDOFF_COMPLETE')
