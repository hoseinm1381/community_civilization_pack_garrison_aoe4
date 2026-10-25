"""Serialize local GPU models and native cooks on this 16 GiB authoring machine."""
from contextlib import contextmanager
from pathlib import Path
import msvcrt

LOCK=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_084/memory-heavy-job.lock')


@contextmanager
def exclusive_job(label,path=LOCK):
    path=Path(path)
    if not path.parent.is_dir():raise RuntimeError('Guarded memory-job directory is unavailable')
    with path.open('a+b') as stream:
        stream.seek(0,2)
        if stream.tell()==0:stream.write(b'0');stream.flush()
        stream.seek(0)
        try:msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as error:
            raise RuntimeError('A memory-heavy job is already running; resume '+label+' after it finishes') from error
        try:yield
        finally:
            stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
