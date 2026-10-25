"""Visually isolate the three native detail source stages against the full hall."""
import numpy as np
from common import OUT,guarded,write,sha
from monastery_render import render,VIEWS

def main():
    guarded();rows=[]
    for age in (3,4):
        source=OUT/f'monastery/diagnostic-canopy-051/previews/age{age:02}/native-healthy-compound.npz'
        with np.load(source) as d:points,faces,m=d['positions'],d['faces'],d['material']
        detail=np.flatnonzero(m==3)
        assert len(detail)==1468
        for label,lo,hi in (('stage00',0,132),('stage40',132,1140),('stage80',1140,1468),('keep00-80',0,0)):
            chosen=np.ones(len(m),dtype=bool)
            chosen[detail]=False
            if label=='keep00-80':chosen[detail[:132]]=True;chosen[detail[1140:]]=True
            else:chosen[detail[lo:hi]]=True
            dst=OUT/f'monastery/diagnostic-stages/age{age:02}/{label}.npz'
            dst.parent.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(dst,positions=points,faces=faces[chosen],material=m[chosen])
            images=[render(dst,age,label+'-'+view,VIEWS[view]) for view in ('iso','front')]
            rows.append({'age':age,'stage':label,'source':str(dst),'sha256':sha(dst),'images':images})
            print('DETAIL_STAGE',age,label,int(chosen.sum()))
    write(OUT/'monastery/diagnostic-stages/receipt.json',{'status':'stage_partition_visual_diagnostic','rows':rows})

if __name__=='__main__':main()
