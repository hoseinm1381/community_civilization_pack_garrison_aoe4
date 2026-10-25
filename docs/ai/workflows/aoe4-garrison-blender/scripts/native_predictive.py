"""Independent predictive packet encoder, qualified by native sample readback."""
import math,struct
def signed14(value):return (int(value)+8192)%16384-8192
def window(values):
    assert len(values)==8
    packed=cursor=0
    for first in range(0,8,2):
        pair=values[first:first+2]
        width=next(w for w in range(15) if all((v==0 if w==0 else -(1<<(w-1))<=v<(1<<(w-1))) for v in pair))
        packed|=width<<cursor;cursor+=4
        for value in pair:
            packed|=(value&((1<<width)-1))<<cursor;cursor+=width
    assert cursor<=128
    return packed.to_bytes(16,'big')
def packet(lanes):
    assert 1<=len(lanes)<=16 and all(len(x)==16 for x in lanes)
    encoded=bytearray([255]*16)
    for lane in list(lanes)+[[0]*16]*(16-len(lanes)):
        residual=[signed14(q-(3*lane[i-1] if i>0 else 0)+(3*lane[i-2] if i>1 else 0)-(lane[i-3] if i>2 else 0)) for i,q in enumerate(lane)]
        encoded.extend(window(residual[:8]));encoded.extend(window(residual[8:]))
    assert len(encoded)==528
    return bytes(encoded)
def replace(animation,rows):
    count=len(rows);width=12*animation.numBones
    assert count>=2 and all(len(r)==width and all(math.isfinite(x) for x in r) for r in rows)
    # Use the native W-drop table and signed L1 quaternion representation.
    # It reconstructs unit quaternions rather than quantizing four independent
    # components into slightly non-unit results.
    rows=[list(r) for r in rows]
    omitted={i*12+7 for i in range(animation.numBones)}
    for row in rows:
        for bone in range(animation.numBones):
            first=bone*12+4;q=row[first:first+4]
            if q[3]<0:q=[-x for x in q]
            norm=sum(abs(x) for x in q);assert norm>0
            row[first:first+4]=[x/norm for x in q]
    columns=list(zip(*rows))
    dynamic=[i for i,c in enumerate(columns) if i not in omitted and max(c)-min(c)>1e-7]
    constants=[i for i in range(width) if i not in dynamic and i not in omitted]
    assert dynamic
    minima=[min(columns[i]) for i in dynamic]
    scales=[(max(columns[i])-lo)/4096 for i,lo in zip(dynamic,minima)]
    quantized=[[max(0,min(4096,round((v-lo)/scale))) for v in columns[i]] for i,lo,scale in zip(dynamic,minima,scales)]
    compressed=bytearray();ends=[]
    for first in range(0,count,15):
        for start in range(0,len(dynamic),16):
            lanes=[[c[min(i,count-1)] for i in range(first,first+16)] for c in quantized[start:start+16]]
            compressed.extend(packet(lanes))
        ends.append(len(compressed))
    tables=[[part for end in ends for part in (end&65535,end>>16)],[],
            [((1<<min(16,animation.numBones-i))-1) for i in range(0,animation.numBones,16)],
            [0]*math.ceil(len(dynamic)/16),dynamic,[],constants,[],list(range(animation.numBones))]
    integers=[];offsets=[]
    for table in tables:offsets.append(len(integers));integers.extend(table)
    integers += [0]*8
    animation.numFrames=count;animation.compressedData=list(compressed)
    animation.intData=integers;animation.intArrayOffsets=tuple(offsets)
    animation.floatData=[columns[i][0] for i in constants]+scales+minima+[0.]*4
    animation.floatArrayOffsets=(0,len(constants),len(constants)+len(dynamic))
    animation.firstFloatBlockScaleAndOffsetIndex=(len(dynamic)//16)*16
    return {'frames':count,'dynamic_components':len(dynamic),'blocks':len(ends),'compressed_bytes':len(compressed),'maximum_quantization_step':max(scales)}
