import sys,json
sys.path.insert(0,r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from garrison import building_project
print('TRAP_GARRISON_CONTRACT '+json.dumps({'schema':building_project.SCHEMA,'stage_property':building_project.STAGE_PROPERTY}))
