import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from recover_inputs import Recovery
from store import sha


class RecoveryTests(unittest.TestCase):
    def test_nested_input_restores_exactly_and_preserves_edited_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            external = root/'external'
            source = root/'source'
            source.mkdir()
            folder = external/'resources_071'
            folder.mkdir(parents=True)
            raw = b'editable donor input'
            blob = gzip.compress(raw)
            (folder/'input.gz').write_bytes(blob)
            config = root/'workspace.json'
            config.write_text(json.dumps(dict(source=str(source),external=str(external))))
            docs = {
                'external/resources_071/index.json':dict(files={'E/art/donor.bin':dict(blob='input.gz',codec='gzip',bytes=len(raw),sha256=sha(raw))}),
                'external/resources_080/index.json':dict(files={})}
            class R:
                doc = {'files':{'external/resources_071/input.gz':{'sha256':sha(blob)}}}
                def read(self,key):
                    return json.dumps(docs[key]).encode()
            recovery = Recovery(R(),config)
            target = recovery.recover('source/art/donor.bin')
            self.assertEqual(target.read_bytes(),raw)
            target.write_bytes(b'user edit')
            with self.assertRaisesRegex(ValueError,'Edited'):
                recovery.recover('source/art/donor.bin')
            self.assertEqual(target.read_bytes(),b'user edit')
            changed = sha(b'user edit')
            (source/'relocation-proof.json').write_text(json.dumps({'runs':[{'changed_working_recipes':[
                {'path':str(target),'before':sha(raw),'after':changed}]}]}))
            recovery.recover('source/art/donor.bin')
            self.assertEqual(target.read_bytes(),b'user edit')
            target.write_bytes(b'further edit')
            with self.assertRaisesRegex(ValueError,'Edited'):
                recovery.recover('source/art/donor.bin')
            recovery.close()


if __name__ == '__main__':
    unittest.main()
