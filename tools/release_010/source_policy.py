"""Strict semantic guard: only existing attachment reference values may change."""
import xml.etree.ElementTree as ET
from common import CONFIG, OUT, ROOT, STAGING, read, sha, write

ACTORS = {f'ebps/vietnam/{name}.xml' for name in (
    'vn_building_house_control_chi', 'vn_building_house_control_faster_chi',
    'vn_building_bambo_outpost_chi', 'vn_building_defense_outpost_bambo_chi')}


def assert_visual_only(before, after):
    changes = []
    def compare(a, b, path):
        if a.tag != b.tag or len(a) != len(b) or (a.text or '').strip() != (b.text or '').strip():
            raise ValueError(f'Nonvisual XML structure/text change at {path}')
        visual = a.tag == 'instance_reference' and a.get('name') in {'attachments', 'animator_attachments'}
        aa, bb = dict(a.attrib), dict(b.attrib)
        if visual:
            for key in ('value', 'mod'):
                aa.pop(key, None)
                bb.pop(key, None)
        if aa != bb:
            raise ValueError(f'Nonvisual XML attribute change at {path}: {aa} != {bb}')
        if a.attrib != b.attrib:
            changes.append({'path': path, 'before': a.attrib, 'after': b.attrib})
        for index, (left, right) in enumerate(zip(a, b)):
            compare(left, right, path + '/' + str(index))
    compare(ET.fromstring(before), ET.fromstring(after), 'root')
    return changes


def verify(added_sources):
    baseline = read(OUT / 'baseline-freeze.json')
    source = STAGING / 'baseline_source'
    expected = set(baseline['assets'])
    actual = {p.relative_to(ROOT / 'assets').as_posix() for p in (ROOT / 'assets').rglob('*') if p.is_file()}
    if expected - actual or actual - expected != set(added_sources):
        raise ValueError(f'Unapproved source inventory change: removed={expected-actual}, added={actual-expected-set(added_sources)}')
    changed = []
    for relative, record in baseline['assets'].items():
        path = ROOT / 'assets' / relative
        if sha(path) == record['sha256']:
            continue
        instance = relative.removeprefix('attrib/instances/')
        if not relative.startswith('attrib/instances/') or instance not in ACTORS:
            raise ValueError(f'Nonvisual source changed: {relative}')
        edits = assert_visual_only((source / 'assets' / relative).read_bytes(), path.read_bytes())
        for edit in edits:
            if edit['after'].get('mod') != CONFIG['project_guid'].replace('-', ''):
                raise ValueError(f'Attachment not owned by final project: {relative}')
        changed.append({'file': relative, 'changes': edits})
    if sha(ROOT / CONFIG['project_file']) != baseline['project_sha256']:
        raise ValueError('Project identity/build manifest changed')
    result = {'status': 'passed', 'changed_existing_source': changed,
              'new_source_files': sorted(added_sources), 'other_original_asset_files': 'byte-identical',
              'source_assets_sha256': {p: sha(ROOT / 'assets' / p) for p in sorted(actual)}}
    write(OUT / 'source-preservation.json', result)
    return result
