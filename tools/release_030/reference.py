"""Fresh native Reflect cook of the exact 0.3.0 private model quartet."""
import hashlib
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ROOT, OUT, ARCH, ART_EDITOR, CORE, guarded, read, run_logged, sha, write
from inventory import native
from bindings import WORK, MODEL_STEMS


def qualify(label):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}', label)
    media = read(WORK / 'media.json')
    models = media['models']
    assert set(models) == set(MODEL_STEMS.values()) | {
        'art/scenario/cc010/t1/model', 'art/scenario/cc010/t2/model'}
    rows = media['payloads']
    private = {r['member']: r for r in rows if r['member'].startswith(('art/scenario/cc010/', 'art/scenario/cc030/'))}
    assert all(sha(r['file']) == r['sha256'] for r in private.values())
    cooked = read(read(OUT / 'art-cook-pointer.json')['receipt'])
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    project = Path(cooked['project']) / 'project'
    reference = OUT / 'reference-cook' / label
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
    for model, owner in media['native_rgo'].items():
        target = source / (model + '.rgo')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(owner['file'], target)
        assert sha(target) == owner['sha256']
    original = project / 'source/art/stamps/garrison/community_030_art/pho_minh.rdo'
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
            ('cc030:reference:' + str(index) + ':' + node.get('Id')).encode()).digest()[:8], 'little'))
               for node in root.iter('DataObject')}
        for node in root.iter():
            for key in ('Id', 'OwnerId'):
                if node.get(key) in ids: node.set(key, ids[node.get(key)])
            if node.tag == 'DataValue' and node.text in ids: node.text = ids[node.text]
            if node.tag == 'DataProperty' and node.get('Name') == 'm_objectID' and node.get('Value') in ids:
                node.set('Value', ids[node.get('Value')])
            if node.tag == 'DataProperty' and node.get('Name') == 'm_blueprint':
                node.set('Value', model.replace('/', '\\'))
        member = f'art/stamps/cc030/reference_{index}'
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
    runroot = OUT / 'reference-runs' / label
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
    write(WORK / 'reference-cook.json', result)
    print('REFERENCE_030_QUALIFIED', len(models))
    return result


if __name__ == '__main__': qualify(sys.argv[1])
