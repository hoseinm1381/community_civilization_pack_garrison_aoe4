"""Reproduce the bounded conversion probe from pinned current official XML.

This is deliberately not the full Persia roster migration. No source blueprint
IDs, global army overrides, or custom Persian effects are installed by stage 1.
"""
import copy
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/persia_port_20261026'
OFFICIAL = WORK / 'official/instances'
GUID = 'a743d7d1d7534cf78817e29d8ded7366'
SOURCE = Path(json.loads((WORK / 'baseline.json').read_text())['persia_source_root'])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(path, base):
    return path.relative_to(base).with_suffix('').as_posix().replace('/', '\\')


def generate():
    pinned = json.loads((WORK / 'official-donors.json').read_text())
    assert sha(Path(pinned['archive'])) == pinned['archive_sha256'], 'Game update: requalify official donors before generation'
    assert all(sha(WORK / 'official' / name) == expected for name, expected in pinned['donors'].items())
    frozen = json.loads((WORK / 'baseline.json').read_text())
    assert all(sha(SOURCE / name) == expected for name, expected in frozen['persia'].items()), 'Persia source changed since the approved baseline'
    identities = json.loads((WORK / 'identities.json').read_text(encoding='utf-8-sig'))
    donors = sorted(p for p in OFFICIAL.rglob('*.xml') if p.parts[len(OFFICIAL.parts)] in ('ebps', 'sbps'))
    assert len(donors) == len(identities['pbg_ids']) == 6
    mappings = {key(p, OFFICIAL): p.parts[len(OFFICIAL.parts)] + '\\persia\\ps_probe_' + p.stem for p in donors}
    records = []
    for file, pbg in zip(donors, identities['pbg_ids']):
        original = ET.parse(file).getroot()
        native = key(file, OFFICIAL)
        private = mappings[native]
        result = ET.Element('instance', version=original.get('version'),
                            description='Persia stage 1 native conversion probe', template=original.get('template'))
        for scope in [original] + list(original.findall('variant')):
            target = result if scope is original else ET.SubElement(result, 'variant', name=scope.get('name'))
            selected = []
            for ext in scope.findall("list[@name='extensions']/template_reference"):
                value = ext.get('value', '')
                if value in ('ebpextensions\\spawner_ext', 'sbpextensions\\squad_loadout_ext', 'sbpextensions\\squad_engineer_ext'):
                    item = copy.deepcopy(ext)
                    # Override the actual native variant identity, never append.
                    item.set('List.ParentItemID', item.get('List.ItemID'))
                    item.attrib.pop('List.ListAction', None)
                    for ref in item.iter('instance_reference'):
                        if ref.get('value') in mappings:
                            ref.set('value', mappings[ref.get('value')])
                            ref.set('mod', GUID)
                            ref.set('overrideParent', 'True')
                    selected.append(item)
            if selected:
                extensions = ET.SubElement(target, 'list', name='extensions')
                extensions.extend(selected)
            ET.SubElement(target, 'uniqueid', name='pbgid', value=str(pbg))
            ET.SubElement(target, 'instance_reference', name='parent_pbg', value=native)
        target = ROOT / 'assets/attrib/instances' / Path(private.replace('\\', '/') + '.xml')
        target.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(result, space='\t')
        ET.ElementTree(result).write(target, encoding='utf-8', xml_declaration=True)
        records.append({'native': native, 'private': private, 'pbg_id': pbg,
                        'donor_sha256': sha(file), 'path': target.relative_to(ROOT).as_posix()})
    source_base = SOURCE / 'assets/attrib/instances'
    source_files = sorted(source_base.rglob('*.xml'))
    source_keys = {key(p, source_base) for p in source_files}
    baseline = json.loads((WORK / 'baseline.json').read_text())
    # Compare against the frozen destination rather than the generated children.
    import zipfile
    with zipfile.ZipFile(WORK / 'normal-before.zip') as archive:
        normal_ids = {x.get('value') for name in archive.namelist() if name.startswith('assets/attrib/instances/') and name.endswith('.xml')
                      for x in ET.fromstring(archive.read(name)).iter('uniqueid')}
    source_ids = set()
    instances = []
    proposed_paths = set()
    for file in source_files:
        tree = ET.parse(file).getroot()
        native = key(file, source_base)
        private = native.split('\\')[0] + '\\persia\\ps_' + file.stem
        assert private not in proposed_paths, 'Ambiguous proposed private path: ' + private
        proposed_paths.add(private)
        ids = [dict(x.attrib) for x in tree.iter('uniqueid')]
        source_ids.update(x['value'] for x in ids)
        refs = [{'value': x.get('value'), 'mod': x.get('mod'),
                 'source_local': x.get('value') in source_keys}
                for x in tree.iter('instance_reference') if x.get('value')]
        instances.append({'source': native, 'proposed_private': private, 'new_pbg_id': None,
                          'status': 'deferred_until_native_probe_acceptance', 'sha256': sha(file),
                          'source_ids_including_variants': ids,
                          'parents': [dict(x.attrib) for x in tree.iter('instance_reference') if x.get('name') == 'parent_pbg'],
                          'references': refs})
    source_army = ET.parse(source_base / 'army/standard_mode/normal_sultanate.xml').getroot()
    official_army = ET.parse(OFFICIAL / 'army/standard_mode/normal_sultanate.xml').getroot()
    def resources(tree):
        return {x.get('name'): float(x.get('value')) for x in tree.findall("group/enum_table[@name='resource_starting_amount']/float") if x.get('name') in ('food', 'wood', 'gold', 'stone')}
    def units(tree):
        return dict(Counter(x.get('value') for x in tree.findall("group/list[@name='starting_units']/instance_reference")))
    src, off = resources(source_army), resources(official_army)
    assert src == off, 'New resource delta requires explicit stage 1 implementation'
    assert source_army.find("group/state_tree_node[@name='start_actions_statetree']").get('value') == official_army.find("group/state_tree_node[@name='start_actions_statetree']").get('value')
    data = {'stage': 'native_conversion_probe', 'destination_guid': GUID, 'source_guid': 'd8e25db92a5647d1892584dba19980f8',
            'overlapping_id_values': len(source_ids & normal_ids), 'probe_instances': records, 'instances': instances,
            'starting_army': {'source_resources': src, 'official_resources': off,
                              'resource_delta': {k: src[k] - off[k] for k in src},
                              'source_units': units(source_army), 'official_units': units(official_army),
                              'startup_state_tree': 'civ_start\\Sultanates', 'player_upgrades': [],
                              'sheep_policy': 'Keep native/map sheep unchanged; source differs only in sheep colour composition. No spawning.'},
            'icons': [p.relative_to(SOURCE / 'assets').as_posix() for p in (SOURCE / 'assets').rglob('*.png')],
            'localization': {'status': 'deferred with full roster; source credits preserved in source baseline',
                             'source_rows': len(list(csv.DictReader((SOURCE / 'assets/locdb/Persia Definitive_en.csv').open(encoding='utf-8-sig'))))}}
    (WORK / 'migration-map.json').write_text(json.dumps(data, indent=2), encoding='utf-8')
    entities = [r['private'].split('\\')[-1] for r in records if r['native'].startswith('ebps\\')]
    squads = [r['private'].split('\\')[-1] for r in records if r['native'].startswith('sbps\\')]
    table = lambda items: '{' + ', '.join('"' + GUID + ':' + item + '"' for item in items) + '}'
    scar = '-- Generated from pinned current official donors by tools/persia_port/prepare_probe.py.\nPersiaBlueprints = {entities = ' + table(entities) + ',\n    squads = ' + table(squads) + '}\n\n'
    scar += '''function PersiaBlueprints_Available()
    for _, name in ipairs(PersiaBlueprints.entities) do
        if not EBP_Exists(name) then return false end
    end
    for _, name in ipairs(PersiaBlueprints.squads) do
        if not SBP_Exists(name) then return false end
    end
    return true
end

function PersiaPrecache_Init()
    if not PersiaBlueprints_Available() then
        print("PERSIA_PROBE_PRECACHE_MISSING")
        return
    end
    for _, name in ipairs(PersiaBlueprints.entities) do Scar_PrecachePrematchResource(BP_GetEntityBlueprint(name)) end
    for _, name in ipairs(PersiaBlueprints.squads) do Scar_PrecachePrematchResource(BP_GetSquadBlueprint(name)) end
end

Scar_AddInit(PersiaPrecache_Init)
'''
    directory = ROOT / 'assets/scar/persia'
    directory.mkdir(exist_ok=True)
    (directory / 'blueprints.scar').write_text(scar, encoding='utf-8')
    print('Generated six private current-official children and full 281-file deferred migration ledger.')


if __name__ == '__main__':
    generate()
