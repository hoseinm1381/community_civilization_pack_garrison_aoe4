"""Software preview of 051 native triangle buffers in their shared stamp space."""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from common import OUT, guarded, read, sha, write

COLORS=np.asarray(((154,143,122),(112,129,135),(73,120,150),(101,72,53),
                   (132,103,75),(71,100,65)),dtype=np.float32)
VIEWS={'iso':(1,-1,.85),'front':(0,-1,.001),'back':(0,1,.001),
       'left':(-1,0,.001),'right':(1,0,.001),'top':(0,-.001,1),
       'bottom':(0,.001,-1)}

def unit(vector):
    array=np.asarray(vector,dtype=np.float64)
    return array/max(np.linalg.norm(array),1e-12)

def render(path,age,name,eye):
    with np.load(path) as data:
        points=data['positions'].astype(np.float64)
        faces=data['faces'].astype(np.int32)
        materials=data['material'].astype(np.uint8)
    v=unit(eye);forward=-v;right=unit(np.cross(forward,(0,0,1)))
    if abs(eye[2])>.99:right=unit((1,0,0))
    up=unit(np.cross(right,forward))
    world=np.stack((points@right,points@up,points@v),axis=1)
    width,height=1200,950
    coord=world[:,:2]
    lo=coord.min(axis=0);hi=coord.max(axis=0)
    span=hi-lo;scale=min((width-110)/max(span[0],.01),(height-130)/max(span[1],.01))
    center=(lo+hi)/2
    pixel=np.column_stack(((coord[:,0]-center[0])*scale+width/2,
                           height/2-(coord[:,1]-center[1])*scale))
    xyz=points[faces]
    normals=np.cross(xyz[:,1]-xyz[:,0],xyz[:,2]-xyz[:,0])
    lengths=np.linalg.norm(normals,axis=1)
    valid=lengths>1e-5
    normals[valid]/=lengths[valid,None]
    avg_z=xyz[:,:,2].mean(axis=1)
    lit=np.clip(.72+.25*(normals@unit((-.4,-.4,1.4))),.45,1.0)
    colors=COLORS[materials].copy()
    detail=materials==3
    roof=detail & (avg_z>1.9) & (np.abs(normals[:,2])>.23)
    colors[roof]=np.asarray((150,71,52),dtype=float)
    stone=detail & (avg_z<.55)
    colors[stone]=np.asarray((130,111,88),dtype=float)
    colors=np.clip(colors*lit[:,None],0,255).astype(np.uint8)
    depth=world[faces,2].mean(axis=1)
    order=np.argsort(depth)
    image=Image.new('RGB',(width,height),(214,209,190))
    draw=ImageDraw.Draw(image)
    # The native geometry includes the original foundation/lot; the neutral
    # terrain background only makes its spatial boundary visible.
    for i in order:
        if not valid[i]:continue
        tri=pixel[faces[i]]
        color=tuple(int(x) for x in colors[i])
        draw.polygon([tuple(row) for row in tri],fill=color)
    draw.rectangle((0,0,width,45),fill=(37,43,42))
    draw.text((16,13),f'Vietnamese monastery age {age:02} / {name} / native stamp coordinates',fill='white')
    draw.rectangle((0,height-43,width,height),fill=(37,43,42))
    draw.text((16,height-28),'0.5.1 native geometry envelope incl. stock roof, details, foliage and props. Selector/material match pending.',fill='white')
    target=Path(path).parent/(name+'.png')
    image.save(target)
    return {'view':name,'file':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
            'drawn_triangles':int(valid.sum())}

def main():
    guarded(); geometry=read(OUT/'monastery/previews/geometry.json')
    ages=[]
    for item in geometry['ages']:
        age=item['age']
        images=[]
        for state,state_info in item['states'].items():
            views=VIEWS if state=='healthy' else {k:VIEWS[k] for k in ('iso','front','top')}
            images.extend(render(state_info['file'],age,state+'-'+name,eye) for name,eye in views.items())
        ages.append({'age':age,'images':images})
        print('MONASTERY_PREVIEW',age,[i['view'] for i in images])
    write(OUT/'monastery/previews/receipt.json',{'status':'source_projection_only_native_match_pending',
          'source_geometry_sha256':sha(OUT/'monastery/previews/geometry.json'),'ages':ages,
          'limit':'Exact native triangles and stamped exterior foliage/props; full roof envelope, software material and source-name state projection. Native selector runtime and shaders require match proof.'})

if __name__=='__main__':main()
