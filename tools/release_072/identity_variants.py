"""Explicitly request the retained private donors' original native variants.

These existing source identities were skeletal; a plain source build emits only
default. Preserve baseline branch coverage without importing any old gameplay.
"""
from port import *
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd
def main():
    r=json.loads((OUT/'source-port.json').read_text());rows=[]
    base=Path(CFG['external_root'])/'staging/r72/baseline-native'
    official=json.loads((OUT/'official-extensions.json').read_text())['records']
    for name in r['retained_art_definitions']:
        if '/instances/attachments/'in name:continue
        p=STAGE/name;t=E.parse(p).getroot();parent=t.find("instance_reference[@name='parent_pbg']");pid=t.find("uniqueid[@name='pbgid']")
        raw=base/('attrib/'+name.split('assets/attrib/instances/',1)[1].removesuffix('.xml')+'.rgd')
        assert raw.exists()
        branches=[n.key for n in rgd.read(raw.read_bytes()).nodes if n.kind in ('List','List2')and n.key!='default']
        for branch in branches:
            assert branch in official[parent.get('value')],(name,branch,'official parent variant absent')
            if t.find("variant[@name='"+branch+"']")is not None:continue
            v=E.SubElement(t,'variant',{'name':branch});v.append(copy.deepcopy(pid));v.append(copy.deepcopy(parent));rows.append({'source':name,'variant':branch,'official_parent':parent.get('value'),'pbgid':pid.get('value')})
        E.indent(t,space='\t');p.write_bytes(E.tostring(t,encoding='utf-8',xml_declaration=True)+b'\n')
    r['private_identity_variants']=rows;dump(OUT/'source-port.json',r);print('Private donor variants',len(rows))
if __name__=='__main__':main()
