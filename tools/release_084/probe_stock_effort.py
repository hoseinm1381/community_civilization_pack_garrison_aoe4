"""Read-only game input, isolated decoder probe; no native installation."""
import json
from pathlib import Path
import subprocess
import sys
import warnings
from pipeline import guard, digest, save_json
from providers import OUT


def main():
    guard()
    dest=OUT/'integration/stock-effort-decoder-probe-v1'
    if dest.exists():raise FileExistsError('Preserve probe evidence')
    runtime=Path('C:/Users/RS/.codex/cache/aoe4-sga-extractor-session-20260717/_skill_sga_live_runtime')
    sys.path[:0]=[str(runtime/'site-packages'),str(runtime/'SGA-V10/src'),
                 'C:/Users/RS/.codex/skills/aoe4-garrison-blender/scripts']
    warnings.filterwarnings('ignore')
    from relic.sga.v10 import EssenceFSHandler
    from relic.sga.core.definitions import Version
    from donso_speech_profile import parse_profile
    EssenceFSHandler.version=Version(10,0)
    archive=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/SoundSpeechChinese.sga')
    with archive.open('rb') as stream:
        fs=EssenceFSHandler.read(stream)
        profile=fs.readbytes('/chinese_villagermale.spd')
        row=next(r for r in parse_profile(profile) if r['context']['text']=='effortPain_iHigh_cNone')
        media=row['media'][0]['text'].replace('\\','/').lower()
        matches=[p for p in fs.walk.files() if p.lower().lstrip('/')==media]
        if len(matches)!=1:raise RuntimeError('Stock effort media resolution differs: '+str(matches))
        original=fs.readbytes(matches[0])
    dest.mkdir(parents=True)
    wem=dest/'original.wem';wem.write_bytes(original)
    encoder=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/tool-cache/local-voices-084/tools/ffmpeg.exe')
    proc=subprocess.run([str(encoder),'-v','error','-nostdin','-i',str(wem),'-ac','1','-ar','48000',
                         '-c:a','pcm_s16le','-n',str(dest/'decoded.wav')],capture_output=True,text=True)
    (dest/'decoder.log').write_text(proc.stderr,encoding='utf-8')
    save_json(dest/'receipt.json',dict(archive=str(archive),archive_sha256=digest(archive),
              profile='chinese_villagermale.spd',context=row['context']['text'],member=matches[0],
              original_sha256=digest(wem),decoder_sha256=digest(encoder),decoder_exit=proc.returncode,
              stock_effort_preservation_qualified=False,native_game=False))
    print('STOCK_EFFORT_DECODER_PROBE',proc.returncode,proc.stderr[-500:])


if __name__=='__main__':main()
