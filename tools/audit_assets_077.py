"""Read-only release audit; writes only a separate report and fresh readback."""
from pathlib import Path
import hashlib, html, json, subprocess, sys, zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from workspace_support import check_storage

def read(p):
    return json.loads((ROOT / p).read_text(encoding='utf-8'))

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

cfg = read('workspace.json')
check_storage(ROOT, cfg)
out = ROOT / 'output/asset_audit_077'
out.mkdir(exist_ok=True)
delivery = ROOT / 'output/release_077/delivery/final-v1'
proof = read('output/release_077/delivery/final-v1/delivery-proof.json')
archive = delivery / 'community_civilization_pack.sga'
assert sha(archive) == proof['sga_sha256']
assert sha(proof['zip']) == proof['zip_sha256']
with zipfile.ZipFile(proof['zip']) as z:
    assert z.testzip() is None
    assert json.loads(z.read('garrison.json'))['details']['version'] == '0.7.7'
    assert hashlib.sha256(z.read(archive.name)).hexdigest() == proof['sga_sha256']

listing = json.loads(subprocess.check_output([cfg['archive_tool'], 'list', str(archive), '--verify'], text=True, encoding='utf-8'))
assert listing['archive']['verification']['verified']
assert listing['archive']['name'] == cfg['project_guid'].replace('-', '')
chain = [read(p) for p in [
    'output/release_073/verification-v1.json',
    'output/release_074/verification-v1.json',
    'output/release_075/candidates/review-v1/verification.json',
    'output/release_076/delivery/final-v1/verification.json',
    'output/release_077/delivery/final-v1/verification.json']]
audit = read('output/asset_audit_073/audit-inputs.json')
assert chain[0]['sga_sha256'] == audit['sga_sha256']
for prev, curr in zip(chain, chain[1:]):
    assert curr.get('baseline_sga_sha256', curr.get('baseline_sha256')) == prev['sga_sha256']
    before, after = prev['member_sha256'], curr['member_sha256']
    assert set(before) <= set(after)
    assert sorted(k for k in before if before[k] != after[k]) == sorted(curr['changed_members'])
    assert sorted(set(after) - set(before)) == sorted(curr.get('added_members', []))
assert chain[-1]['sga_sha256'] == proof['sga_sha256']
mounts = {m['path']: m['toc'] for m in listing['members']}
assert mounts == chain[-1]['mounts']
back = out / 'readback'
if not back.exists():
    subprocess.run([cfg['archive_tool'], 'extract', str(archive), str(back), '--filter', ''], check=True, capture_output=True)
actual = {p.relative_to(back).as_posix(): sha(p) for p in back.rglob('*') if p.is_file()}
assert actual == chain[-1]['member_sha256']

# Existing detailed graph audit is carried forward only across verified exact
# member comparisons. Later visual changes are recorded explicitly below.
assessment = read('output/asset_audit_073/assessment.json')
assessment['version'] = '0.7.7'
for row in assessment['buildings']:
    if row[0] == 'Economic Ministry':
        row[3] = 'Custom hall/yard compound, revised in 075; three static custom buffalo replace the decorative elephants in 077.'
for row in assessment['units']:
    if row[0] == 'Water Buffalo':
        row[1:] = ['Custom geometry', 'Shared', '076 buffalo body is selected through private cattle visual attachments; former elephant tier visuals are redirected to an empty private list. Supervision animation remains source-only.']
    elif row[0] == 'Lam Sơn Skirmisher':
        row[1:] = ['Custom geometry', 'II–IV', '076 supplies three custom body tiers, held javelins and matching projectile models, each with geometric LODs; native throwing lifecycle retained.']
