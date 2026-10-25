"""Owned, deterministic mesh helpers for the Ministry and farm-edge art.

Only run from a dedicated factory-startup Blender process with the root Blender token.
"""
import bmesh
import bpy
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mesh(name, vertices, faces, material, tile):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.materials.append(material)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    uv = data.uv_layers.new(name="UVMap")
    idx = {"brick": 0, "timber": 1, "tile": 2, "plaster": 3,
           "earth": 4, "water": 5, "rice": 6, "thatch": 7}[tile]
    col, row = idx % 4, idx // 4
    for face in data.polygons:
        points = [data.vertices[data.loops[li].vertex_index].co for li in face.loop_indices]
        span = [max(v[i] for v in points) - min(v[i] for v in points) for i in range(3)]
        axes = sorted(range(3), key=lambda i: span[i], reverse=True)[:2]
        for li, v in zip(face.loop_indices, points):
            uv.data[li].uv = ((col + .06 + .88 * (v[axes[0]] - min(p[axes[0]] for p in points)) / max(span[axes[0]], 1e-8)) / 4,
                              (row + .06 + .88 * (v[axes[1]] - min(p[axes[1]] for p in points)) / max(span[axes[1]], 1e-8)) / 2)
    return obj


def box(name, center, dimensions, material, tile):
    x, y, z = center
    a, b, c = [d / 2 for d in dimensions]
    verts = [(x-a,y-b,z-c),(x+a,y-b,z-c),(x+a,y+b,z-c),(x-a,y+b,z-c),
             (x-a,y-b,z+c),(x+a,y-b,z+c),(x+a,y+b,z+c),(x-a,y+b,z+c)]
    faces = [(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    return mesh(name, verts, faces, material, tile)


def gable(name, center, width, depth, eave, ridge, thickness, material, tile):
    """Solid six-point extrusion, ridge along X; no paper-thin roof plane."""
    x, y = center
    half = depth / 2
    cross = [(y-half,eave-thickness),(y,eave+ridge-thickness),
             (y+half,eave-thickness),(y+half,eave),(y,eave+ridge),(y-half,eave)]
    verts = [(xx, yy, zz) for xx in (x-width/2, x+width/2) for yy,zz in cross]
    faces = [tuple(reversed(range(6))), tuple(range(6,12))]
    faces += [(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)]
    return mesh(name, verts, faces, material, tile)


def hipped_tile_roof(name, center, width, depth, eave, rise, thickness, material):
    """Closed pitched roof with shallow hipped ends and restrained eave kick."""
    cx,cy=center
    xs=[-width/2,-width*.43,-width*.30,-width*.15,0,width*.15,width*.30,width*.43,width/2]
    ys=[-depth/2,-depth*.44,-depth*.33,-depth*.17,0,depth*.17,depth*.33,depth*.44,depth/2]
    nx=len(xs);ny=len(ys)
    verts=[]
    for level in (0,1):
        for x in xs:
            for y in ys:
                side=abs(y)/(depth/2)
                end=abs(x)/(width/2)
                hip=1-.29*max(0,(end-.73)/.27)
                kick=.12*max(0,(side-.78)/.22)**2
                corner=.06*max(0,(end-.77)/.23)*max(0,(side-.75)/.25)
                z=eave+rise*(1-side)*hip+kick+corner-level*thickness
                verts.append((cx+x,cy+y,z))
    faces=[]
    for i in range(nx-1):
        for j in range(ny-1):
            a=i*ny+j;b=(i+1)*ny+j
            faces.append((a,b,b+1,a+1))
            faces.append(tuple(reversed((a+nx*ny,b+nx*ny,b+nx*ny+1,a+nx*ny+1))))
    boundary=list(range(ny))
    boundary += [i*ny+ny-1 for i in range(1,nx)]
    boundary += [(nx-1)*ny+j for j in range(ny-2,-1,-1)]
    boundary += [i*ny for i in range(nx-2,0,-1)]
    for a,b in zip(boundary,boundary[1:]+boundary[:1]):
        faces.append((a,b,b+nx*ny,a+nx*ny))
    obj=mesh(name,verts,faces,material,"tile")
    # One continuous atlas scale over the roof; course lines do not restart at
    # every quad boundary. The shared atlas remains the sole material.
    uv=obj.data.uv_layers.active.data
    for loop in obj.data.loops:
        v=obj.data.vertices[loop.vertex_index].co
        uv[loop.index].uv=((2+.06+.88*(v.x-(cx-width/2))/width)/4,
                           (.06+.88*(v.y-(cy-depth/2))/depth)/2)
    return obj


def faceted_vessel(name, center, profile, material, tile, sides=10):
    """Closed low-poly storage jar/basket with profile (height,radius) rings."""
    cx,cy,z0=center
    verts=[]
    for height,radius in profile:
        for i in range(sides):
            angle=2*math.pi*i/sides
            verts.append((cx+radius*math.cos(angle),cy+radius*math.sin(angle),z0+height))
    faces=[tuple(reversed(range(sides))),tuple(range((len(profile)-1)*sides,len(profile)*sides))]
    for ring in range(len(profile)-1):
        for i in range(sides):
            faces.append((ring*sides+i,ring*sides+(i+1)%sides,
                          (ring+1)*sides+(i+1)%sides,(ring+1)*sides+i))
    return mesh(name,verts,faces,material,tile)


def join_stage(objects, name, stage):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = name
    result["garrison_building_first_stage"] = stage
    return result


def validate(objects):
    rows = []
    for obj in objects:
        bm = bmesh.new(); bm.from_mesh(obj.data)
        row = {"name": obj.name, "vertices": len(bm.verts), "faces": len(bm.faces),
               "triangles": sum(len(face.verts)-2 for face in bm.faces),
               "non_manifold_edges": sum(not edge.is_manifold for edge in bm.edges),
               "degenerate_faces": sum(face.calc_area() < 1e-9 for face in bm.faces),
               "signed_volume": bm.calc_volume(signed=True),
               "material_slots": len(obj.data.materials),
               "uv_loops": len(obj.data.uv_layers.active.data)}
        bm.free()
        assert row["non_manifold_edges"] == row["degenerate_faces"] == 0, row
        assert row["signed_volume"] > 0 and row["uv_loops"] > 0, row
        rows.append(row)
    return rows


def export_building(objects, target):
    from garrison import building_project
    building_project.parts([{"name": o.name, "first_stage": o["garrison_building_first_stage"]} for o in objects], "english-house")
    target.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    clones = []
    for index, obj in enumerate(objects):
        clone = obj.copy(); clone.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(clone)
        clone.name = f"garrison_part_{index:04}"
        for loop in clone.data.uv_layers.active.data: loop.uv.y = 1 - loop.uv.y
        clone.select_set(True); clones.append(clone)
    bpy.context.view_layer.objects.active = clones[0]
    bpy.ops.export_scene.fbx(filepath=str(target/"model.fbx"), use_selection=True,
        object_types={"MESH"}, use_mesh_modifiers=False, add_leaf_bones=False,
        bake_anim=False, axis_forward="-Z", axis_up="Y", use_custom_props=False)
    manifest = {"schema": building_project.SCHEMA, "profile": "english-house",
                "parts": [{"name": o.name, "first_stage": int(src["garrison_building_first_stage"])} for o,src in zip(clones,objects)],
                "material_name": objects[0].data.materials[0].name,
                "textures": {name: name+".png" for name in ("albedo","normal","roughness","metalness")}}
    write(target/"building.json", manifest)
    for obj in clones: bpy.data.objects.remove(obj, do_unlink=True)
    return manifest


def render_views(objects, target):
    corners = [v.co for o in objects for v in o.data.vertices]
    lo = Vector([min(v[i] for v in corners) for i in range(3)])
    hi = Vector([max(v[i] for v in corners) for i in range(3)])
    center = (lo+hi)/2
    size = max(hi-lo)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
    if scene.world is None: scene.world = bpy.data.worlds.new("CCP preview world")
    scene.world.color = (.30,.30,.30)
    scene.view_settings.view_transform = "AgX"
    scene.render.resolution_x = 900; scene.render.resolution_y = 750
    scene.render.resolution_percentage = 100
    target.mkdir(parents=True, exist_ok=True)
    light_data = bpy.data.lights.new("Presentation key", "AREA")
    light = bpy.data.objects.new("Presentation key", light_data)
    scene.collection.objects.link(light)
    light.location = center + Vector((size*.8,-size*.8,size*1.6))
    light_data.energy = size*size*70
    light_data.size = size*1.2
    fill_data=bpy.data.lights.new("Presentation fill","AREA")
    fill=bpy.data.objects.new("Presentation fill",fill_data)
    scene.collection.objects.link(fill)
    fill.location=center+Vector((-size*.6,-size*.8,size*.65))
    fill_data.energy=size*size*40
    fill_data.size=size*1.3
    for label, direction in (("iso",(1,-1,.8)),("front",(0,-1,.2)),("back",(0,1,.2)),
                             ("left",(-1,0,.2)),("right",(1,0,.2)),("top",(0,0,1)),("bottom",(0,0,-1))):
        cam = bpy.data.objects.new("Presentation only", bpy.data.cameras.new("Presentation only"))
        scene.collection.objects.link(cam)
        cam.location = center + Vector(direction).normalized()*size*2
        cam.rotation_euler = (center-cam.location).to_track_quat("-Z","Y").to_euler()
        cam.data.type = "ORTHO"; cam.data.ortho_scale = size*1.5
        scene.camera = cam; scene.render.filepath = str(target/(label+".png"))
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
    scene.camera = None
    bpy.data.objects.remove(light,do_unlink=True)
    bpy.data.objects.remove(fill,do_unlink=True)
