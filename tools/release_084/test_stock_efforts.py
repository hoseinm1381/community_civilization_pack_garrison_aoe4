import unittest


class StockEffortTests(unittest.TestCase):
    def test_stock_efforts_bind_to_each_private_consumer_and_keep_native_aliases(self):
        from stock_efforts import attach_stock_efforts
        bank=dict(units={'owner:private':dict(role='INFANTRY')},clips={})
        rows=[dict(name='stock',member='attrib/sbps/races/chinese/stock.rgd',generation_admitted=True)]
        stock=dict(consumers={'stock':dict(male='manatarms',female='villagerfemale')},
                   clips={'manatarms':{'death':[dict(member='audio/stock_efforts/one.ogg',duration=1)]}})
        attach_stock_efforts(bank,rows,{rows[0]['member']:'private'},'owner',stock)
        self.assertEqual(bank['units']['owner:private']['stock_female_speaker'],'villagerfemale')
        self.assertEqual(bank['stock_efforts']['manatarms']['death'],[['audio/stock_efforts/one.ogg',1]])
        with self.assertRaises(RuntimeError):attach_stock_efforts(bank,rows,{},'owner',stock)

    def test_actual_female_profile_has_one_valid_67_media_record(self):
        from stock_profile import read_stock_profile
        from providers import OUT
        path=OUT/'integration/stock-effort-inventory-v1/profiles/chinese_villagerfemale.spd'
        raw=path.read_bytes();rows=read_stock_profile(raw)
        self.assertEqual(len(rows),964)
        self.assertEqual(max(len(r['media']) for r in rows),67)
        with self.assertRaises(ValueError):read_stock_profile(raw[:-50])

    def test_only_native_nonverbal_contexts_are_admitted(self):
        from stock_efforts import context_event
        self.assertEqual(context_event('effortDeath_iHigh_cNone'),'death')
        self.assertEqual(context_event('effortPain_iHigh_cNone'),'pain_light')
        self.assertEqual(context_event('effortPainBig_iHigh_cNone'),'pain_heavy')
        self.assertIsNone(context_event('underAttack_iHigh_cHigh'))
        self.assertIsNone(context_event('effortDeathWords_iHigh_cNone'))

    def test_speaker_mapping_is_per_consumer_and_female_is_explicit(self):
        from stock_efforts import consumer_speakers
        row=dict(speech=[dict(path='/default/squad_speech_ext/squad_speaker_code',value='manatarms')],
                 roles=['INFANTRY','INFANTRY_F'],attachment_speakers=[dict(value='manatarmsFemale')])
        self.assertEqual(consumer_speakers(row),dict(male='manatarms',female='manatarmsFemale'))
        row['speech'].append(dict(path='/default/squad_speech_ext/squad_speaker_code',value='scout'))
        with self.assertRaises(ValueError):consumer_speakers(row)


if __name__=='__main__':unittest.main()
