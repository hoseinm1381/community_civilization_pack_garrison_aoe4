import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import files


class CompleteInventoryTests(unittest.TestCase):
    def test_archive_and_active_source_include_private_release_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);relative='attrib/attachments/attachment_lists/vietnam/release_060/private.rgd'
            path=root/relative;path.parent.mkdir(parents=True);path.write_bytes(b'private native payload')
            complete=files(root,reject_links=True,exclude_release_060=False)
            self.assertEqual(set(complete),{relative})
            self.assertEqual(complete[relative]['bytes'],len(b'private native payload'))

    def test_historical_preservation_scan_still_excludes_new_owned_art(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'release_060').mkdir();(root/'release_060/new.blend').write_bytes(b'new')
            (root/'older.blend').write_bytes(b'preserved')
            self.assertEqual(set(files(root,reject_links=True)),{'older.blend'})


if __name__=='__main__':unittest.main()
