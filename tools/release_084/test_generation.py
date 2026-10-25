import unittest
from generation import segment_transcripts, status_counts


class GenerationTests(unittest.TestCase):
    def test_words_are_assigned_by_timestamps_without_prompt_injection(self):
        spans=[dict(id='a',start=0,end=1,text='Có tôi đây.'),dict(id='b',start=1.5,end=2.5,text='Tôi đi ngay.')]
        words=[dict(type='word',text='Có',start=0,end=.1),dict(type='word',text='tôi',start=.2,end=.3),
               dict(type='word',text='đây.',start=.4,end=.5),dict(type='word',text='Đi',start=1.6,end=1.8),
               dict(type='word',text='ngay.',start=2,end=2.2)]
        result=segment_transcripts(spans,dict(words=words,text='Có tôi đây. Đi ngay.'))
        self.assertTrue(result['a']['match'])
        self.assertFalse(result['b']['match'])

    def test_pending_and_failed_are_never_complete(self):
        self.assertEqual(status_counts(['a','b','c'],{'a':True},{'b':3}),dict(accepted=1,exhausted_retakes=1,pending=1,total=3))


if __name__=='__main__':unittest.main()
