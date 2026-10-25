import json,tempfile,unittest
from unittest.mock import patch
import budget
from providers import ProviderError
class BudgetTests(unittest.TestCase):
    def test_chooses_only_account_with_existing_balance(self):
        responses=[(json.dumps(dict(character_limit=100,character_count=99,can_extend_character_limit=False)).encode(),{}),(json.dumps(dict(character_limit=100,character_count=10,can_extend_character_limit=False)).encode(),{})]
        with patch('budget.request',side_effect=responses),patch('budget.save_json'):
            self.assertEqual(budget.account_for(dict(elevenlabs='a',elevenlabs_accounts=['a','b']),20),'b')
    def test_insufficient_credits_and_overages_stop(self):
        for extend,error in [(False,ProviderError),(True,ValueError)]:
            raw=json.dumps(dict(character_limit=100,character_count=100,can_extend_character_limit=extend)).encode()
            with patch('budget.request',return_value=(raw,{})),patch('budget.save_json'):
                with self.assertRaises(error):budget.account_for(dict(elevenlabs='a'),1)
if __name__=='__main__':unittest.main()
