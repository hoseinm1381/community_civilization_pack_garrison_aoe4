"""Measure connected native-detail components in common stamp-space axes."""
import numpy as np
from common import OUT,guarded,write,sha

def components(points,faces):
    parent=list(range(len(points)))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for a,b,c in faces:
        a=int(a);b=int(b);c=int(c)
        parent[find(b)]=find(a);parent[find(c)]=find(a)
    rows={}
    for fi,tri in enumerate(faces):rows.setdefault(find(int(tri[0])),[]).append(fi)
    return sorted(rows.values(),key=len,reverse=True)

def main():
    guarded();ages=[]
    for age in (3,4):
        file=OUT/f'monastery/diagnostic-canopy-051/previews/age{age:02}/native-healthy-compound.npz'
        with np.load(file) as d:p,f,m=d['positions'],d['faces'],d['material']
        ids=np.flatnonzero(m==3);detail=f[ids]
        parts=[]
        for ci,local in enumerate(components(p,detail)):
            tris=detail[local];xyz=p[tris];lo=xyz.min(axis=(0,1));hi=xyz.max(axis=(0,1))
            stages=sorted({'0' if t<132 else '40' if t<1140 else '80' for t in local})
            parts.append({'part':ci,'triangles':len(local),'triangle_ordinals':local,
                          'stamp_bounds_xyz':[lo.tolist(),hi.tolist()], 'stages':stages})
        write(OUT/f'monastery/diagnostic-stages/age{age:02}-components.json',
              {'age':age,'source_sha256':sha(file),'parts':parts})
        ages.append({'age':age,'components':len(parts),'largest':[(x['part'],x['triangles'],x['stamp_bounds_xyz']) for x in parts[:12]]})
        print('DETAIL_COMPONENTS',age,len(parts),[(x['part'],x['triangles']) for x in parts[:12]])
    write(OUT/'monastery/diagnostic-stages/components-summary.json',{'ages':ages})

if __name__=='__main__':main()
