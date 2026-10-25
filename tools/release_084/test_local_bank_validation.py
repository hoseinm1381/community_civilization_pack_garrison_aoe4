import copy
import unittest

from local_bank_validation import validate_structure, coverage


def fixture():
    jobs=[dict(id=f'{n}-{take}',role='CIV_M',age='A1',event='select',phrase_number=n,take=take)
          for n in range(1,7) for take in ['T1','T2','T3']]
    aliases=[dict(id='alias-'+j['id'],job=j['id'],role='CIV_M',age='A1',event='select') for j in jobs]
    return dict(jobs=jobs,aliases=aliases,pools=[dict(role='CIV_M',age='A1',event='select',jobs=[j['id'] for j in jobs])])


class BankValidationTests(unittest.TestCase):
    def test_cloud_ids_missing_alternatives_and_cross_role_references_are_rejected(self):
        source=fixture()
        validate_structure(source)
        for mutate in [lambda m:m['pools'][0]['jobs'].__setitem__(0,'cloud'),
                       lambda m:m['pools'][0]['jobs'].pop(),
                       lambda m:m['aliases'][0].update(role='MONK'),
                       lambda m:m['jobs'][0].update(phrase_number=2)]:
            changed=copy.deepcopy(source);mutate(changed)
            with self.assertRaises(ValueError):validate_structure(changed)

    def test_partial_coverage_cannot_activate_a_bank(self):
        source=fixture();keys=[j['id'] for j in source['jobs']]
        partial=coverage(source,set(keys[:-1]))
        self.assertFalse(partial['technical_coverage_complete'])
        self.assertEqual(partial['complete_pools'],0)
        self.assertEqual(partial['missing_jobs'],[keys[-1]])
        self.assertTrue(coverage(source,set(keys))['technical_coverage_complete'])

    def test_shared_effort_can_cover_multiple_ages_but_not_another_role(self):
        source=fixture()
        for j in source['jobs']:j['age']='ANY'
        pool=copy.deepcopy(source['pools'][0]);pool['age']='A2';source['pools'].append(pool)
        source['aliases'] += [dict(a,id=a['id']+'-A2',age='A2') for a in list(source['aliases'])]
        validate_structure(source)


if __name__=='__main__':unittest.main()
