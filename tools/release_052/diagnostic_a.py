"""Diagnostic A: restore stock models through the exact 051 landmark stamps.

No actor, state, transform, identity, geometry, material or gameplay edits. Original
native string allocations are retained by the 050 writer, so the stock paths fit
their verified original allocations without moving any native object or pointer.
"""
import sqlite3,struct
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
from common import *

RUN=OUT/'diagnostic-a'

def visuals(tree):
    root=next(x for x in tree.objects.values() if x['type']=='StampBlueprint' and not x['owner'])
    arr=tree.field(root,root['fields']['m_blueprints']);rows=[]
    for i in range(arr['count']):
        slot=arr['data_address']+8*i
        obj=tree.by_offset[slot+struct.unpack('<q',tree.bytes(slot,8))[0]]
        if obj['type']=='VisualStampBlueprint':
            rows.append({'id':str(obj['id']),'model':tree.field(obj,obj['fields']['m_blueprint'])['text'].replace('\\','/'),
                         'transform':tree.field(obj,obj['fields']['m_transform'])['raw']})
    return rows

def contract():
    old=read(OUT.parent/'release_050/integration/private-bindings.json')
    rows=[]
    for key in ('imperial_citadel','resistance_hq'):
        for stamp in old['bindings'][key]['private_stamp_proofs']:
            change=stamp['changed_model_strings'];assert len(change)==1
            member=Path(stamp['output']).relative_to(OUT.parent/'release_050/integration/payload').as_posix()
            rows.append({'landmark':key,'member':member,'stock_source':stamp['source'],
                         'stock_source_sha256':stamp['source_sha256'],
                         'custom_model':change[0]['after'].replace('\\','/'),
                         'stock_model':change[0]['before'].replace('\\','/')})
    assert len(rows)==3 and len({r['member'] for r in rows})==3
    return rows

def extract(archive,member,target):
    if target.exists():return target
    target.parent.mkdir(parents=True,exist_ok=True)
    command('extract-'+target.parent.name+'-'+target.stem,[ARCH,'extract-member',archive,member,target])
    return target

def assert_model(path,expected):
    rows=visuals(NativeTree(path))
    assert sum(r['model']==expected for r in rows)==1,(str(path),expected,rows)

def restore_stock(source,original,out,row):
    tree=NativeTree(source);native=NativeTree(original)
    assert sha(original)==row['stock_source_sha256']
    assert len(tree.memory.payload)==len(native.memory.payload)
    before=visuals(tree);assert_model(source,row['custom_model'])
    mem=bytearray(tree.memory.payload);allowed=set();changed=[]
    for obj in tree.objects.values():
        f=obj['fields'].get('m_blueprint')
        if f is None or f.get('FieldTypeName')!='util::ReflectString<StdTraits>':continue
        current=tree.field(obj,f)['text'].replace('\\','/')
        if current!=row['custom_model']:continue
        old_obj=native.by_offset[obj['offset']]
        assert old_obj['type']==obj['type']=='VisualStampBlueprint'
        old_field=old_obj['fields']['m_blueprint']
        assert int(old_field.get('Offset'))==int(f.get('Offset'))
        value=native.field(old_obj,old_field)['text']
        assert value.replace('\\','/')==row['stock_model']
        at=obj['offset']+int(f.get('Offset'))-tree.memory.payload_offset
        nat=old_obj['offset']+int(old_field.get('Offset'))-native.memory.payload_offset
        disp,count=struct.unpack_from('<qQ',mem,at)
        ndisp,capacity=struct.unpack_from('<qQ',native.memory.payload,nat)
        assert disp==ndisp and at==nat and count<=capacity
        raw=value.encode('utf-8');assert len(raw)==capacity
        start=at+disp
        assert mem[start+count:start+capacity]==b'\0'*(capacity-count)
        mem[start:start+capacity]=raw
        struct.pack_into('<Q',mem,at+8,capacity)
        allowed.update(range(start,start+capacity));allowed.update(range(at+8,at+16))
        changed.append({'visual_id':str(obj['id']),'old':current,'new':row['stock_model'],
                        'original_allocation_bytes':capacity,'no_relocation':True})
    assert len(changed)==1
    differences={i for i,(a,b) in enumerate(zip(tree.memory.payload,mem)) if a!=b}
    assert differences and differences<=allowed
    raw=rc.rebuild(tree.document,lambda c:bytes(mem) if c.offset==tree.memory.offset else None)
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():assert out.read_bytes()==raw,'Preserve conflicting partial diagnostic payload'
    else:out.write_bytes(raw)
    final=NativeTree(out);after=visuals(final)
    expected=[dict(r,model=row['stock_model']) if r['model']==row['custom_model'] else r for r in before]
    assert after==expected
    for tag,chunk in tree.chunks.items():
        if tag!=b'RFCI':assert final.chunks[tag].payload==chunk.payload
    def object_layout(model):
        return {oid:({k:v for k,v in obj.items() if k!='fields'},
                     {name:dict(field.attrib) for name,field in obj['fields'].items()})
                for oid,obj in model.objects.items()}
    assert object_layout(tree)==object_layout(final),'Native identities or layout changed'
    assert_model(out,row['stock_model'])
    return {'member':row['member'],'file':str(out),'sha256':sha(out),'bytes':len(raw),
            'changes':changed,'changed_memory_bytes':len(differences),'all_other_memory_bytes_identical':True,
            'all_nonmemory_chunks_byte_identical':True,'all_native_identities_transforms_and_visual_memberships_unchanged':True,
            'source_sha256':sha(source),'original_stock_stamp_sha256':sha(original)}

