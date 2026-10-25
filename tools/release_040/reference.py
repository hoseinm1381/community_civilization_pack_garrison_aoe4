"""Fresh native Reflect cook of the 0.4.0 landmark repair model pair."""
import hashlib
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, ARCH, ART_EDITOR, CORE, guarded, read, run_logged, sha, write
from landmark_media import native
from bindings import WORK, STEMS


def qualify(label, kind='landmarks'):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    assert kind in ('landmarks', 'details')
    if kind == 'landmarks':
        media = read(WORK / 'landmark-media.json')
        models = media['models']
        assert set(models) == set(STEMS.values())
        prefix = 'art/scenario/cc040/'
        cooked = read(read(OUT / 'art-cook-pointer.json')['receipt'])
        project_name = 'community_040_landmarks'
        template_name = 'pho_minh'
        reference_root = OUT / 'reference-cook' / label
        result_path = WORK / 'reference-cook.json'
    else:
        media = read(WORK / 'building-details-media.json')
        models = [row['detail_model'] for row in media['models']]
        assert len(models) == len(set(models)) == 12
        prefix = 'art/scenario/garrison/community_040_details/'
        cooked = read(read(OUT / 'details/cook-pointer.json')['receipt'])
        project_name = 'community_040_details'
        template_name = 'detail_blacksmith_age02'
        reference_root = OUT / 'detail-reference-cook' / label
        result_path = WORK / 'detail-reference-cook.json'
    rows = media['payloads']
    private = {r['member']: r for r in rows if r['member'].startswith(prefix)}
    assert all(sha(r['file']) == r['sha256'] for r in private.values())
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    project = Path(cooked['project']) / 'project'
    reference = reference_root
    assert not reference.exists(), reference
    source = reference / 'source'
    source.mkdir(parents=True)
    mod_files = list(project.glob('*.aoe4mod'))
    assert len(mod_files) == 1
    shutil.copy2(mod_files[0], reference / 'reference.aoe4mod')
    for row in private.values():
        target = source / row['member']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row['file'], target)
        if target.suffix == '.rrmaterial': shutil.copy2(target, target.with_suffix('.material'))
    # Stage unchanged lifecycle owners too. Reflect needs the complete model quartet.
    if kind == 'landmarks':
        for model, owner in media['native_rgo'].items():
            target = source / (model + '.rgo')
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(owner['file'], target)
            assert sha(target) == owner['sha256']
    original = project / f'source/art/stamps/garrison/{project_name}/{template_name}.rdo'
    assert original.is_file(), original
    burn = (project / 'source/_default.burnproj').read_text(encoding='utf-8-sig')
    burn = re.sub(r'<BurnRule>.*?</BurnRule>',
                  lambda m: m[0].replace('<IsEnabled>true</IsEnabled>', '<IsEnabled>false</IsEnabled>'),
                  burn, flags=re.S)
    rules, references = [], []
    for index, model in enumerate(models):
        doc = ET.parse(original)
        root = doc.getroot()
        ids = {node.get('Id'): str(int.from_bytes(hashlib.sha256(
            ('cc040:reference:' + str(index) + ':' + node.get('Id')).encode()).digest()[:8], 'little'))
               for node in root.iter('DataObject')}
        for node in root.iter():
            for key in ('Id', 'OwnerId'):
                if node.get(key) in ids: node.set(key, ids[node.get(key)])
            if node.tag == 'DataValue' and node.text in ids: node.text = ids[node.text]
            if node.tag == 'DataProperty' and node.get('Name') == 'm_objectID' and node.get('Value') in ids:
                node.set('Value', ids[node.get('Value')])
            if node.tag == 'DataProperty' and node.get('Name') == 'm_blueprint':
                node.set('Value', model.replace('/', '\\'))
        member = f'art/stamps/cc040/{"detail_" if kind == "details" else ""}reference_{index}'
        target = source / (member + '.rdo')
        target.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root)
        target.write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True))
        rules.append('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner>'
                     '<Configurations>Debug Release Profile RTM</Configurations>'
                     '<Excludes i:nil="true"/><Includes>' + member.replace('/', '\\') +
                     '.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters>'
                     '<PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>')
        references.append({'member': member + '.bin', 'model': model})
    assert burn.count('</Rules>') == 1
    (source / '_default.burnproj').write_text(burn.replace('</Rules>', ''.join(rules) + '</Rules>'), encoding='utf-8')
    inputs = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    exact = {k: r['sha256'] for k, r in private.items()}
    assert all(inputs[k] == digest for k, digest in exact.items())
    write(reference / 'input-freeze.json', {'inputs': inputs, 'models': models, 'references': references})
    runroot = OUT / ('detail-reference-runs' if kind == 'details' else 'reference-runs') / label
    assert not runroot.exists()
    command = run_logged('reference-' + label, [CORE, 'essence', 'build-mod', '--editor', ART_EDITOR,
                        '--mod', reference / 'reference.aoe4mod', '--run-root', runroot, '--timeout', '900'], timeout=1100)
    state = read(runroot / 'run.json')
    assert state['status'] == 'succeeded' and state['exit_code'] == 0
    archives = list((runroot / 'output').rglob('*.sga'))
    assert len(archives) == 1
    for row in references:
        target = reference / 'readback' / row['member']
        target.parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        subprocess.run([str(ARCH), 'extract-member', str(archives[0]), row['member'], str(target)],
                       capture_output=True, check=True)
        assert [v['model'].replace('\\', '/').lower() for v in native.active_visuals(native.NativeTree(target))] == [row['model'].lower()]
    assert inputs == {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    result = {'status': 'passed', 'archive': str(archives[0]), 'sha256': sha(archives[0]),
              'native_run': state, 'command': command, 'models': models,
              'exact_inputs_sha256': exact, 'all_source_inputs_sha256': inputs,
              'runtime': 'pending client import and fresh match'}
    write(result_path, result)
    print('REFERENCE_040_QUALIFIED', kind, len(models))
    return result


if __name__ == '__main__': qualify(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'landmarks')
