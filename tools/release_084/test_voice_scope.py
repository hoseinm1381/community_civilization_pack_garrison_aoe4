import copy
import unittest
from test_local_bank_validation import fixture


class VoiceScopeTests(unittest.TestCase):
    def test_spoken_scope_retains_recording_ids_and_original_manifest(self):
        from voice_scope import spoken_manifest
        source=fixture()
        for job in source['jobs']:job['kind']='dialogue'
        extra=copy.deepcopy(source)
        for job in extra['jobs']:
            job.update(id='effort-'+job['id'],event='death',kind='nonverbal_effort')
        for alias in extra['aliases']:
            alias.update(id='effort-'+alias['id'],job='effort-'+alias['job'],event='death')
        for pool in extra['pools']:
            pool.update(event='death',jobs=['effort-'+key for key in pool['jobs']])
        mixed={key:source[key]+extra[key] for key in ['jobs','aliases','pools']}
        saved=copy.deepcopy(mixed)
        self.assertEqual(spoken_manifest(mixed),source)
        self.assertEqual(mixed,saved)

    def test_unknown_or_mixed_pool_cannot_silently_disappear(self):
        from voice_scope import spoken_manifest
        source=fixture()
        for job in source['jobs']:job['kind']='dialogue'
        source['jobs'][0]['kind']='nonverbal_effort'
        with self.assertRaises(ValueError):spoken_manifest(source)


if __name__=='__main__':unittest.main()
