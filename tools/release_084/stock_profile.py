"""Read-only reflected SPD parser for the inspected Chinese stock profiles.

The older Donso fixture caps lists at 64. Chinese villagerFemale has a valid
67-media list; this reader admits up to 128 while checking every pointer/span.
It never writes or clones a native profile.
"""
import struct


def read_stock_profile(data):
    if len(data)<24 or data[:16]!=b'Relic Chunky\r\n\x1a\x00' or struct.unpack_from('<I',data,16)[0]!=4:
        raise ValueError('Unexpected SPD container')
    chunks=[];offset=24
    while offset<len(data):
        if offset+20>len(data):raise ValueError('Truncated SPD chunk')
        kind,tag,version,size,name_size=struct.unpack_from('<4s4sIII',data,offset)
        start=offset+20+name_size;end=start+size
        if kind!=b'DATA' or end>len(data):raise ValueError('Invalid SPD chunk span')
        chunks.append((tag,start,end,version));offset=end
    if [c[0] for c in chunks]!=[b'RFCI',b'RFUP',b'RNEW',b'RSHI',b'ROBJ',b'RERF']:
        raise ValueError('Unexpected SPD chunk layout')
    _,start,end,version=chunks[0]
    if version!=4131415 or end-start<16:raise ValueError('Unexpected SPD reflection schema')
    count=struct.unpack_from('<I',data,start+12)[0];first=start+16;table_end=first+120*count
    if not 0<count<=10000 or table_end>end:raise ValueError('Invalid SPD record count')
    def text_at(location,size):
        if location<table_end or location+size>=end or data[location+size]!=0:
            raise ValueError('Invalid SPD text span')
        try:text=data[location:location+size].decode('ascii')
        except UnicodeDecodeError as error:raise ValueError('Unexpected SPD text encoding') from error
        return dict(offset=location,size=size,text=text)
    def record_text(header):
        pointer=header+4
        return text_at(pointer+struct.unpack_from('<i',data,pointer)[0],struct.unpack_from('<I',data,header+12)[0])
    rows=[]
    for index in range(count):
        record=first+120*index;pointer=record+52
        media_start=pointer+struct.unpack_from('<i',data,pointer)[0]
        media_count=struct.unpack_from('<I',data,record+60)[0]
        if not 1<=media_count<=128 or not table_end<=media_start<end or media_start+24*media_count>end:
            raise ValueError('Invalid SPD media span')
        media=[]
        for n in range(media_count):
            item=media_start+24*n
            entry=text_at(item+struct.unpack_from('<q',data,item)[0],struct.unpack_from('<Q',data,item+8)[0])
            if not entry['text'].lower().endswith('.wem'):raise ValueError('Unexpected SPD media type')
            media.append(entry)
        rows.append(dict(index=index,context=record_text(record),race=record_text(record+16),
                         speaker=record_text(record+32),media=media))
    return rows
