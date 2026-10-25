"""Bounded parser/identity clone for the inspected native Donso SPD fixture.

This preserves the original memory image layout. It is an experimental profile
authoring operation; a structural pass does not establish game acceptance.
"""
import struct
import hashlib

QUALIFIED_DONSO_SHA256 = "e37eafc275b19db533b03b00658d32c677b21134467fca5d34de82ca21686b76"


def chunks(data):
    if len(data) < 24 or data[:16] != b'Relic Chunky\r\n\x1a\x00':
        raise ValueError('Not a Relic Chunky container')
    if struct.unpack_from('<I', data, 16)[0] != 4:
        raise ValueError('Unsupported Chunky version')
    offset = 24
    result = []
    while offset < len(data):
        if offset + 20 > len(data):
            raise ValueError('Truncated chunk header')
        kind, tag, version, size, name_size = struct.unpack_from('<4s4sIII', data, offset)
        start = offset + 20 + name_size
        end = start + size
        if kind != b'DATA' or end > len(data):
            raise ValueError('Invalid or truncated chunk')
        result.append((tag, start, end, version))
        offset = end
    return result


def parse_profile(data):
    parts = chunks(data)
    if [tag for tag, *_ in parts] != [b'RFCI', b'RFUP', b'RNEW', b'RSHI', b'ROBJ', b'RERF']:
        raise ValueError('Unexpected speech profile chunk layout')
    _, start, end, version = parts[0]
    if version != 4131415:
        raise ValueError('Unexpected reflected profile version')
    if end - start < 16:
        raise ValueError("Truncated profile table header")
    count = struct.unpack_from('<I', data, start + 12)[0]
    first = start + 16
    table_end = first + count * 120
    if not 0 < count <= 10000 or table_end > end:
        raise ValueError('Invalid profile record count')

    def text_at(location, size):
        if location < table_end or location + size >= end or data[location + size] != 0:
            raise ValueError('String reference outside the pool or not terminated')
        return dict(offset=location, size=size, text=data[location:location + size].decode('ascii'))

    def record_string(header):
        pointer = header + 4
        location = pointer + struct.unpack_from('<i', data, pointer)[0]
        size = struct.unpack_from('<I', data, header + 12)[0]
        return text_at(location, size)

    records = []
    for index in range(count):
        record = first + index * 120
        pointer = record + 52
        media_start = pointer + struct.unpack_from('<i', data, pointer)[0]
        media_count = struct.unpack_from('<I', data, record + 60)[0]
        if not 1 <= media_count <= 64 or not table_end <= media_start < end or media_start + media_count * 24 > end:
            raise ValueError('Invalid media list')
        media = []
        for number in range(media_count):
            item = media_start + number * 24
            location = item + struct.unpack_from('<q', data, item)[0]
            size = struct.unpack_from('<Q', data, item + 8)[0]
            entry = text_at(location, size)
            if not entry['text'].lower().endswith('.wem'):
                raise ValueError('Unexpected media resource')
            media.append(entry)
        records.append(dict(index=index, context=record_string(record), race=record_string(record + 16),
                            speaker=record_string(record + 32), media=media))
    return records


def clone_private(original, speaker):
    if hashlib.sha256(original).hexdigest() != QUALIFIED_DONSO_SHA256:
        raise ValueError('Source differs from the qualified Donso fixture; reinspect before authoring')
    if len(speaker) != 5 or not speaker.isascii() or not speaker.isalnum() or speaker.lower() == 'donso':
        raise ValueError('Private identity must be five ASCII alphanumeric characters')
    records = parse_profile(original)
    output = bytearray(original)
    permitted = set()
    for record in records:
        if record['speaker']['text'] != 'donso' or record['race']['text'] != 'malian':
            raise ValueError('Source is not the qualified Donso fixture')
        replacements = [(record['speaker'], speaker)]
        for media in record['media']:
            path = media['text']
            if path.lower().count('malian_donso') != 2:
                raise ValueError('Unexpected stock media path')
            replacements.append((media, path.replace('malian_donso', 'malian_' + speaker)))
        for field, value in replacements:
            encoded = value.encode('ascii')
            if len(encoded) != field['size']:
                raise ValueError('Identity edit would relocate native pointers')
            offset = field['offset']
            output[offset:offset + len(encoded)] = encoded
            permitted.update(range(offset, offset + len(encoded)))
    cloned = bytes(output)
    parse_profile(cloned)
    return cloned, permitted


