import unittest
from size_projection import project_size


class SizeProjectionTests(unittest.TestCase):
    def test_stock_effort_bytes_are_included_in_the_cap(self):
        result=project_size(198_000_000,1_000_000,100,10_000,stock_bytes=95_000_000)
        self.assertEqual(result['projected_final_zip_bytes'],403_000_000)
        self.assertTrue(result['exceeds_limit'])

    def test_decimal_limit_includes_baseline_voices_and_margin(self):
        result=project_size(198_000_000,1_000_000,100,10_000)
        self.assertEqual(result['projected_final_zip_bytes'],308_000_000)
        self.assertFalse(result['exceeds_limit'])
        self.assertTrue(project_size(198_000_000,2_000_000,100,10_000)['exceeds_limit'])

    def test_empty_or_inconsistent_sample_fails(self):
        for count,required in [(0,1),(2,1)]:
            with self.assertRaises(ValueError):project_size(0,0,count,required)


if __name__=='__main__':unittest.main()
