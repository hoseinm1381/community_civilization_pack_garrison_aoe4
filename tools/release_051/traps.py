"""Port normal completion conversion while retaining Garrison trap visuals."""
from __future__ import annotations
import copy, importlib.util, re, sys, xml.etree.ElementTree as ET
from common import *
NORMAL=Path(CONFIG['source_root']); TARGET=OUT/'traps'
NAMES=('vn_building_bambo_outpost_chi','vn_building_defense_outpost_bambo_chi')
def reserve():
    guarded();pbg=set();reflect=set()
    for root in (ROOT/'assets',NORMAL/'assets'):
        for p in (root/'attrib/instances').rglob('*.xml'):
            pbg.update(int(n.get('value')) for n in ET.parse(p).getroot().iter('uniqueid') if n.get('name')=='pbgid')
        for p in root.rglob('*.rdo'):
            reflect.update(n.get('Id') for n in ET.parse(p).getroot().iter('DataObject') if n.get('Id'))
    write(TARGET/'reserved-pbg.json',sorted(pbg));write(TARGET/'reserved-reflect.json',sorted(reflect,key=int))
    print('RESERVED051',len(pbg),len(reflect))
def fixture():
    guarded();source=NORMAL/'tests/test_trap_completion_switch.py';target=ROOT/'tests/test_trap_completion_switch_051.py'
    text=source.read_text();text=text.replace("        super().setUp()", "        super().setUp()\n        self.runlua('function Entity_ConvertBlueprint(e,bp) e.bp=bp;e.conversions=(e.conversions or 0)+1 end')")
    if target.exists():assert target.read_text()==text
    else:target.write_text(text,encoding='utf-8')
    write(TARGET/'test-provenance.json',{'source':str(source),'source_sha256':sha(source),'destination':str(target),'namespace':'existing Garrison PREFIX fixture','fixture_addition':'Entity_ConvertBlueprint stub in this class only'})
def apply():
    guarded();ids=read(TARGET/'identities.json');assert ids['project_guid']==GUID
    assert len(set(ids['pbg_ids']))==2 and not(set(ids['pbg_ids'])&set(read(TARGET/'reserved-pbg.json')))
    assert len(set(ids['reflect_ids']))==4 and not(set(ids['reflect_ids'])&set(read(TARGET/'reserved-reflect.json')))
    assets=ROOT/'assets';base=OUT/'baseline/source/assets'; guid=GUID.replace('-','')
    rows=[]
    trap=assets/'scar/vietnam/traps.scar'; donor=NORMAL/'assets/scar/vietnam/traps.scar'
    assert trap.read_bytes() in ((base/'scar/vietnam/traps.scar').read_bytes(),donor.read_bytes())
    trap.write_bytes(donor.read_bytes());rows.append(trap)
    for name,pid in zip(NAMES,ids['pbg_ids']):
        parent=assets/f'attrib/instances/ebps/vietnam/{name}.xml'
        assert sha(parent)==sha(base/parent.relative_to(assets)),'Blocking parent modified'
        donor=NORMAL/f'assets/attrib/instances/ebps/vietnam/{name}_passable.xml'
        text=donor.read_text(encoding='utf-8-sig').replace(CONFIG['source_project_guid'].replace('-',''),guid)
        text,count=re.subn(r'(<uniqueid name="pbgid" value=")\d+("\s*/>)',lambda m:m[1]+str(pid)+m[2],text);assert count==2
        child=parent.with_name(name+'_passable.xml')
        if child.exists():assert child.read_text()==text
        else:child.write_text(text,encoding='utf-8')
        doc=ET.parse(child).getroot();assert all(n.get('mod')==guid for n in doc.iter('instance_reference'))
        rows.append(child)
    rdo=assets/'scar/winconditions/VietnamMode.rdo'; original=(base/rdo.relative_to(assets)).read_bytes()
    doc=ET.fromstring(original)
    prop=next(n for n in doc.iter('DataProperty') if n.get('Name')=='m_precacheItems')
    owner=next(n for n in doc.iter('DataObject') if prop in list(n)).get('Id')
    samples=prop.findall('DataValue');template=next(n for n in prop.findall('DataObject') if n.get('Type')=='EntityPrecacheItem')
    assert samples and template is not None
    sample=next(n for n in template.iter('DataObject') if n is not template)
    for i,name in enumerate(NAMES):
        first,second=ids['reflect_ids'][2*i:2*i+2]
        dv=copy.deepcopy(samples[0]);dv.text=first
        node=copy.deepcopy(template)
        old={template.get('Id'):first,sample.get('Id'):second}
        for x in node.iter():
            for attr in ('Id','OwnerId'):
                if x.get(attr) in old:x.set(attr,old[x.get(attr)])
            if x.tag=='DataValue' and x.text in old:x.text=old[x.text]
            if x.tag=='DataProperty' and x.get('Name')=='m_fileName':x.set('Value',guid+':'+name+'_passable')
        assert node.get('OwnerId')==owner
        insertion=ET.tostring(dv,encoding='unicode')+ET.tostring(node,encoding='unicode')
        # Preserve all existing source bytes and object identities; insert only
        # the two new precache entries before this property's closing tag.
        location=original.index(b'<DataProperty Name="m_precacheItems"')
        indent=original[original.rfind(b'\n',0,location)+1:location]
        marker=b'\n'+indent+b'</DataProperty>'
        end=original.index(marker,location)
        original=original[:end]+insertion.encode('utf-8')+b'\n'+original[end:]
    if rdo.read_bytes()!=(base/rdo.relative_to(assets)).read_bytes():assert rdo.read_bytes()==original
    else:rdo.write_bytes(original)
    current=ET.parse(rdo).getroot();old=ET.parse(base/rdo.relative_to(assets)).getroot()
    oldids={n.get('Id'):ET.tostring(n) for n in old.iter('DataObject')}
    newids={n.get('Id'):n for n in current.iter('DataObject')}
    assert set(newids)-set(oldids)==set(ids['reflect_ids'])
    # Remove the additions and demand XML-tree identity, including old owners.
    clone=copy.deepcopy(current);cp=next(n for n in clone.iter('DataProperty') if n.get('Name')=='m_precacheItems')
    for n in list(cp):
        if n.get('Id') in ids['reflect_ids'] or (n.tag=='DataValue' and n.text in ids['reflect_ids']):cp.remove(n)
    def shape(n):return (n.tag,sorted(n.attrib.items()),(n.text or '').strip(),[shape(x) for x in n])
    assert shape(clone)==shape(old),'Existing RDO records changed'
    rows.append(rdo)
    spec=importlib.util.spec_from_file_location('precache051',ROOT/'tools/generate_prematch_precache.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.main();rows.append(assets/'scar/vietnam/prematch_precache.scar')
    write(TARGET/'source-changes.json',{'status':'passed','normal_writes':False,'changed':{p.relative_to(assets).as_posix():sha(p) for p in rows},'blocking_parent_hashes':{name:sha(assets/f'attrib/instances/ebps/vietnam/{name}.xml') for name in NAMES},'native_match':'pending'})
    print('TRAPS051_APPLIED',len(rows),'source files')
if __name__=='__main__':{'reserve':reserve,'fixture':fixture,'apply':apply}[sys.argv[1]]()
