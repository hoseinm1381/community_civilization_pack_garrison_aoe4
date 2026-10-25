"""Read selected official v10 members in memory; never extract or modify archives.

Existing SGA reader parses the table only. Brotli decoding uses the bundled Git
DLL; decoded length is verified before returning bytes. Archive verification
mode and CRC semantics are not inferred by this inspection helper.
"""
import ctypes, enum, os, sys, warnings, zlib
from pathlib import Path

RUNTIME = Path(r'C:\Users\RS\.codex\cache\aoe4-sga-extractor-session-20260717\_skill_sga_live_runtime')
sys.path[:0] = [str(RUNTIME/'site-packages'), str(RUNTIME/'SGA-V10/src')]
warnings.filterwarnings('ignore', message='pkg_resources is deprecated.*')
import relic.sga.v10.serialization as v
from relic.sga.v10 import EssenceFSHandler as handler
from relic.sga.core.serialization import FSAssembler
v.StorageType = enum.IntEnum('StorageType', {'STORE':0, 'BUFFER_COMPRESS':1, 'STREAM_COMPRESS':2, 'BROTLI':3})
DLL_ROOT = Path(r'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\mingw64\bin')
_dll_dir = os.add_dll_directory(str(DLL_ROOT))
_dll = ctypes.CDLL(str(DLL_ROOT/'libbrotlidec.dll'))
_decode = _dll.BrotliDecoderDecompress
_decode.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t), ctypes.c_void_p]
BASE = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives')

def members(archive, predicate):
    with (BASE/archive).open('rb') as stream:
        assert stream.read(12) == b'_ARCHIVE\x0a\x00\x00\x00'
        meta = handler.meta_serializer.unpack(stream)
        stream.seek(meta.ptrs.header_pos)
        toc = handler.toc_serializer.unpack(stream)
        assembler = FSAssembler(stream=stream, ptrs=meta.ptrs, toc=toc,
            toc_serialization_info=handler.toc_serialization_info, build_file_meta=handler.build_file_meta)
        _, _, files, names = assembler.read_toc()
        for entry in files:
            name = names[entry.name_pos]
            if not predicate(name):
                continue
            assert int(entry.encryption) == 0
            stream.seek(meta.ptrs.data_pos + entry.data_pos)
            raw = stream.read(entry.length_in_archive)
            if int(entry.storage_type) == 3:
                out = ctypes.create_string_buffer(entry.length_on_disk)
                size = ctypes.c_size_t(entry.length_on_disk)
                assert _decode(len(raw), raw, ctypes.byref(size), out) == 1
                data = out.raw[:size.value]
            else:
                data = zlib.decompress(raw) if int(entry.storage_type) else raw
            assert len(data) == entry.length_on_disk
            yield name, data

if __name__ == '__main__':
    for name, data in members(sys.argv[1], lambda name: name in sys.argv[2:]):
        print(name)
        print(data.decode('utf-8-sig'))
