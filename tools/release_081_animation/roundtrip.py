"""Isolated native cattle codec qualification using source-declared metadata."""
from pathlib import Path
import copy, hashlib, json, re, struct, sys, traceback
ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / 'workspace.json').read_text())
sys.path.insert(0, str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT, CFG)
OUT = ROOT/'output/release_081_animation/retry-1'
RUNTIME = Path(r'E:\age of empires 4 mods\AI_Assisted_modding\Berber_future_kingdom_ai\output\discoveries\tuareg_force_trial\codec_runtime')
sys.path.insert(0,str(RUNTIME))
from soulstruct.havok import HKX
from soulstruct.havok.types import hk2018
from soulstruct.havok.tagfile.unpacker import TagFileUnpacker
from soulstruct.havok.tagfile.packer import TagFilePacker
from soulstruct.utilities.binary import BinaryReader
from soulstruct.havok.tagfile.structs import TagFileItem
from soulstruct.havok.enums import TagDataType
from soulstruct.havok.types import tagfile as tagfile_types
SOURCE=ROOT/'output/release_081/animation/source/art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rhka'
report={'source':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'runtime':str(RUNTIME),'native_game_tested':False,'release_modified':False}

try:
    reader=BinaryReader(SOURCE.read_bytes()); info=TagFileUnpacker()
    try: info.unpack(reader,types_only=True)
    finally: reader.close()
    pending={}
    for row in info.hk_type_infos[1:]:
        if row.name in row.GENERIC_TYPE_NAMES: continue
        try: row.check_py_class_match(getattr(hk2018,row.py_name))
        except Exception: pending[row.py_name]=row
    report['generated_types']=list(pending)
    for _ in range(12):
        if not pending: break
        progressed=False
        for name,row in list(pending.items()):
            code,_=row.get_new_type_module_and_import(list(vars(hk2018.core)))
            code=re.sub(r'^from \..* import .*\n','',code,flags=re.MULTILINE)
            namespace=dict(vars(hk2018)); namespace['__name__']=__name__
            try: exec(compile(code,name+'.py','exec'),namespace)
            except NameError: continue
            cls=namespace[name]; row.check_py_class_match(cls)
            setattr(hk2018,name,cls);del pending[name];progressed=True
        if not progressed: raise ValueError('Unresolved native types: '+','.join(pending))
    original_item_type=TagFileItem.get_item_hk_data_type
    def native_item_type(item):
        if item.hk_type is hk2018._HavokAnimSet and item.is_ptr and item.length==1:return item.hk_type
        if item.hk_type is not None and item.hk_type.get_tag_data_type()==TagDataType.ConstCharArray:return item.hk_type.get_data_type()
        return original_item_type(item)
    TagFileItem.get_item_hk_data_type=native_item_type
    original_string_pack=tagfile_types.pack_string
    class NativeString(str):
        # Native annotation names include allocated empty strings; a null
        # pointer is semantically different to the independent game decoder.
        def __bool__(self):return True
    def native_string_pack(string_hk_type,item,value,items,queues,is_variant_name=False):
        return original_string_pack(string_hk_type,item,NativeString(value),items,queues,is_variant_name=is_variant_name)
    tagfile_types.pack_string=native_string_pack
    obj=HKX.from_path(SOURCE)
    report['read_clip_count']=len(obj.root.animations)
    report['clip_names']=[x.name.replace('\u00a5','\\') for x in obj.root.animations]
    # Keep native metadata rather than reconstructing missing generic flags.
    # Original type order is legal and lets native template/member indices stay exact.
    def original_metadata(packer,long_varints):
        packer.type_info_dict={}
        for index,row in enumerate(info.hk_type_infos[1:],1):
            key=row.get_full_py_name()
            if key in packer.type_info_dict:key += '#native_index_'+str(index)
            packer.type_info_dict[key]=copy.deepcopy(row)
        generated_names={item.hk_type.__name__ for item in packer.items[1:]}
        missing=generated_names-set(packer.type_info_dict)
        if missing:raise ValueError('Writer introduced types absent from native metadata: '+str(sorted(missing)))
    TagFilePacker.build_type_info_dict=original_metadata
    native_bytes=SOURCE.read_bytes()
    native_sections={}; offset=8
    while offset<len(native_bytes):
        size=struct.unpack_from('>I',native_bytes,offset)[0]&0x3fffffff
        name=native_bytes[offset+4:offset+8].decode('ascii')
        assert size>=8
        native_sections[name]=native_bytes[offset:offset+size];offset+=size
    def original_type_section(packer,writer,hsh_overrides):
        writer.append(native_sections['TYPE'])
    TagFilePacker.pack_type_section=original_type_section
    data=bytes(obj.to_writer())
    target=OUT/'cattle-roundtrip-v7.rhka'
    if target.exists():assert target.read_bytes()==data
    else:
        with target.open('xb') as f:f.write(data)
    decoded=HKX.from_path(target)
    assert obj.root.name==decoded.root.name
    assert len(obj.root.animations)==len(decoded.root.animations)
    def compare(a,b,path):
        if hasattr(a,'members'):
            assert type(a).__name__==type(b).__name__,path
            for member in a.members:compare(getattr(a,member.name),getattr(b,member.name),path+'.'+member.name)
        elif isinstance(a,(list,tuple)) or getattr(a,'ndim',0)>0:
            assert len(a)==len(b),path+'.length'
            for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'['+str(i)+']')
        else:assert a==b,(path,a,b)
    for a,b in zip(obj.root.animations,decoded.root.animations):
        assert a.name==b.name
        compare(a.skeleton,b.skeleton,a.name+'.skeleton')
        compare(a.animationBinding,b.animationBinding,a.name+'.binding')
    report.update(status='roundtrip_headers_skeletons_bindings_payloads_equal',output=str(target),output_sha256=hashlib.sha256(data).hexdigest())
except Exception as e:
    report.update(status='failed',error_type=type(e).__name__,error=str(e))
    traceback.print_exc()
(OUT/'roundtrip-result.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if report['status']=='failed':sys.exit(1)
