"""Match editable-master preview to the explicit V flip used by FBX exporters.

Authoring UVs encode top-origin atlas rows. The clone-only export flips V into
Blender/FBX convention. A shader-only mapping makes masters preview that same
coordinate conversion without altering any qualified geometry or export UV.
"""
import bpy
names=('CCP070_Garden','CCP070_Foundry','CCP070_Kinh_Thien','CCP070_University')
changed=[]
for m in bpy.data.materials:
    if not m.name.startswith(names) or not m.use_nodes:continue
    n=m.node_tree.nodes
    images=[i for i in n if i.bl_idname=='ShaderNodeTexImage']
    if not images:continue
    mapping=n.get('CCP070_Export_V_Convention')
    if mapping is None:
        coords=n.new('ShaderNodeTexCoord')
        mapping=n.new('ShaderNodeMapping');mapping.name='CCP070_Export_V_Convention'
        mapping.inputs['Scale'].default_value=(1,-1,1)
        mapping.inputs['Location'].default_value=(0,1,0)
        m.node_tree.links.new(coords.outputs['UV'],mapping.inputs['Vector'])
    for image in images:m.node_tree.links.new(mapping.outputs['Vector'],image.inputs['Vector'])
    changed.append(m.name)
print({'preview_materials_corrected':changed,'mesh_uv_changed':False,'native_runtime_proof':False})
