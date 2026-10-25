"""Bounded Rattan representative from the clean, weighted Archer base."""
from pathlib import Path
import sys
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ART, OUT, guard, owned, sha, write

SOURCE = ART/'archer/archer-base-v3i-clean.blend'
SOURCE_SHA = 'f6baf5bd9bb623d16fcdd7b4b3bd976ddb094f5d066db8d559fb7ab4f44a145b'
TARGET = ART/'archer/archer-rattan-v3j-representative.blend'
TARGET_SHA = '2c7783ecebdfec287160a5d389345d01d63baa76f5c7d89a121843da63d9efb8'
FITTED = ART/'archer/archer-rattan-v3k-contact.blend'
BODY = 'CCP060 · Archer II weighted body · base'
ORIGINAL_VEST = 'CCP060 · Continuous torso rattan vest'
NEW_VEST = 'CCP060 · Representative rattan vest'
KEEP = {
    'CCP060 · Back carried rattan shield',
    'CCP060 · Shield bound rounded rim',
    'CCP060 · Shield diagonal carrying strap',
    'CCP060 · Shield rear shoulder strap',
    'CCP060 · Cross reed 1', 'CCP060 · Cross reed 3',
    'CCP060 · Raised vertical reed 1', 'CCP060 · Raised vertical reed 3',
}


def _stock_brown_uv(mesh):
    """Use the donor's dark brown cloth chart, with one shared stock material."""
    layer = mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap')
    xs=[v.co.x for v in mesh.vertices]
    zs=[v.co.z for v in mesh.vertices]
    xmin,xmax=min(xs),max(xs)
    zmin,zmax=min(zs),max(zs)
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co=mesh.vertices[mesh.loops[li].vertex_index].co
            layer.data[li].uv=(.487+.018*(co.x-xmin)/max(.00001,xmax-xmin),
                               .532+.020*(co.z-zmin)/max(.00001,zmax-zmin))


def stage_rattan_representative():
    guard(); owned(TARGET)
    receipt=owned(OUT/'qualification/archer-v3j-rattan.json')
    if TARGET.exists() or receipt.exists():
        raise FileExistsError('Preserve existing v3j output')
    if Path(bpy.data.filepath).resolve()!=SOURCE.resolve() or sha(SOURCE)!=SOURCE_SHA:
        raise RuntimeError('Open pinned clean Archer v3i')
    old=bpy.data.objects[ORIGINAL_VEST]
    body=bpy.data.objects[BODY]
    native_material=body.data.materials[0]
    if len(old.data.vertices)!=416 or len(old.data.polygons)!=384:
        raise RuntimeError('Unexpected prototype vest topology')
    # Sample alternate rings and columns from the already fitted 32 x 12
    # weighted surface. Exact sample weights remain attached to their points.
    old_index=[row*32+column for row in range(0,13,2)
               for column in range(0,32,2)]
    vertices=[tuple(old.data.vertices[i].co) for i in old_index]
    faces=[]
    for row in range(6):
        for column in range(16):
            a=row*16+column
            b=row*16+(column+1)%16
            faces.append((a,b,b+16,a+16))
    mesh=bpy.data.meshes.new('CCP060 representative rattan vest mesh')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    mesh.materials.append(native_material)
    _stock_brown_uv(mesh)
    vest=bpy.data.objects.new(NEW_VEST,mesh)
    old.users_collection[0].objects.link(vest)
    vest.parent=old.parent
    for source_group in old.vertex_groups:
        vest.vertex_groups.new(name=source_group.name)
    for new_index,source_index in enumerate(old_index):
        influences=sorted(((old.vertex_groups[g.group].name,g.weight)
                           for g in old.data.vertices[source_index].groups),
                          key=lambda item:-item[1])[:4]
        total=sum(weight for _,weight in influences)
        if total<.999:
            raise RuntimeError(f'Unweighted vest vertex: {source_index}')
        for bone,weight in influences:
            vest.vertex_groups[bone].add([new_index],weight/total,'REPLACE')
    armatures=[m for m in old.modifiers if m.type=='ARMATURE']
    if len(armatures)!=1:
        raise RuntimeError('Unexpected prototype vest armature')
    modifier=vest.modifiers.new('CCP060 native archer armature','ARMATURE')
    modifier.object=armatures[0].object
    selected={NEW_VEST}|KEEP
    for name in KEEP:
        obj=bpy.data.objects.get(name)
        if obj is None or obj.type!='MESH':
            raise RuntimeError(f'Missing Rattan broad form: {name}')
        obj.data.materials.clear()
        obj.data.materials.append(native_material)
        _stock_brown_uv(obj.data)
        obj.hide_render=False
    vest.hide_render=False
    for obj in bpy.data.objects:
        if obj.type=='MESH' and (obj.name.startswith('CCP060 · Shield longitudinal reed')
                                 or obj.name.startswith('CCP060 · Shield transverse reed')
                                 or obj.name.startswith('CCP060 · Cross reed')
                                 or obj.name.startswith('CCP060 · Raised vertical reed')):
            if obj.name not in selected:
                obj.hide_render=True
    for obj in list(bpy.context.selected_objects):
        obj.select_set(False)
    body.select_set(True)
    bpy.context.view_layer.objects.active=body
    bpy.data.objects.remove(old,do_unlink=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),check_existing=False)
    detail={'source':str(SOURCE),'source_sha256':SOURCE_SHA,
            'blend':str(TARGET),'blend_sha256':sha(TARGET),
            'status':'authoring_only','native_game':False,
            'native_rattan_switch':'unresolved',
            'vest_faces_before':384,'vest_faces_after':len(mesh.polygons),
            'shield_faces':len(bpy.data.objects['CCP060 · Back carried rattan shield'].data.polygons),
            'visible_upgrade_meshes':sorted(selected),
            'material':'shared stock donor atlas material',
            'atlas_private_variant':'requires separate native integration qualification',
            'quiver':'preserved from pinned v3i'}
    write(receipt,detail)
    return detail


def stage_fit_back_shield():
    """Seat the carried shield against the back and its upper carrying strap."""
    guard(); owned(FITTED)
    receipt=owned(OUT/'qualification/archer-v3k-shield-contact.json')
    if FITTED.exists() or receipt.exists():
        raise FileExistsError('Preserve existing v3k output')
    if Path(bpy.data.filepath).resolve()!=TARGET.resolve() or sha(TARGET)!=TARGET_SHA:
        raise RuntimeError('Open pinned v3j Rattan source')
    shifts={'CCP060 · Back carried rattan shield':-.055,
            'CCP060 · Shield bound rounded rim':-.055,
            'CCP060 · Shield rear shoulder strap':-.040}
    for name,delta_y in shifts.items():
        obj=bpy.data.objects[name]
        for vertex in obj.data.vertices:
            vertex.co.y+=delta_y
        obj.data.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(FITTED),check_existing=False)
    detail={'schema':'ccp-060-archer-v3k/v1','status':'authoring_only',
            'source':str(TARGET),'source_sha256':TARGET_SHA,
            'blend':str(FITTED),'blend_sha256':sha(FITTED),
            'shield_and_strap_y_translations_m':shifts,
            'native_quiver':'unchanged from v3i',
            'native_rattan_switch':'unresolved'}
    write(receipt,detail)
    return detail
