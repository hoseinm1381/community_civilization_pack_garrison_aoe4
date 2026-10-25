"""Explicit 0.8.3 media-only owning-resource policy."""
FAMILIES={f'{kind}{age}' for kind in ['skirmisher','javelin','projectile'] for age in [2,3,4]}
PREFIX='art/scenario/garrison/cc076/'
def allowed(path):
    if not path.startswith(PREFIX):return False
    tail=path[len(PREFIX):];parts=tail.split('/')
    return len(parts)==2 and parts[0] in FAMILIES and (parts[1] in {'model.rgm','model.rrgeom','model.rrmaterial'} or parts[1].endswith('.rrtex'))
def validate_changes(changed):
    forbidden=[p for p in changed if not allowed(p)]
    if forbidden:raise ValueError('Outside 083 media allowlist: '+str(forbidden))
    for family in FAMILIES:
        if PREFIX+family+'/model.rrgeom' not in changed:raise ValueError('Missing redesigned geometry '+family)
