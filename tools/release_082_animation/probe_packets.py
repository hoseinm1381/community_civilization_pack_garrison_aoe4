"""Offline bit-basis experiment against the unchanged installed native decoder."""
from native_codec import *
import concurrent.futures,subprocess
DEST=OUT/'packet-probe-v2';DEST.mkdir(parents=True,exist_ok=False)
model=read();a=model.root.animations[10].animationBinding.animation
sample=json.loads((ROOT/'output/release_081/animation/cattle_idle_01.json').read_text())['samples'][0]
rest=[]
for bone in sample['bones']:rest += [*bone['translation_xyz'],0,*bone['quaternion_xyzw'],*bone['scale_xyz'],0]
dynamic=12
constants=[i for i in range(540) if i!=dynamic]
a.numFrames=16;a.duration=.5
a.compressedData=([255]*16+[0]*512)*2
a.intArrayOffsets=(0,4,4,7,8,9,9,548,548)
a.intData=[528,0,1056,0,65535,65535,8191,0,dynamic]+constants+[0]*8
a.floatArrayOffsets=(0,539,540)
a.floatData=[rest[i] for i in constants]+[1.,0.]+[0.]*4
a.firstFloatBlockScaleAndOffsetIndex=0
raw=write(model,DEST/'baseline.rhka')
packet=bytes(a.compressedData);position=raw.find(packet)
assert position>=0 and raw.find(packet,position+1)<0
def sample_file(path,target):
    args=[CFG['garrison_core'],'-m','src.core.animation_clip','--source',str(path),'--clip-index','10','--output',str(target)]
    p=subprocess.run(args,capture_output=True,text=True,timeout=60)
    if p.returncode:return {'error':p.stderr}
    data=json.loads(target.read_text())
    return {'values':[f['bones'][1]['translation_xyz'][0] for f in data['samples']]}
baseline=sample_file(DEST/'baseline.rhka',DEST/'baseline.json')
assert 'values' in baseline,baseline
assert baseline['values']==[0.]*16,baseline
def probe(bit):
    changed=bytearray(raw)
    byte=position+16+bit//128*16+15-(bit%128)//8
    changed[byte]^=1<<(bit%8)
    path=DEST/f'bit-{bit:03d}.rhka';path.write_bytes(changed)
    result=sample_file(path,DEST/f'bit-{bit:03d}.json')
    result['bit']=bit
    return result
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for result in pool.map(probe,range(256)):
        results.append(result)
        if len(results)%32==0:print('SAMPLED_BITS',len(results),flush=True)
(DEST/'basis.json').write_text(json.dumps({'baseline':baseline,'bits':results,'packet_offset':position},indent=2))
assert all('values' in x for x in results)
print('PACKET_BASIS_COMPLETE',str(DEST/'basis.json'))
