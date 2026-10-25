"""Envelope render of every stock native roof face, for selector ambiguity review."""
import sys
import numpy as np
from common import ROOT,OUT,read,guarded,write,sha
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import source_map
from monastery_preview_extract import mesh

def main():
    guarded();media={p['member']:p for p in read(ROOT/'output/castle_next/integration/building-media.json')['payloads']}
    donors=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors'];rows=[]
    for age in (3,4):
        donor=donors[f'monastery{age:02}'];names,_=source_map(donor)
        base=media[f'art/scenario/cccastle/monastery_age{age:02}/model.rrgeom']['file']
        bp,bf,bm,_=mesh(base,donor['decoded_static']['geometry']['groups'],names,None,'all')
        old=OUT/f'monastery/previews/age{age:02}/native-healthy-compound.npz'
        with np.load(old) as d:p,f,m=d['positions'],d['faces'],d['material']
        assert len(p)>=len(bp)
        keep=m>=3
        dst=OUT/f'monastery/diagnostic-all-native-roof/age{age:02}/envelope.npz'
        dst.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(dst,positions=p,faces=np.concatenate((bf,f[keep])),material=np.concatenate((bm,m[keep])))
        rows.append({'age':age,'file':str(dst),'sha256':sha(dst)})
    write(OUT/'monastery/diagnostic-all-native-roof/receipt.json',{'status':'all_faces_envelope_not_runtime_selector_result','ages':rows})

if __name__=='__main__':main()
