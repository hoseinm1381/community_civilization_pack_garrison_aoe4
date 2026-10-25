"""Only approved 0.2.0 visual attachment references may differ from frozen 0.1.0 source."""
import xml.etree.ElementTree as ET
from pathlib import Path
from common import CONFIG, OUT, ROOT, STAGING, guarded, read, sha, write

CONSUMERS = (
    'vn_building_unit_infantry_control_chi',
    'vn_building_town_center_chi', 'vn_building_town_center_2_chi',
    'vn_building_town_center_capital_chi', 'vn_building_town_center_capital_2_chi',
    'vn_building_resource_farm_chi', 'vn_building_resource_farm2_chi',
    'vn_building_defense_outpost_chi', 'vn_building_defense_outpost_2_chi',
    'vn_building_econ_food_control_chi',
)
ACTORS = {f'attrib/instances/ebps/vietnam/{name}.xml' for name in CONSUMERS}


def visual_changes(before, after):
    changes = []
    def walk(a, b, path):
        if a.tag != b.tag or len(a) != len(b) or (a.text or '').strip() != (b.text or '').strip():
            raise ValueError(f'Changed XML structure/text at {path}')
        old, new = dict(a.attrib), dict(b.attrib)
        visual = a.tag == 'instance_reference' and a.get('name') in ('attachments', 'animator_attachments')
        if visual:
            for key in ('value', 'mod'):
                old.pop(key, None); new.pop(key, None)
        if old != new:
            raise ValueError(f'Changed nonvisual XML property at {path}')
        if a.attrib != b.attrib:
            assert visual and b.get('mod') == CONFIG['project_guid'].replace('-', '')
            changes.append({'path': path, 'before': a.attrib, 'after': b.attrib})
        for index, (left, right) in enumerate(zip(a, b)):
            walk(left, right, f'{path}/{index}')
    walk(ET.fromstring(before), ET.fromstring(after), 'root')
    return changes


def verify(added_sources=()):
    baseline = guarded()
    frozen = baseline['source_hashes']['assets']
    stage = Path(baseline['source_stage']) / 'assets'
    actual = {p.relative_to(ROOT / 'assets').as_posix(): p for p in (ROOT / 'assets').rglob('*') if p.is_file()}
    added = set(added_sources)
    if set(actual) != set(frozen) | added or set(frozen) & added:
        raise ValueError(f'Unapproved asset inventory delta: missing={set(frozen)-set(actual)}, extra={set(actual)-set(frozen)-added}')
    changed = []
    for relative, record in frozen.items():
        if sha(actual[relative]) == record['sha256']:
            continue
        if relative not in ACTORS:
            raise ValueError(f'Nonvisual frozen asset changed: {relative}')
        edits = visual_changes((stage / relative).read_bytes(), actual[relative].read_bytes())
        if not edits:
            raise ValueError(f'Actor byte drift without approved visual change: {relative}')
        changed.append({'file': relative, 'changes': edits})
    if sha(ROOT / CONFIG['project_file']) != baseline['source_hashes']['project'][CONFIG['project_file']]['sha256']:
        raise ValueError('Project identity file changed')
    result = {'status': 'passed', 'changed_existing_source': changed,
              'new_source_files': sorted(added), 'unchanged_original_asset_files': len(frozen)-len(changed),
              'source_assets_sha256': {p: sha(actual[p]) for p in sorted(actual)}}
    write(OUT / 'source-preservation.json', result)
    return result
