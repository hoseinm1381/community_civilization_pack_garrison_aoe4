"""Narrow, reversible presentation hooks for the existing Vietnam mode."""


def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Lifecycle anchor changed or already patched: '+old.strip())
    return text.replace(old,new,1)


def patch_mode(text):
    if 'VietnamVoice_' in text:raise ValueError('Voice lifecycle already present')
    edits=[
        ('import("vietnam/presentation.scar")','import("vietnam/presentation.scar")\nimport("vietnam/voices_084.scar")'),
        ('    VietnamPresentation_Start()\n','    VietnamPresentation_Start()\n    VietnamVoice_Start(state.civilizations)\n'),
        ('    VietnamPresentation_Restore()\n','    VietnamPresentation_Restore()\n    VietnamVoice_Stop()\n    if state.selection ~= nil and state.selection.closed and not state.ending then\n        VietnamVoice_Start(state.civilizations)\n    end\n'),
        ('    VietnamInitialization_Cleanup()\n','    VietnamVoice_Stop()\n    VietnamInitialization_Cleanup()\n'),
    ]
    original=text
    for old,new in edits:text=replace_once(text,old,new)
    restored=text
    for old,new in reversed(edits):restored=replace_once(restored,new,old)
    if restored!=original:raise RuntimeError('Lifecycle edits are not exactly reversible')
    return text


def patch_precache(text,identities,guid):
    for category,variable in [('ebps','entities'),('sbps','squads')]:
        names=sorted(guid+':'+r['name'] for r in identities if r['category']==category)
        if len(names)!=len(set(names)):raise ValueError('Duplicate new precache identity')
        if any('"'+n+'"' in text for n in names):raise ValueError('New identity already precached')
        anchor='local '+variable+' = {\n'
        text=replace_once(text,anchor,anchor+''.join('    "'+n+'",\n' for n in names))
    return text