def listing(p):
    r=subprocess.run([str(ARCH),'list',str(p),'--verify'],capture_output=True,text=True,check=True)
    x=json.loads(r.stdout);assert x['archive']['verification']['verified']
    assert x['archive']['name'].replace('-','').lower()==GUID.replace('-','').lower()
    names=[m['path'].replace('\\','/').casefold() for m in x['members']]
    assert len(names)==len(set(names));return x

def unpack(p,label):
    target=RUN/'readback'/label
    if not target.exists():command('unpack-'+label,[ARCH,'unpack',p,'--output',target])
    return target

def main():
    guard();assert sha(BASELINE)==SGA051_SHA and sha(ZIP051)==ZIP051_SHA
    assert (OUT/'baseline/freeze.json').exists(),'Freeze first'
    assert not (RUN/'receipt.json').exists(),'Preserve completed diagnostic runs'
    rows=contract();payloads=[];red=[]
    db=sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro',uri=True)
    for row in rows:
        source=extract(BASELINE,row['member'],RUN/'baseline'/row['member'])
        try:assert_model(source,row['stock_model'])
        except AssertionError:red.append(row['member'])
        else:raise AssertionError('Baseline unexpectedly already uses diagnostic stock model')
        for suffix in ('.rgm','.rgo','.rrgeom','.rrmaterial'):
            assert db.execute('SELECT 1 FROM resolved_assets WHERE lower(logical_path)=?',(row['stock_model']+suffix,)).fetchone(),(row,suffix)
        payloads.append(restore_stock(source,Path(row['stock_source']),RUN/'payload'/row['member'],row))
    db.close();assert len(red)==3
    candidate=RUN/(KEY+'.sga');assert not candidate.exists()
    mapping=RUN/'members.txt';mapping.write_text(''.join(r['member']+'='+r['file']+'\n' for r in payloads),encoding='utf-8')
    command('compose-diagnostic-a',[ARCH,'set-members',BASELINE,mapping,candidate,'--alias','data'])
    old,new=listing(BASELINE),listing(candidate)
    assert old['archive']['tocs']==new['archive']['tocs']
    names={m['path'] for m in old['members']};assert names=={m['path'] for m in new['members']}
    a,b=unpack(BASELINE,'baseline051'),unpack(candidate,'diagnostic-a')
    changes={m for m in names if sha(a/m)!=sha(b/m)}
    assert changes=={r['member'] for r in payloads}
    for r,row in zip(payloads,rows):
        assert sha(b/r['member'])==r['sha256'];assert_model(b/r['member'],row['stock_model'])
    verify_frozen()
    result={'status':'passed_diagnostic_package_preparation','purpose':'Stock geometry through the exact 051 completed landmark attachment/stamp chain; NOT the final custom-model repair',
            'version':'0.5.2','diagnostic':'A','baseline_sga_sha256':SGA051_SHA,'archive':str(candidate),'archive_sha256':sha(candidate),
            'changed_members':sorted(changes),'unchanged_members':len(names)-len(changes),'added_members':[],
            'all_other_members_byte_identical':True,'baseline_rejection_tests':red,'payloads':payloads,'contract':rows,
            'gameplay_traps_monasteries':'byte-identical to user-accepted051','native_cook':'No geometry/source recook: existing stock models are referenced through a constrained stamp string restoration. Native test is the diagnostic.',
            'native_test':'pending user comparison','next_gate':'Do not finalize 052 custom landmark repair until the comparison outcome identifies the failing layer'}
    write(RUN/'receipt.json',result);package(result)
    print('DIAGNOSTIC052_READY',result['archive_sha256'],flush=True)

