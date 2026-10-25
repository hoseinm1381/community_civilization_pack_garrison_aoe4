"""Run existing normal behavioral fixtures against actual staged Garrison SCAR.

Only archive identity is normalized in fixture strings/snapshots. Historical
evidence stays in normal; live asset reads route to the Garrison candidate.
"""
from freeze import *
import unittest,io,importlib,re
STAGE=Path(CFG['external_root'])/'staging/r72/ported-source'
sys.path.insert(0,str(NORMAL/'tests'))
names=['test_tunnel_crowd_v12','test_supervision_v11','test_tunnel_notifications_v10',
       'test_runtime_v9_paddy.PaddyCreationV9','test_runtime_v9_paddy.PaddyBuildStartV9']
suite=unittest.defaultTestLoader.loadTestsFromNames(names)
class RootRouter:
    def __truediv__(self,key):return (STAGE if str(key).replace('\\','/').split('/')[0]=='assets' else NORMAL)/key
    def __fspath__(self):return str(STAGE)
    def __str__(self):return str(STAGE)
router=RootRouter()
for key,m in list(sys.modules.items()):
    if key.startswith(('test_','tunnel_fixture')):
        if hasattr(m,'ROOT'):m.ROOT=router
        for attr,v in list(vars(m).items()):
            if isinstance(v,str) and OLD in v:setattr(m,attr,v.replace(OLD,GUID))
import blueprint_paths
blueprint_paths.A=STAGE/'assets/attrib/instances'
import test_runtime_repairs
original_runlua=test_runtime_repairs.RuntimeFixture.runlua
def runlua(self,source):return original_runlua(self,source.replace(OLD,GUID))
test_runtime_repairs.RuntimeFixture.runlua=runlua
# Frozen tests occasionally execute old SCAR to reproduce historical failures.
# Normalize its archive identity in memory, leaving the frozen bytes unchanged.
read=zipfile.ZipFile.read
def identity_read(self,name,*args,**kwargs):return read(self,name,*args,**kwargs).replace(OLD.encode(),GUID.encode())
zipfile.ZipFile.read=identity_read
def flatten(s):
    for t in s:
        if isinstance(t,unittest.TestSuite):yield from flatten(t)
        else:yield t
excluded={
 'test_supervision_v11.ControlsV11.test_only_requested_visual_fields_change_in_buildings':'normal-only visual freeze intentionally superseded by preservation of existing Garrison art; full gameplay parity checked independently',
 'test_supervision_v11.ControlsV11.test_speed_ui_key_and_presentation_preserve_graph':'historical exact-source freeze superseded by v12 and Garrison visual-only source parity',
 'test_tunnel_notifications_v10.TunnelNotificationsV10Tests.test_simulation_source_matches_frozen_working_v9_after_presentation_removal':'historical freeze superseded by v12 entrance allowance'}
tests=[t for t in flatten(suite)if t.id()not in excluded]
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite(tests))
(OUT/'gameplay-tests.log').write_text(stream.getvalue(),encoding='utf-8')
data={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'excluded':excluded,'details':[(t.id(),s)for t,s in result.failures+result.errors]}
dump(OUT/'gameplay-tests.json',data);print(json.dumps(data,indent=2));sys.exit(not result.wasSuccessful())
