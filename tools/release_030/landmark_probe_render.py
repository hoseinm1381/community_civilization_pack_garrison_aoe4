"""Temporary read-only material/UV diagnostic from a saved landmark scene."""
import bpy
import sys
from mathutils import Vector
from pathlib import Path

name=sys.argv[sys.argv.index('--')+1]
view=sys.argv[sys.argv.index('--')+2] if len(sys.argv)>sys.argv.index('--')+2 else 'top'
root=Path(__file__).resolve().parents[2]
mat=next(m for m in bpy.data.materials if m.name.startswith('CCP030_') and m.name.endswith('_atlas'))
nodes=mat.node_tree.nodes;links=mat.node_tree.links
albedo=next(n for n in nodes if n.type=='TEX_IMAGE' and 'albedo' in n.image.name)
emission=nodes.new('ShaderNodeEmission');links.new(albedo.outputs['Color'],emission.inputs['Color'])
out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');links.new(emission.outputs['Emission'],out.inputs['Surface'])
mesh_objects=[o for o in bpy.data.objects if o.type=='MESH']
co=[v.co for o in mesh_objects for v in o.data.vertices]
lo=Vector([min(v[i] for v in co) for i in range(3)]);hi=Vector([max(v[i] for v in co) for i in range(3)])
center=(lo+hi)/2;size=max(hi-lo)
cam=bpy.data.objects.new('UV probe camera',bpy.data.cameras.new('UV probe camera'))
bpy.context.scene.collection.objects.link(cam)
direction=Vector((0,0,2)) if view=='top' else Vector((1.45,-1.65,1.25))
cam.location=center+direction*size;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=size*1.5
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=2
scene.render.resolution_x=900;scene.render.resolution_y=750;scene.render.resolution_percentage=100
scene.render.filepath=str(root/'output/release_030/landmarks'/name/('probe-emission-'+view+'.png'))
bpy.ops.render.render(write_still=True)
