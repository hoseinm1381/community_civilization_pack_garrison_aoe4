"""Import editable Persia source into private Normal definitions.

Run only for an intentional migration using the preserved editor identity receipt.
Ordinary editing/building uses the imported assets and needs no sibling project.
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import io
import json
import shutil
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUID = 'a743d7d1d7534cf78817e29d8ded7366'
SOURCE_GUID = 'd8e25db92a5647d1892584dba19980f8'
MARKER = 'upgrade\\persia\\ps_gundeshapur_functioning'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(source, work):
    locale_file=next((ROOT/'assets/locdb').glob('*_en.csv'))
    occupied={r['ID'] for r in csv.DictReader(locale_file.open(encoding='utf-8-sig',newline=''))}
    planned={str(5000+int(r['ID'])) for r in csv.DictReader((source/'assets/locdb/Persia Definitive_en.csv').open(encoding='utf-8-sig',newline=''))}
    assert not occupied.intersection(planned), 'Persia is already imported; edit current assets directly instead of rerunning the one-time importer'
    base = source/'assets/attrib/instances'
    files = sorted(p for p in base.rglob('*.xml') if p.relative_to(base).parts[0] != 'army')
    assert len(files) == 280
    identities = json.loads((work/'identities.json').read_text(encoding='utf-8-sig'))
    assert len(identities['pbg_ids']) == 281
    key = lambda p: p.relative_to(base).with_suffix('').as_posix().replace('/', '\\')
    paths = {key(p): key(p).split('\\')[0] + '\\persia\\ps_' + p.stem for p in files}
    aliases = {(key(p).split('\\')[0], p.stem.lower()): key(p) for p in files}
    assert len(aliases) == 280, 'Ambiguous original blueprint basename'
    roots, records, translated = {}, [], []
    icons = {p.relative_to(source/'assets/ui/icons').with_suffix('').as_posix().replace('/', '\\').lower():p
             for p in (source/'assets/ui/icons').rglob('*.png')}
    locale = {str(int(r['ID'])): str(5000+int(r['ID'])) for r in csv.DictReader((source/'assets/locdb/Persia Definitive_en.csv').open(encoding='utf-8-sig', newline=''))}
    for file, new_id in zip(files, identities['pbg_ids']):
        oldkey = key(file)
        root = E.parse(file).getroot()
        for node in root.iter():
            if node.tag == 'uniqueid' and node.get('name') == 'pbgid':
                node.set('value', str(new_id))
            elif node.tag == 'locstring' and node.get('mod') == SOURCE_GUID:
                node.set('value', locale[node.get('value')]); node.set('mod', GUID)
            elif node.tag == 'instance_reference' and node.get('value'):
                value = node.get('value')
                old_mod = node.get('mod', '')
                target = value if value in paths else aliases.get((value.split('\\')[0], value.split('\\')[-1].lower()))
                # A private clone may deliberately inherit its official namesake.
                if target == oldkey and node.get('name') == 'parent_pbg' and old_mod != SOURCE_GUID:
                    target = None
                if target in paths and old_mod in ('', SOURCE_GUID):
                    node.set('value', paths[target]); node.set('mod', GUID)
                    translated.append({'owner':paths[oldkey], 'old':value, 'new':paths[target], 'alias':value != target})
                elif old_mod == SOURCE_GUID:
                    raise ValueError('Unresolved source-owned reference: '+oldkey+' '+value)
            elif node.tag == 'file' and node.get('value','').lower() in icons:
                node.set('value', 'persia\\'+node.get('value').lower())
        roots[paths[oldkey]] = root
        records.append({'source':oldkey,'private':paths[oldkey], 'pbg_id':new_id,
                        'source_pbg_id':E.parse(file).getroot().find("uniqueid[@name='pbgid']").get('value'),
                        'source_sha256':digest(file.read_bytes())})

    # Resolve the complete private/current-official chain before changing any
    # singleton extension identity. Values and nested gameplay data stay intact.
    spec = importlib.util.spec_from_file_location('extension_audit', ROOT/'tools/check_extension_inheritance.py')
    audit = importlib.util.module_from_spec(spec); spec.loader.exec_module(audit)
    official = json.loads((work/'official-extensions.json').read_text())['records']
    repairs, finished = [], set()
    def repair(k, trail=()):
        if k in finished:return
        if k in trail:raise ValueError('Private inheritance cycle '+k)
        root=roots[k]
        for parent in root.iter('instance_reference'):
            if parent.get('name')=='parent_pbg' and parent.get('mod')==GUID and parent.get('value') in roots:
                repair(parent.get('value'),trail+(k,))
        for scope in [root]+list(root.findall('variant')):
            extensions=scope.find("list[@name='extensions']")
            if extensions is None or extensions.get('overrideParent')=='True':continue
            local={name:audit.summarize(E.tostring(tree)) for name,tree in roots.items() if name.startswith(('ebps\\','sbps\\'))}
            resolver=audit.Resolver(local,official)
            inherited=resolver.inherited(k,scope.get('name','default'))
            seen=set()
            for ext in extensions:
                value=ext.get('value'); assert value not in seen, ('Duplicate direct source extension',k,value)
                seen.add(value)
                matches=[x for x in inherited if x.get('value')==value]
                assert len(matches)<=1,(k,value,'Ambiguous native singleton')
                before=dict(ext.attrib)
                if matches:
                    identity=matches[0]['List.ItemID']
                    ext.set('List.ItemID',identity);ext.set('List.ParentItemID',identity)
                    ext.attrib.pop('List.ListAction',None)
                else:
                    ext.attrib.pop('List.ParentItemID',None)
                    ext.set('List.ListAction','Append')
                if before!=ext.attrib:
                    repairs.append({'private':k,'variant':scope.get('name','default'),'extension':value,
                                    'before':before,'after':dict(ext.attrib),
                                    'gameplay_subtree_sha256':digest(b''.join(E.tostring(x) for x in ext))})
        finished.add(k)
    for k in roots:
        if k.startswith(('ebps\\','sbps\\')):repair(k)

    # The source already has an OR wrapper around Castle Age. Add one private,
    # reversible functioning-landmark signal without removing dynasty/self guards.
    dynasty=roots['upgrade\\persia\\ps_persia_unit_feudal_to_castle']
    requirements=dynasty.find("group/list[@name='requirements']")
    alternatives=requirements.find("template_reference[@value='requirements\\required_any_in_list']/list[@name='requirements']")
    assert alternatives is not None and len(alternatives)==1
    condition=copy.deepcopy(alternatives[0])
    condition.set('List.ItemID',str(identities['requirement_item_id']))
    condition.set('List.ListAction','Append')
    ref=condition.find("instance_reference[@name='upgrade_name']"); ref.set('value',MARKER);ref.set('mod',GUID)
    alternatives.append(condition)
    marker=E.Element('instance',version='4',template='upgrade')
    bag=E.SubElement(marker,'group',name='upgrade_bag')
    E.SubElement(bag,'enum',name='owner_type',value='player')
    E.SubElement(bag,'float',name='local_max_limit',value='1')
    E.SubElement(bag,'bool',name='ui_event_cue',value='False')
    E.SubElement(marker,'uniqueid',name='pbgid',value=str(identities['pbg_ids'][280]))
    E.SubElement(marker,'instance_reference',name='parent_pbg',value='')
    roots[MARKER]=marker
    for k,root in roots.items():
        target=ROOT/'assets/attrib/instances'/Path(k.replace('\\','/')+'.xml')
        target.parent.mkdir(parents=True,exist_ok=True);E.indent(root,space='\t')
        E.ElementTree(root).write(target,encoding='utf-8',xml_declaration=True)
    for icon,file in icons.items():
        target=ROOT/'assets/ui/icons/persia'/Path(icon.replace('\\','/')+'.png')
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
    csv_path=next((ROOT/'assets/locdb').glob('*_en.csv'))
    raw=csv_path.read_bytes();rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));header=list(rows[0])
    existing={r['ID'] for r in rows};assert not existing.intersection(locale.values()),'Locale IDs already imported'
    incoming=list(csv.DictReader((source/'assets/locdb/Persia Definitive_en.csv').open(encoding='utf-8-sig',newline='')))
    incoming_text={row['ID']:row['Text'] for row in incoming}
    stream=io.StringIO(newline='');writer=csv.writer(stream,lineterminator='\r\n' if b'\r\n' in raw else '\n')
    for row in incoming:
        text=row['Text']
        if row['ID'] in ('170','171') and text.startswith('<locstring '):
            text=incoming_text['168']
        if row['ID'] in ('59','60'):
            text='Functions as an additional Divan of War.\\r\\nUnlocks Daylamites in the Feudal Age.\\r\\nWhile functioning, permits Il-Khanid research in Feudal after the preceding dynasty.'
        if row['ID']=='2':
            text=text.replace('enable the “Persians” tuning pack and select the Delhi Sultanate (due to modding constraints, Persia replaces Delhi as a civilization)', 'enable Community Civilization Pack Normal, select the Delhi Sultanate, then choose Persia at match start')
        writer.writerow([locale[row['ID']],'','','','','',text])
    csv_path.write_bytes(raw+stream.getvalue().encode('utf-8'))
    entities=[k.split('\\')[-1] for k in roots if k.startswith('ebps\\')]
    squads=[k.split('\\')[-1] for k in roots if k.startswith('sbps\\')]
    table=lambda values:'{\n'+''.join('    "'+GUID+':'+v+'",\n' for v in sorted(values))+'}'
    scar='-- Complete private Persian roster; generated by tools/import_persia.py.\nPersiaBlueprints = {entities = '+table(entities)+',\n    squads = '+table(squads)+'}\n\n'
    scar+='''function PersiaBlueprints_Available()
    for _, name in ipairs(PersiaBlueprints.entities) do if not EBP_Exists(name) then return false end end
    for _, name in ipairs(PersiaBlueprints.squads) do if not SBP_Exists(name) then return false end end
    return true
end

function PersiaPrecache_Init()
    for _, name in ipairs(PersiaBlueprints.entities) do
        if EBP_Exists(name) then Scar_PrecachePrematchResource(BP_GetEntityBlueprint(name))
        else print("PERSIA_PRECACHE_MISSING_ENTITY " .. name) end
    end
    for _, name in ipairs(PersiaBlueprints.squads) do
        if SBP_Exists(name) then Scar_PrecachePrematchResource(BP_GetSquadBlueprint(name))
        else print("PERSIA_PRECACHE_MISSING_SQUAD " .. name) end
    end
end

Scar_AddInit(PersiaPrecache_Init)
'''
    (ROOT/'assets/scar/persia/blueprints.scar').write_text(scar,encoding='utf-8')
    data={'destination_guid':GUID,'source_guid':SOURCE_GUID,'instances':records,'reference_translations':translated,
          'extension_identity_repairs':repairs,'localization_map':locale,'icons':sorted(icons),
          'identity_generator':identities['generator'],'identity_assembly_sha256':identities['assembly_sha256'],
          'marker':{'key':MARKER,'pbg_id':identities['pbg_ids'][280]},
          'army_policy':'Stock Delhi army unchanged; source and official resource/start-unit audit retained from stage 1.'}
    (ROOT/'docs/persia-import.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Imported',len(records),'instances; repaired',len(repairs),'extension identities; remapped',len(translated),'references; copied',len(icons),'icons.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--work',type=Path,default=ROOT/'work/persia_full_20261026')
    args=parser.parse_args();run(args.source.resolve(),args.work.resolve())
