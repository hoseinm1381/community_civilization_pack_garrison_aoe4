import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import minor_exceptions as m
from pipeline import digest,save_json


class Exceptions(unittest.TestCase):
    def test_exact_exception_identity_and_integrity(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);manifest=root/'recording-manifest.json';manifest.write_text('{}')
            job=dict(id='one',kind='dialogue',text='approved')
            row=dict(path='candidate.wav',sha256='audio',metadata=dict(transcription={'actual':'minor'},
                     request_sha256='request',original_sha256='original'))
            receipt=root/'exceptions.json'
            entry=dict(job=job,path=row['path'],sha256=row['sha256'],**row['metadata'])
            save_json(receipt,dict(authorization=m.AUTHORIZATION,manifest_sha256=digest(manifest),recordings={'one':entry}))
            row['metadata']['minor_speech_exception']=dict(receipt_sha256=digest(receipt))
            with patch.object(m,'BANK',root),patch.object(m,'RECEIPT',receipt):
                self.assertTrue(m.valid_exception(row,job))
                self.assertFalse(m.valid_exception(row,dict(job,id='another')))
                row['sha256']='changed';self.assertFalse(m.valid_exception(row,job));row['sha256']='audio'
                row['metadata']['transcription']={'actual':'unrelated'}
                self.assertFalse(m.valid_exception(row,job))
                row['metadata']['transcription']={'actual':'minor'}
                manifest.write_text('{"changed":true}')
                self.assertFalse(m.valid_exception(row,job))

    def test_unattested_mismatch_rejected(self):
        self.assertFalse(m.valid_exception({'metadata':{}},{'id':'one'}))
