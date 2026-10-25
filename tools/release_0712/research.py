"""Freeze effective private generator ranges and current official inheritance."""
from common import *
import xml.etree.ElementTree as E

def main():
    guard();sys.path.insert(0,str(ROOT/'tools/release_072/vendor'))
    import extension_audit as a
    a.ROOT=ROOT;a.GUID=CFG['project_guid'].replace('-','')
    official=a.refresh(OUT/'official-extensions.json');local=a.load_local(ROOT);resolver=a.Resolver(local,official)
    errors=resolver.audit();assert not errors,errors
    sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import rgd
    rows=[]
    for key,record in sorted(local.items()):
        if not key.startswith('ebps\\vietnam\\'):continue
        bp=BASE/'readback'/('attrib/'+key.replace('\\','/')+'.rgd')
        doc=rgd.read(bp.read_bytes());flat={p:n for p,n in rgd.flatten(doc.nodes)}
        for variant in record:
            item=next((n for n in resolver.effective(key,variant) if n['value']=='ebpextensions\\district_generator_ext'),None)
            if item is None:continue
            path=variant+'/district_generator_ext/range_metres'
            assert path in flat,(key,variant)
            value=flat[path].value
            if value<=0:continue
            rows.append({'key':key,'variant':variant,'native_path':path,'before':value,'after':value+2,'extension':item,
                'member':'attrib/'+key.replace('\\','/')+'.rgd','baseline_sha256':sha(bp)})
    assert rows
    write(OUT/'range-inventory.json',{'rows':rows,'official_blueprints':len(official),'local_blueprints':len(local),'inheritance_errors':errors,
        'authorization':'User explicitly authorized +2m actual influence as well as display if no separate visual-only offset could be qualified.'})
    from read_official_members import members
    donor={}
    wanted={'weapon_javelin_2.xml','weapon_javelin_3.xml','weapon_javelin_4.xml','districts.xml'}
    for name,data in members('ReferenceAttributes.sga',lambda n:n in wanted):
        p=OUT/'official'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);donor[name]=sha(p)
    assert wanted<=donor.keys()
    write(OUT/'official/donors.json',donor)
    print('RANGES',len(rows),'variant scopes',len({r['key'] for r in rows}),'blueprints')

if __name__=='__main__':main()
