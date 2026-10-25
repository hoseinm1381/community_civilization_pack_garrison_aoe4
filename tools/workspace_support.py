"""Read-only guards for this prepared Content Editor / Garrison workspace."""
import csv
import hashlib
import io
import json
import re
import struct
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configuration(root=ROOT):
    return json.loads((root / 'workspace.json').read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_storage(root, config):
    external = Path(config['external_root'])
    if not external.is_absolute() or not external.is_dir():
        raise ValueError(f'External storage unavailable: {external}. Connect F:; no folders were created.')
    checked = {}
    for relative, target_relative in config['links'].items():
        local, target = root / relative, external / target_relative
        if Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError(f'Unsafe local link path: {relative}')
        if not target.resolve().is_relative_to(external.resolve()):
            raise ValueError(f'External target escapes owned storage: {target}')
        if not local.is_junction():
            raise ValueError(f'Expected junction: {local}; refusing ordinary-directory fallback')
        if not target.is_dir() or local.resolve() != target.resolve():
            raise ValueError(f'Junction target missing or changed: {local} -> {target}')
        checked[relative] = str(target.resolve())
    return checked


def _guid_parts(guid):
    return struct.unpack('<4I', uuid.UUID(guid).bytes_le)


def _restore_parts(data, config):
    old_parts = _guid_parts(config['source_project_guid'])
    new_parts = _guid_parts(config['project_guid'])
    pattern = re.compile(rb'<DataObject\b[^>]*Type="util::ReflectLocString"[^>]*>.*?</DataObject>', re.S)
    def restore(match):
        block = match.group()
        if not all(re.search(fr'Name="m_modPart{i}"[^>]*Value="{n}"'.encode(), block)
                   for i, n in enumerate(new_parts)):
            return block
        for i, (new, old) in enumerate(zip(new_parts, old_parts)):
            block = re.sub(fr'(Name="m_modPart{i}"[^>]*Value="){new}("[^>]*>)'.encode(),
                           lambda m: m[1] + str(old).encode() + m[2], block)
        return block
    return pattern.sub(restore, data)


def baseline_bytes(relative, data, config):
    """Undo only authorized identity changes; gameplay bytes remain significant."""
    new, old = config['project_guid'], config['source_project_guid']
    data = data.replace(new.encode(), old.encode()).replace(new.replace('-', '').encode(), old.replace('-', '').encode())
    if relative.endswith('.rdo'):
        data = _restore_parts(data, config)
        if relative == 'assets/mod.rdo':
            data = data.replace(b'Name="Community_Civilization_Pack"', b'Name="Vietnam_v2"')
    if relative in ('Vietnam_v2.aoe4mod', 'assets/attrib/Vietnam_v2.xml', 'assets/_default.burnproj') or relative.startswith(('tests/', 'tools/')):
        data = data.replace(config['package_key'].encode(), b'Vietnam_v2')
    if relative == 'tests/test_legacy_trap_tunnel.py':
        data = data.replace(b"OLD = Path(json.loads((ROOT/'workspace.json').read_text())['donor_root'])/'assets/attrib/instances'",
                            b"OLD = ROOT.parent/'Real_Vietnam_1/assets/attrib/instances'")
    return data


def check_identity(root, config):
    guid = config['project_guid'].replace('-', '').lower()
    project = ET.parse(root / config['project_file']).getroot()
    actual = next(n.text for n in project if n.tag.rsplit('}', 1)[-1] == 'ID')
    if actual.replace('-', '').lower() != guid:
        raise ValueError('Project GUID mismatch')
    key = config['package_key']
    manifest = ET.parse(root / f'assets/attrib/{key}.xml').getroot()
    if manifest.get('guid') != guid:
        raise ValueError('Attribute manifest GUID mismatch')
    locdb = root / f'assets/locdb/{key}.locdb'
    if next(n.text for n in project if n.tag.rsplit('}', 1)[-1] == 'LocDBPath').replace('\\', '/') != f'locdb/{key}.locdb':
        raise ValueError('Project localization path mismatch')
    if manifest.get('locdb_path').replace('\\', '/') != f'../locdb/{key}.locdb' or not locdb.is_file():
        raise ValueError('Attribute localization path mismatch')
    with (root / f'assets/locdb/{key}_en.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    loc = {r['ID']: r['Text'] for r in rows}
    if len(loc) != len(rows) or loc.get('1001') != config['display_name']:
        raise ValueError('Localization IDs or display name mismatch')
    mode = ET.parse(root / 'assets/scar/winconditions/VietnamMode.rdo').getroot()
    if mode.find("./DataObject/DataProperty[@Name='m_tuningModGUID']").get('Value') != guid:
        raise ValueError('Game-mode tuning GUID mismatch')
    parts = _guid_parts(config['project_guid'])
    for path in (root / 'assets/mod.rdo', root / 'assets/scar/winconditions/VietnamMode.rdo'):
        for node in ET.parse(path).getroot().iter('DataObject'):
            if node.get('Type') != 'util::ReflectLocString':
                continue
            values = {n.get('Name'): n.get('Value') for n in node.findall('DataProperty')}
            # Foreign RDO references are untouched by migration and checked by preservation.
            if tuple(int(values[f'm_modPart{i}']) for i in range(4)) != parts:
                raise ValueError(f'RDO localization GUID mismatch: {path}')
            if values['m_locStringKey'] not in loc:
                raise ValueError(f'RDO localization key missing: {path}')
    instances = root / 'assets/attrib/instances'
    files = list(instances.rglob('*.xml'))
    keys = {p.relative_to(instances).with_suffix('').as_posix().replace('/', '\\').lower() for p in files}
    for path in files:
        for node in ET.parse(path).getroot().iter():
            if node.get('mod', '').replace('-', '').lower() == guid:
                if node.tag == 'instance_reference' and node.get('value', '').lower() not in keys:
                    raise ValueError(f'Unresolved private reference: {path}: {node.get("value")}')
                if node.tag == 'locstring' and node.get('value') not in loc:
                    raise ValueError(f'Unresolved private localization: {path}')
    old_tokens = (config['source_project_guid'], config['source_project_guid'].replace('-', ''))
    for path in (root / 'assets').rglob('*'):
        if path.is_file() and path.suffix in ('.scar', '.xml', '.rdo', '.burnproj', '.locdb'):
            if any(token.encode() in path.read_bytes() for token in old_tokens):
                raise ValueError(f'Old project identity remains active: {path}')
    project_record = json.loads((root / config['garrison_project'] / 'mod-project.json').read_text())
    if project_record['key'] != key or project_record['mod_id'].replace('-', '') != guid:
        raise ValueError('Garrison identity mismatch')
    mode_settings = project_record['game_mode']
    if any(mode_settings.get(k, False) for k in ('enabled', 'requested', 'live_reload')):
        raise ValueError('Generated Garrison game mode and Live Reload must remain off')
    if project_record.get('release', {}).get('version') != config['version']:
        raise ValueError('Reserved Garrison version mismatch')
    for field in ('python', 'garrison_core', 'archive_tool', 'content_editor', 'art_editor'):
        if not Path(config[field]).is_file():
            raise ValueError(f'Required tool unavailable: {field}: {config[field]}')
    return {'project_guid': actual, 'instances': len(files), 'localization_rows': len(rows),
            'garrison_assets': len(project_record.get('assets', [])), 'cooks': len(project_record.get('cooks', []))}


def check_preservation(root, config):
    source = Path(config['source_root'])
    baseline = json.loads((root / 'docs/preparation/normal-before.json').read_text())
    current_files = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    if current_files != set(baseline):
        raise ValueError('Normal edition file inventory changed')
    for relative, record in baseline.items():
        if sha(source / relative) != record['sha256']:
            raise ValueError(f'Normal edition changed: {relative}')
    provenance = json.loads((root / 'docs/migration-provenance.json').read_text())
    renames = provenance['renames']
    protected = [r for r in baseline if r.startswith('assets/') or r == 'Vietnam_v2.aoe4mod']
    expected_assets = {renames.get(r, r) for r in protected if r.startswith('assets/')}
    actual_assets = {p.relative_to(root).as_posix() for p in (root / 'assets').rglob('*') if p.is_file()}
    if actual_assets != expected_assets:
        raise ValueError('Copied asset inventory changed')
    for relative in protected:
        actual = (root / renames.get(relative, relative)).read_bytes()
        expected = (source / relative).read_bytes()
        if relative == 'assets/locdb/Vietnam_v2_en.csv':
            a = list(csv.reader(io.StringIO(actual.decode('utf-8-sig'), newline='')))
            b = list(csv.reader(io.StringIO(expected.decode('utf-8-sig'), newline='')))
            for row in a[1:]:
                if row[0] == '1001':
                    row[a[0].index('Text')] = next(r[b[0].index('Text')] for r in b[1:] if r[0] == '1001')
            if a != b:
                raise ValueError('Localization changed outside the pack name')
        elif baseline_bytes(relative, actual, config) != expected:
            raise ValueError(f'Gameplay/source preservation mismatch: {relative}')
    preserved_docs = 0
    for relative in baseline:
        if relative.startswith('docs/') and relative != 'docs/editor-identity.json':
            if sha(root / relative) != baseline[relative]['sha256']:
                raise ValueError(f'Historical evidence changed: {relative}')
            preserved_docs += 1
        if relative.startswith('tests/') and not relative.endswith('.pyc') and '__pycache__' not in relative:
            if baseline_bytes(relative, (root / relative).read_bytes(), config) != (source / relative).read_bytes():
                raise ValueError(f'Copied test assertion changed: {relative}')
    return {'normal_files_unchanged': len(baseline), 'protected_source_files': len(protected),
            'historical_docs_unchanged': preserved_docs, 'copied_test_assertions': 'unchanged'}
