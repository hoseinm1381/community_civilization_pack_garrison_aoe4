"""Read-only stage 1 preservation/identity checks; writes only its evidence report."""
import csv
import hashlib
import io
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'work/persia_port_20261026'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    baseline = json.loads((WORK / 'baseline.json').read_text())
    allowed = {'assets/scar/winconditions/VietnamMode.scar', 'assets/scar/vietnam/selection_core.scar',
               'assets/locdb/Vietnam_v2_en.csv'}
    changed = [name for name, expected in baseline['normal'].items() if not (ROOT / name).exists() or digest(ROOT / name) != expected]
    assert set(changed) == allowed, ('Unexpected existing source change', changed)
    source = Path(baseline['persia_source_root'])
    assert all((source / name).exists() and digest(source / name) == expected for name, expected in baseline['persia'].items()), 'Original Persia source changed'
    assert digest(WORK / 'normal-before.zip') == baseline['normal_zip_sha256']
    with zipfile.ZipFile(WORK / 'normal-before.zip') as archive:
        assert archive.testzip() is None
        oldrows = {r['ID']: r for r in csv.DictReader(io.StringIO(archive.read('assets/locdb/Vietnam_v2_en.csv').decode('utf-8-sig')))}
        newrows = {r['ID']: r for r in csv.DictReader((ROOT / 'assets/locdb/Vietnam_v2_en.csv').open(encoding='utf-8-sig', newline=''))}
        assert [key for key in oldrows if oldrows[key] != newrows[key]] == ['1010']
        assert set(newrows) - set(oldrows) == {'1104', '1105', '1107', '1109', '1110', '1111'}
    project = ET.parse(ROOT / 'Vietnam_v2.aoe4mod').getroot()
    ids = [x.text.replace('-', '').lower() for x in project.iter() if x.tag.split('}')[-1] == 'ID']
    assert ids == ['a743d7d1d7534cf78817e29d8ded7366']
    burn = ET.parse(ROOT / 'assets/_default.burnproj').getroot()
    names = [x.text for x in burn.iter() if x.tag.split('}')[-1] == 'NiceName']
    assert names == ids, (names, ids)
    manifest = ET.parse(ROOT / 'assets/attrib/Vietnam_v2.xml').getroot()
    assert manifest.get('guid') == ids[0]
    records = json.loads((WORK / 'migration-map.json').read_text())
    generated = {r['path'] for r in records['probe_instances']}
    existing = set(baseline['normal'])
    current = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'assets').rglob('*') if p.is_file()}
    expected_added = generated | {'assets/scar/persia/blueprints.scar', 'assets/scar/persia/initialization.scar', 'assets/scar/persia/lifecycle.scar'}
    assert current - existing == expected_added, ('Unexpected new active source', current - existing)
    reserved = set(json.loads((WORK / 'reserved-ids.json').read_text()))
    newids = [r['pbg_id'] for r in records['probe_instances']]
    assert len(newids) == len(set(newids)) == 6 and not reserved.intersection(newids)
    donors = json.loads((WORK / 'official-donors.json').read_text())
    assert digest(Path(donors['archive'])) == donors['archive_sha256'], 'Game update: requalify pinned official donors'
    for name, expected in donors['donors'].items():
        assert digest(WORK / 'official' / name) == expected
    instances = ROOT / 'assets/attrib/instances'
    local = {str(p.relative_to(instances).with_suffix('')).replace('/', '\\') for p in instances.rglob('*.xml')}
    for path in generated:
        for ref in ET.parse(ROOT / path).getroot().iter('instance_reference'):
            if ref.get('mod'):
                assert ref.get('mod') == ids[0] and ref.get('value') in local
    result = {'status': 'passed', 'existing_changed_allowlist': sorted(changed),
              'preserved_existing_attribute_files': sum(name.startswith('assets/attrib/instances/') for name in baseline['normal']),
              'preserved_original_persia_files': len(baseline['persia']), 'new_private_instances': 6,
              'source_project_archive_identity': ids[0], 'official_archive_sha256': donors['archive_sha256'],
              'content_editor': 'not run - user gate', 'compiled_archive': 'not built or verified',
              'native_gameplay_and_multiplayer': 'not run - user gate'}
    (WORK / 'preservation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
