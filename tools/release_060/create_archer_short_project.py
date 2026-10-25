"""Create one task-owned short-path cook probe while holding the native byte lock."""
import msvcrt
import subprocess
from common import CORE, NATIVE_LOCK, OUT, STAGING, guard, owned, sha, write

LIBRARY = STAGING / 'v'
PROJECT_FILE = LIBRARY / 'Mods/v60av/mod-project.json'
LOG = OUT / 'qualification/archer-variant-short-create.log'
RECEIPT = OUT / 'qualification/archer-variant-short-create.json'


def main():
    guard()
    owned(LIBRARY); owned(LOG); owned(RECEIPT)
    if PROJECT_FILE.exists() or LOG.exists():
        raise FileExistsError('Short project or its creation log already exists; preserve evidence')
    with NATIVE_LOCK.open('r+b') as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            write(RECEIPT, {'status': 'byte_lock_busy_no_mutation', 'error': str(error)})
            raise RuntimeError('Shared native byte lock busy') from error
        try:
            result = subprocess.run([str(CORE), 'mod-project', 'create', '--library',
                                     str(LIBRARY), '--name', 'v60av'],
                                    capture_output=True, text=True, errors='replace', timeout=120)
            LOG.parent.mkdir(parents=True, exist_ok=True)
            LOG.write_text('EXIT: ' + str(result.returncode) + '\nSTDOUT:\n'
                           + result.stdout + '\nSTDERR:\n' + result.stderr,
                           encoding='utf-8')
            write(RECEIPT, {'status': 'created' if result.returncode == 0 else 'failed',
                            'project_file': str(PROJECT_FILE), 'exit_code': result.returncode,
                            'log': str(LOG), 'log_sha256': sha(LOG),
                            'project_file_sha256': sha(PROJECT_FILE) if PROJECT_FILE.is_file() else None,
                            'lock_protocol': 'msvcrt.LK_NBLCK first byte'})
            if result.returncode or not PROJECT_FILE.is_file():
                raise RuntimeError('Short project creation failed; inspect retained log')
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == '__main__':
    main()
