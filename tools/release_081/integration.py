"""Carry the owning actor's marker identities through a fresh geometry cook."""
from common import *
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc
def preserve_buffalo_markers(old,new):
    before=rc.parse(old);after=rc.parse(new);a,b=before.roots[0].children,after.roots[0].children
    assert [(c.tag,c.name,c.version) for c in a]==[(c.tag,c.name,c.version) for c in b]
    assert all(x.payload==y.payload for x,y in zip(a,b) if x.tag not in (b'SKMS',b'MRKS'))
    prior=next(c for c in a if c.tag==b'MRKS');target=next(c for c in b if c.tag==b'MRKS')
    result=rc.rebuild(after,lambda c:prior.payload if c.offset==target.offset else None)
    merged=rc.parse(result).roots[0].children
    assert all(x.payload==y.payload for x,y in zip(a,merged) if x.tag!=b'SKMS')
    assert next(c.payload for c in merged if c.tag==b'SKMS')==next(c.payload for c in b if c.tag==b'SKMS')
    return result
