import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import finish_saved_qa
class FinalBudgetTests(unittest.TestCase):
    def test_zero_balance_never_submits_transcription(self):
        response=dict(tier='free',can_extend_character_limit=False,character_limit=10000,character_count=10000)
        with tempfile.TemporaryDirectory() as folder,patch('finish_saved_qa.OUT',Path(folder)),patch('finish_saved_qa.request',return_value=(json.dumps(response).encode(),{})),patch('finish_saved_qa.scribe') as transcribe:
            finish_saved_qa.main('test-placeholder')
            transcribe.assert_not_called()
if __name__=='__main__':unittest.main()
