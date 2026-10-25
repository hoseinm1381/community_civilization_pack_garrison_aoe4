"""Verify final native structure materials, owner masks and both UV channels."""
import struct
from pathlib import Path
from common import OUT,WORK,read,sha,write,guarded
from native_support import rc,mv
from owner_colour import structure_parameters

def main():
    guarded();media=read(WORK/'landmark-media.json');rows=[]
    payloads={r['member']:r for r in media['payloads']};params=structure_parameters()
    for model in media['models']:
        stem=model['model'];path=Path(payloads[stem+'.rrmaterial']['file'])
        material=rc.load(path);descriptors=[];masks=set()
        for mat in material.roots:
            if mat.tag!=b'GMat':continue
            descriptor=next(c.payload[4:].decode() for c in mat.children if c.tag==b'MatD')
            descriptors.append(descriptor)
            one=rc.pack_document([rc.pack_chunk(mat.kind,mat.tag,mat.payload,name=mat.name,version=mat.version)])
            slots=mv.material_slots(one)
            for key,values in params.items():
                actual=slots['parameters'][key]['values']
                assert len(actual)==len(values) and all(abs(float(a)-float(b))<1e-6 for a,b in zip(actual,values)),key
            for key,value in slots['textures'].items():
                if value=='__default':continue
                member=value.replace('\\','/').lower()
                if not member.endswith('.rrtex'):member+='.rrtex'
                assert member in payloads and sha(payloads[member]['file'])==payloads[member]['sha256'],(key,member)
                if key=='maskTex5':masks.add(member)
        assert set(descriptors)=={'structure','structure_collection'} and len(masks)==1
        count=0;groups=[]
        geometry=rc.load(payloads[stem+'.rrgeom']['file'])
        for geom in (c for c in rc.walk(geometry.roots) if c.tag==b'GEOM'):
            chunks=list(geom.children)
            for index,chunk in enumerate(chunks):
                if chunk.tag!=b'GEOB':continue
                n,_,stride,_=struct.unpack_from('<4I',chunk.payload)
                if stride==2:continue
                assert stride==24
                decl=chunks[index-1];assert decl.tag==b'GEOC'
                values=struct.unpack('<'+str(len(decl.payload)//4)+'I',decl.payload)
                assert values[0]==11 and len(values)==529
                # GEOC has 11 semantic arrays, each containing 16 typed
                # (format,byte-size,offset) declarations. Semantic8 is TEXCOORD.
                tex=1+8*16*3
                a,b=values[tex:tex+3],values[tex+3:tex+6]
                assert a[:2]==b[:2]==(13,4) and a[2]!=b[2],(a,b)
                nonzero=0
                for vertex in range(n):
                    offset=16+vertex*stride
                    uv0=chunk.payload[offset+a[2]:offset+a[2]+4]
                    uv1=chunk.payload[offset+b[2]:offset+b[2]+4]
                    assert uv0==uv1,(model['key'],vertex)
                    nonzero+=any(uv0)
                assert nonzero>0
                groups.append({'vertices':n,'stride':stride,'uv_declarations':[list(a),list(b)],'nonzero_uv_vertices':nonzero})
                count+=n
        assert groups
        rows.append({'key':model['key'],'material_sha256':sha(path),'shader_descriptors':descriptors,
                     'mask_member':next(iter(masks)),'mask_sha256':payloads[next(iter(masks))]['sha256'],
                     'native_uv0_uv1_byte_identical':True,'native_vertices_checked':count,'groups':groups,
                     'parameter_provenance':'official English ram structure shader with neutral atlas grading, normalized mask ranges and documented 0 .57 0 0 owner recipe'})
    result={'status':'passed_native_shader_mask_and_uv_binding_pending_match','models':rows,
            'media_sha256':sha(WORK/'landmark-media.json'),
            'native_match':'Two owner colours and actual rendered appearance remain untested',
            'material_pipeline':'native source material cook + supported Garrison typed model-variant parameter edits + fresh final reference cook required',
            'wrapper_limitation':media['cook'].get('package_wrapper_status'),
            'auxiliary_texture_choices':media['cook'].get('auxiliary_texture_choices',{})}
    write(OUT/'owner-colour/verification.json',result)
    print('CASTLE_OWNER_MASK_UV_PASS',len(rows),sum(r['native_vertices_checked'] for r in rows))
    return result

if __name__=='__main__':main()
