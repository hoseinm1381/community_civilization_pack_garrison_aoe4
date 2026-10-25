import unittest
from prepare_foot_source_delta import transform, GUID


class NarrowSourceDeltaTests(unittest.TestCase):
    def edit(self,count=1,mod=None):
        return {'field':'attachments','before':'attachments\\body',
                'before_mod':mod,'after':'attachments\\vietnam\\private',
                'expected_count':count}

    def test_visual_tag_only_preserves_gameplay_and_whitespace(self):
        original=(b'<instance>\r\n\t<instance_reference name="attachments" value="attachments\\body"/>\r\n'
                  b' <string name="note" value="attachments\\body"/><float name="health" value="100"/></instance>')
        actual,proof=transform(original,[self.edit()])
        self.assertIn(b'<float name="health" value="100"/>',actual)
        self.assertIn(b'<string name="note" value="attachments\\body"/>',actual)
        self.assertIn(b'\r\n\t',actual)
        self.assertIn(('mod="'+GUID+'"').encode(),actual)
        self.assertEqual(len(proof),1)

    def test_wrong_count_rejected(self):
        with self.assertRaises(ValueError):
            transform(b'<instance><instance_reference name="attachments" value="attachments\\body"/></instance>',
                      [self.edit(2)])

    def test_foreign_owner_rejected(self):
        with self.assertRaises(ValueError):
            transform(b'<instance><instance_reference name="attachments" value="attachments\\body" mod="foreign"/></instance>',
                      [self.edit()])


if __name__=='__main__':unittest.main()
