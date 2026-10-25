import tempfile
from pathlib import Path
import unittest
import os

from exclusive_job import exclusive_job


@unittest.skipUnless(os.name=='nt','Windows memory-heavy job serialization')
class ExclusiveJobTests(unittest.TestCase):
    def test_native_and_local_workers_cannot_overlap_and_lock_releases_on_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'memory-job.lock'
            with self.assertRaisesRegex(ValueError,'work failed'):
                with exclusive_job('native cook',path):
                    with self.assertRaisesRegex(RuntimeError,'already running'):
                        with exclusive_job('local GPU worker',path):pass
                    raise ValueError('work failed')
            with exclusive_job('resumed GPU worker',path):pass


if __name__=='__main__':unittest.main()
