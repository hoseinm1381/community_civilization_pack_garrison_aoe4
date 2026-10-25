"""Two task-owned baseline captures from frozen 074 authoring source; never save."""
import bpy,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(Path(__file__).parent))
from render_reference import configure_render
source=ROOT/'art/authoring/buildings_070/architecture-final-r4.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
settings=json.loads((ROOT/'output/release_075/comparators/render-recipes/palace.json').read_text())['render_settings']
for family,colname in [('garden','CCP070_Imperial_Garden_Detailed_r4'),('foundry','CCP070_Trung_Foundries_Detailed_r3')]:
 bpy.ops.wm.open_mainfile(filepath=str(source));col=bpy.data.collections[colname]
 healthy=[o for o in col.all_objects if o.type=='MESH' and int(o.name.rsplit('_',1)[-1]) in (0,1,4,5,6)]
 for o in bpy.context.scene.objects:
  if o.type=='MESH':o.hide_render=o not in healthy
 folder=ROOT/'output/release_075/comparators/baselines'/family
 if folder.exists():raise FileExistsError(folder)
 capture=configure_render(healthy,folder,settings)
 (folder/'capture.json').write_text(json.dumps({'source':str(source),'source_sha256':digest,'collection':colname,'healthy_parts':[o.name for o in healthy],'capture':capture,'native':False},indent=2)+'\n')
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
