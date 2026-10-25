import unittest


class ReleaseGateTests(unittest.TestCase):
    def test_windows_bank_file_is_exact_utf8_with_lf(self):
        import tempfile
        from pathlib import Path
        from voice_bank import write_bank,lua_value
        bank={'complete':True,'clips':{}}
        expected=('-- Generated Vietnamese presentation-only voice bank.\nVietnamVoiceBank='+lua_value(bank)+'\n').encode('utf-8')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'bank.scar';write_bank(path,bank)
            self.assertEqual(path.read_bytes(),expected)

    def test_same_manifest_and_count_do_not_allow_stale_audio_hashes(self):
        from assemble_release import require_bank_coherence
        from test_local_bank_validation import fixture
        from voice_bank import compose_bank,lua_value
        manifest=fixture()
        old={j['id']:dict(sha256=j['id'],duration=1,member='audio/voices/'+j['id']+'.ogg') for j in manifest['jobs']}
        fresh={k:dict(v) for k,v in old.items()}
        fresh['1-T1'].update(sha256='replacement',member='audio/voices/replacement.ogg')
        scar=lambda recordings:lua_value(compose_bank(manifest,recordings,[],{},'owner')).encode()
        payload={r['member']:dict(sha256=r['sha256']) for r in old.values()}
        require_bank_coherence(scar(old),scar(old),payload,old)
        with self.assertRaises(RuntimeError):require_bank_coherence(scar(old),scar(fresh),payload,fresh)

    def test_missing_audio_or_partial_overlay_cannot_be_a_full_release(self):
        from assemble_release import require_complete
        audio=dict(technical_coverage_complete=True,errors={},verified_jobs=18,required_jobs=18)
        bank=dict(complete=True,partial_preview=False,verified_recordings=18,codec='vorbis-64k-mono-48k')
        overlay=dict(plan_only=False)
        require_complete(audio,bank,overlay)
        for changed in [dict(audio,technical_coverage_complete=False),dict(audio,verified_jobs=17),dict(audio,errors={'x':'bad'})]:
            with self.assertRaises(RuntimeError):require_complete(changed,bank,overlay)
        with self.assertRaises(RuntimeError):require_complete(audio,dict(bank,partial_preview=True),overlay)
        with self.assertRaises(RuntimeError):require_complete(audio,bank,dict(plan_only=True))


if __name__=='__main__':unittest.main()
