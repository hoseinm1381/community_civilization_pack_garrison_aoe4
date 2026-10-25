"""Fresh native Reflect qualification of every exact final private model input."""
import hashlib
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from common import ARCH, ART_EDITOR, CONFIG, CORE, OUT, guarded, read, run_logged, sha, write
from inventory import native

sys.dont_write_bytecode = True
WORK = OUT / 'integration'


def qualify(label):
    guarded()
    assert re.fullmatch(r'cc020ref[a-z0-9]{2,18}', label)
    reference = OUT / 'reference-cook' / label
    assert not reference.exists(), 'Keep prior native reference evidence; retry with a new label'
    media = read(WORK / 'media-020.json')
    assert media['status'] == 'passed'
    models = media['models']
    assert len(models) == len(set(models)) and models
    rows = media['payloads']
    private = {r['member']: r for r in rows if r['member'].startswith('art/scenario/cc020/')}
    assert len(private) == sum(r['member'].startswith('art/scenario/cc020/') for r in rows)
    for row in private.values(): assert sha(row['file']) == row['sha256']
    art_cook = read(read(OUT / 'art-cook/cook-pointer.json')['receipt'])
    assert art_cook['status'] == 'passed'
    template = Path(art_cook['project']) / 'project'
    original = template / 'source/art/stamps/garrison/community_020_art/vn020_ministry.rdo'
    assert original.is_file()
    mod_files = list(template.glob('*.aoe4mod'))
    assert len(mod_files) == 1
    reference.mkdir(parents=True)
    shutil.copy2(mod_files[0], reference / 'reference.aoe4mod')
    source = reference / 'source'
    source.mkdir()
    for row in private.values():
        target = source / row['member']; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row['file'], target)
        if target.suffix == '.rrmaterial': shutil.copy2(target, target.with_suffix('.material'))
    burn = (template / 'source/_default.burnproj').read_text(encoding='utf-8-sig')
    burn = re.sub(r'<BurnRule>.*?</BurnRule>',
                  lambda m: m[0].replace('<IsEnabled>true</IsEnabled>', '<IsEnabled>false</IsEnabled>'),
                  burn, flags=re.S)
    rules, references = [], []
    for index, model in enumerate(models):
        doc = ET.parse(original); root = doc.getroot()
        ids = {node.get('Id'): str(int.from_bytes(hashlib.sha256(
            ('cc020:reference:' + str(index) + ':' + node.get('Id')).encode()).digest()[:8], 'little'))
               for node in root.iter('DataObject')}
        for node in root.iter():
            for key in ('Id', 'OwnerId'):
                if node.get(key) in ids: node.set(key, ids[node.get(key)])
            if node.tag == 'DataValue' and node.text in ids: node.text = ids[node.text]
            if node.tag == 'DataProperty' and node.get('Name') == 'm_objectID' and node.get('Value') in ids:
                node.set('Value', ids[node.get('Value')])
            if node.tag == 'DataProperty' and node.get('Name') == 'm_blueprint':
                node.set('Value', model.replace('/', '\\'))
        member = f'art/stamps/cc020/reference_{index}'
        target = source / (member + '.rdo'); target.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root); target.write_bytes(ET.tostring(root, encoding='utf-8', xml_declaration=True))
        rules.append('<BurnRule><Alias>data</Alias><Burner>ReflectBurner</Burner>'
                     '<Configurations>Debug Release Profile RTM</Configurations>'
                     '<Excludes i:nil="true"/><Includes>' + member.replace('/', '\\') +
                     '.rdo</Includes><IsEnabled>true</IsEnabled><NamedParameters>Reflect</NamedParameters>'
                     '<PathOverride i:nil="true"/><Target>Archive</Target></BurnRule>')
        references.append({'member': member + '.bin', 'model': model})
    assert burn.count('</Rules>') == 1
    (source / '_default.burnproj').write_text(burn.replace('</Rules>', ''.join(rules) + '</Rules>'),
                                             encoding='utf-8')
    inputs = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    exact = {key: row['sha256'] for key, row in private.items()}
    assert all(inputs[key] == digest for key, digest in exact.items())
    write(reference / 'input-freeze.json', {'inputs': inputs, 'models': models,
                                            'references': references, 'source': str(source)})
    # The supported CLI requires its run directory outside the source mod root.
    runroot = OUT / 'reference-runs' / label
    assert not runroot.exists(), 'Preserve previous native run; use a new label'
    command = run_logged('reference-020-' + label, [CORE, 'essence', 'build-mod', '--editor', ART_EDITOR,
                          '--mod', reference / 'reference.aoe4mod', '--run-root', runroot, '--timeout', '900'])
    state = read(runroot / 'run.json')
    assert state['status'] == 'succeeded' and state['exit_code'] == 0
    archives = list((runroot / 'output').rglob('*.sga'))
    assert len(archives) == 1
    for row in references:
        target = reference / 'readback' / row['member']; target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run([str(ARCH), 'extract-member', str(archives[0]), row['member'],
                                 str(target)], capture_output=True, text=True,
                                encoding='utf-8', errors='replace')
        if result.returncode: raise RuntimeError(result.stdout + result.stderr)
        assert [v['model'].replace('\\', '/').lower() for v in native.active_visuals(native.NativeTree(target))] == [row['model'].lower()]
    assert inputs == {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
    receipt = {'status': 'passed', 'archive': str(archives[0]), 'sha256': sha(archives[0]),
               'native_run': state, 'command': command, 'models': models,
               'exact_inputs_sha256': exact, 'all_source_inputs_sha256': inputs,
               'limitation': 'Final native stamp copies retain donor marker and functional records; native match appearance remains unverified.'}
    write(reference / 'receipt.json', receipt)
    write(WORK / 'reference-cook.json', receipt)
    print('FINAL_020_MODELS_NATIVE_REFERENCE_QUALIFIED', len(models))
    return receipt


if __name__ == '__main__': qualify(sys.argv[1])
