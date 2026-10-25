"""Present actual Blender evidence without altering or synthesizing screenshots."""
from html import escape
from pathlib import Path
from urllib.parse import quote
import os

from common import OUT, RECIPES, owned, read, sha

DEST = OUT/'review/index.html'


def preview(label, record):
    path = Path(record['path'])
    if not path.resolve().is_relative_to(OUT.resolve()):
        raise ValueError(f'Preview outside release evidence: {path}')
    if not path.is_file() or sha(path) != record['sha256']:
        raise ValueError(f'Preview missing or changed since receipt: {path}')
    link = quote(os.path.relpath(path, DEST.parent).replace('\\', '/'), safe='/')
    return f'<figure><a href="{link}" target="_blank"><img src="{link}" loading="lazy" alt="{escape(label)}"></a><figcaption>{escape(label)}</figcaption></figure>'


def main():
    sections = []
    directions = {item['pilot']: item for item in read(RECIPES/'historical-reference.json')['pilot_directions']}
    def direction(identifier):
        item = directions['siege_sample' if identifier == 'siege_mangonel3' else identifier]
        return ('<details><summary>Design direction and historical evidence</summary>'
                f'<p>{escape(item["silhouette"])}</p><p>{escape(item["clothing_equipment"])}</p>'
                f'<p class="gate">{escape(item["evidence"])}</p>'
                '<p><a href="#references">Inspect the period objects and museum sources below.</a></p></details>')
    checkpoints = sorted((OUT/'qualification').glob('archer-v3*-review/presentation.json'))
    if checkpoints:
        latest = read(checkpoints[-1])
        source = Path(latest['source'])
        if sha(source) != latest['source_sha256']:
            raise ValueError('Latest Archer checkpoint source changed')
        images = ''.join(preview(name+' material inspection', record)
                         for name, record in latest['renders'].items())
        rejected = 'archer-v3'+checkpoints[-1].parent.name.split('archer-v3',1)[-1].split('-review',1)[0] in {'archer-v3a','archer-v3b','archer-v3c'}
        warning = ('Rejected diagnostic: the quiver bag was partly removed during clothing cleanup. '
                   'Restoration must start from the preserved v2c checkpoint. ' if rejected else '')
        sections.append('<section><h2>Archer II · clothing construction evidence</h2>'
            f'<p class="gate">{warning}Construction review in Blender. Cloth materials, headgear, '
            'shoulders and complete Rattan design remain in progress. This is not the '
            'representative style approval or native-game evidence.</p>'
            f'<p class="donor">Editable checkpoint: {escape(source.name)}</p>'
            f'<div class="images">{images}</div>{direction("archer2")}</section>')
    archer_path = OUT/'qualification/archer-sample.json'
    if archer_path.exists():
        archer = read(archer_path)
        pictures = ''.join(preview(name.replace('archer-', '').replace('-', ' '), record)
                           for name, record in archer['views'].items())
        issues = ''.join(f'<li>{escape(str(issue))}</li>' for issue in archer.get('review_issues', []))
        sections.append(f'<section><h2>Archer II · base and Rattan drafts</h2><p class="gate">Authoring prototype. Cook and native switch unqualified.</p><div class="images">{pictures}</div>{direction("archer2")}<details><summary>Review notes and technical limits</summary><ul>{issues}</ul></details></section>')
    index = read(OUT/'pilots/sample-index.json')
    for pilot in index['samples']:
        identifier = pilot['id']
        receipt_path = OUT/'pilots'/identifier/'review-textured.json'
        pictures = '<p>No textured comparison receipt yet.</p>'
        details = 'Authoring and visual qualification pending.'
        if receipt_path.exists():
            receipt = read(receipt_path)
            pictures = '<div class="images">' + ''.join(preview(name.replace('_', ' '), record)
                      for name, record in receipt['images'].items()) + '</div>'
            details = receipt['surface_limit'] + ' · ' + receipt['pose']
        pose_check = ''
        for folder in ('idle-inspection-v2', 'idle-inspection'):
            pose_receipt = OUT/'pilots'/identifier/folder/'receipt.json'
            if pose_receipt.exists():
                pose = read(pose_receipt)
                if sha(pose['blend']) != pose['blend_sha256']:
                    raise ValueError(f'Pose inspection blend changed: {pose["blend"]}')
                pose_check = ('<details open><summary>Stock idle alignment inspection</summary>'
                              '<p class="gate">Imported stock clip in Blender. Geometry and material redesign, '
                              'native gameplay tests and style approval remain pending.</p>'
                              + preview('Actual stock idle pose · solid inspection', pose['image'])
                              + f'<p>{escape(pose["appearance_review"])}</p></details>')
                break
        sections.append(f'<section><h2>{escape(pilot["name"])}</h2><p class="gate">{escape(details)}</p><p class="donor">Stock donor: {escape(pilot["official_donor_model"])}</p>{pictures}{pose_check}{direction(identifier)}</section>')
    references = read(OUT/'references/source-index.json')
    links = ''.join(f'<li><a href="{escape(item["page_url"], quote=True)}" target="_blank" rel="noreferrer">{escape(item["title"])}</a> — {escape(item["institution"])}</li>' for item in references['sources'])
    visual_refs = ''
    supplement = OUT/'references/visual-reference-supplement.json'
    if supplement.exists():
        credits = {'tran_jar_warriors': ('Gryffindor', 'CC BY-SA 3.0', 'https://creativecommons.org/licenses/by-sa/3.0/'),
                   'tran_ridge_figure': ('Daderot', 'CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/')}
        for item in read(supplement)['successful_visual_evidence']:
            author, license_name, license_url = credits[item['id']]
            visual_refs += (f'<figure><a href="{escape(item["image_record"], quote=True)}" target="_blank" rel="noreferrer">'
                            f'<img style="height:430px;object-fit:contain" src="{escape(item["direct_image"], quote=True)}" loading="lazy" alt="{escape(item["artifact"], quote=True)}"></a>'
                            f'<figcaption>{escape(item["artifact"])}<br>Photo: {author} · <a href="{license_url}">{license_name}</a> · Unmodified remote image.<br>'
                            f'{escape(item["visual_inspection"])}</figcaption></figure>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vietnamese land units · 0.6.0 workshop</title><style>
    *{box-sizing:border-box}body{margin:0;background:#171c1a;color:#e8e7dd;font:16px/1.6 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:40px 28px}h1{font-size:40px;line-height:1.1;margin:10px 0 20px}h2{font-size:25px;margin:0 0 12px}a{color:#d1b678}header{max-width:900px;margin-bottom:40px}.eyebrow{color:#c7ae72;text-transform:uppercase;letter-spacing:.14em}.notice{padding:18px 22px;border-left:3px solid #c7ae72;background:#252c28}section{padding:28px 0;border-top:1px solid #49514a}.gate{color:#d0b77e}.donor{font:13px/1.7 ui-monospace,monospace;overflow-wrap:anywhere;color:#b6c3b8}.images{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:0;background:#252b27;border:1px solid #434c44}figure img{display:block;width:100%;height:auto}figcaption{padding:12px 16px;text-transform:capitalize;color:#d2d9cf}li{margin:5px 0}footer{color:#aab7ad;padding:30px 0}@media(max-width:760px){main{padding:24px 16px}.images{grid-template-columns:1fr}h1{font-size:30px}}
    </style><main><header><p class="eyebrow">Community Civilization Pack · 0.6.0</p><h1>Vietnamese land-unit workshop</h1><p>Actual stock donors and Blender drafts. Open any image for its original capture.</p><p class="notice">Work in progress: Blender previews, with approximate game-view framing. Export, cook, the Rattan switch and native acceptance remain separate qualification gates.</p></header>'''
    page += ''.join(sections)
    page += f'<section id="references"><h2>Historical references</h2><p>Period objects and museum descriptions guide the designs. Clothing construction and Rattan equipment are artistic interpretations, not claims of exact surviving uniforms. These two artifact photographs were visually inspected. They do not establish civilian garment cuts or actual armor materials.</p><div class="images">{visual_refs}</div><ul>{links}</ul></section><footer>Credits: hosein81 and chilly5 · Representative style approval pending · No 0.6.0 ZIP produced.</footer></main></html>'
    target = owned(DEST)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
