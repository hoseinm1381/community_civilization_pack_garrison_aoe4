"""Regression cases for release preservation, independent of native acceptance."""
import unittest
from verify_archive_delta import compare_maps, require_evidence_area
from pin_final053 import verify_protection
from common import OUT, TOOLS


def record(value):
    return {'sha256':value*64, 'bytes':10}


class ArchiveDeltaTests(unittest.TestCase):
    def test_exact_visual_change_keeps_unrelated_bytes(self):
        before = {'art/model.rrgeom':record('a'), 'attrib/game.rgd':record('b')}
        after = {**before, 'art/model.rrgeom':record('c')}
        result = compare_maps(before, after, [{'member':'art/model.rrgeom',
            'before_sha256':'a'*64, 'after_sha256':'c'*64}], set())
        self.assertEqual(result['unchanged_count'], 1)
        self.assertEqual(result['changed'], ['art/model.rrgeom'])

    def test_unlisted_gameplay_change_is_rejected(self):
        before = {'attrib/game.rgd':record('a')}
        with self.assertRaisesRegex(ValueError, 'allowlist'):
            compare_maps(before, {'attrib/game.rgd':record('b')}, [], set())

    def test_wrong_expected_baseline_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'before'):
            compare_maps({'art/model.rrgeom':record('a')}, {'art/model.rrgeom':record('b')},
                [{'member':'art/model.rrgeom','before_sha256':'c'*64,'after_sha256':'b'*64}], set())

    def test_protected_final053_fix_cannot_be_allowlisted(self):
        with self.assertRaisesRegex(ValueError, 'protected'):
            compare_maps({'attrib/stealth.rgd':record('a')}, {'attrib/stealth.rgd':record('b')},
                [{'member':'attrib/stealth.rgd','before_sha256':'a'*64,'after_sha256':'b'*64}],
                {'attrib/stealth.rgd'})

    def test_declared_addition_accepted_but_removal_refused(self):
        added = [{'member':'art/private.rrgeom','before_sha256':None,'after_sha256':'c'*64}]
        self.assertEqual(compare_maps({}, {'art/private.rrgeom':record('c')}, added, set())['added'],
                         ['art/private.rrgeom'])
        with self.assertRaisesRegex(ValueError, 'removed'):
            compare_maps({'attrib/game.rgd':record('a')}, {}, [], set())

    def test_duplicate_or_unsafe_declarations_refused(self):
        row = {'member':'art/private.rrgeom','before_sha256':None,'after_sha256':'a'*64}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            compare_maps({}, {}, [row,row], set())
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            compare_maps({}, {}, [{**row,'member':'../foreign.rrgeom'}], set())

    def test_evidence_cannot_write_into_editable_tools(self):
        with self.assertRaisesRegex(ValueError, 'qualification'):
            require_evidence_area(TOOLS/'unexpected-readback')
        self.assertEqual(require_evidence_area(OUT/'qualification/new-audit'),
                         OUT/'qualification/new-audit')

    def test_protected_list_is_bound_to_delivered_zip_payloads(self):
        rows = [{'member':f'art/{n}.rrmaterial','sha256':str(n)*64} for n in range(1,5)]
        frozen = {'preserved053_resources':rows, 'archive_members':
                  {r['member']:{'sha256':r['sha256']} for r in rows}}
        verify_protection(frozen, rows)
        with self.assertRaisesRegex(ValueError, 'protected'):
            verify_protection({**frozen,'preserved053_resources':[]}, rows)
        modified = [dict(row) for row in rows]
        modified[0]['sha256'] = '9'*64
        with self.assertRaisesRegex(ValueError, 'protected'):
            verify_protection({**frozen,'preserved053_resources':modified}, rows)


if __name__ == '__main__':
    unittest.main()
