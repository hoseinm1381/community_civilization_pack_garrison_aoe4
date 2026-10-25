import unittest
from effort_probe import nonverbal_matches


class EffortTests(unittest.TestCase):
    def test_only_empty_or_nonlexical_interjections_pass(self):
        for text in ['', 'À.', 'Hự!', 'Huh! Huh!', '(groans)']:
            self.assertTrue(nonverbal_matches(text),text)
        for text in ['Say grunt.', 'Có tôi đây.', 'Tôi đau quá.']:
            self.assertFalse(nonverbal_matches(text),text)


if __name__=='__main__':unittest.main()
