"""Map independent decoder responses to bits at a full-width packet fixture."""
from native_codec import CFG,OUT
import concurrent.futures,json,subprocess
SOURCE=OUT/'packet-probe-v2';DEST=OUT/'packet-fields-v2';DEST.mkdir(parents=True,exist_ok=False)
position=json.loads((SOURCE/'basis.json').read_text())['packet_offset']
raw=bytearray((SOURCE/'baseline.rhka').read_bytes())
raw[position+16:position+48]=bytes([85])*32
def sample(bit):
    data=bytearray(raw)
    if bit>=0:data[position+16+bit//128*16+15-(bit%128)//8]^=1<<(bit%8)
    path=DEST/f'field-{bit:03d}.rhka';path.write_bytes(data)
    target=path.with_suffix('.json')
    proc=subprocess.run([CFG['garrison_core'],'-m','src.core.animation_clip','--source',str(path),'--clip-index','10','--output',str(target)],capture_output=True,text=True)
    if proc.returncode:return {'bit':bit,'error':proc.stderr}
    parsed=json.loads(target.read_text())
    return {'bit':bit,'values':[f['bones'][1]['translation_xyz'][0] for f in parsed['samples']]}
baseline=sample(-1);assert 'values' in baseline,baseline
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(sample,range(256)))
(DEST/'basis.json').write_text(json.dumps({'baseline':baseline,'bits':results},indent=2))
print('FIELD_BASIS_COMPLETE',baseline)
