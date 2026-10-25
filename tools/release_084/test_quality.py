import unittest
from quality import text_matches, select_casting


class QualityTests(unittest.TestCase):
    def test_transcript_must_not_drop_or_add_words(self):
        self.assertTrue(text_matches('Có tôi đây.', 'Có tôi đây!'))
        self.assertFalse(text_matches('Tôi đi ngay.', 'Đi ngay.'))
        self.assertFalse(text_matches('Có tôi đây.', 'Speak Vietnamese. Có tôi đây.'))
        self.assertFalse(text_matches('Tôi đi ngay.', 'Tôi đi ngày.'))

    def test_casting_requires_each_configured_system_voice(self):
        with self.assertRaises(ValueError):
            select_casting([])


if __name__ == '__main__':
    unittest.main()
