"""Build the compact seven-sample style review from explicitly selected evidence.

Game previews retain native pixel scale: CSS clips empty framing, without
resampling or modifying the Blender images. Click through for full originals.
"""
from html import escape
import os
from pathlib import Path
import struct
from urllib.parse import quote
from common import ART, OUT, RECIPES, guard, owned, read, sha

DEST=OUT/'review/representatives.html'
SELECTION=RECIPES/'representative-review-selection.json'
EXPECTED={'archer2','spear2','male_villager1','female_villager1','horseman2','elephant','siege_mangonel3'}


def main(selection=SELECTION):
    guard()
    selection=owned(selection)
    data=read(selection)
    rows=data['samples']
    if len(rows)!=7 or {r['id'] for r in rows}!=EXPECTED:
        raise ValueError('Explicit selections for all seven representatives required')
    sections=[]
    def figure(label,record,game=False):
        path=Path(record['path'])
        if not path.resolve().is_relative_to(OUT.resolve()) or sha(path)!=record['sha256']:
            raise RuntimeError(f'Changed/outside preview: {path}')
        link=quote(os.path.relpath(path,DEST.parent).replace('\\','/'),safe='/')
        css='game' if game else 'close'
        with path.open('rb') as stream:header=stream.read(24)
        if header[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('Expected native PNG render')
        width,height=struct.unpack('>II',header[16:24])
        style=f' style="width:{width}px;height:{height}px"' if game else ''
        return f'<figure><figcaption>{escape(label)}</figcaption><a class="{css}" href="{link}" target="_blank"><img src="{link}"{style} loading="lazy" alt="{escape(label)}"></a></figure>'
    for row in rows:
        source=Path(row['blend'])
        if not source.resolve().is_relative_to(ART.resolve()) or sha(source)!=row['blend_sha256']:
            raise RuntimeError(f'Changed/outside editable source: {source}')
        if 'rattan_blend' in row:
            rattan=Path(row['rattan_blend'])
            if not rattan.resolve().is_relative_to(ART.resolve()) or sha(rattan)!=row['rattan_blend_sha256']:
                raise RuntimeError('Rattan editable source changed')
        pictures=row['images']
        if not {'stock_game','finish_game','finish_close'}<=pictures.keys():
            raise ValueError(f'Missing matched game/close evidence: {row["id"]}')
        game=figure('Stock donor · game distance',pictures['stock_game'],True)
        game+=figure('Vietnamese design · game distance',pictures['finish_game'],True)
        for key,label in [('rattan_game','Rattan art · game distance'),
                          ('red_game','Red player · game distance'),('blue_game','Blue player · game distance'),
                          ('rattan_red_game','Rattan art · red player'),('rattan_blue_game','Rattan art · blue player')]:
            if key in pictures:game+=figure(label,pictures[key],True)
        close=figure('Vietnamese design · close inspection',pictures['finish_close'])
        if 'finish_back_close' in pictures:close+=figure('Vietnamese design · rear inspection',pictures['finish_back_close'])
        if 'rattan_close' in pictures:close+=figure('Rattan art · close inspection',pictures['rattan_close'])
        if 'rattan_back_close' in pictures:close+=figure('Rattan art · rear shield',pictures['rattan_back_close'])
        sections.append(f'<section><h2>{escape(row["title"])}</h2><p>{escape(row.get("notes",""))}</p>'
                        f'<div class="row">{game}</div><details><summary>Close inspection and donor identity</summary>'
                        f'<p>{escape(row["donor"])}</p><div class="row">{close}</div></details>'
                        '<p class="small">Historical reference: <a href="#reference">Ly–Tran objects below</a>. Clothing and palette are design interpretations.</p></section>')
    refs=read(OUT/'references/visual-reference-supplement.json')
    photos=[]
    for ref in refs['successful_visual_evidence']:
        credit=('Gryffindor · CC BY-SA 3.0' if ref['id']=='tran_jar_warriors' else 'Daderot · CC0 1.0')
        photos.append(f'<figure><a href="{escape(ref["image_record"],quote=True)}" target="_blank" rel="noreferrer">'
                      f'<img class="artifact" src="{escape(ref["direct_image"],quote=True)}" alt="{escape(ref["artifact"],quote=True)}"></a>'
                      f'<figcaption>{escape(ref["artifact"])} · {credit}</figcaption></figure>')
    html='''<!doctype html><meta charset="utf-8"><title>Vietnamese unit representative review</title>
<style>body{font:16px system-ui;background:#171b1d;color:#eef0ed;margin:0 auto;padding:28px;max-width:1120px}a{color:#9dd4df}h1{font-size:26px}h2{font-size:22px}section{border-top:1px solid #485052;padding:22px 0}.row{display:flex;flex-wrap:wrap;gap:16px}figure{margin:0 0 16px;max-width:360px}figcaption{padding:8px 0}.game{display:block;position:relative;width:320px;height:320px;overflow:hidden;background:#aaa}.game img{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:960px;height:960px;max-width:none}.close img,.artifact{max-width:360px;height:auto}.small{font-size:13px;color:#b9c4c7}summary{cursor:pointer;padding:12px 0}</style>
<h1>Vietnamese land units · representative designs</h1>
<p>Judge the large shapes, equipment and player colors at game distance. Close views are available for inspection; minor close-only imperfections are acceptable.</p>
<p class="small">Actual Blender renders. Style review only; exports, cooks, import and native-game acceptance remain separate. Game images are clipped at their original pixel scale, not enlarged. Click any image to open its complete render.</p>'''
    html+=''.join(sections)+'<section id="reference"><h2>Historical references</h2><div class="row">'+''.join(photos)+'''</div>
<p class="small">These period ceramics and decorative figures inform the design; they do not establish surviving uniforms or a documented rattan-armor construction.</p></section>
<p class="small">Community Civilization Pack 0.6.0 · credits: hosein81 and chilly5 · final baseline: 0.5.3</p>'''
    owned(DEST).parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(html,encoding='utf-8')
    print(str(DEST))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,default=SELECTION)
    main(parser.parse_args().selection)
