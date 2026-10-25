"""Fail closed if 0710 changes source beyond the approved visual/UI surface."""
import zipfile
import xml.etree.ElementTree as ET
from common import *

FORTIFIED={f'assets/attrib/instances/ebps/vietnam/buildings/hideouts/{n}.xml' for n in
    ('vn_building_defense_outpost_chi_fortified','vn_building_defense_outpost_2_chi_fortified')}
MODE='assets/scar/winconditions/VietnamMode.scar'
PADDY='assets/scar/vietnam/paddy_wood.scar'
ATTACH='assets/attrib/instances/attachments/attachment_lists/vietnam/release_0710/vn_0710_hideout_fortified_visual.xml'
def canonical(node):
    return (node.tag,tuple(sorted(node.attrib.items())),(node.text or '').strip(),tuple(canonical(c) for c in node))

def main():
    guard();baseline=OUT/'baseline'
    original={Path(p).relative_to(ROOT).as_posix():h for p,h in read(baseline/'source-hashes.json').items()}
    current={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    for name in ('workspace.json',CFG['project_file']):current[name]=sha(ROOT/name)
    deleted=set(original)-set(current);assert not deleted,deleted
    changed={k for k in original if current[k]!=original[k]}
    assert changed <= FORTIFIED|{MODE,PADDY},changed
    assert FORTIFIED|{MODE,PADDY} <= changed,'Required source integration absent'
    added=set(current)-set(original)
    allowed_add={ATTACH,'assets/scar/vietnam/presentation.scar',
        'assets/ui/hud/controls/playerscores.xaml','assets/ui/hud/pages/cardinalhudpage.xaml',
        'assets/ui/resources/hudresources.xaml',
        'assets/ui/images/vietnam_0710/buffalo.png','assets/ui/images/vietnam_0710/dai_viet_dragon.png'}
    assert added<=allowed_add,added-allowed_add
    assert ATTACH in added and 'assets/scar/vietnam/presentation.scar' in added
    with zipfile.ZipFile(baseline/'source.zip') as z:
        for name in FORTIFIED:
            old=ET.fromstring(z.read(name));new=ET.parse(ROOT/name).getroot()
            for scope in [new,*new.findall('variant')]:
                exts=scope.find("list[@name='extensions']")
                for ext in list(exts):
                    if ext.get('value') in ('ebpextensions\\entity_blueprint_ext','ebpextensions\\tier_ext'):
                        exts.remove(ext)
            assert canonical(old)==canonical(new),('Nonvisual fortified source changed',name)
        old=z.read(PADDY).decode('utf-8-sig').replace('\r\n','\n')
        new=(ROOT/PADDY).read_text(encoding='utf-8-sig')
        # Permit only template reference and its adjacent explanatory comment.
        def executable(text):return '\n'.join(l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith('--'))
        assert executable(old.replace('TagArrowDataTemplate','VietnamBuffaloSupervisionTemplate'))==executable(new),'Paddy gameplay changed'
        old=z.read(MODE).decode('utf-8-sig').replace('\r\n','\n')
        new=(ROOT/MODE).read_text(encoding='utf-8-sig')
        hooks={'import("vietnam/presentation.scar")','VietnamPresentation_Update()',
               'VietnamPresentation_Start()','VietnamPresentation_Restore()','VietnamPresentation_Cleanup()'}
        new='\n'.join(l for l in new.splitlines() if l.strip() not in hooks)
        assert executable(old)==executable(new),'Mode gameplay changed beyond presentation hooks'
    # Both gameplay cap fields and influence generators are unchanged except
    # added visual extensions already stripped above.
    write(OUT/'validation/source-policy.json',{'passed':True,'changed':sorted(changed),'added':sorted(added),
        'current_hashes':current,'paddy_gameplay_exact':True,'mode_gameplay_exact':True,
        'fortified_nonvisual_source_exact':True,'influence_generation_unchanged':True})
    print('SOURCE_POLICY_PASSED',len(changed),len(added))

if __name__=='__main__':main()
