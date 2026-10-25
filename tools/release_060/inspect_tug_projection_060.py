"""Read-only exact tug worker projection inspection in disposable Blender."""
import json,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import OUT,guard,read
import pilot_author_blender as donor
guard()
import addon_utils
mods=[m.__name__ for m in addon_utils.modules() if m.__name__.endswith('garrison')]
addon_utils.enable(mods[0],default_set=False,persistent=False)
manifest=next((OUT/'qualification/nonhumanoid-route-preflight/worker-elephant-stock/decoded').rglob('decoded-static.json'))
_,objects=donor.import_donor('tug_worker_exact',manifest,'art/civilizations/sultanate_ha_tug/animals/tug_elephant_worker_age01/tug_elephant_worker_age01.rgm')
print('TUG_OBJECTS='+json.dumps([{'name':o.name,'verts':len(o.data.vertices),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'material':[m.name if m else '' for m in o.data.materials],'groups':[g.name for g in o.vertex_groups][:4]} for o in objects if o.type=='MESH']))
