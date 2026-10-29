"""One-time, source-only Korea migration. Ordinary checks/builds need no donor.

The immutable identity receipt and source hashes make this an intentional migration
recipe, not a command to run during ordinary development.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import shutil
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUID = 'b7fcea91257b408fb9e8ae4d8bc402e1'
SOURCE_GUID = '97b53d72bd354bfd82d171ada023431f'
WORK = ROOT / 'work/korea_port'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def key(path, base):
    return path.relative_to(base).with_suffix('').as_posix().replace('/', '\\')


def source_instances(source):
    base = source / 'assets/attrib/instances'
    return base, sorted(p for p in base.rglob('*.xml') if p.relative_to(base).parts[0] not in ('army', 'resource_type_info'))


def prepare(source):
    import official_archive
    reserved = set()
    for base in [ROOT/'assets/attrib/instances', source/'assets/attrib/instances']:
        for p in base.rglob('*.xml'):
            for e in E.parse(p).getroot().iter():
                for name in ('List.ItemID', 'List.ParentItemID'):
                    if e.get(name): reserved.add(int(e.get(name)))
                if e.tag == 'uniqueid' and e.get('value'): reserved.add(int(e.get('value')))
    official = {}
    for name, data in official_archive.members(official_archive.archive_path(), lambda n: n.startswith('instances\\') and n.endswith('.xml')):
        r = E.fromstring(data)
        pbg = r.find("uniqueid[@name='pbgid']")
        if pbg is not None: reserved.add(int(pbg.get('value')))
        official[name[len('instances\\'):-4]] = data.decode('utf-8-sig')
    (WORK/'reserved-ids.json').write_text(json.dumps(sorted(reserved)), encoding='utf-8')
    (WORK/'official.json').write_text(json.dumps(official), encoding='utf-8')
    print('Reserved', len(reserved), 'identities; inspected', len(official), 'current official instances')


def repair_extensions(roots, official=None):
    import check_extension_inheritance as audit
    if official is None:
        official = json.loads((ROOT/'.local/official-extensions.json').read_text())['records']
    done, repairs = set(), []

    def visit(k, trail=()):
        if k in done: return
        if k in trail: raise ValueError('Private inheritance cycle '+k)
        r = roots[k]
        for p in r.iter('instance_reference'):
            if p.get('name') == 'parent_pbg' and p.get('mod') == GUID and p.get('value') in roots:
                visit(p.get('value'), trail+(k,))
        for scope in [r]+r.findall('variant'):
            ext = scope.find("list[@name='extensions']")
            if ext is None or ext.get('overrideParent') == 'True': continue
            local = {n:audit.summarize(E.tostring(t)) for n,t in roots.items() if n.startswith(('ebps\\','sbps\\'))}
            inherited = audit.Resolver(local, official).inherited(k, scope.get('name','default'))
            for e in ext:
                matches = [x for x in inherited if x.get('value') == e.get('value')]
                assert len(matches) <= 1, (k, e.get('value'), matches)
                before = dict(e.attrib)
                if matches:
                    identity = matches[0]['List.ItemID']
                    e.set('List.ItemID', identity); e.set('List.ParentItemID', identity)
                    e.attrib.pop('List.ListAction', None)
                else:
                    e.attrib.pop('List.ParentItemID', None); e.set('List.ListAction','Append')
                if before != e.attrib:
                    repairs.append({'private':k,'variant':scope.get('name','default'),'extension':e.get('value'),
                                    'before':before,'after':dict(e.attrib),
                                    'gameplay_subtree_sha256':sha(b''.join(E.tostring(x) for x in e))})
        done.add(k)
    for k in roots:
        if k.startswith(('ebps\\','sbps\\')): visit(k)
    return repairs


def lua(value):
    if isinstance(value, dict):
        return '{'+','.join('['+lua(str(k))+']='+lua(v) for k,v in value.items())+'}'
    if isinstance(value, list): return '{'+','.join(lua(v) for v in value)+'}'
    if isinstance(value, bool): return 'true' if value else 'false'
    if isinstance(value, (int,float)): return str(value)
    return json.dumps(value, ensure_ascii=True)


def research_map(source):
    result = {}
    folder = source/'assets/scar/winconditions/senobi'
    for p in folder.glob('*.scar'):
        if p.name in ('senbi_seowon.scar','out_dated.scar'): continue
        code = re.sub(r'--[^\n]*', '', p.read_text(encoding='utf-8-sig'))
        # Each active donor branch queues one technology. Duplicate branches
        # must agree; the complete map is checked against donor ability IDs.
        for m in re.finditer(r'(?:if|elseif)\s+context_numberi\s*==\s*(\d+)\s+then(.*?)(?=\belseif\b|\n\s*end\b)', code, re.S):
            targets = re.findall(r'BP_GetUpgradeBlueprint\("([^"\n]+)"\)',m[2])
            if not targets: continue
            assert len(set(targets)) == 1, (p, m[1], targets)
            entry = {'upgrade':targets[0],'foreign':p.name=='foreign_tech.scar'}
            assert m[1] not in result or result[m[1]] == entry
            result[m[1]] = entry
    return result


def run(source):
    base, files = source_instances(source)
    assert len(files) == 378
    locale_path = next((ROOT/'assets/locdb').glob('*_en.csv'))
    old_locale = locale_path.read_bytes()
    occupied = {r['ID'] for r in csv.DictReader(io.StringIO(old_locale.decode('utf-8-sig')))}
    assert '12000' not in occupied, 'Korea already imported; edit maintained assets instead of rerunning the migration'
    identity = json.loads((WORK/'identities.json').read_text(encoding='utf-8-sig'))
    paths = {key(p,base):p.relative_to(base).parts[0]+'\\korea\\kr_'+p.stem for p in files}
    aliases = {(k.split('\\')[0],k.split('\\')[-1]):k for k in paths}
    assert len(aliases) == len(files)
    source_rows = list(csv.DictReader(next((source/'assets/locdb').glob('*_en.csv')).open(encoding='utf-8-sig',newline='')))
    locmap = {r['ID']:str(12000+int(r['ID'])) for r in source_rows}
    assert not occupied.intersection(locmap.values())
    iconbase = source/'assets/ui/icons'
    icons = {p.relative_to(iconbase).with_suffix('').as_posix().replace('/','\\').lower():p for p in iconbase.rglob('*.png')}
    roots, records, translations, source_ids = {}, [], [], {}
    for p, new_id in zip(files, identity['ids']):
        oldkey = key(p,base); r = E.parse(p).getroot()
        old_id = r.find("uniqueid[@name='pbgid']").get('value'); source_ids[old_id] = new_id
        for e in r.iter():
            if e.tag == 'uniqueid' and e.get('name') == 'pbgid': e.set('value',str(new_id))
            elif e.tag == 'locstring' and e.get('mod','').replace('-','') == SOURCE_GUID:
                e.set('mod',GUID); e.set('value',locmap[e.get('value')])
            elif e.tag == 'instance_reference' and e.get('value'):
                v = e.get('value'); mod = e.get('mod','').replace('-','')
                if v == 'abilities\\always_on_abilities\\shaolin_monk_passive_heal_self':
                    v = 'abilities\\always_on_abilities\\chinese_ha_01\\shaolin_monk_passive_heal_self'
                    e.set('value', v)
                target = v if v in paths else aliases.get((v.split('\\')[0],v.split('\\')[-1]))
                if target == oldkey and e.get('name') == 'parent_pbg' and mod != SOURCE_GUID: target = None
                if target in paths and mod in ('',SOURCE_GUID):
                    e.set('value',paths[target]); e.set('mod',GUID)
                    translations.append({'owner':paths[oldkey],'source':v,'private':paths[target]})
                elif mod == SOURCE_GUID: raise ValueError('Unresolved source reference '+oldkey+' '+v)
            elif e.tag == 'file' and e.get('value','').lower() in icons:
                e.set('value','korea\\'+e.get('value').lower())
        roots[paths[oldkey]] = r
        records.append({'source':oldkey,'private':paths[oldkey],'source_pbg_id':int(old_id),
                        'pbg_id':new_id,'source_sha256':sha(p.read_bytes())})
    repairs = repair_extensions(roots)
    for k,r in roots.items():
        target = ROOT/'assets/attrib/instances'/Path(k.replace('\\','/')+'.xml')
        target.parent.mkdir(parents=True,exist_ok=True); E.indent(r,space='\t')
        E.ElementTree(r).write(target,encoding='utf-8',xml_declaration=True)
    for name,p in icons.items():
        target = ROOT/'assets/ui/icons/korea'/Path(name.replace('\\','/')+'.png')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
    stream = io.StringIO(newline=''); writer = csv.writer(stream,lineterminator='\r\n')
    corrections = {
        '111':'While this Observatory is functioning, completed technologies refund 15% of Literature actually paid.\\r\\nProvides four additional distinct Foreign Technology offers and two additional research allowances.',
        '86':'Supervise a production building for +150% production.\\r\\nNear a Seowon Academy, adds +25% Literature generation.',
        '142':'Eligible Seonbi Scholars near a Seowon Academy now add +40% Literature generation each (up from +25%).',
        '191':'Confucian Scholar that can supervise production buildings for +150% production speed, without a resource drop-off bonus.\\r\\nNear a Seowon Academy, adds +25% Literature generation. Multiple nearby eligible Scholars stack their bonuses.',
        '347':'Seonbi Scholars near a Seowon Academy add +25% Literature generation each. Multiple Scholars stack their bonuses.\\r\\nThey can also supervise production buildings for +150% production speed, without increasing resource drop-off.',
    }
    for row in source_rows:
        text = corrections.get(row['ID'],row['Text'])
        if row['ID']=='2':text=text.replace('Select Zhu xi , game mode and tuning pack to play korea','Select Community Civilization Pack Normal as game mode and tuning pack, choose Zhu Xi\u2019s Legacy, then choose Korea at match start.')
        record = [locmap[row['ID']],'','','','','',text]
        if text and text[-1].isspace():
            csv.writer(stream,lineterminator='\r\n',quoting=csv.QUOTE_ALL).writerow(record)
        else:
            writer.writerow(record)
    for id,text in {12000:'Korea',11990:'Zhu Xi\u2019s Legacy',11991:'Choose Zhu Xi\u2019s Legacy or Korea. Timeout keeps Zhu Xi\u2019s Legacy.',11992:'Play Korea with its private roster and Literature economy.'}.items():
        assert str(id) not in occupied and str(id) not in locmap.values()
        writer.writerow([id,'','','','','',text])
    locale_path.write_bytes(old_locale+stream.getvalue().encode('utf-8'))

    # Runtime tables use blueprint names, never donor numeric identities.
    maps = {category:{} for category in ('ebps','sbps','weapon','upgrade','abilities','menu')}
    for old,new in paths.items():maps[old.split('\\')[0]][old.split('\\')[-1]]=GUID+':'+new.split('\\')[-1]
    research = research_map(source)
    for id,item in research.items():
        source_key = next((k for k in paths if k.startswith('abilities\\') and E.parse(base/Path(k.replace('\\','/')+'.xml')).getroot().find("uniqueid[@name='pbgid']").get('value')==id),None)
        assert source_key, ('Missing ability',id)
        item['ability']=GUID+':'+paths[source_key].split('\\')[-1]
        r=roots[paths[source_key]]
        item['costs']={e.get('name'):float(e.get('value')) for e in r.findall("group/enum_table[@name='cost_to_player']/float")}
    out = ROOT/'assets/scar/korea'; out.mkdir(parents=True,exist_ok=True)
    (out/'catalog.scar').write_text('-- Generated source migration catalog; no donor/runtime filesystem dependency.\nKoreaCatalog = '+lua(maps)+'\nKoreaResearchCatalog = '+lua(list(research.values()))+'\n',encoding='utf-8')
    (WORK/'research-source.json').write_text(json.dumps(research,indent=2),encoding='utf-8')
    data={'destination_guid':GUID,'source_guid':SOURCE_GUID,'identity_generator':identity['generator'],
          'identity_assembly_sha256':identity['assembly_sha256'],'instances':records,
          'reference_translations':translations,'extension_identity_repairs':repairs,
          'localization_map':locmap,'icons':sorted(icons),'research_abilities':len(research),
          'omitted_global_definitions':['army/standard_mode/normal_chinese_ha_01','resource_type_info/merc_byz'],
          'source_numeric_ids':source_ids}
    (ROOT/'docs/korea-import.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Imported',len(records),'private definitions;',len(research),'research routes;',len(repairs),'extension identity repairs')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    (prepare if args.prepare else run)(args.source.resolve())
