"""Portable source contracts. No editor, cache, sibling checkout or game required."""
import csv
import json
import re
import sys
import uuid
import xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GUID='a743d7d1d7534cf78817e29d8ded7366'


def verify(root=ROOT):
    projects=list(root.glob('*.aoe4mod'))
    assert len(projects)==1, 'Expected one editable project'
    project=E.parse(projects[0]).getroot()
    fields={x.tag.split('}')[-1]:x.text for x in project}
    assert fields['ID'].replace('-','')==GUID
    assert fields['DataGenericPath']=='assets'
    locale_meta=root/'assets'/fields['LocDBPath'].replace('\\','/')
    meta=E.parse(locale_meta).getroot()
    locales=[x.text for x in meta.iter() if x.tag.split('}')[-1]=='Name']
    assert locales==['en']
    locale_file=locale_meta.with_name(locale_meta.stem+'_en.csv')
    with locale_file.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.reader(f))
    assert rows[0]==['ID','Pipeline','PipelineStage','Notes','TranslationNotes','Tags','Text']
    assert all(len(r)==7 and r[0].isdigit() for r in rows[1:]), 'Malformed locale row'
    ids=[r[0] for r in rows[1:]];assert len(ids)==len(set(ids)), 'Duplicate locale ID'
    text={r[0]:r[-1] for r in rows[1:]}
    assert text['1001']=='Community Civilization Pack Normal'
    assert text['1105']=='Persia'
    assert not any('<locstring ' in value for value in text.values()), 'Attribute XML in locale text'
    manifests=list((root/'assets/attrib').glob('*.xml'))
    assert len(manifests)==1
    manifest=E.parse(manifests[0]).getroot()
    assert manifest.get('guid')==GUID
    assert (manifests[0].parent/manifest.get('locdb_path').replace('\\','/')).resolve()==locale_meta.resolve()
    burn=E.parse(root/'assets/_default.burnproj').getroot()
    assert [x.text for x in burn.iter() if x.tag.split('}')[-1]=='NiceName']==[GUID]
    base=root/'assets/attrib/instances'
    instances={p.relative_to(base).with_suffix('').as_posix().replace('/', '\\'):E.parse(p).getroot() for p in base.rglob('*.xml')}
    root_ids=[]
    for key,tree in instances.items():
        identity=tree.find("uniqueid[@name='pbgid']")
        assert identity is not None, key
        root_ids.append(identity.get('value'))
        for variant in tree.findall('variant'):
            item=variant.find("uniqueid[@name='pbgid']")
            if item is not None:assert item.get('value')==identity.get('value'),key
        for node in tree.iter():
            if node.get('mod'):
                assert node.get('mod').replace('-','')==GUID, ('Foreign mod dependency',key,node.attrib)
                if node.tag=='instance_reference':assert node.get('value') in instances,(key,node.attrib)
                if node.tag=='locstring':assert node.get('value') in text,(key,node.attrib)
            if node.tag=='list':
                item_ids=[x.get('List.ItemID') for x in node if x.get('List.ItemID')]
                assert len(item_ids)==len(set(item_ids)),('Duplicate list identity',key,node.attrib)
    assert len(root_ids)==len(set(root_ids)), 'Colliding root PBG IDs'
    assert not any(key.startswith('army\\') and key.endswith('normal_sultanate') for key in instances)
    assert not any('ps_probe_' in key for key in instances)
    ledger=json.loads((root/'docs/persia-import.json').read_text())
    assert len(ledger['instances'])==280
    for row in ledger['instances']:
        assert row['private'] in instances
        assert instances[row['private']].find("uniqueid[@name='pbgid']").get('value')==str(row['pbg_id'])
    for icon in ledger['icons']:
        assert (root/'assets/ui/icons/persia'/Path(icon.replace('\\','/')+'.png')).is_file(),icon
    # All project imports must exist; native engine imports remain engine-owned.
    for file in (root/'assets/scar').rglob('*.scar'):
        code=file.read_text(encoding='utf-8-sig')
        assert 'd8e25db92a5647d1892584dba19980f8' not in code
        for item in re.findall(r'import\("((?:vietnam|persia|korea|ccp)/[^\"]+)"\)',code):
            assert (root/'assets/scar'/item).is_file(),(file,item)
        assert '97b53d72bd354bfd82d171ada023431f' not in code
    korea_path=root/'docs/korea-import.json'
    if korea_path.exists():
        korea=json.loads(korea_path.read_text())
        assert len(korea['instances'])==378
        for row in korea['instances']:
            assert row['private'] in instances
            assert instances[row['private']].find("uniqueid[@name='pbgid']").get('value')==str(row['pbg_id'])
        try:
            from .korea_resource_contract import verify as verify_resources
        except ImportError:
            from korea_resource_contract import verify as verify_resources
        verify_resources(root)
        assert text['12000']=='Korea'
    expected_parts=[int.from_bytes(uuid.UUID(GUID).bytes_le[i:i+4],'little') for i in range(0,16,4)]
    for file in (root/'assets').rglob('*.rdo'):
        tree=E.parse(file).getroot()
        if file.name == 'VietnamMode.rdo':
            assert not any(x.get('Type') in ('EntityPrecacheItem','SquadPrecacheItem') for x in tree.iter('DataObject')), 'Unconditional RDO precache bypasses roster gates'
        for obj in tree.iter('DataObject'):
            if obj.get('Type')=='util::ReflectLocString':
                parts={n.get('Name'):n.get('Value') for n in obj.findall('DataProperty')}
                assert parts.get('m_locStringKey') in text,(file,parts)
                assert [int(parts['m_modPart'+str(i)]) for i in range(4)]==expected_parts
    return {'status':'passed','instances':len(instances),'persia_source_instances':280,
            'korea_source_instances':len(korea['instances']) if korea_path.exists() else 0,
            'persia_icons':len(ledger['icons']),'localization_rows':len(ids),'guid':GUID}


if __name__=='__main__':
    try:print(json.dumps(verify(),indent=2))
    except (AssertionError,ValueError,KeyError,OSError,E.ParseError) as error:
        print('Source verification failed:',error,file=sys.stderr);sys.exit(1)
