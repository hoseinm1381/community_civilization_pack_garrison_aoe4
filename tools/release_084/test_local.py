import copy
import unittest
from pathlib import Path
import tempfile
import os


class LocalBankTests(unittest.TestCase):
    def test_local_manifest_remaps_pools_and_aliases_without_changing_cloud_source(self):
        from local_bank import local_manifest
        source=dict(jobs=[dict(id='cloud',role='CIV_M',age='A1',text='A',take='T1')],
                    aliases=[dict(job='cloud')],pools=[dict(jobs=['cloud'])])
        before=copy.deepcopy(source)
        result=local_manifest(source,{'CIV_M':'Actor'})
        local=result['jobs'][0]['id']
        self.assertNotEqual(local,'cloud')
        self.assertEqual(result['aliases'][0]['job'],local)
        self.assertEqual(result['pools'][0]['jobs'],[local])
        self.assertEqual(source,before)

    @unittest.skipUnless(os.name == 'nt', 'Windows file sharing regression')
    def test_atomic_checkpoint_survives_a_brief_windows_reader_lock(self):
        import ctypes
        from ctypes import wintypes
        import threading
        import json
        from pipeline import save_json
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'checkpoint.json';save_json(path,{'count':1})
            handle = kernel.CreateFileW(str(path),0x80000000,3,None,3,0x80,None)
            if handle == ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
            release = threading.Timer(.15,lambda:kernel.CloseHandle(handle));release.start()
            try: save_json(path,{'count':2})
            finally: release.join()
            self.assertEqual(json.loads(path.read_text()),{'count':2})

    def test_new_bank_never_reuses_cloud_job_ids_and_locks_actor_across_ages(self):
        from local_bank import local_jobs
        source = [{'id': 'paid1', 'role': 'CIV_M', 'age': 'A1', 'text': 'A', 'take': 'T1'},
                  {'id': 'paid2', 'role': 'CIV_M', 'age': 'A4', 'text': 'B', 'take': 'T2'}]
        before = copy.deepcopy(source)
        jobs = local_jobs(source, {'CIV_M': 'Hải Đăng'}, 'pinned-revision')
        self.assertEqual(source, before)
        self.assertEqual(jobs[0]['casting'], jobs[1]['casting'])
        self.assertTrue(all(j['id'] != s['id'] for j, s in zip(jobs, source)))
        self.assertEqual(jobs, local_jobs(source, {'CIV_M': 'Hải Đăng'}, 'pinned-revision'))
        self.assertNotEqual(jobs[0]['id'], local_jobs(source, {'CIV_M': 'Quốc Tuấn'}, 'pinned-revision')[0]['id'])

    def test_independent_take_seeds_and_bounded_retakes(self):
        from local_bank import take_seed
        seeds = {take_seed('job', n) for n in range(3)}
        self.assertEqual(len(seeds), 3)
        self.assertEqual(take_seed('job', 1), take_seed('job', 1))
        with self.assertRaises(ValueError): take_seed('job', 3)

    def test_resume_rechecks_audio_bytes(self):
        from pipeline import StateStore
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'audio.wav'
            p.write_bytes(b'original')
            store = StateStore(tmp)
            store.complete('job', p, {})
            self.assertTrue(store.ready('job'))
            p.write_bytes(b'corrupted')
            self.assertFalse(store.ready('job'))

    def test_interrupted_original_container_is_rejected_without_overwrite(self):
        import struct
        from local_work import validate_saved_wave
        from pipeline import AudioError
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'original-float.wav'
            original=b'RIFF'+struct.pack('<I',20)+b'WAVE'+b'data'+struct.pack('<I',8)+b'12345678'
            path.write_bytes(original);validate_saved_wave(path)
            truncated=original[:-1];path.write_bytes(truncated)
            with self.assertRaises(AudioError):validate_saved_wave(path)
            self.assertEqual(path.read_bytes(),truncated)

    def test_nonverbal_instructions_are_not_spoken(self):
        from local_bank import synthesis_text
        self.assertEqual(synthesis_text(dict(kind='dialogue', text='Tiến lên!')), 'Tiến lên!')
        with self.assertRaises(ValueError):
            synthesis_text(dict(kind='nonverbal_effort', text='[groan]'))

    def test_model_download_selection_excludes_other_backends(self):
        from download_local_models import selected_file
        self.assertTrue(selected_file('vieneu', 'update/model.safetensors'))
        self.assertTrue(selected_file('vieneu', 'speaker_encoder.onnx'))
        self.assertFalse(selected_file('vieneu', 'onnx/vieneu_backbone_shared.data'))
        self.assertFalse(selected_file('vieneu', 'gguf/vieneu-v3-turbo-bf16.gguf'))

    def test_one_good_context_does_not_qualify_a_role(self):
        from local_bank import text_qualified_roles
        results = {f'CIV_M-calm-T{take}': {'text_match': True} for take in range(1, 4)}
        self.assertEqual(text_qualified_roles(results, ['CIV_M']), set())
        for context in ['urgent', 'quiet']:
            for take in range(1, 3): results[f'CIV_M-{context}-T{take}'] = {'text_match': True}
        self.assertEqual(text_qualified_roles(results, ['CIV_M', 'MONK']), {'CIV_M'})

    def test_local_aliases_resolve_to_new_jobs(self):
        from local_bank import local_manifest
        source = {'jobs': [{'id': 'paid', 'role': 'CIV_M', 'age': 'A1', 'text': 'A', 'take': 'T1'}],
                  'aliases': [{'job': 'paid', 'reason': 'direct'}]}
        result = local_manifest(source)
        self.assertEqual(result['aliases'][0]['job'], result['jobs'][0]['id'])
        self.assertEqual(source['aliases'][0]['job'], 'paid')

    def test_changed_model_file_is_rejected(self):
        from local_inputs import verify_files
        from pipeline import digest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); p = root / 'model.bin'; p.write_bytes(b'original')
            files = [{'file': 'model.bin', 'sha256': digest(p)}]
            verify_files(root, files)
            p.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): verify_files(root, files)

    def test_saved_asr_cannot_qualify_corrupted_or_recast_auditions(self):
        from local_inputs import validated_audition_results
        from pipeline import StateStore
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root / 'clip.wav'; path.write_bytes(b'example')
            store = StateStore(root)
            meta = dict(role='CIV_M',voice='Hải Đăng',context='calm',take=1,text='Có tôi đây.',input_fingerprint='pinned')
            store.complete('CIV_M-calm-T1', path, meta)
            results={'CIV_M-calm-T1':dict(sha256=store.data['CIV_M-calm-T1']['sha256'], expected=meta['text'],text_match=True)}
            self.assertEqual(len(validated_audition_results(results,store,{'CIV_M':'Hải Đăng'},'pinned')),1)
            self.assertFalse(validated_audition_results(results,store,{'CIV_M':'Other'},'pinned'))
            self.assertFalse(validated_audition_results(results,store,{'CIV_M':'Hải Đăng'},'new-model'))
            path.write_bytes(b'corrupt')
            self.assertFalse(validated_audition_results(results,store,{'CIV_M':'Hải Đăng'},'pinned'))

    def test_interrupted_saved_take_is_recovered_before_allocating_new_take(self):
        from local_work import attempt_plan
        from pipeline import save_json
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); folder = root / 'attempt-1'; folder.mkdir()
            job = {'id':'one'}
            save_json(folder/'request-started.json',dict(job=job,input_fingerprint='pinned'))
            original = folder/'original-float.wav'; original.write_bytes(b'saved recording')
            planned = list(attempt_plan(root, 3, job, 'pinned'))
            self.assertEqual(planned, [(0, folder, True)])
            self.assertEqual(original.read_bytes(), b'saved recording')

    def test_attempt_budget_bounds_failed_work_too(self):
        from local_work import WorkBudget
        budget = WorkBudget(2)
        self.assertTrue(budget.reserve())
        self.assertTrue(budget.reserve())
        self.assertFalse(budget.reserve())
        self.assertEqual(budget.used, 2)

    def test_shared_actor_qualification_requires_distinct_audio_in_every_context(self):
        from local_bank import actor_qualified_roles
        voices = {'CIV_M':'Actor', 'TRADER':'Actor'}
        results = {}
        for context in ['calm','urgent','quiet']:
            results[f'CIV_M-{context}-T1'] = dict(text_match=True,sha256=context+'-one')
            results[f'CIV_M-{context}-T2'] = dict(text_match=True,sha256=context+'-one')
        self.assertFalse(actor_qualified_roles(results,voices))
        for context in ['calm','urgent','quiet']:
            results[f'CIV_M-{context}-T2']['sha256'] = context+'-two'
        self.assertEqual(actor_qualified_roles(results,voices),set(voices))

    def test_batched_generations_keep_takes_and_actors_separate(self):
        from local_work import performance_groups
        source = [dict(role='CIV_M',age='A1',event='select',take=take,casting={'voice':'A'},text=text)
                  for take in ['T1','T2','T3'] for text in ['one','two']]
        groups = performance_groups(source)
        self.assertEqual(len(groups),3)
        self.assertTrue(all(len(g)==2 and len({j['take'] for j in g})==1 for g in groups))

    def test_effort_recipes_never_speak_english_directions(self):
        from local_bank import effort_input,performance_text
        cues=set()
        for number in range(1,7):
            job=dict(kind='nonverbal_effort',event='death',phrase_number=number,text='[groan]')
            cue=effort_input(job);cues.add(cue)
            job.update(performance_recipe='phonetic-effort-v1',phonetic_input=cue)
            self.assertEqual(performance_text(job),cue)
            self.assertNotIn('groan',cue)
        self.assertEqual(len(cues),6)
        with self.assertRaises(ValueError):effort_input(dict(kind='dialogue',event='death',phrase_number=1))

    def test_nonverbal_screen_rejects_words_and_long_hallucinations(self):
        from local_efforts import nonlexical
        self.assertTrue(nonlexical('Hự!'))
        self.assertTrue(nonlexical('Ư...'))
        self.assertFalse(nonlexical('Tôi đi ngay.'))
        self.assertFalse(nonlexical('Hãy subscribe cho kênh.'))
        self.assertFalse(nonlexical('ha ha ha ha ha'))
        for ambiguous in ['', 'ở', 'hạ', 'hư']:
            self.assertFalse(nonlexical(ambiguous))

    def test_efforts_require_two_positive_unprompted_screens(self):
        from local_efforts import verified_performance
        job=dict(kind='nonverbal_effort',text='[grunt]')
        proof=dict(expected='[grunt]',prompted=False,phowhisper='Hự',whisper=None)
        self.assertFalse(verified_performance(job,proof))
        proof['whisper']=''
        self.assertFalse(verified_performance(job,proof))
        proof['whisper']='[grunts]'
        self.assertTrue(verified_performance(job,proof))


if __name__ == '__main__': unittest.main()
