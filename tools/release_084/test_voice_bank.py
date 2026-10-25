import unittest
from test_local_bank_validation import fixture
from voice_bank import compose_bank,lua_value


class VoiceBankTests(unittest.TestCase):
    def test_compressed_paths_are_used_without_pcm_extension_rewrite(self):
        manifest=fixture()
        recordings={j['id']:dict(sha256=j['id'],duration=1,member='audio/voices/'+j['id']+'.ogg') for j in manifest['jobs']}
        bank=compose_bank(manifest,recordings,[],{},'owner')
        self.assertEqual(bank['clips']['CIV_M']['A1']['select'][0][0],'audio/voices/1-T1.ogg')

    def test_phrase_order_changes_words_before_repeating_another_take(self):
        manifest=fixture()
        recordings={j['id']:dict(sha256=j['id'],duration=1.0) for j in manifest['jobs']}
        bank=compose_bank(manifest,recordings,[],{},'owner')
        paths=[x[0] for x in bank['clips']['CIV_M']['A1']['select']]
        self.assertEqual(paths[:6],[f'audio/voices/{n}-T1.wav' for n in range(1,7)])
        self.assertTrue(bank['complete'])
        del recordings['6-T3']
        self.assertFalse(compose_bank(manifest,recordings,[],{},'owner')['complete'])

    def test_age_gender_and_private_naval_names_are_explicit(self):
        consumers=[dict(name='infantry',member='attrib/sbps/private.rgd',roles=['INFANTRY','INFANTRY_F'],
                        age_policy='unit_tier',ages=[3],generation_admitted=True),
                   dict(name='ship',member='attrib/sbps/races/chinese/ship.rgd',roles=['NAVAL_FISH'],
                        age_policy='player_age',ages=[1,2,3,4],generation_admitted=True)]
        bank=compose_bank(fixture(),{},consumers,{'attrib/sbps/races/chinese/ship.rgd':'vn084_s_ship'},'owner')
        self.assertEqual(bank['units']['owner:infantry'],dict(role='INFANTRY',female_role='INFANTRY_F',age=3,private=True))
        self.assertEqual(bank['units']['owner:vn084_s_ship'],dict(role='NAVAL_FISH',private=True))
        self.assertNotIn('ship',bank['units'])
        self.assertFalse(bank['complete'])

    def test_lua_bank_is_executable_data(self):
        import sys
        from pathlib import Path
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.tools/python'))
        from lupa.lua53 import LuaRuntime
        lua=LuaRuntime()
        self.assertEqual(lua.execute('return '+lua_value({'complete':False,'clips':[['audio/voices/a.wav',1.25]]}))['clips'][1][2],1.25)

    def test_complete_recordings_cannot_cover_an_unmapped_consumer_role(self):
        manifest=fixture();recordings={j['id']:dict(sha256=j['id'],duration=1) for j in manifest['jobs']}
        consumers=[dict(name='monk',member='attrib/sbps/private.rgd',roles=['MONK'],
                        age_policy='player_age',ages=[3,4],generation_admitted=True)]
        self.assertFalse(compose_bank(manifest,recordings,consumers,{},'owner')['complete'])


if __name__=='__main__':unittest.main()
