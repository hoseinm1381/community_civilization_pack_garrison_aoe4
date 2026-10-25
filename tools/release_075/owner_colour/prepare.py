"""Prepare isolated native flag stamp sources and reversible visual-list candidates.

Run with workspace.json blender_python and -B. Never cooks, installs, edits active
source, or modifies the baseline. Sources intentionally retain provisional donor
placement: no production acceptance is implied by successful preparation.
"""
from pathlib import Path
import copy
import hashlib
import json
import sqlite3
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
CFG = json.loads((ROOT / 'workspace.json').read_text())
OUT = ROOT / 'output/release_075/owner_colour'
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import building_project, rgd
sys.path.insert(0, str(ROOT / 'tools/release_072/vendor'))
from read_official_members import members

MODEL = 'art/civilizations/common/flags/flag_rectangle/flag_rectangle'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def put(relative, data):
    path = OUT / relative
    if not path.resolve().is_relative_to(OUT.resolve()):
        raise ValueError('Output escapes owner-colour evidence root')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise FileExistsError(f'Preserve divergent pilot evidence: {path}')
    if not path.exists():
        path.write_bytes(data)
    return str(path)


def write_json(relative, data):
    return put(relative, (json.dumps(data, indent=2) + '\n').encode())


def main():
    check_storage(ROOT, CFG)
    inventory = json.loads((ROOT / 'output/release_075/inspection/current-consumers.json').read_text())
    baseline = json.loads((ROOT / 'output/release_074/verification-v1.json').read_text())
    if inventory['baseline_sga_sha256'] != baseline['sga_sha256']:
        raise ValueError('Consumer inventory baseline differs')
    back = Path(CFG['external_root']) / 'staging/r74/v1/readback'
    stamp_inventory = json.loads((ROOT / 'output/release_075/inspection/stamps.json').read_text())
    donor = stamp_inventory['flag_donor']
    if not donor['visuals']:
        raise ValueError('No exact native flag transform found')
    transform = donor['visuals'][0]['transform']
    sources = []
    for family in inventory['families']:
        name = family + '_owner_flag'
        source = ET.fromstring(building_project.stamp_source('cc075flags', name))
        visual = source.find('.//DataObject[@Type="VisualStampBlueprint"]')
        visual.find('./DataProperty[@Name="m_blueprint"]').set('Value', MODEL.replace('/', '\\'))
        for field in ('m_isSelectable', 'm_addToPathfinding'):
            visual.find(f'./DataProperty[@Name="{field}"]').set('Value', 'false')
        # Preserve the exact stock flag orientation/scale and placement as a
        # visible diagnostic starting point, not a final building-specific fit.
        for kind, fields, values in (
            ('Math::Quaternionf', ('x', 'y', 'z', 's'), transform[:4]),
            ('Math::Vector3f', ('x', 'y', 'z'), transform[4:7]),
        ):
            obj = visual.find(f'.//DataObject[@Type="{kind}"]')
            for key, value in zip(fields, values):
                obj.find(f'./DataProperty[@Name="{key}"]').set('Value', repr(value))
        scale = visual.find('.//DataProperty[@Name="m_scale"]/DataObject')
        for key, value in zip(('x', 'y', 'z'), transform[7:]):
            scale.find(f'./DataProperty[@Name="{key}"]').set('Value', repr(value))
        raw = ET.tostring(source, encoding='utf-8', xml_declaration=True) + b'\n'
        member = str(building_project.stamp_path('cc075flags', name)).replace('\\', '/')
        # Confirmed against the fresh cc075citadel source project: DataWarehouse
        # stamp sources use .rdo; the native compiled output uses .bin.
        source_path = put('source/' + family + '.rdo', raw)
        sources.append(dict(family=family, source=source_path, source_sha256=digest(raw),
                            api_stamp_path=member,
                            cooked_member=f'art/stamps/garrison/cc075flags/{name}.bin',
                            transform=transform, placement_status='provisional_exact_donor_transform'))

    stock = []
    db = sqlite3.connect('file:C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3?mode=ro', uri=True)
    try:
        for extension in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'):
            member = MODEL + extension
            row = db.execute('select archive_path,size from resolved_assets where logical_path=?', (member,)).fetchone()
            if not row:
                raise ValueError('Missing current native stock resource: ' + member)
            matches = list(members(Path(row[0]).name, lambda n: n == Path(member).name))
            if len(matches) != 1 or len(matches[0][1]) != row[1]:
                raise ValueError('Ambiguous official resource lookup: ' + member)
            raw = matches[0][1]
            stock.append(dict(member=member, archive=row[0], sha256=digest(raw),
                              file=put('official/' + member, raw), bytes=len(raw)))
    finally:
        db.close()

    candidates = []
    seen = {f: 0 for f in inventory['families']}
    for path in sorted((back / 'attrib/attachments/attachment_lists').rglob('*.rgd')):
        raw = path.read_bytes()
        member = path.relative_to(back).as_posix()
        if digest(raw) != baseline['member_sha256'][member]:
            raise ValueError('Baseline readback drift: ' + member)
        original = rgd.read(raw)
        candidate = copy.deepcopy(original)
        edits = []
        for node_path, node in list(rgd.flatten(candidate.nodes)):
            if node.kind != 'List2':
                continue
            for family, family_data in inventory['families'].items():
                stamps = {s.removesuffix('.bin').replace('/', '\\') for s in family_data['private_stamps']}
                matching = [item for item in node.value if item.key == 'stamp_attachment' and
                            any(c.key == 'stamp' and c.value in stamps for c in item.value)]
                if not matching:
                    continue
                if len(matching) != 1:
                    raise ValueError(f'Ambiguous main stamp list: {member} {node_path}')
                template = matching[0]
                blocker = next(c for c in template.value if c.key == 'add_impass_blockers')
                if blocker.value is not False:
                    raise ValueError('Do not clone blocking attachment')
                appended = copy.deepcopy(template)
                stamp = next(c for c in appended.value if c.key == 'stamp')
                previous = stamp.value
                stamp.value = f'art\\stamps\\garrison\\cc075flags\\{family}_owner_flag'
                index = len(node.value)
                node.value.append(appended)
                edits.append(dict(family=family, list_path=node_path, appended_index=index,
                                  donor_stamp=previous, flag_stamp=stamp.value,
                                  add_impass_blockers=False))
                seen[family] += 1
        if not edits:
            continue
        restored = copy.deepcopy(candidate)
        for edit in reversed(edits):
            rgd.find(restored.nodes, edit['list_path']).value.pop(edit['appended_index'])
        if rgd.write(restored) != raw or rgd.write(original) != raw:
            raise ValueError('Exact baseline serialization restoration failed')
        candidate_bytes = rgd.write(candidate)
        reread = rgd.read(candidate_bytes)
        if rgd.write(reread) != candidate_bytes:
            raise ValueError('Candidate serialization is not stable')
        pbgids = {p: n.value for p, n in rgd.flatten(original.nodes) if n.key == 'pbgid'}
        if pbgids != {p: n.value for p, n in rgd.flatten(reread.nodes) if n.key == 'pbgid'}:
            raise ValueError('PBG identities changed')
        put('baseline/' + member, raw)
        file = put('candidate/' + member, candidate_bytes)
        candidates.append(dict(member=member, file=file, before_sha256=digest(raw),
                               after_sha256=digest(candidate_bytes), pbgids=pbgids, edits=edits,
                               removal_restores_exact_original=True))
    if not all(seen.values()):
        raise ValueError('Missing main visual consumer: ' + str(seen))
    report = dict(schema='ccp075-owner-colour-pilot-preparation/v1',
                  status='prepared_isolated_uncooked_unqualified', baseline_sga_sha256=baseline['sga_sha256'],
                  stock_resources=stock, sources=sources, attachment_candidates=candidates,
                  allowed_changed_members=[x['member'] for x in candidates],
                  allowed_added_members=[x['cooked_member'] for x in sources],
                  active_source_modified=False, cook_run=False, native_tested=False,
                  source_registration='Stage each DataWarehouse XML at project/source/<api_stamp_path>.rdo (confirmed fresh cc075citadel native source convention), then compile serially. The cooked member uses the same logical stem with .bin. Existing attachment PBG identities remain unchanged; apply exact compiled visual overlays only after qualification, retaining this source and recipe as rebuild inputs.',
                  unresolved=['Donor transform is diagnostic only: root must fit each pole base to final building ground/courtyard and prove contact.',
                              'Stock flag model is retained whole, including its original pole/cloth; mesh bounds and pole-ground contact need visual inspection.',
                              'Flag RGO lifecycle and owner-colour propagation on these seven owner chains are unqualified.',
                              'Appending a visual stamp does not itself hide it in ruins. Verify construction, healthy, damage, destroyed and repaired states before acceptance.',
                              'Native cook and archive texture/model closure not yet run; stock material dependencies remain official game references.'])
    write_json('preparation-v2.json', report)
    print(json.dumps(dict(status=report['status'],sources=len(sources),lists=len(candidates),variants=seen)))


if __name__ == '__main__':
    main()
