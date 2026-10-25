"""Read the stock compiled simulation state-tree references without mutation."""
from __future__ import annotations
import hashlib,json,struct,sys,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
CFG=configuration(ROOT);OUT=Path(CFG['external_root'])/'output/release_052/stealth/official'
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent))
from garrison.addon_common import core_module
chunky=core_module('relic_chunky')
TARGETS=('activate_stealth_mal','landmark_stealth_castle_construction_complete_mal',
         'stealth_castle_spawn_forest_mal','passive_stealth_ayy')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Tree:
    def __init__(self,path,reflection):
        doc=chunky.load(path);self.chunks={x.tag:x for x in doc.roots}
        self.types={int(x.get('Id')):x for x in ET.parse(reflection).getroot()}
        self.memory=self.chunks[b'RFCI'];self.strings={};data=self.chunks[b'RSHI'].payload
        n=struct.unpack_from('<Q',data)[0];cursor=8
        for _ in range(n):
            key,length=struct.unpack_from('<QI',data,cursor);cursor+=12
            self.strings[key]=data[cursor:cursor+length].decode('utf-8',errors='replace');cursor+=length
        assert cursor==len(data)
        raw=self.chunks[b'ROBJ'].payload;n=struct.unpack_from('<Q',raw)[0]
        assert len(raw)==8+36*n
        self.objects={}
        for i in range(n):
            oid,tid,offset,owner,checksum=struct.unpack_from('<QQQQI',raw,8+36*i)
            kind=self.types[tid]
            assert checksum==int(kind.get('Checksum'))
            assert 0<=offset-self.memory.payload_offset<=len(self.memory.payload)-int(kind.get('Size'))
            fields={x.get('Name'):x for x in kind.findall('Fields/ReflectField')}
            self.objects[oid]={'id':oid,'type':kind.get('Name'),'offset':offset,'owner':owner,'fields':fields}
        self.by_offset={o['offset']:o for o in self.objects.values()}

    def buf(self,addr,size):
        idx=addr-self.memory.payload_offset
        assert 0<=idx and idx+size<=len(self.memory.payload)
        return self.memory.payload[idx:idx+size]

    def field(self,obj,f):
        addr=obj['offset']+int(f.get('Offset'));kind=f.get('FieldTypeName');size=int(f.get('BaseSize'))
        if kind=='Reflect::ReflectStringHash' or kind.startswith('FamilyManagerEnum<'):
            key=struct.unpack('<Q',self.buf(addr,8))[0]
            return {'hash':key,'text':self.strings.get(key)}
        if kind=='util::ReflectString<StdTraits>':
            displacement,length=struct.unpack('<qQ',self.buf(addr,16))
            return {'text':self.buf(addr+displacement,length).decode('utf-8',errors='replace') if length else ''}
        if kind in ('uint64_t','int64_t'):return struct.unpack('<Q',self.buf(addr,8))[0]
        if kind=='bool':return bool(self.buf(addr,1)[0])
        if kind=='float':return struct.unpack('<f',self.buf(addr,4))[0]
        if kind.startswith('util::ReflectObjectRef<'):
            refkind=self.types[int(f.get('FieldTypeId'))]
            identity=refkind.find('Fields/ReflectField[@Name="m_objectID"]')
            assert identity is not None
            return {'object_ref':struct.unpack('<Q',self.buf(addr+int(identity.get('Offset')),8))[0]}
        if kind.startswith('util::ReflectArray<'):
            displacement,count,capacity=struct.unpack('<qII',self.buf(addr,16))
            return {'data_address':addr+displacement if displacement else 0,'count':count,'capacity':capacity,'element_type':kind}
        if size==8:
            displacement=struct.unpack('<q',self.buf(addr,8))[0]
            other=self.by_offset.get(addr+displacement) if displacement else None
            return {'relative_pointer':displacement,'target_id':other['id'] if other else None,
                    'target_type':other['type'] if other else None}
        return {'type':kind,'raw':self.buf(addr,min(size,32)).hex()}

    def describe(self,obj):
        return {'id':obj['id'],'type':obj['type'],'owner':obj['owner'],
                'fields':{name:self.field(obj,f) for name,f in obj['fields'].items()}}

def main():
    check_storage(ROOT,CFG)
    path=OUT/'statetree-simulation.bin';reflection=OUT/'reflect.db'
    tree=Tree(path,reflection)
    hits=[]
    for obj in tree.objects.values():
        f=obj['fields'].get('m_name')
        if f is not None and f.get('FieldTypeName')=='Reflect::ReflectStringHash':
            value=tree.field(obj,f).get('text')
            if value and any(target in value for target in TARGETS):hits.append(obj)
    selected={x['id'] for x in hits}
    for _ in range(35):
        grown=selected|{x['id'] for x in tree.objects.values() if x['owner'] in selected}
        if grown==selected:break
        selected=grown
    rows=[tree.describe(tree.objects[i]) for i in selected]
    external=[]
    for row in rows:
        for key,value in row['fields'].items():
            if isinstance(value,dict) and 'object_ref' in value:
                ref=value['object_ref']
                if ref in tree.objects and ref not in selected:
                    external.append({'from_id':row['id'],'from_type':row['type'],'field':key,
                                     'target':tree.describe(tree.objects[ref])})
    report={'schema':'ccp.release052.stealth-state-tree-trace/v1','source':str(path),
            'sha256':sha(path),'reflect_sha256':sha(reflection),'validated_objects':len(tree.objects),
            'string_count':len(tree.strings),'root_hits':[tree.describe(x) for x in hits],
            'selected_objects':rows,'external_refs':external,'status':'read_only_reflected'}
    target=OUT/'stealth-state-trees.json';target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('STEALTH_STATE_TREE',len(tree.objects),len(hits),len(rows),len(external),target)

if __name__=='__main__':main()
