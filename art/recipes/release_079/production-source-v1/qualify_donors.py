"""Refresh authoritative rig and attachment evidence from installed official archives."""
import sqlite3
from common import *
from rig_contract import read_contract
guard();donors=read(OUT/'donors.json');index=Path.home()/'AppData/Local/Garrison/Kit/game-assets.sqlite3'
dest=OUT/'diagnosis/current-official'
if dest.exists():raise FileExistsError('Preserve official qualification attempt')
dest.mkdir(parents=True);report={}
with sqlite3.connect('file:'+index.as_posix()+'?mode=ro',uri=True) as db:
    for family in ('buffalo','skirmisher2','skirmisher3','skirmisher4'):
        member=donors[family]['logical_path'];rows=db.execute('select archive_path from resolved_assets where lower(logical_path)=?',(member.lower(),)).fetchall()
        assert len(rows)==1
        archive=Path(rows[0][0]);p=dest/member;p.parent.mkdir(parents=True,exist_ok=True)
        run('fresh-'+family,[CFG['archive_tool'],'extract-member',archive,member,p],dest/'logs')
        original=read(donors[family]['manifest'])
        assert sha(p)==original['skeleton']['source_sha256']
        report[family]={'member':member,'archive':str(archive),'archive_size':archive.stat().st_size,'archive_mtime_ns':archive.stat().st_mtime_ns,'source_sha256':sha(p),'matches_retained_donor':True,'contract':read_contract(p.read_bytes())}
    members=['attrib/attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal.rgd']+[f'attrib/attachments/attachment_lists/civilizations/malian/units/tier{age}_javelin_mal.rgd' for age in (2,3,4)]
    archive=Path(CFG['content_editor']).parent/'cardinal/archives/Attrib.sga'
    for member in members:
        p=dest/member;p.parent.mkdir(parents=True,exist_ok=True)
        run('fresh-'+p.stem,[CFG['archive_tool'],'extract-member',archive,member,p],dest/'logs')
        assert sha(p)==sha(ROOT/'output/release_076/official'/member)
        report[member]={'source_sha256':sha(p),'matches_retained_donor':True}
write(dest/'proof.json',report);print('CURRENT_OFFICIAL_DONORS_MATCH',len(report))
