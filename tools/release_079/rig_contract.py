"""Inspect native SKLN partition metadata; generate donor-faithful .rig source.

No binary patching: exported FBX and this source are passed to the native cooker.
"""
import struct
from common import *
sys.path.insert(0,CFG['garrison_extension'])

def read_contract(raw):
    from garrison_shared import relic_chunky as rc
    chunks=[c for c in rc.walk(rc.parse(raw).roots) if c.tag==b'SKLN']
    if len(chunks)!=1:raise ValueError('Expected one native skeleton')
    data=chunks[0].payload;offset=0
    def integer(fmt='I'):
        nonlocal offset
        value=struct.unpack_from('<'+fmt,data,offset)[0];offset+=struct.calcsize(fmt);return value
    def string():
        nonlocal offset
        size=integer()
        if not 0<size<1024 or offset+size>len(data):raise ValueError('Invalid skeleton string')
        value=data[offset:offset+size].decode('utf-8');offset+=size;return value
    version=integer();count=integer()
    if version!=0 or not 0<count<1024:raise ValueError('Unknown skeleton layout')
    bones=[{'name':string(),'parent':integer('h')} for _ in range(count)]
    reserved=integer()
    if reserved!=0:raise ValueError('Unknown post-hierarchy field')
    partitions=[{'name':string(),'start':integer(),'count':integer()} for _ in range(integer())]
    groups=[]
    for _ in range(integer()):
        name=string();slots=[integer('i') for _ in range(integer())];groups.append({'name':name,'slots':slots})
    lod_counts=[integer() for _ in range(integer())]
    if len(data)-offset!=count*40:raise ValueError('Partition parser does not end at bind block')
    return {'bones':bones,'partitions':partitions,'groups':groups,'lod_counts':lod_counts,'bind_offset':offset}

def validate_contract(actual,expected):
    if actual['bones']!=expected['bones']:raise ValueError('Native bone hierarchy/order mismatch')
    for p in actual['partitions']:
        if p['count']<=0 or p['start']+p['count']>len(actual['bones']):raise ValueError('Invalid partition span')
    if any(i<0 or i>=len(actual['partitions']) for g in actual['groups'] for i in g['slots']):
        raise ValueError('Missing native partition LOD slot')
    for key in ('partitions','groups','lod_counts'):
        if actual[key]!=expected[key]:raise ValueError('Native partition/LOD contract mismatch: '+key)

def rig_text(contract):
    validate_contract(contract,contract)
    names=[b['name'] for b in contract['bones']]
    lines=['[HAVOK SKELETON DEFINITION FILE]','','[BONES START]',*names,'[END]','']
    for p in contract['partitions']:
        lines.extend(['[PARTITION START]',p['name']+' '+names[p['start']]+' '+names[p['start']+p['count']-1],'[END]',''])
    return '\n'.join(lines)+'\n'

def fold_weights(weights,contract,lod):
    counts=contract['lod_counts'];limit=counts[min(lod,len(counts))-1]
    bones=contract['bones'];indices={b['name']:i for i,b in enumerate(bones)};result={}
    for name,weight in weights.items():
        if weight<=0:continue
        if name not in indices:raise ValueError('Unknown weighted bone '+name)
        index=indices[name]
        while index>=limit:
            parent=bones[index]['parent']
            if parent<0 or parent>=index:raise ValueError('Invalid ancestor while folding LOD weights')
            index=parent
        target=bones[index]['name'];result[target]=result.get(target,0)+weight
    total=sum(result.values())
    if total<=0:raise ValueError('Unweighted vertex')
    return {name:w/total for name,w in result.items()}

if __name__=='__main__':
    donors=read(ROOT/'output/release_076/donors.json');report={}
    for family in ('buffalo','skirmisher2'):
        d=read(donors[family]['manifest']);official=read_contract(Path(d['skeleton']['source']).read_bytes())
        failed=read_contract((BASE/'readback/art/scenario/garrison/cc076'/family/'model.rgm').read_bytes())
        try:validate_contract(failed,official);failure=None
        except ValueError as exc:failure=str(exc)
        report[family]={'official':official,'failed_076':failed,'failure':failure,'native_root_cause_confirmed':False}
    guard();write(OUT/'diagnosis/rig-contract.json',report)
    print(json.dumps({k:{'official_groups':v['official']['groups'],'official_lods':v['official']['lod_counts'],'failed_groups':v['failed_076']['groups'],'failed_lods':v['failed_076']['lod_counts'],'failure':v['failure']} for k,v in report.items()},indent=2))
