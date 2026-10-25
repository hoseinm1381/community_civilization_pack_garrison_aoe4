"""Native Chunky readback of 051 compacted detail and exact 050 body roof."""
from __future__ import annotations
import struct,sys
from pathlib import Path
from common import ROOT,OUT,guarded,read,sha,write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import rc

def main():
    guarded();media={r['member']:r for r in read(ROOT/'output/castle_next/integration/building-media.json')['payloads']}
    report=[]
    for age in (3,4):
        member=f'art/scenario/cccastle/monastery_detail_age{age:02}/model.rrgeom'
        before=Path(media[member]['file']);after=OUT/'monastery/payload'/member
        assert sha(before)==media[member]['sha256']
        recipe=read(ROOT/f'art/recipes/release_051/monastery/age{age:02}-detail-retained-ordinals.json')
        assert recipe['source_sha256']==sha(before)
        original=list(rc.walk(rc.load(before).roots));updated=list(rc.walk(rc.load(after).roots))
        assert [c.tag for c in original]==[c.tag for c in updated]
        b=[c for c in original if c.tag==b'GEOB'];a=[c for c in updated if c.tag==b'GEOB']
        assert len(b)==len(a)==2
        vc,_,vs,_=struct.unpack_from('<4I',a[0].payload)
        old_ic,_,old_width,_=struct.unpack_from('<4I',b[1].payload)
        ic,_,width,_=struct.unpack_from('<4I',a[1].payload)
        assert vs==20 and width==old_width==2 and vc in (2565,2582)
        assert old_ic//3==1468 and ic//3==684
        assert a[0].payload==b[0].payload
        assert a[1].payload[4:16]==b[1].payload[4:16]
        assert len(a[1].payload)==16+ic*2
        for x,y in zip(original,updated):
            if x.offset!=b[1].offset and not x.children:assert x.payload==y.payload,(age,x.tag,x.offset)
        parts=[]
        for fi,ordinal in enumerate(recipe['retained_triangle_ordinals']):
            tri=struct.unpack_from('<3H',a[1].payload,16+fi*6)
            donor=struct.unpack_from('<3H',b[1].payload,16+ordinal*6)
            assert tri==donor and max(tri)<vc and len(set(tri))==3
        for component in recipe['components']:
            lo,hi=component['start'],component['end']
            parts.append({'name':component['name'],'source_triangles':hi-lo,
                          'retained_triangles':hi-lo if component['retained'] else 0})
        body=f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom'
        assert sha(media[body]['file'])==media[body]['sha256']
        assert not (OUT/'monastery/payload'/body).exists()
        report.append({'age':age,'detail_member':member,'detail_sha256':sha(after),
                       'body_native_roof_member':body,'body_native_roof_sha256':media[body]['sha256'],
                       'native_codec':'installed Garrison relic_chunky parser',
                       'detail_vertices':vc,'detail_triangles_before':1468,'detail_triangles_after':684,
                       'detail_removed_canopy_frame_triangles':784,
                       'original_detail_vertex_uv_and_selector_layout_byte_identical':True,
                       'detail_index_count_and_chunk_sizes_coherent':True,
                       'retained_indices_and_source_face_ranges_exact':True,
                       'new_degenerate_triangles':0,'invalid_indices':0,
                       'components':parts})
        print('NATIVE_DETAIL_READBACK',age,vc,684,784)
    write(OUT/'monastery/native-readback.json',{'status':'passed_native_chunk_and_index_readback',
          'ages':report,'garrison_decode_static':'exact frozen 050 private body already fails nonfinite UV; native Chunky readback independent of that limitation'})

if __name__=='__main__':main()
