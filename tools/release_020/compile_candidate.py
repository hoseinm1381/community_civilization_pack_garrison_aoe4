"""Compile an isolated copy of the 0.2.0 Content Editor source."""
import json
import re
import shutil
import sys
from pathlib import Path
from common import CONFIG, EDITOR, OUT, ROOT, guarded, read, run_logged, sha, write
from source_policy import verify as verify_sources
from guard_source_contract import verify as verify_source_graph

sys.dont_write_bytecode = True
WORK = OUT / 'integration'


def compile_candidate(label):
    guarded()
    assert re.fullmatch(r'[a-z][a-z0-9-]{2,30}', label)
    identities = read(WORK / 'registered-identities.json')
    proof = verify_sources([row['source'] for row in identities])
    assert verify_source_graph()['source_assets_sha256'] == proof['source_assets_sha256']
    source = WORK / 'candidate-sources' / label
    if source.exists(): raise ValueError(f'Candidate source already exists: {source}')
    source.mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', source / 'assets')
    shutil.copy2(ROOT / CONFIG['project_file'], source / CONFIG['project_file'])
    before = {p.relative_to(source / 'assets').as_posix(): sha(p)
              for p in (source / 'assets').rglob('*') if p.is_file()}
    assert before == proof['source_assets_sha256']
    write(WORK / f'candidate-input-{label}.json', {'source_assets_sha256': before,
                                                    'project_sha256': sha(source / CONFIG['project_file']),
                                                    'source_preservation': proof})
    target = WORK / 'candidate-builds' / label
    command = run_logged(f'candidate-020-{label}', [EDITOR, '-rtm', '--safe_settings',
        '--do_not_restore', '--quiet_crash_report', '--no_source_control',
        '--log_path', WORK / f'candidate-logs-{label}', '--build_mod', source / CONFIG['project_file'],
        '--build_path', target, '--no_burn_window', '--burn_cache_type', 'Local',
        '--burn_max_threads', '1', '--burn_platform', 'PC',
        '--burn_log_path', WORK / f'candidate-burn-{label}.log',
        '--intermediate_path', WORK / f'candidate-intermediate-{label}'], cwd=EDITOR.parent, timeout=1800)
    output = Path(command['log']).read_text(encoding='utf-8', errors='replace')
    errors = [line for line in output.splitlines() if 'EssenceEditor.exe Error:' in line or 'System does not support' in line]
    missing = [line for line in output.splitlines() if str(source).lower() in line.lower()
               and ("doesn't exist" in line or 'does not exist' in line)]
    validated = [int(m.group(1)) for m in re.finditer(r'(\d+) instances validated', output)]
    expected_instances = len(list((source / 'assets/attrib/instances').rglob('*.xml')))
    assert expected_instances == 255
    assert not errors and not missing and validated and validated[-1] == expected_instances, (errors, missing, validated, expected_instances)
    archives = list(target.rglob('*.sga'))
    assert len(archives) == 1, archives
    assert before == {p.relative_to(source / 'assets').as_posix(): sha(p)
                      for p in (source / 'assets').rglob('*') if p.is_file()}
    result = {'status': 'passed', 'label': label, 'source': str(source),
              'archive': str(archives[0]), 'sha256': sha(archives[0]),
              'native_validated_instances': validated[-1], 'native_errors': errors,
              'native_missing_references': missing, 'source_preservation': proof,
              'command': command, 'runtime': 'unverified'}
    write(WORK / f'candidate-build-{label}.json', result)
    write(WORK / 'candidate-build-pointer.json', {'label': label,
              'receipt': str(WORK / f'candidate-build-{label}.json')})
    print('NATIVE_CANDIDATE_SOURCE_COMPILED', validated[-1], sha(archives[0]))
    return result


if __name__ == '__main__':
    compile_candidate(sys.argv[1])