assessment.pop('concurrent_nonvisual_source_changes', None)
assessment.pop('static_checks', None)
assessment['notes'] = [n for n in assessment['notes'] if not n.startswith('Static production')]
assessment['scope'] = 'Vietnam roster in Garrison 0.7.7. Custom refers to selected 3D models/materials, not icons, speech or gameplay. Family rows combine ages and variants. Availability is static graph evidence, not native-match proof. Other stock civilizations are outside this Vietnamese visual roster.'
assessment['method'] = 'Reuse detailed 073 actor/squad/inheritance/model-provenance audit after verifying each 073->074->075->076->077 member-hash delta. Update seven 075 building revisions, 076 buffalo/skirmisher bindings and 077 Ministry buffalo. Freshly verify final ZIP, archive identity and every extracted final member.'
assessment['verification'] = dict(sga_sha256=proof['sga_sha256'], members=len(actual), all_final_members_reextracted_and_hash_matched=True, archive_identity_verified=True, zip_verified=True, native_tested=False, chain=[dict(version=c['version'], sga_sha256=c['sga_sha256'], changed=len(c.get('changed_members', [])), added=len(c.get('added_members', []))) for c in chain])
assessment['evidence'] = ['output/asset_audit_073/actors.json', 'output/asset_audit_073/squads.json', 'output/asset_audit_073/reachability.json', 'output/asset_audit_073/model-provenance.json', 'output/release_075/candidates/review-v1/verification.json', 'output/release_076/integration/v1/recipe.json', 'output/release_077/delivery/final-v1/verification.json']
(out / 'assessment.json').write_text(json.dumps(assessment, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def table(headers, rows):
    return '<table><thead><tr>' + ''.join('<th>' + html.escape(s) + '</th>' for s in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + html.escape(str(v)) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'

page = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>Garrison 0.7.7 asset audit</title><style>body{font:16px/1.55 system-ui;background:#111722;color:#e8eaf0;max-width:1400px;margin:36px auto;padding:0 24px}h1,h2{color:#8fdae1}table{width:100%;border-collapse:collapse;margin:16px 0 30px}th,td{border:1px solid #455469;padding:10px;text-align:left;vertical-align:top}th{background:#253345}tr:nth-child(even){background:#192331}code{overflow-wrap:anywhere}</style>', '<h1>Garrison 0.7.7 — selected custom and stock assets</h1>', '<p>' + html.escape(assessment['scope']) + '</p>', '<p><b>Custom geometry:</b> authored/remodeled meshes. <b>Material remix only:</b> stock geometry with custom materials. <b>Partial:</b> custom additions with a stock main component. <b>Stock:</b> no selected custom replacement. Stock fallback does not mean a missing resource.</p>', '<p><b>Changes since the 073 audit:</b> seven building compounds revised in 075; Water Buffalo and Lam Sơn Skirmisher gain custom geometry in 076; Ministry yard has three static custom buffalo in 077.</p>', '<h2>Buildings</h2>', table(['Family','Status','Ages / variants','Detail'], assessment['buildings']), '<h2>Units</h2>', table(['Family','Status','Ages / variants','Detail'], assessment['units']), '<h2>Retained / alternate definitions</h2><p>These records exist, but the earlier construction/production graph did not establish them as active main-roster families. They are not silently added to the active art backlog.</p>', table(['Record','Status','Availability limit'], assessment['source_present_or_alternate']), '<h2>Component limits</h2><ul>' + ''.join('<li>' + html.escape(n) + '</li>' for n in assessment['notes']) + '</ul>', '<h2>Package verification</h2><p>' + html.escape(assessment['method']) + '</p><pre>' + html.escape(json.dumps(assessment['verification'], indent=2)) + '</pre><p>No gameplay, art, release package or normal-edition file was modified. This audit does not establish native appearance, animation, construction/ruins/repair, save/load or multiplayer.</p></html>']
target = ROOT / 'docs/ASSET_AUDIT_077.html'
target.write_text('\n'.join(page), encoding='utf-8')
print(json.dumps(dict(report=str(target), members=len(actual), buildings=len(assessment['buildings']), unit_groups=len(assessment['units']), verified=True)))
