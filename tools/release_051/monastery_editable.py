"""Durable editable native-local OBJ of retained 051 monastery detail components."""
from __future__ import annotations
import struct,sys
import numpy as np
from common import ROOT,OUT,ART,RECIPES,guarded,read,sha,write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import rc

def main():
    guarded();rows=[]
    for age in (3,4):
        recipe_path=RECIPES/f'monastery/age{age:02}-detail-retained-ordinals.json'
        recipe=read(recipe_path);assert recipe['age']==age
        rrgeom=OUT/f'monastery/payload/art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
        geobs=[c for c in rc.walk(rc.load(rrgeom).roots) if c.tag==b'GEOB']
        assert len(geobs)==2
        v,i=geobs;vc,_,stride,_=struct.unpack_from('<4I',v.payload)
        ic,_,width,_=struct.unpack_from('<4I',i.payload)
        assert stride==20 and width==2 and ic//3==len(recipe['retained_triangle_ordinals'])
        raw=np.ndarray((vc,4),dtype='<f2',buffer=v.payload,offset=16,strides=(stride,2))
        xyz=np.stack((-raw[:,0],-raw[:,2],raw[:,1]),axis=1).astype(np.float32)
        uv=np.ndarray((vc,2),dtype='<f2',buffer=v.payload,offset=28,strides=(stride,2)).astype(np.float32)
        assert np.isfinite(xyz).all() and np.isfinite(uv).all()
        obj=ART/f'monastery/age{age:02}/detail-051-retained-native-local.obj'
        obj.parent.mkdir(parents=True,exist_ok=True)
        components=recipe['components'];prior=None
        with obj.open('w',encoding='utf-8',newline='\n') as stream:
            stream.write('# 0.5.1 retained native detail. Original native body roof stays in exact 0.5.0 RRGeom.\n')
            for point in xyz:stream.write('v %.9g %.9g %.9g\n'%tuple(point))
            for point in uv:stream.write('vt %.9g %.9g\n'%tuple(point))
            for fi,ordinal in enumerate(recipe['retained_triangle_ordinals']):
                component=next(c['name'] for c in components if c['start']<=ordinal<c['end'])
                if component!=prior:stream.write('g '+component+'\n');prior=component
                tri=struct.unpack_from('<3H',i.payload,16+fi*6)
                assert len(set(tri))==3 and max(tri)<vc
                stream.write('f '+' '.join(f'{index+1}/{index+1}' for index in tri)+'\n')
        row={'age':age,'editable_detail_obj':str(obj),'sha256':sha(obj),'bytes':obj.stat().st_size,
             'vertices':vc,'triangles':ic//3,'source_groups':'exact 050 authored component face ranges',
             'uv':'native UVMap half floats preserved per vertex',
             'native_rrgeom':str(rrgeom),'native_rrgeom_sha256':sha(rrgeom),
             'retained_index_recipe':str(recipe_path),'retained_index_recipe_sha256':sha(recipe_path),
             'body_mesh':'unchanged native 050 RRGeom; no separate edited body OBJ',
             'reference_blends_are_not_saved_051_repair':True}
        write(RECIPES/f'monastery/age{age:02}-editable.json',row)
        rows.append(row)
        print('EDITABLE_DETAIL',age,vc,ic//3,obj.stat().st_size)
    write(OUT/'monastery/editable-assets.json',{'status':'durable_editable_detail_obj_and_native_rebuild_recipe',
          'blender_background_startup':'timed out in task-owned isolated attempts; unrelated live scene not saved',
          'ages':rows})

if __name__=='__main__':main()
