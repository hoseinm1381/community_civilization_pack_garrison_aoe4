"""Textured presentation of saved native donor/remodel pairs at game height."""
import bpy, json, sys, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'output/release_010/houses';ART=ROOT/'art/authoring/houses_010'
recipe=json.loads((OUT/'materials-ready.json').read_text());ages=list(map(int,sys.argv[sys.argv.index('--')+1:])) if '--' in sys.argv else [1,2,3,4]
proof=[]
for age in ages:
 row=next(r for r in recipe['models'] if r['age']==age)
 donor_source=json.loads(next((ROOT/f'art/stock_cache/houses_010/age{age:02}').rglob('decoded-static.json')).read_text())
 pts=[p for g in donor_source['geometry']['groups'] for p in g['positions']];hi=[max(v[i] for v in pts) for i in range(3)];lo=[min(v[i] for v in pts) for i in range(3)]
 center=Vector(((hi[0]+lo[0])/2,(hi[1]+lo[1])/2,hi[2]*.44));span=max(hi[0]-lo[0],hi[1]-lo[1],hi[2])
 for kind in ['before','after']:
  blend=ART/(f'Chinese_A_age{age:02}_donor.blend' if kind=='before' else f'Vietnam_Kinh_House_Age{age:02}.blend');bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene
  for m in bpy.data.materials:
   if not m.use_nodes:continue
   for node in m.node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image:
     original=str(Path(bpy.path.abspath(node.image.filepath)));path=recipe['preview_projections'].get(original)
     if path:
      old=node.image;im=bpy.data.images.load(path,check_existing=True);im.colorspace_settings.name=old.colorspace_settings.name;node.image=im
   control=m.node_tree.nodes.get('GARRISON Material Controls')
   if control and control.inputs.get('Team Colour Strength'):control.inputs['Team Colour Strength'].default_value=0
  if kind=='after':
   for ob in [x for x in sc.objects if x.type=='MESH']:
    matrow=next(r for r in row['materials'] if r['name']==ob.get('garrison_material_slot'))
    for mat in ob.data.materials:
     for edit in matrow['textures']:
      node=mat.node_tree.nodes.get('Essence · '+edit['slot'])
      assert node,(mat.name,edit['slot'])
      im=bpy.data.images.load(edit['image'],check_existing=True);im.colorspace_settings.name='sRGB' if edit['slot'].startswith('albedo') else 'Non-Color';node.image=im
   bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(blend))
  # These presentation objects are only created after editable asset save.
  groundmat=bpy.data.materials.new('Presentation ground');groundmat.diffuse_color=(.18,.19,.13,1);groundmat.use_nodes=True;groundmat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.18,.19,.13,1)
  bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.025));ground=bpy.context.object;ground.name='Presentation ground';ground.data.materials.append(groundmat)
  world=sc.world or bpy.data.worlds.new('Presentation world');sc.world=world;world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.3,.36,.43,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.7
  light=bpy.data.objects.new('Presentation sun',bpy.data.lights.new('Presentation sun','SUN'));sc.collection.objects.link(light);light.rotation_euler=(.45,-.65,-.5);light.data.energy=3;light.data.angle=.12
  sc.render.engine='CYCLES';sc.cycles.samples=16;sc.cycles.use_denoising=True;sc.render.resolution_x=1100;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
  for view,vec in [('game',(1,-1,.85)),('facade',(1,0,.35))]:
   cam=bpy.data.objects.new('Presentation camera',bpy.data.cameras.new('Presentation camera'));sc.collection.objects.link(cam);cam.location=center+Vector(vec).normalized()*span*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span*1.34;sc.camera=cam
   dest=OUT/f'age{age:02}-{kind}-textured-{view}.png';sc.render.filepath=str(dest);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
  proof.append({'age':age,'state':kind,'source':str(blend),'sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'center':list(center),'ortho_scale':span*1.34,'ground_z':-.025,'view':'same actual donor framing before/after; below-ground donor foundation occluded by presentation ground','engine':'Cycles16samples','runtime_proof':False})
  (OUT/'textured-preview-validation.json').write_text(json.dumps(proof,indent=2))
 print('HOUSE_TEXTURED_READY',age,flush=True)
