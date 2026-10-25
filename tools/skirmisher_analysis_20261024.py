"""Read existing masters and render isolated review images; never save a blend."""
from pathlib import Path
import bpy,json,sys,math,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,json.loads((ROOT/'workspace.json').read_text()))
OUT=ROOT/'output/skirmisher_analysis_20261024';OUT.mkdir(parents=True,exist_ok=True)
report={};donor='--donor' in sys.argv
for family in (['skirmisher2','skirmisher4'] if donor else ['skirmisher2','skirmisher3','skirmisher4','javelin2']):
    path=ROOT/'art/authoring/release_079'/family/'r3/model.blend'
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene=bpy.context.scene;body=next(o for o in scene.objects if o.type=='MESH' and o.get('garrison_lod_level')==1 and o.get('garrison_logical_path')) if donor else bpy.data.objects['body_lod1']
    for o in scene.objects:
        if o.type=='MESH':o.hide_render=o!=body
    vs=[body.matrix_world@v.co for v in body.data.vertices]
    minimum=Vector([min(p[i] for p in vs) for i in range(3)]);maximum=Vector([max(p[i] for p in vs) for i in range(3)])
    areas={};uv=body.data.uv_layers.active
    for face in body.data.polygons:
        coords=[uv.data[i].uv for i in face.loop_indices];u=sum(p.x for p in coords)/len(coords);v=sum(p.y for p in coords)/len(coords)
        tile=min(3,int(u*4))+4*min(3,int(v*4));areas[tile]=areas.get(tile,0)+face.area
    nodes=[]
    for mat in body.data.materials:
        nodes.append({'material':mat.name,'images':[{'node':n.name,'image':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file)} for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]})
    report[family]={'source':str(path),'source_sha256':before,'dimensions':list(maximum-minimum),'lod_triangles':{o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in scene.objects if o.type=='MESH' and o.name.startswith('body_lod')},'area_by_uv_tile':areas,'masked_tile9_surface_fraction':areas.get(9,0)/sum(areas.values()),'components':[{'name':o.name,'tile':o.get('079_tile'),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)} for o in scene.objects if o.type=='MESH' and o.get('079_component')],'materials':nodes,'bones':len(next((o for o in scene.objects if o.type=='ARMATURE'),body).data.bones) if family.startswith('skirmisher') else 0}
    scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world.color=(.09,.09,.09);shade=scene.display.shading;shade.light='STUDIO';shade.studiolight_rotate_z=.5;shade.color_type='TEXTURE';shade.show_shadows=True;shade.show_cavity=True;shade.cavity_type='BOTH';shade.background_type='WORLD'
    for mat in body.data.materials:
        tex=next((n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'albedo' in n.image.name.lower()),None)
        if tex:mat.node_tree.nodes.active=tex
    scene.view_settings.view_transform='Standard'
    center=(minimum+maximum)/2
    camera=bpy.data.objects.new('Analysis camera',bpy.data.cameras.new('Analysis camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=max(maximum-minimum)*1.18
    for label,offset in [('front',(0,-5,.3)),('threequarter',(3,-5,1.8))]:
        camera.location=center+Vector(offset);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(('donor-' if donor else '')+family+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
(OUT/('donor-source-analysis.json' if donor else 'source-analysis.json')).write_text(json.dumps(report,indent=2))
print('ANALYSIS_COMPLETE',str(OUT))
