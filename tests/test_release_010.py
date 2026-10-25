"""Release source guard rejects gameplay changes hidden among visual edits."""
import sys
import re
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/release_010'))
from source_policy import assert_visual_only


class ReleaseVisualPolicyTests(unittest.TestCase):
    def test_private_identity_headers_use_content_editor_encoding_name(self):
        # ElementTree accepts "utf8", but the native Attribute Editor rejects it.
        root = Path(__file__).resolve().parents[1]
        files = list((root / 'assets/attrib/instances/attachments/attachment_lists/vietnam').glob('vn_*.xml'))
        self.assertEqual(len(files), 7)
        for path in files:
            with self.subTest(path=path.name):
                text = path.read_text(encoding='utf-8-sig')
                declaration = re.match(r'<\?xml\s+[^?]*encoding=[\'"]([^\'"]+)[\'"][^?]*\?>', text)
                self.assertIsNotNone(declaration)
                self.assertEqual(declaration.group(1).lower(), 'utf-8')

    def test_private_attachment_rebinding_is_allowed_and_reported(self):
        before = b'<instance><instance_reference name="attachments" value="stock"/><float name="hitpoints" value="60"/></instance>'
        after = b'<instance><instance_reference name="attachments" value="private" mod="new"/><float name="hitpoints" value="60"/></instance>'
        self.assertEqual(len(assert_visual_only(before, after)), 1)

    def test_cost_or_actor_scale_change_is_rejected_even_with_visual_rebinding(self):
        before = b'<instance><instance_reference name="animator_attachments" value="stock"/><float name="animator_scale" value="75"/></instance>'
        after = b'<instance><instance_reference name="animator_attachments" value="private" mod="new"/><float name="animator_scale" value="100"/></instance>'
        with self.assertRaisesRegex(ValueError, 'Nonvisual'):
            assert_visual_only(before, after)

    def test_removed_tier_requirements_or_changed_list_ids_are_rejected(self):
        before = b'<instance><group name="tier" List.ItemID="1"><instance_reference name="attachments" value="stock"/><bool name="requirement" value="True"/></group></instance>'
        for after in (
            before.replace(b'List.ItemID="1"', b'List.ItemID="2"'),
            before.replace(b'<bool name="requirement" value="True"/>', b''),
        ):
            with self.assertRaisesRegex(ValueError, 'Nonvisual'):
                assert_visual_only(before, after)


if __name__ == '__main__':
    unittest.main()
