"""Extend the six-sample review manifest with the final Archer authoring sample."""
from pathlib import Path
from common import ART, OUT, guard, owned, read, sha, write

guard()
source=OUT/'representatives/selection-six.json'
target=owned(OUT/'representatives/selection-seven.json')
if target.exists():
    raise FileExistsError(target)
catalog=read(source)
if catalog.get('schema')!='ccp-060-representative-selection/v1' or len(catalog['samples'])!=6:
    raise RuntimeError('Expected six pinned representative samples')
if any(item['id']=='archer2' for item in catalog['samples']):
    raise RuntimeError('Archer already included in source selection')
base=ART/'archer/archer-base-v3l-owner-tunic.blend'
rattan=ART/'archer/archer-rattan-v3m-owner-tunic.blend'
if sha(base)!='0092ebe4a428f12f3a0770d21cdde1a1758876ad16ecf3944ee2f432e5a6125c':
    raise RuntimeError('Final Archer base changed')
if sha(rattan)!='421f3865427b76451ed005e1c4d71edda3b944b17d787fb6c4a3e06631656213':
    raise RuntimeError('Final Archer Rattan changed')

base_out=OUT/'qualification/archer-v3l-final-base'
rattan_out=OUT/'qualification/archer-v3m-final-rattan'
donor=OUT/'qualification/archer-v3i-representative-base/stock-donor-game.png'

def record(path):
    path=Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    return {'path':str(path),'sha256':sha(path)}

sample={
    'id':'archer2',
    'title':'Age II archer and Rattan upgrade',
    'blend':str(base),
    'blend_sha256':sha(base),
    'rattan_blend':str(rattan),
    'rattan_blend_sha256':sha(rattan),
    'donor':'art/civilizations/chinese/humans/chi_ranged_bow_age02/chi_ranged_bow_age02.rgm',
    'notes':'Teal fitted tunic with broad native-pattern owner-color split panel; stock anatomy, full quiver, bow and rig remain. Rattan authoring state adds a weighted coarse vest and carried back shield. Native Rattan switch and material integration remain separate gates.',
    'images':{
        'stock_game':record(donor),
        'finish_game':record(base_out/'game-stock.png'),
        'finish_close':record(base_out/'close-front.png'),
        'finish_back_close':record(base_out/'close-back.png'),
        'red_game':record(base_out/'game-red.png'),
        'blue_game':record(base_out/'game-blue.png'),
        'rattan_game':record(rattan_out/'game-stock.png'),
        'rattan_close':record(rattan_out/'close-front.png'),
        'rattan_back_close':record(rattan_out/'close-back.png'),
        'rattan_red_game':record(rattan_out/'game-red.png'),
        'rattan_blue_game':record(rattan_out/'game-blue.png'),
    },
    'revision':'v3l base / v3m Rattan',
    'source_receipt':str(OUT/'qualification/archer-base-owner-tunic.json'),
    'rattan_source_receipt':str(OUT/'qualification/archer-rattan-owner-tunic.json'),
    'review_receipt':str(base_out/'presentation.json'),
    'rattan_review_receipt':str(rattan_out/'presentation.json'),
}
catalog['samples'].append(sample)
catalog['source_selection']=record(source)
catalog['status']='authoring_review_ready'
catalog['style_approved']=False
write(target,catalog)
print(str(target),sha(target),len(catalog['samples']))
