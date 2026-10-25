import unittest,tempfile,hashlib
from pathlib import Path
from overlay import validate_overlay
class OverlayTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);(self.root/'body.rgm').write_bytes(b'new')
  self.payload={'asset':'buffalo','files':[{'source':'body.rgm','destination':'art/private076/buffalo.rgm','sha256':hashlib.sha256(b'new').hexdigest()}]}
 def tearDown(self):self.tmp.cleanup()
 def test_matching_baseline(self):self.assertEqual(len(validate_overlay(self.root,[self.payload],{},{})),1)
 def test_baseline_drift(self):
  with self.assertRaisesRegex(ValueError,'baseline'):validate_overlay(self.root,[self.payload],{'old':'newhash'},{'old':'oldhash'})
 def test_collision(self):
  with self.assertRaisesRegex(ValueError,'collision'):validate_overlay(self.root,[self.payload,self.payload],{}, {})
 def test_unexpected_overwrite(self):
  with self.assertRaisesRegex(ValueError,'overwrite'):validate_overlay(self.root,[self.payload],{'art/private076/buffalo.rgm':'old'}, {})
 def test_corrupt_payload(self):
  (self.root/'body.rgm').write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'hash'):validate_overlay(self.root,[self.payload],{}, {})
 def test_path_escape(self):
  self.payload['files'][0]['destination']='../outside.rgm'
  with self.assertRaisesRegex(ValueError,'path'):validate_overlay(self.root,[self.payload],{}, {})
 def test_gameplay_payload(self):
  self.payload['files'][0]['destination']='attrib/ebps/actor.rgd'
  with self.assertRaisesRegex(ValueError,'allowlist'):validate_overlay(self.root,[self.payload],{}, {})
if __name__=='__main__':unittest.main()
