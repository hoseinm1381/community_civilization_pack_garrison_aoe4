"""Fail-closed source hash check and installed unit-prototype validator."""
import json
import subprocess
from pathlib import Path

from common import CORE, OUT, guard, owned, read, sha, write

SOURCE_RECEIPT = OUT / 'qualification/archer-matched-control-export.json'
LOG = OUT / 'qualification/archer-matched-control-validate.log'
RECEIPT = OUT / 'qualification/archer-matched-control-validate.json'


def main():
    guard()
    owned(LOG); owned(RECEIPT)
    if LOG.exists() or RECEIPT.exists():
        raise FileExistsError('Preserve earlier validation result')
    source = read(SOURCE_RECEIPT)
    if source['schema'] != 'ccp-060-archer-matched-control-export/v1' or source['status'] != 'source_export_only_not_unit_validated_or_cooked':
        raise ValueError('Unexpected source export receipt')
    folder = Path(source['folder'])
    if not folder.resolve().is_relative_to((Path(__file__).resolve().parents[2] / 'art/exports/release_060').resolve()):
        raise ValueError('Export is outside owned 0.6.0 directory')
    for name, item in source['files'].items():
        path = folder / name
        if not path.is_file() or path.stat().st_size != item['bytes'] or sha(path) != item['sha256']:
            raise ValueError(f'Export file changed: {path}')
    doc = json.loads((folder / 'action.json').read_text(encoding='utf-8'))
    if (doc.get('prototype') != 'english-spearman-2'
            or doc.get('fingerprint') != source['prototype_fingerprint']
            or doc.get('overrides') != [] or doc.get('attachments') != []
            or len(doc.get('bones', [])) != 48):
        raise ValueError('Source action contract changed')
    command = [str(CORE), 'mod-project', 'unit-validate', '--source', str(folder / 'action.json')]
    result = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=180)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text('COMMAND: ' + ' '.join(command) + '\nEXIT: ' + str(result.returncode)
                   + '\nSTDOUT:\n' + result.stdout + '\nSTDERR:\n' + result.stderr,
                   encoding='utf-8')
    write(RECEIPT, {'schema': 'ccp-060-archer-matched-control-validation/v1',
                    'status': 'passed' if result.returncode == 0 else 'rejected',
                    'source_receipt': str(SOURCE_RECEIPT), 'source_receipt_sha256': sha(SOURCE_RECEIPT),
                    'action_sha256': sha(folder / 'action.json'),
                    'exit_code': result.returncode, 'log': str(LOG), 'log_sha256': sha(LOG),
                    'no_animation_or_attachment_replacements': True})
    print('validator_exit=' + str(result.returncode))
    print(result.stdout[:3000] or result.stderr[:3000])
    if result.returncode:
        raise RuntimeError('Installed unit-validate rejected source; inspect retained log')


if __name__ == '__main__':
    main()
