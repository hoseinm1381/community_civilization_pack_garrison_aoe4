"""Read-only inspection of retained donor and cooked animation contracts."""
import json, sys, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc

def inspect(path):
    d=json.loads(path.read_text())
    print('\nMANIFEST',str(path))
    print('KEYS',list(d))
    sk=d.get('skeleton',{})
    print('SKELETON',json.dumps({k:sk.get(k) for k in ('bone_count','root_indices','trailing_bytes')}))
    print('PALETTES',[(p['name'],p['bone_count']) for p in sk.get('skin_palettes',[])])
    src=Path(sk['source'])
    chunk=next(c for c in rc.walk(rc.parse(src.read_bytes()).roots) if c.tag==b'SKLN')
    end=sk['rest_pose']['block_offset_in_skln']
    print('SKLN_PARTITION_REGION',repr(chunk.payload[sk['hierarchy_bytes']:end]))
    print('ANIMATION',json.dumps(d.get('animation_projection',{}))[:1800])
    print('GROUPS',json.dumps([{k:g.get(k) for k in ('name','material','stream','vertex_count','triangle_count')} for g in d['geometry']['groups']]))

if __name__=='__main__':
    donors=json.loads((ROOT/'output/release_076/donors.json').read_text())
    for family in ('buffalo','skirmisher2'):
        inspect(Path(donors[family]['manifest']))
        inspect(next((ROOT/'output/release_076/cooks/v5/decoded-local'/family).glob('*/decoded-static.json')))
        for label,p in [('donor',ROOT/'output/release_076/official'/donors[family]['logical_path']),('cooked',ROOT/'output/release_078/delivery/final-v1/readback/art/scenario/garrison/cc076'/family/'model.rgm')]:
            if not p.exists():continue
            print('CHUNKS',label,str(p))
            for c in rc.walk(rc.parse(p.read_bytes()).roots):
                if c.tag in (b'SKLN',b'INFO',b'SKEL',b'SKBP',b'SKB ',b'MSBP',b'ANIM'):print(c.tag,len(c.payload),c.payload[:90])
