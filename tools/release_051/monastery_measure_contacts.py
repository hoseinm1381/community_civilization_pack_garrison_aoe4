"""Measure current native roof and retained shrine contacts in common metre axes."""
from __future__ import annotations
import math,struct,sys
from collections import defaultdict
import numpy as np
from common import ROOT,OUT,guarded,read,sha,write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import rc

def native_detail_points(path):
    v=next(c for c in rc.walk(rc.load(path).roots) if c.tag==b'GEOB')
    count,_,stride,_=struct.unpack_from('<4I',v.payload);assert stride==20
    raw=np.ndarray((count,4),dtype='<f2',buffer=v.payload,offset=16,strides=(stride,2))
    return np.stack((-raw[:,0],-raw[:,2],raw[:,1]),axis=1).astype(np.float32)

def component_bounds(points,indices,start,end):
    tri=np.asarray(indices[start:end],dtype=np.int32)
    used=points[np.unique(tri.reshape(-1))]
    return {'minimum':used.min(axis=0).tolist(),'maximum':used.max(axis=0).tolist(),
            'vertex_count':len(used),'triangle_count':end-start}

def nearest_contacts(roof,support,cell=.10):
    # Exact source vertices, deduplicated only for proximity measurement.
    roof=np.unique(np.asarray(roof,dtype=np.float32),axis=0)
    support=np.unique(np.asarray(support,dtype=np.float32),axis=0)
    cells=defaultdict(list)
    for i,p in enumerate(support):cells[tuple(np.floor(p/cell).astype(int))].append(i)
    near=[]
    for p in roof:
        key=np.floor(p/cell).astype(int)
        ids=[idx for dx in (-1,0,1) for dy in (-1,0,1) for dz in (-1,0,1)
             for idx in cells.get((int(key[0]+dx),int(key[1]+dy),int(key[2]+dz)),())]
        if ids:
            q=support[ids]
            dist=np.linalg.norm(q-p,axis=1)
            best=int(np.argmin(dist))
            near.append((float(dist[best]),p.tolist(),q[best].tolist()))
    near.sort(key=lambda x:x[0])
    return {'roof_unique_vertices':len(roof),'support_unique_vertices':len(support),
            'nearest_vertex_m':near[0][0] if near else None,
            'within_2cm':sum(r[0]<=.02 for r in near),
            'within_5cm':sum(r[0]<=.05 for r in near),
            'within_10cm':sum(r[0]<=.10 for r in near),
            'nearest_pairs_xyz':near[:5]}

def main():
    guarded();media={x['member']:x for x in read(ROOT/'output/castle_next/integration/building-media.json')['payloads']}
    donors=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors']
    receipt=read(OUT/'monastery/receipt.json');report=[]
    for age in (3,4):
        donor=donors[f'monastery{age:02}']['decoded_static']
        groups=donor['geometry']['groups']
        roof=np.asarray(groups[0]['positions'],dtype=np.float32)
        supports=np.concatenate([np.asarray(x['positions'],dtype=np.float32) for x in groups[1:]])
        native=nearest_contacts(roof,supports)
        member=f'art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
        source=media[member]['file'];target=OUT/'monastery/payload'/member
        points=native_detail_points(source)
        old=[c for c in rc.walk(rc.load(source).roots) if c.tag==b'GEOB'][1]
        old_ic=struct.unpack_from('<I',old.payload)[0]
        indices=np.frombuffer(old.payload,dtype='<u2',offset=16,count=old_ic).reshape((-1,3))
        assert len(indices)==1468
        parts={name:component_bounds(points,indices,a,b) for name,a,b in
               [('bell_pad',108,120),('bell_posts',796,820),('bell_tile_roof',820,1140),
                ('lotus_plinth',120,132),('lotus_basin',1280,1372)]}
        contacts={'bell_post_bottom_minus_pad_top_m':parts['bell_posts']['minimum'][2]-parts['bell_pad']['maximum'][2],
                  'lotus_basin_bottom_minus_plinth_top_m':parts['lotus_basin']['minimum'][2]-parts['lotus_plinth']['maximum'][2],
                  'bell_roof_eave_min_minus_posts_top_m':parts['bell_tile_roof']['minimum'][2]-parts['bell_posts']['maximum'][2]}
        assert abs(contacts['bell_post_bottom_minus_pad_top_m'])<.03
        assert abs(contacts['lotus_basin_bottom_minus_plinth_top_m'])<.03
        transform=next(a for a in receipt['ages'] if a['age']==age)['stamp_proof']['base_transform']
        assert transform[:4]==[0.0,1.0,0.0,-0.0] and transform[4:7]==[0.0,0.0,-.75]
        report.append({'age':age,'native_body_roof_to_support':native,
                       'retained_detail_component_bounds_local_m':parts,
                       'retained_detail_contact_gaps':contacts,
                       'stamp_game_quaternion_xyzw':transform[:4],
                       'stamp_game_translation_xyz':transform[4:7],
                       'projection':'Game Y-up: local decoded x,y,z -> game -x,z,-y; 180-degree game-Y yaw maps to Blender vertical-Z yaw, game Z -0.75 maps to decoded Y +0.75; rigid transform preserves measured gap distances.',
                       'body_roof_sha256':media[f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom']['sha256'],
                       'detail_after_sha256':sha(target)})
        print('MEASURED_CONTACTS',age,native['within_5cm'],contacts)
    write(OUT/'monastery/geometry-contacts.json',{'status':'measured_on_native_roof_and_retained_detail',
          'ages':report,'runtime_material_and_selector_gate':'pending match'})

if __name__=='__main__':main()
