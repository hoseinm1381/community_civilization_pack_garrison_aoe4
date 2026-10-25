"""Presentation-only renderer; never saves cameras into authoring sources."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
source=Path(args[0]).resolve();out=Path(args[1]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(source))
s=bpy.context.scene
objs=[o for o in s.objects if o.type=='MESH' and not o.hide_render]
pts=[o.matrix_world@v.co for o in objs for v in o.data.vertices]
lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
c=(lo+hi)/2;size=max(hi-lo)
s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=1100;s.render.resolution_y=850;s.render.resolution_percentage=100
s.world.color=(.3,.3,.3);s.view_settings.view_transform='AgX'
for vec,power in [((.8,-.8,1.6),70),((-.6,-.8,.65),40)]:
 d=bpy.data.lights.new('Review','AREA');o=bpy.data.objects.new('Review',d);s.collection.objects.link(o)
 o.location=c+Vector(vec)*size;d.energy=size*size*power;d.size=size*1.2
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));s.collection.objects.link(cam)
cam.data.type='ORTHO';cam.data.ortho_scale=size*1.4;s.camera=cam
views={'iso':(1,-1,.9),'front':(0,-1,.02),'back':(0,1,.02),'left':(-1,0,.02),'right':(1,0,.02),'top':(0,0,1),'bottom':(0,0,-1),'gameplay':(1,-1,1.35)}
if len(args)>2:views={k:v for k,v in views.items() if k in args[2].split(',')}
for name,vec in views.items():
 cam.location=c+Vector(vec).normalized()*size*2;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.ortho_scale=size*(2.1 if name=='gameplay' else 1.4)
 s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'capture.json').write_text(json.dumps({'source':str(source),'views':list(views),'projection':'orthographic','lighting':'matched prior audit','native':False},indent=2))
