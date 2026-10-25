"""Decode fresh pilot cook and enforce native partition metadata as a new gate."""
import runpy
from common import *
from rig_contract import read_contract,validate_contract
sys.path.insert(1,str(ROOT/'tools/release_076'))
label=sys.argv[1]
runpy.run_path(str(ROOT/'tools/release_076/decode_cook.py'),run_name='__main__')
receipt=read(OUT/'cooks'/label/'receipt.json');report={}
for row in receipt['records']:
    family=row['family'];export=read(OUT/'art'/family/row['revision']/'export.json')
    raw=(OUT/'cooks'/label/'readback'/row['member_root']/'model.rgm').read_bytes()
    contract=read_contract(raw);validate_contract(contract,export['donor_contract'])
    report[family]={'partitions':contract['partitions'],'groups':contract['groups'],'lod_counts':contract['lod_counts'],'exact_donor_contract':True}
write(OUT/'cooks'/label/'partition-proof.json',report)
print('NATIVE_PARTITION_CONTRACTS_VERIFIED',len(report))