def package(result):
    folder=RUN/'package';folder.mkdir(exist_ok=True)
    with ZipFile(ZIP051) as z:manifest=json.loads(z.read('garrison.json'))
    manifest['members'][0]['sha256']=result['archive_sha256']
    manifest['details'].update({'version':'0.5.2','summary':'DIAGNOSTIC A - Castle landmark stock-model comparison','description':'Diagnostic only. Stock models temporarily replace the two Castle landmark visuals through the exact 051 stamp chain. Custom designs are preserved; final repair waits for the native comparison.'})
    instructions='''COMMUNITY CIVILIZATION PACK 0.5.2 - DIAGNOSTIC A
Credits: hosein81 and chilly5

THIS IS A COMPARISON BUILD, NOT THE FINAL CUSTOM LANDMARK REPAIR.
The two Castle landmarks temporarily show their stock Chinese models. Their
names, gameplay, footprints, native entities and all 051 traps/monasteries remain.

1. Close AoE4, import this ZIP into Garrison and enable this pack.
2. Select Community Civilization Pack as Game Mode and Tuning Pack.
3. Start a fresh match, choose China, then Vietnam.
4. Build Resistance Headquarters to Castle Age. Observe it during construction
   and after it reaches 5000/5000 HP. A selection outline alone does not count.
5. In a second fresh match, do the same with Imperial Citadel.
6. Report these two rows (screenshots welcome):
   Headquarters: stock model visible during construction? visible after completion?
   Citadel: stock model visible during construction? visible after completion?

This distinguishes model/rendering from the completed attachment path. Do not
judge the temporary stock architecture as the intended final design.
Final 0.5.2 will restore the custom designs after the failing layer is isolated.
The original 0.5.1 ZIP is preserved for rollback; Live Reload remains disabled.
'''
    write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',result)
    (folder/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    target=OUT/(KEY+'-0.5.2-diagnostic-a.zip');assert not target.exists()
    sources={'garrison.json':folder/'garrison.json',KEY+'.sga':Path(result['archive']),'START-HERE.txt':folder/'START-HERE.txt','EVIDENCE.json':folder/'EVIDENCE.json'}
    with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sources.items():
            info=ZipInfo(name,date_time=(2026,10,17,0,0,0));info.create_system=3;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes(),compress_type=ZIP_DEFLATED,compresslevel=6)
    with ZipFile(target) as z:
        assert z.testzip() is None and z.namelist()==list(sources)
        assert all(z.read(n)==p.read_bytes() for n,p in sources.items())
        assert hashlib.sha256(z.read(KEY+'.sga')).hexdigest()==result['archive_sha256']
    write(RUN/'package-verification.json',{'status':'passed','zip':str(target),'zip_sha256':sha(target),'bytes':target.stat().st_size,'sga_sha256':result['archive_sha256'],'native_test':'pending user comparison','is_final_release':False})

if __name__=='__main__':main()