def inspect_wem(path):
    data = path.read_bytes()
    if len(data) < 12 or data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        raise ValueError('Not a native RIFF/WAVE media file: ' + str(path))
    if struct.unpack_from('<I', data, 4)[0] + 8 != len(data):
        raise ValueError('Media RIFF size mismatch: ' + str(path))
    offset = 12
    tags = []
    fmt = None
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated media header: ' + str(path))
        tag, size = struct.unpack_from('<4sI', data, offset)
        start, end = offset + 8, offset + 8 + size
        if end > len(data):
            raise ValueError('Truncated media chunk: ' + str(path))
        tags.append(tag)
        if tag == b'fmt ':
            if size < 8:
                raise ValueError('Truncated media format: ' + str(path))
            fmt = struct.unpack_from('<HHI', data, start)
        offset = end + size % 2
    if fmt != (65535, 1, 48000) or b'data' not in tags:
        raise ValueError('Media differs from qualified Windows Vorbis mono/48k format: ' + str(path))
    return hashlib.sha256(data).hexdigest()


def verify_media(profile, audio_root):
    from pathlib import Path
    root = Path(audio_root).resolve(strict=True)
    records = parse_profile(profile)
    names = {media['text'].replace('\\', '/').lower() for row in records for media in row['media']}
    hashes = set()
    for name in sorted(names):
        parts = name.split('/')
        if ':' in name or name.startswith('/') or any(part in ('', '.', '..') for part in parts):
            raise ValueError('Unsafe native media reference: ' + name)
        path = (root / name).resolve()
        if root not in path.parents:
            raise ValueError('Media escapes the provided audio root: ' + name)
        if not path.is_file():
            raise ValueError('Missing native media: ' + str(path))
        hashes.add(inspect_wem(path))
    return {'status': 'media_container_readback_passed', 'profile_records': len(records),
            'media_references': len(names), 'distinct_audio_sha256': len(hashes),
            'audio_root': str(root), 'native_playback': 'unverified_by_this_check'}


def main():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Bounded Donso SPD inspection/clone; no native playback claim.')
    sub = parser.add_subparsers(dest='command', required=True)
    inspect = sub.add_parser('inspect', help='Read profile layout and identity summary.')
    inspect.add_argument('profile', type=Path)
    inspect.add_argument('--records', action='store_true', help='Export raw context and all media paths for a coverage inventory.')
    clone = sub.add_parser('clone', help='Clone only the exact qualified stock Donso fixture.')
    clone.add_argument('source', type=Path)
    clone.add_argument('output', type=Path)
    clone.add_argument('--speaker', required=True)
    verify = sub.add_parser('verify-media', help='Read back all referenced native media containers.')
    verify.add_argument('profile', type=Path)
    verify.add_argument('audio_root', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'clone':
            if args.output.exists():
                raise ValueError('Output already exists; preserve it and choose a new authoring path')
            original = args.source.read_bytes()
            private, _ = clone_private(original, args.speaker)
            # Exclusive creation also guards an output appearing after the initial check.
            with args.output.open('xb') as stream:
                stream.write(private)
            result = {'status': 'qualified_private_clone_written', 'output': str(args.output),
                      'bytes': len(private), 'sha256': hashlib.sha256(private).hexdigest(),
                      'speaker': args.speaker, 'native_playback': 'unverified_by_this_check'}
        elif args.command == 'verify-media':
            result = verify_media(args.profile.read_bytes(), args.audio_root)
        else:
            data = args.profile.read_bytes()
            rows = parse_profile(data)
            result = {'status': 'structural_readback_only', 'sha256': hashlib.sha256(data).hexdigest(),
                      'qualified_stock_source': hashlib.sha256(data).hexdigest() == QUALIFIED_DONSO_SHA256,
                      'profile_records': len(rows),
                      'media_references': sum(len(row['media']) for row in rows),
                      'speakers': sorted({row['speaker']['text'] for row in rows}),
                      'races': sorted({row['race']['text'] for row in rows}),
                      'native_playback': 'unverified_by_this_check'}
            result['qualification_note'] = 'This flag qualifies unchanged stock input only; a private clone normally reports false.'
            if args.records:
                result['records'] = [{'context': row['context']['text'], 'race': row['race']['text'],
                                      'speaker': row['speaker']['text'],
                                      'media_paths': [entry['text'] for entry in row['media']]} for row in rows]
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, UnicodeError, struct.error) as error:
        parser.exit(1, 'ERROR: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
