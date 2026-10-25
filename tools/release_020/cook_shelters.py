"""Cook frozen Hideout shelter modules in their own Garrison art project."""
import sys
from pathlib import Path
from common import CONFIG, CORE, OUT, ROOT, guarded, read, sha, write
from integrate import run
from inventory import native

sys.dont_write_bytecode = True
WORK = OUT / 'shelter-cook'
PROJECT = WORK / 'library/Mods/community_020_shelters'
ASSETS = ('shelter_default', 'shelter_stone')


def verify_exports():
    guarded()
    rows = []
    for key in ASSETS:
        recipe_path = ROOT / f'art/recipes/release_020/{key}-source.json'
        recipe = read(recipe_path)
        assert recipe['asset'] == key and recipe['schema'] == 'ccp.020-art-recipe/v1'
        assert sha(recipe['source']) == recipe['source_sha256']
        export = Path(recipe['export'])
        actual = {p.name: sha(p) for p in export.iterdir() if p.is_file()}
        assert actual == recipe['export_files'], (key, actual, recipe['export_files'])
        rows.append({'asset': key, 'recipe': str(recipe_path), 'recipe_sha256': sha(recipe_path),
                     'source': recipe['source'], 'source_sha256': recipe['source_sha256'],
                     'export': str(export), 'export_files': actual})
    return rows


def prepare(label=None):
    rows = verify_exports()
    project = WORK / 'projects' / label / 'library/Mods/community_020_shelters' if label else PROJECT
    assert not label or not project.exists(), 'Preserve prior shelter project; use a new run label'
    suffix = '-' + label if label else ''
    if not (project / 'mod-project.json').exists():
        project.parent.parent.mkdir(parents=True, exist_ok=True)
        run('shelter-020-create' + suffix, [CORE, 'mod-project', 'create', '--library', project.parent.parent, '--name', project.name])
    run('shelter-020-settings' + suffix, [CORE, 'mod-project', 'settings', '--project', project,
                                 '--live-reload', 'off', '--mod-id', CONFIG['project_guid']])
    registered = {r['name'] for r in read(project / 'mod-project.json').get('buildings', [])}
    for row in rows:
        name = 'vn020_' + row['asset']
        if name not in registered:
            run('shelter-020-building-' + row['asset'] + suffix, [CORE, 'mod-project', 'building', '--project', project,
                '--source', row['export'], '--name', name, '--profile', 'english-house', '--integration', 'script'])
    record = read(project / 'mod-project.json')
    assert record['game_mode']['enabled'] is False and record['game_mode']['live_reload'] is False
    for row in rows:
        registered = project / 'project/source/art/scenario/garrison/community_020_shelters/buildings' / ('vn020_' + row['asset'])
        for filename, digest in row['export_files'].items():
            if filename != 'building.json': assert sha(registered / filename) == digest
    frozen_path = WORK / ('frozen-inputs-' + label + '.json' if label else 'frozen-inputs.json')
    write(frozen_path, {'status': 'passed', 'assets': rows,
                        'project': str(project), 'project_sha256': sha(project / 'mod-project.json')})
    write(WORK / 'project-pointer.json', {'project': str(project), 'frozen': str(frozen_path),
                                          'frozen_sha256': sha(frozen_path)})
    print('SHELTER_020_PREPARED', len(rows))


def cook(label):
    assert label.startswith('cc020-shelters-')
    pointer = read(WORK / 'project-pointer.json')
    project = Path(pointer['project'])
    frozen = read(pointer['frozen'])
    assert pointer['frozen_sha256'] == sha(pointer['frozen'])
    assert frozen['status'] == 'passed' and frozen['project'] == str(project)
    assert frozen['project_sha256'] == sha(project / 'mod-project.json')
    assert verify_exports() == frozen['assets']
    native.WORK = WORK
    native.PROJECT = project
    native.cook(project, label)
    write(WORK / 'cook-pointer.json', {'receipt': str(WORK / (label + '-cook.json')),
                                       'frozen': pointer['frozen'], 'frozen_inputs_sha256': pointer['frozen_sha256']})


if __name__ == '__main__':
    if sys.argv[1] == 'prepare': prepare(sys.argv[2] if len(sys.argv) > 2 else None)
    elif sys.argv[1] == 'cook': cook(sys.argv[2])
    else: raise SystemExit('Usage: cook_shelters.py prepare|cook label')
