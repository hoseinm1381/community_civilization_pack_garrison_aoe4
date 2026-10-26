import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import check_extension_inheritance as check


class ActualSourceInheritanceTests(unittest.TestCase):
    def test_actual_source_and_normalized_private_import_preserve_valid_inheritance(self):
        fixtures=Path(__file__).parent/'fixtures'
        official=json.loads((fixtures/'official_parent_extensions.json').read_text())['records']
        old=check.summarize((fixtures/'inheritance_pre_repair.xml').read_bytes())
        new=check.summarize((ROOT/'assets/attrib/instances/ebps/persia/ps_unit_villager_1_sul.xml').read_bytes())
        self.assertEqual(check.Resolver({'ebps\\persia\\original_villager':old},official).audit(),[])
        self.assertEqual(check.Resolver({'ebps\\persia\\new_villager':new},official).audit(),[])


if __name__=='__main__':unittest.main()
