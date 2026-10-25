"""Encode only existing cattle idle/walk slots; keep every other clip exact."""
from native_codec import *
from predictive import replace
import argparse,math,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--output-label',default='encoded-v3')
args=parser.parse_args()
assert re.fullmatch(r'encoded-[A-Za-z0-9_-]+',args.output_label),'Invalid output label'
DEST=OUT/args.output_label;DEST.mkdir(parents=True,exist_ok=False)
source=json.loads((OUT/'source-v2/samples.json').read_text())
def pose_at(action,phase,track_names):
    rows=action['rows'];phase=phase%1.;position=phase*(len(rows)-1)
    left=int(position);right=min(left+1,len(rows)-1);alpha=position-left
    old={name.casefold():i for i,name in enumerate(action['names'])};result=[]
    for name in track_names:
        i=old[name.casefold()]*12;a=rows[left][i:i+12];b=rows[right][i:i+12]
        q1=a[4:8];q2=b[4:8]
        if sum(x*y for x,y in zip(q1,q2))<0:q2=[-x for x in q2]
        q=[x*(1-alpha)+y*alpha for x,y in zip(q1,q2)];norm=math.sqrt(sum(x*x for x in q));q=[x/norm for x in q]
        result += [*(x*(1-alpha)+y*alpha for x,y in zip(a[:3],b[:3])),0,*q,1,1,1,0]
    return result
def equal(a,b,path=''):
    if hasattr(a,'members'):
        assert type(a).__name__==type(b).__name__,path
        for member in a.members:equal(getattr(a,member.name),getattr(b,member.name),path+'.'+member.name)
    elif isinstance(a,(list,tuple)) or getattr(a,'ndim',0)>0:
        assert len(a)==len(b),path
        for i,(x,y) in enumerate(zip(a,b)):equal(x,y,path+f'[{i}]')
    else:assert a==b,(path,a,b)
receipts={}
baseline=read()
for label,indices in [('idle',[10]),('idle-walk',[10,3])]:
    model=read();expected={};clips=[]
    for index in indices:
        clip=model.root.animations[index];a=clip.animationBinding.animation
        names=[b.name for b in clip.skeleton.bones]
        binding=list(clip.animationBinding.transformTrackToBoneIndices)
        assert binding==list(range(45)),binding
        track_names=[names[i] for i in binding]
        source_action=source['buffalo_082_idle' if index==10 else 'buffalo_082_walk']
        # Preserve the original native durations and frame counts exactly.
        frames=a.numFrames;cycles=2 if index==10 else 4
        rows=[pose_at(source_action,i/(frames-1)*cycles,track_names) for i in range(frames)]
        proof=replace(a,rows)
        expected[index]=rows
        proof.update(index=index,name=clip.name.replace('\u00a5','\\'),duration=a.duration,cycles=cycles)
        clips.append(proof)
    path=DEST/(label+'.rhka');write(model,path);after=read(path)
    for index,(a,b) in enumerate(zip(baseline.root.animations,after.root.animations)):
        equal(a.skeleton,b.skeleton,'skeleton')
        if index not in indices:equal(a,b,'untouched-clip')
        else:
            equal(a.animationBinding.animation.extractedMotion,b.animationBinding.animation.extractedMotion,'root-motion')
            equal(a.animationBinding.animation.annotationTracks,b.animationBinding.animation.annotationTracks,'annotations')
            assert a.animationBinding.animation.duration==b.animationBinding.animation.duration
            assert a.animationBinding.animation.numFrames==b.animationBinding.animation.numFrames
    for proof in clips:
        index=proof['index'];target=DEST/(label+'-'+str(index)+'-sampled.json')
        p=subprocess.run([CFG['garrison_core'],'-m','src.core.animation_clip','--source',str(path),'--clip-index',str(index),'--output',str(target)],capture_output=True,text=True)
        (DEST/(label+'-'+str(index)+'-sample.log')).write_text(p.stdout+p.stderr)
        assert p.returncode==0,p.stderr
        parsed=json.loads(target.read_text());maximum=0;max_angle=0;max_q_component=0;max_norm_error=0
        assert len(parsed['samples'])==len(expected[index])
        for desired,frame in zip(expected[index],parsed['samples']):
            for bi,bone in enumerate(frame['bones']):
                a=desired[bi*12:bi*12+12]
                maximum=max(maximum,max(abs(x-y) for x,y in zip(a[:3],bone['translation_xyz'])))
                q=bone['quaternion_xyzw'];norm=math.sqrt(sum(x*x for x in q));max_norm_error=max(max_norm_error,abs(norm-1))
                sign=1 if sum(x*y for x,y in zip(a[4:8],q))>=0 else -1
                max_q_component=max(max_q_component,max(abs(x-sign*y) for x,y in zip(a[4:8],q)))
                dot=abs(sum(x*y for x,y in zip(a[4:8],q)))/norm
                max_angle=max(max_angle,2*math.acos(min(1,max(0,dot))))
        assert maximum<.001,(index,maximum)
        assert max_angle<.001,(index,max_angle)
        assert max_q_component<.001 and max_norm_error<.001,(index,max_q_component,max_norm_error)
        proof.update(maximum_translation_error=maximum,maximum_rotation_error_radians=max_angle,maximum_quaternion_component_error=max_q_component,maximum_quaternion_norm_error=max_norm_error,
                     independent_sample_readback=True)
    receipts[label]={'path':str(path),'sha256':sha(path),'clips':clips,'untouched_clips_exact':11-len(indices),
                     'skeletons_exact':True,'root_motion_exact':True,'annotations_exact':True,'gameplay_tested':False}
    print('ENCODED_VERIFIED',label,[(p['name'],p['maximum_translation_error'],p['maximum_rotation_error_radians']) for p in clips],flush=True)
(DEST/'receipt.json').write_text(json.dumps(receipts,indent=2))
