"""Read current owned ReferenceAttributes SGA v10 XML without external caches.

This small read-only implementation checks format/bounds/decoded lengths. It is
not an archive signature/CRC verifier. Brotli is optional for source-only checks;
native inheritance refresh needs requirements-native.txt or a configured DLL.
"""
import ctypes
import json
import os
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configuration():
    path = ROOT/'workspace.local.json'
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}


def archive_path():
    config = configuration()
    editor = os.environ.get('AOE4_EDITOR_ROOT') or config.get('editor_root')
    if not editor:
        raise ValueError('Set editor_root in workspace.local.json or AOE4_EDITOR_ROOT for native inheritance refresh.')
    return Path(editor)/'cardinal/archives/ReferenceAttributes.sga'


def brotli_decode(raw, expected):
    try:
        import brotli
    except ImportError:
        dll = configuration().get('brotli_dll')
        if not dll:
            raise RuntimeError('Install requirements-native.txt, or configure brotli_dll for native archive inspection.')
        with os.add_dll_directory(str(Path(dll).parent)):
            library = ctypes.CDLL(dll)
            decoder = library.BrotliDecoderDecompress
            decoder.argtypes = [ctypes.c_size_t,ctypes.c_void_p,ctypes.POINTER(ctypes.c_size_t),ctypes.c_void_p]
            output = ctypes.create_string_buffer(expected); size=ctypes.c_size_t(expected)
            if decoder(len(raw),raw,ctypes.byref(size),output)!=1:
                raise ValueError('Brotli decoding failed')
            return output.raw[:size.value]
    return brotli.decompress(raw)


def members(archive, predicate=lambda name: True):
    archive=Path(archive); total=archive.stat().st_size
    with archive.open('rb') as stream:
        if stream.read(12)!=b'_ARCHIVE\x0a\x00\x00\x00':
            raise ValueError('Expected current official SGA v10')
        _, header_pos, header_size, data_pos, data_size, reserved0, reserved1, _ = struct.unpack('<128sQI QI 2I256s',stream.read(416))
        if (reserved0,reserved1)!=(0,1) or header_pos+header_size>total or data_pos+data_size>total:
            raise ValueError('Invalid SGA header bounds')
        stream.seek(header_pos); header=stream.read(header_size)
        _,_,folder_pos,folder_count,file_pos,file_count,name_pos,name_size=struct.unpack_from('<8I',header)
        if folder_pos+20*folder_count>len(header) or file_pos+30*file_count>len(header) or name_pos+name_size>len(header):
            raise ValueError('Invalid SGA table bounds')
        names=header[name_pos:name_pos+name_size]
        def name(offset):
            if not 0<=offset<len(names):raise ValueError('Invalid SGA name offset')
            end=names.find(b'\0',offset)
            if end<0:raise ValueError('Unterminated SGA name')
            return names[offset:end].decode('utf-8')
        for index in range(folder_count):
            directory,_,_,first,last=struct.unpack_from('<5I',header,folder_pos+20*index)
            if not 0<=first<=last<=file_count:raise ValueError('Invalid SGA file range')
            directory=name(directory)
            for slot in range(first,last):
                filename,_,offset,packed,unpacked,_,flags,_=struct.unpack_from('<2IQ2I2BI',header,file_pos+30*slot)
                full=directory+'\\'+name(filename) if directory else name(filename)
                if not predicate(full):continue
                if flags>>4 or offset+packed>data_size:raise ValueError('Encrypted or out-of-bounds SGA member')
                stream.seek(data_pos+offset);raw=stream.read(packed);storage=flags&15
                if storage==0:decoded=raw
                elif storage in (1,2):decoded=zlib.decompress(raw)
                elif storage==3:decoded=brotli_decode(raw,unpacked)
                else:raise ValueError('Unsupported SGA storage type '+str(storage))
                if len(decoded)!=unpacked:raise ValueError('Decoded SGA member length mismatch')
                yield full,decoded
