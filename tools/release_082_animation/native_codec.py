"""Cattle tagfile adapter. Copies native TYPE bytes; invents no ABI metadata."""
from pathlib import Path
import copy,hashlib,json,re,struct,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_082_animation'
SOURCE=ROOT/'output/release_081/animation/source/art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rhka'
RUNTIME=Path(r'F:\aoe_4_temp\Community_civilization_pack_garrison_temp\resources_082_animation\runtime')
if not RUNTIME.is_dir():raise RuntimeError('Restore the project-owned Python 3.13 codec runtime; see docs/BUFFALO_ANIMATION_082_TRIAL.md')
sys.path.insert(0,str(RUNTIME))
from soulstruct.havok import HKX
from soulstruct.havok.types import hk2018
from soulstruct.havok.tagfile.unpacker import TagFileUnpacker
from soulstruct.havok.tagfile.packer import TagFilePacker
from soulstruct.utilities.binary import BinaryReader
from soulstruct.havok.tagfile.structs import TagFileItem
from soulstruct.havok.enums import TagDataType
from soulstruct.havok.types import tagfile as tagfile_types
reader=BinaryReader(SOURCE.read_bytes());info=TagFileUnpacker()
try:info.unpack(reader,types_only=True)
finally:reader.close()
pending={}
for row in info.hk_type_infos[1:]:
    if row.name in row.GENERIC_TYPE_NAMES:continue
    try:row.check_py_class_match(getattr(hk2018,row.py_name))
    except Exception:pending[row.py_name]=row
for _ in range(12):
    if not pending:break
    progressed=False
    for name,row in list(pending.items()):
        code,_=row.get_new_type_module_and_import(list(vars(hk2018.core)))
        code=re.sub(r'^from \..* import .*\n','',code,flags=re.MULTILINE)
        namespace=dict(vars(hk2018));namespace['__name__']=__name__
        try:exec(compile(code,name+'.py','exec'),namespace)
        except NameError:continue
        cls=namespace[name];row.check_py_class_match(cls);setattr(hk2018,name,cls)
        del pending[name];progressed=True
    if not progressed:raise ValueError('Unresolved native types: '+','.join(pending))
original_item_type=TagFileItem.get_item_hk_data_type
def native_item_type(item):
    if item.hk_type is hk2018._HavokAnimSet and item.is_ptr and item.length==1:return item.hk_type
    if item.hk_type is not None and item.hk_type.get_tag_data_type()==TagDataType.ConstCharArray:return item.hk_type.get_data_type()
    return original_item_type(item)
TagFileItem.get_item_hk_data_type=native_item_type
original_string_pack=tagfile_types.pack_string
class NativeString(str):
    def __bool__(self):return True
def native_string_pack(string_hk_type,item,value,items,queues,is_variant_name=False):
    return original_string_pack(string_hk_type,item,NativeString(value),items,queues,is_variant_name=is_variant_name)
tagfile_types.pack_string=native_string_pack
native_bytes=SOURCE.read_bytes();sections={};offset=8
while offset<len(native_bytes):
    size=struct.unpack_from('>I',native_bytes,offset)[0]&0x3fffffff
    assert size>=8
    sections[native_bytes[offset+4:offset+8].decode('ascii')]=native_bytes[offset:offset+size];offset+=size
def original_metadata(packer,long_varints):
    packer.type_info_dict={}
    for index,row in enumerate(info.hk_type_infos[1:],1):
        key=row.get_full_py_name()
        if key in packer.type_info_dict:key+='#native_index_'+str(index)
        packer.type_info_dict[key]=copy.deepcopy(row)
    missing={item.hk_type.__name__ for item in packer.items[1:]}-set(packer.type_info_dict)
    if missing:raise ValueError('Types absent from native metadata: '+str(missing))
def original_type_section(packer,writer,hsh_overrides):writer.append(sections['TYPE'])
TagFilePacker.build_type_info_dict=original_metadata
TagFilePacker.pack_type_section=original_type_section
def read(path=SOURCE):return HKX.from_path(path)
def write(model,path):
    raw=bytes(model.to_writer());path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():assert path.read_bytes()==raw
    else:path.write_bytes(raw)
    return raw
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
