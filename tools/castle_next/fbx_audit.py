"""Small read-only binary FBX inventory for native export diagnostics."""
import json,struct,sys
from pathlib import Path

def parse(path):
    data=Path(path).read_bytes();version=struct.unpack_from('<I',data,23)[0]
    fmt='<QQQB' if version>=7500 else '<IIIB';header=struct.calcsize(fmt)
    def node(at):
        end,count,_,size=struct.unpack_from(fmt,data,at)
        if not end:return None,at+header
        pos=at+header;name=data[pos:pos+size].decode();pos+=size;props=[]
        for index in range(count):
            kind=chr(data[pos]);pos+=1
            if kind in 'YILFDC':
                f={'Y':'h','I':'i','L':'q','F':'f','D':'d','C':'?'}[kind]
                value=struct.unpack_from('<'+f,data,pos)[0];pos+=struct.calcsize(f)
            elif kind in 'SR':
                length=struct.unpack_from('<I',data,pos)[0];pos+=4
                value=data[pos:pos+length].decode('utf-8',errors='replace');pos+=length
            else:
                length,encoding,packed=struct.unpack_from('<III',data,pos);pos+=12
                value={'array_type':kind,'length':length,'encoding':encoding};pos+=packed
            props.append(value)
        children=[]
        while pos<end-header:
            child,pos=node(pos)
            if child:children.append(child)
        return {'name':name,'props':props,'children':children},end
    result=[];at=27
    while at<len(data)-header:
        item,at=node(at)
        if not item:break
        result.append(item)
    return result

if __name__=='__main__':
    for path in sys.argv[1:]:
        tree=parse(path)
        selected=[n for n in tree if n['name'] in ('Objects','Connections')]
        print(path);print(json.dumps(selected,indent=2))
