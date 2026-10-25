import bpy,json,sys,os,importlib.util
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];E=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
sys.path.insert(0,str(E));spec=importlib.util.spec_from_file_location('garrison_shared',str(E/'garrison_shared.cp313-win_amd64.pyd'));shared=importlib.util.module_from_spec(spec);sys.modules['garrison_shared']=shared;spec.loader.exec_module(shared);sys.path.insert(0,str(E.parent));import garrison;sys.modules['garrison.garrison_shared']=shared;garrison.register()
from garrison.decode_projection import _apply_decoded_static
bpy.ops.wm.read_factory_settings(use_empty=True)
p=next((R/'art/stock_cache/houses_010/age04').rglob('decoded-static.json'));d=json.loads(p.read_text());o=bpy.data.objects.new('Stock Chinese A age04',None);bpy.context.scene.collection.objects.link(o);o['garrison_decode_manifest']=str(p);o['garrison_logical_path']=d['request']['logical_path'];o['garrison_display_name']='Chinese A age04';root=_apply_decoded_static(o,d,create_controls=False)
rows=[]
for ob in bpy.context.scene.objects:
 if ob.type=='MESH':rows.append({'name':ob.name,'visible':not ob.hide_get(),'render':not ob.hide_render,'vertices':len(ob.data.vertices),'materials':[m.name for m in ob.data.materials],'props':dict(ob.items()),'bounds':[[min((ob.matrix_world@Vector(c))[i] for c in ob.bound_box) for i in range(3)],[max((ob.matrix_world@Vector(c))[i] for c in ob.bound_box) for i in range(3)]]})
(R/'output/release_010/houses/donor-inspect.json').write_text(json.dumps(rows,indent=2));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(R/'art/authoring/houses_010/Chinese_A_age04_donor.blend'))
vis=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_get() and not o.hide_render];pts=[o.matrix_world@Vector(c) for o in vis for c in o.bound_box];lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)]);center=(lo+hi)/2;span=max(hi-lo)
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.render.resolution_x=1000;sc.render.resolution_y=800;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('World');sc.world.color=(.15,.15,.15)
for name,vec in [('front',(0,-1,.1)),('iso',(1,-1,.8)),('back',(-1,1,.8))]:
 cam=bpy.data.objects.new('presentation',bpy.data.cameras.new('presentation'));sc.collection.objects.link(cam);cam.location=center+Vector(vec).normalized()*span*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span*1.4;sc.camera=cam;sc.render.filepath=str(R/'output/release_010/houses'/('donor-age04-'+name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
print('HOUSE_DONOR_INSPECTED')


