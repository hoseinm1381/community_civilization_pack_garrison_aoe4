import unittest
from common import OUT, read
from verify_active_source_delta_060 import historical_art_records, source_rows


class SourcePreservationTests(unittest.TestCase):
    def test_historical_art_uses_all_three_actual_category_roots(self):
        groups={'authoring':{'old.blend':{'sha256':'a'}},'exports':{'old.fbx':{'sha256':'b'}},
                'recipes':{'old.json':{'sha256':'c'}}}
        self.assertEqual(set(historical_art_records(groups)),
                         {'authoring/old.blend','exports/old.fbx','recipes/old.json'})

    def test_actual_first_ten_source_selection_is_exact_and_rejects_stale_expected_bytes(self):
        path=OUT/'integration/private-foot-source-overlay/source-delta.json'
        if not path.exists():self.skipTest('Owned staged source fixture unavailable')
        stage=read(path);baseline=read(OUT/'baseline/final053/freeze.json')['inputs']['assets']
        entries,selection=source_rows(stage,baseline)
        self.assertEqual(len(entries),25)
        self.assertEqual(len(selection),25)
        stage['files'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'final053'):source_rows(stage,baseline)


if __name__=='__main__':unittest.main()
