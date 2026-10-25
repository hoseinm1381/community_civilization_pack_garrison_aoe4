"""Typed four-part native model states, with construction and repair ownership retained."""
from __future__ import annotations
from native_support import rc, lifecycle

FOUNDATION='garrison_part_0000'
HEALTHY='garrison_part_0001'
RUINS='garrison_part_0002'
DAMAGED='garrison_part_0003'

def table(raw):
    _,pairs=lifecycle._pairs(raw)
    return [(lifecycle._selector(s),lifecycle._conditions(c)) for s,c in pairs]

def truth(raw,state):
    return sorted({p for (_,parts),conditions in table(raw) for p in parts
                   if any(c==(2,0,1,'life_cycle_state',state) for c in conditions)})

def install(raw):
    document,pairs=lifecycle._pairs(raw)
    parsed=table(raw)
    seen={p for (_,parts),_ in parsed for p in parts}
    assert {FOUNDATION,HEALTHY,RUINS,DAMAGED}<=seen,seen
    healthy=sorted(seen-{FOUNDATION,RUINS,DAMAGED})
    assert all(p.startswith('garrison_part_') for p in healthy)
    edits={};ruin_index=None;damage_index=None
    for index,((name,parts),conditions) in enumerate(parsed):
        selector,predicate=pairs[index]
        if name=='sel_healthy' and not parts:
            assert ruin_index is None;ruin_index=index
            edits[selector.offset]=lifecycle._pack_selector('sel_ruins',[RUINS])
            edits[predicate.offset]=lifecycle._pack_conditions(['ruins'])
        elif name=='sel_construct_80':
            assert set(parts)<={DAMAGED};damage_index=index
            edits[selector.offset]=lifecycle._pack_selector('sel_heavy_damage',[DAMAGED])
            edits[predicate.offset]=lifecycle._pack_conditions(['damage_3','damage_4','damage_5'])
        else:
            keep=[p for p in parts if p not in (RUINS,DAMAGED)]
            if keep!=parts:edits[selector.offset]=lifecycle._pack_selector(name,keep)
            if set(keep)&set(healthy):
                assert set(keep)<=set(healthy)
                states=[c[-1] for c in conditions if c[-1] not in ('damage_3','damage_4','damage_5')]
                assert all(c[:4]==(2,0,1,'life_cycle_state') for c in conditions)
                edits[predicate.offset]=lifecycle._pack_conditions(states)
    assert ruin_index is not None and damage_index is not None
    result=rc.rebuild(document,lambda c:edits.get(c.offset))
    expected={'healthy':[FOUNDATION]+healthy, 'damage_1':[FOUNDATION]+healthy,
              'damage_2':[FOUNDATION]+healthy, 'damage_3':[FOUNDATION,DAMAGED],
              'damage_4':[FOUNDATION,DAMAGED], 'damage_5':[FOUNDATION,DAMAGED],
              'ruins':[RUINS], 'preview':[FOUNDATION]+healthy, 'targeting':[FOUNDATION]+healthy}
    for stage in range(0,100,5):
        expected[f'construct_{stage:02}']=[FOUNDATION]+(healthy if stage>=20 else [])
    for state,parts in expected.items():assert truth(result,state)==sorted(parts),(state,truth(result,state),parts)
    return result,{'status':'passed_static_selector_table','truth_table':expected,
                   'native_collapse_and_repair_owner':'unchanged exact stock RGO',
                   'repair_transition':'native life_cycle_state returns to healthy; requires fresh match',
                   'native_runtime':'not tested'}
