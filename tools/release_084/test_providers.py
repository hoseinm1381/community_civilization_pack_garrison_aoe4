import unittest
from providers import retry_delay, eleven_text, eleven_payload


class ProviderTests(unittest.TestCase):
    def test_nonverbal_inputs_contain_only_nonlexical_vowel_anchors(self):
        self.assertEqual(eleven_text('[grunt]'),'[grunts] Hự.')
        self.assertEqual(eleven_text('[groan]'),'[groans] Ah...')
        self.assertEqual(eleven_text('Đi ngay.'),'Đi ngay.')

    def test_effort_directions_are_compact_tags_not_spoken_sentences(self):
        direction='Sudden lost breath; no final words. Small, contained realization of this effort.'
        payload=eleven_payload('[groan]',direction)
        self.assertNotIn('final words',payload)
        self.assertIn('[exhales sharply]',payload)
        self.assertTrue(payload.endswith('Ah...'))
        self.assertEqual(eleven_payload('Đi ngay.','calm'),'[calm] Đi ngay.')

    def test_quota_and_auth_never_retry(self):
        self.assertIsNone(retry_delay(401,{},0,None))
        self.assertIsNone(retry_delay(402,{},0,None))
        self.assertIsNone(retry_delay(429,{'detail':{'status':'quota_exceeded'}},0,'1'))

    def test_rate_limit_respects_server_delay_and_bounded_attempts(self):
        self.assertEqual(retry_delay(429,{},0,'7'),7)
        self.assertIsNone(retry_delay(429,{},0,'90'))
        self.assertIsNone(retry_delay(503,{},2,None))


if __name__=='__main__':unittest.main()
