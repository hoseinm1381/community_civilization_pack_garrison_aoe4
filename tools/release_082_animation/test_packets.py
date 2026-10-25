"""Native decoder checks for non-smooth and smooth independently encoded poses."""
from native_codec import *
from predictive import replace
import math,random,subprocess
DEST=OUT/'encoder-qualification-v1';DEST.mkdir(parents=True,exist_ok=False)
sample=json.loads((ROOT/'output/release_081/animation/cattle_idle_01.json').read_text())['samples'][0]
rest=[]
for bone in sample['bones']:rest += [*bone['translation_xyz'],0,*bone['quaternion_xyzw'],*bone['scale_xyz'],0]
rng=random.Random(24082)
results=[]
for label,values in [('random',[rng.uniform(-.2,.2) for _ in range(47)]),('smooth',[.2*math.sin(i*.2) for i in range(65)])]:
    model=read();a=model.root.animations[10].animationBinding.animation
    rows=[list(rest) for _ in values]
    for row,value in zip(rows,values):row[12]=value
    proof=replace(a,rows);a.duration=(len(rows)-1)/30
    path=DEST/(label+'.rhka');write(model,path)
    target=DEST/(label+'.json')
    p=subprocess.run([CFG['garrison_core'],'-m','src.core.animation_clip','--source',str(path),'--clip-index','10','--output',str(target)],capture_output=True,text=True)
    assert p.returncode==0,p.stderr
    parsed=json.loads(target.read_text())
    error=max(abs(f['bones'][1]['translation_xyz'][0]-v) for f,v in zip(parsed['samples'],values))
    assert error<.0001,error
    proof.update(label=label,maximum_error=error,passed=True);results.append(proof)
    print('NATIVE_ENCODER_CHECK',label,error,flush=True)
(DEST/'result.json').write_text(json.dumps(results,indent=2))
