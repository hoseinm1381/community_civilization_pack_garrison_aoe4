"""Cook the optional 24 native roof albedo carriers after frozen input audit."""
import sys
from pathlib import Path
from common import GUID, OUT, ROOT, guarded, read, sha, write
from inventory import native

sys.dont_write_bytecode = True
WORK = OUT / 'barracks_tc'
PROJECT = WORK / 'library/Mods/community_civilization_pack'


def verify_inputs():
    guarded()
    ready = read(WORK / 'materials-ready.json')
    assert ready['schema'] == 'ccp.barracks-tc-roof-carriers/v1' and len(ready['models']) == 8
    project = read(PROJECT / 'mod-project.json')
    assert project['mod_id'] == GUID and project['release']['version'] == '0.2.0'
    assert project['game_mode']['enabled'] is False and project['game_mode']['live_reload'] is False
    expected = []
    for row in ready['models']:
        for material in row['roof_materials']:
            assert sha(material['source_png']) == material['source_png_sha256']
            assert sha(material['image']) == material['image_sha256']
            assert sha(material['registered_project_input']) == material['registered_project_input_sha256']
            expected.append(material['carrier'])
    actual = {row['name'] for row in project['model_variants']}
    assert len(expected) == 24 and set(expected) <= actual
    return {'status': 'passed', 'materials_ready_sha256': sha(WORK / 'materials-ready.json'),
            'recipe_sha256': sha(ROOT / 'art/recipes/release_020/barracks-tc-materials.json'),
            'project_sha256': sha(PROJECT / 'mod-project.json'), 'carrier_count': len(expected)}


def cook(label):
    assert label.startswith('cc020-roofs-')
    before = verify_inputs()
    write(WORK / 'roof-cook-inputs.json', before)
    native.WORK = WORK
    native.PROJECT = PROJECT
    native.cook(PROJECT, label)
    assert verify_inputs() == before
    receipt = WORK / (label + '-cook.json')
    result = read(receipt)
    write(WORK / 'roof-cook-pointer.json', {'receipt': str(receipt),
                                           'archive_sha256': result['cook']['sha256'],
                                           'inputs_sha256': sha(WORK / 'roof-cook-inputs.json')})
    print('ROOF_CARRIERS_NATIVE_COOKED', len(result['cook']['model_variants']))


if __name__ == '__main__': cook(sys.argv[1])
