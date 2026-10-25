from pathlib import Path
import sys
import unittest


class LifecycleTests(unittest.TestCase):
    def test_actual_mode_hooks_parse_and_restore_only_after_selection(self):
        from voice_lifecycle import patch_mode
        root=Path(__file__).resolve().parents[2]
        source=(root/'assets/scar/winconditions/VietnamMode.scar').read_text(encoding='utf-8')
        result=patch_mode(source)
        self.assertIn('import("vietnam/voices_084.scar")',result)
        self.assertEqual(result.count('VietnamVoice_Start(state.civilizations)'),2)
        self.assertEqual(result.count('VietnamVoice_Stop()'),2)
        with self.assertRaises(ValueError):patch_mode(result)
        sys.path.insert(0,str(root/'.tools/python'))
        from lupa.lua53 import LuaRuntime
        lua=LuaRuntime()
        lua.execute('function import(x) end; function Core_RegisterModule(x) end')
        lua.execute(result)
        lua.execute('''starts=0;stops=0
        function VietnamVoice_Start(x) starts=starts+1 end
        function VietnamVoice_Stop() stops=stops+1 end
        function VietnamPaddyWood_RestoreUI() end
        function VietnamPresentation_Restore() end
        function Rule_AddOneShot(f,t) end
        VietnamModeState.selection={closed=true};VietnamModeState.civilizations={}
        VietnamMode_OnGameRestore()
        assert(starts==1 and stops==1)
        VietnamModeState.selection=nil;VietnamMode_OnGameRestore()
        assert(starts==1 and stops==2)
        ''')

    def test_precache_additions_keep_original_lists_and_skip_attachment_catalogues(self):
        from voice_lifecycle import patch_precache
        source='local entities = {\n "original",\n}\nlocal squads = {\n "old_squad",\n}\n'
        rows=[dict(category='ebps',name='new_actor'),dict(category='sbps',name='new_unit'),dict(category='attachments',name='female')]
        result=patch_precache(source,rows,'owner')
        self.assertIn('"owner:new_actor"',result);self.assertIn('"owner:new_unit"',result)
        self.assertNotIn('owner:female',result)
        self.assertIn('"original"',result);self.assertIn('"old_squad"',result)


if __name__=='__main__':unittest.main()
