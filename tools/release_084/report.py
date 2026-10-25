"""Offline evidence and human-readable handoff; never declares a native release."""
import contextlib,io,json,subprocess,sys,unittest
from pathlib import Path
from pipeline import save_json
from providers import ROOT,OUT

def main():
    syntax=[]
    for p in Path(__file__).parent.glob('*.py'):
        compile(p.read_text(encoding='utf-8-sig'),str(p),'exec');syntax.append(p.name)
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):result=unittest.TextTestRunner(stream=stream).run(suite)
    (OUT/'offline-tests.log').write_text(stream.getvalue(),encoding='utf-8')
    if not result.wasSuccessful():raise SystemExit('Offline tests failed; see offline-tests.log')
    baseline=subprocess.run([sys.executable,'-X','utf8','-B',str(Path(__file__).with_name('freeze.py'))],capture_output=True,text=True,check=True)
    (OUT/'baseline-recheck.log').write_text(baseline.stdout,encoding='utf-8')
    subprocess.run([sys.executable,'-X','utf8','-B',str(Path(__file__).with_name('checkpoint.py'))],check=True)
    coverage=json.loads((OUT/'checkpoint.json').read_text())
    proof=dict(offline_tests=dict(run=result.testsRun,failures=len(result.failures),errors=len(result.errors)),
        python_sources_compiled=len(syntax),baseline_recheck=baseline.stdout.strip(),
        audio=coverage,native_compile='not_run',new_archive_assembly='not_run',new_zip='not_built')
    save_json(OUT/'verification.json',proof)
    balances=json.loads((OUT/'generation/account-balances.json').read_text())
    text=['# Garrison 0.8.4 partial voice checkpoint','',
        'The approved full release is incomplete. No 0.8.4 native archive or Garrison ZIP has been built.',
        '',f"Automatically accepted recordings: **{coverage['accepted']} / {coverage['required']}**. Directed slots covered: {coverage['covered_slots']} / {coverage['directed_slots']}.",
        '', 'Audio passes automated format, waveform, recipe/hash and text/nonlexical checks. Pronunciation, acting and historical authenticity still require listening; historical pronunciation is a creative approximation.',
        '', '| Role | Accepted | Required | Provider | Actor |','|---|---:|---:|---|---|']
    for role,row in coverage['roles'].items():text.append(f"| {role} | {row['accepted']} | {row['required']} | {row['provider']} | {row['voice']} |")
    text+=['','## Budget','', 'Only the three supplied ElevenLabs accounts and existing Inworld credits were used. No credit purchase, overage change, Google generation or scheduled automation was performed.',
        '','Inworld stopped with HTTP 402; its unfinished roles keep their original actors. The final ElevenLabs balances below are the latest service reports; small balances may be insufficient for another checked request.','']
    for row in balances['accounts']:text.append(f"- Account {row['account']}: {row['remaining']} of {row['limit']} credits remaining.")
    text+=['','## Verification','',f"- {result.testsRun} offline tests passed; {len(syntax)} Python source files compiled.",
        '- Baseline identity, final-v2 ZIP/SGA hashes and 7,847 protected normal/source/art files rechecked unchanged.',
        '- Accepted audio was freshly checked for matching recipe/hash, mono 48 kHz 16-bit PCM format, silence/clipping/duration and duplicate recording hashes.',
        '- All 686 required pools retain 18 distinct jobs. Missing jobs remain required; failed or exhausted jobs are not counted as coverage.',
        '- Native compilation, new archive identity/readback and new ZIP verification have not run.',
        '- Native import, audible quality, age/gender routing, stock overlap, save/load and multiplayer remain unverified.',
        '', '## Files','',
        '[Partial listening page](<'+(OUT/'LISTEN_PARTIAL.html').as_posix()+'>)',
        '[Machine-readable checkpoint](<'+(OUT/'checkpoint.json').as_posix()+'>)',
        '[Verification receipts](<'+(OUT/'verification.json').as_posix()+'>)',
        '', 'Provider originals, failed responses, auditions, submitted-request markers and accepted playback remain under output/release_084. Credentials are excluded. State and job manifests support resumption; never recast a started role or install this as a full release.',
        '', '## Remaining implementation','',
        'Complete the required voice banks; finish SCAR-only/naval ownership reconciliation; generate the audio bank and proven Garrison.audio embedding; apply presentation-only paired squad/entity/attachment speech suppression for fully covered consumers; run tuning/inheritance preservation checks and actual native compilation; verify final namespace, fresh SGA member/mount readback and the ordinary version-0.8.4 ZIP. The dispatcher is a tested template, not active native integration.']
    (ROOT/'docs/RELEASE_084_CHECKPOINT.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print('084_OFFLINE_VERIFICATION',result.testsRun,'TESTS_PASSED',coverage['accepted'],'ACCEPTED',flush=True)

if __name__=='__main__':main()
