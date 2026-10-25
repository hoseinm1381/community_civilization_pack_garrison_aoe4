"""Shared deterministic mesh and atlas helpers for 0.7.0 architecture masters.

Executed only by the claimed Blender MCP owner. No scene deletion or native cook.
"""
from pathlib import Path
import math
import bpy
from mathutils import Vector

CATEGORIES = ("stone", "wood", "plaster", "roof", "water", "clay", "metal", "foliage")
VIEW_COLORS = ((.48,.44,.37,1),(.32,.17,.10,1),(.76,.69,.55,1),
               (.48,.24,.15,1),(.19,.41,.42,1),(.57,.34,.20,1),
               (.29,.31,.30,1),(.25,.43,.25,1))

def atlas_material(name, directory, kind):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    material.node_tree.links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    for channel, socket in (("albedo", "Base Color"),
                            ("roughness", "Roughness"),
                            ("metalness", "Metallic")):
        image = bpy.data.images.load(str(directory / (kind + "_" + channel + "_2048.png")), check_existing=True)
        if channel != "albedo":
            image.colorspace_settings.name = "Non-Color"
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.label = kind + " " + channel
        material.node_tree.links.new(tex.outputs["Color"], shader.inputs[socket])
    image = bpy.data.images.load(str(directory / (kind + "_normal_2048.png")), check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    normal_texture = nodes.new("ShaderNodeTexImage")
    normal_texture.image = image
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.inputs["Strength"].default_value = .42
    material.node_tree.links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
    material.node_tree.links.new(normal_map.outputs["Normal"], shader.inputs["Normal"])
    return material

class Batch:
    def __init__(self, label, collection, material, offset=(0,0,0)):
        self.label = label
        self.collection = collection
        self.material = material
        self.offset = Vector(offset)
        self.verts = []
        self.faces = []
        self.categories = []

    def add(self, vertices, faces, category):
        start = len(self.verts)
        self.verts.extend(tuple(map(float, v)) for v in vertices)
        self.faces.extend(tuple(start+i for i in f) for f in faces)
        self.categories.extend([category]*len(faces))

    def box(self, center, size, category):
        x,y,z=center
        w,d,h=(s*.5 for s in size)
        v=[(x+sx*w,y+sy*d,z+sz*h) for sz in (-1,1)
           for sy in (-1,1) for sx in (-1,1)]
        self.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),
                    (2,6,7,3),(0,4,6,2),(1,3,7,5)],category)

    def cylinder(self, origin, radius, height, category, sides=12):
        x,y,z=origin
        v=[(x+radius*math.cos(i*2*math.pi/sides),
            y+radius*math.sin(i*2*math.pi/sides),z+j*height)
           for j in (0,1) for i in range(sides)]
        f=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
        f += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides)
              for i in range(sides)]
        self.add(v,f,category)

    def tube(self, points, radii, category, sides=8):
        v=[]
        for i,p in enumerate(points):
            tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
            tangent.normalize()
            reference=Vector((0,0,1)) if abs(tangent.z)<.85 else Vector((0,1,0))
            a=tangent.cross(reference).normalized()
            b=tangent.cross(a).normalized()
            for j in range(sides):
                angle=j*2*math.pi/sides
                v.append(Vector(p)+radii[i]*(a*math.cos(angle)+b*math.sin(angle)))
        f=[tuple(reversed(range(sides)))]
        for i in range(len(points)-1):
            for j in range(sides):
                k=(j+1)%sides
                f.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
        f.append(tuple(range((len(points)-1)*sides,len(points)*sides)))
        self.add(v,f,category)

    def slab(self, xy, top, thickness, category):
        n=len(xy)
        v=[(x,y,top-thickness) for x,y in xy]+[(x,y,top) for x,y in xy]
        f=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        self.add(v,f,category)

    def roof_tile(self, center, width, depth, category="roof"):
        x,y,z=center
        top=[(x+sx*width*.5,y+sy*depth*.5,z+(.07 if sx else 0))
             for sy in (-1,1) for sx in (-1,0,1)]
        v=top+[(a,b,c-.045) for a,b,c in top]
        f=[(0,1,4,3),(1,2,5,4),(6,9,10,7),(7,10,11,8),
           (0,6,7,1),(1,7,8,2),(3,4,10,9),(4,5,11,10),
           (0,3,9,6),(2,8,11,5)]
        self.add(v,f,category)

    def emit(self):
        mesh=bpy.data.meshes.new(self.collection.name+"_"+self.label)
        mesh.from_pydata(self.verts,[],self.faces)
        mesh.update()
        obj=bpy.data.objects.new(self.collection.name+"_"+self.label,mesh)
        self.collection.objects.link(obj)
        obj.location=self.offset
        mesh.materials.append(self.material)
        uv=mesh.uv_layers.new(name="UVMap")
        color=mesh.color_attributes.new(name="CCP070_Color",type="BYTE_COLOR",domain="CORNER")
        for poly,category in zip(mesh.polygons,self.categories):
            ci=CATEGORIES.index(category)
            cx,cy=ci%4,ci//4
            normal=poly.normal
            axes=(0,1) if abs(normal.z)>.7 else ((0,2) if abs(normal.y)>.7 else (1,2))
            for li in poly.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(cx*.25+.005+((co[axes[0]]*.42)%1)*.24,
                                cy*.5+.005+((co[axes[1]]*.42)%1)*.49)
                color.data[li].color=VIEW_COLORS[ci]
        obj["ccp070_lifecycle_part"]=self.label
        return obj
