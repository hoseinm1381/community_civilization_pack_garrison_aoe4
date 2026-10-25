"""Technical nonlexical screening; this never certifies acted pain or death."""
import json
import re
import unicodedata
from local_audition import DEST
from local_bank import local_guard, local_manifest
from pipeline import StateStore, digest, save_json
from providers import OUT
from quality import text_matches


def nonlexical(text):
    if text.strip().casefold() in ['(groans)','(grunts)','(sighs)','[groans]','[grunts]','[sighs]']: return True
    # Retain Vietnamese tone/vowel distinctions: ở, hạ and hư are words.
    # Empty ASR is ambiguous, not positive evidence of a nonverbal performance.
    base = unicodedata.normalize('NFC',text.casefold())
    words = re.findall(r'\w+',base)
    return 0<len(words)<=3 and all(w in {'hự','ư','á','hừ','a','ơ','ah','ha','hu','huu','u','uh','uhm','um','o','oh','ugh','huh','mm','mmm'} for w in words)


def performance_matches(job, text):
    return text_matches(job['text'],text) if job['kind']=='dialogue' else nonlexical(text)


def verified_performance(job, verification):
    if verification.get('prompted') is not False or verification.get('expected')!=job['text']: return False
    texts=[verification.get(k) for k in ['phowhisper','whisper']]
    if job['kind']=='nonverbal_effort':
        return all(text is not None and nonlexical(text) for text in texts)
    texts.append(verification.get('phowhisper_medium'))
    return any(text is not None and performance_matches(job,text) for text in texts)


def prepare():
    local_guard()
    path=DEST/'recording-manifest.json';old=json.loads(path.read_text())
    voices={j['role']:j['casting']['voice'] for j in old['jobs']}
    new=local_manifest(json.loads((OUT/'recording-manifest.json').read_text()),voices)
    keep={j['id'] for j in new['jobs']}
    started=set(StateStore(DEST/'generation').data)
    for request in (DEST/'generation').glob('*/attempt-*/request-started.json'):
        started.add(json.loads(request.read_text())['job']['id'])
    if started-keep: raise RuntimeError('Cannot change a started recording recipe')
    if old!=new:
        archive=DEST/'manifest-revisions'/(digest(path)+'.json')
        archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists(): archive.write_bytes(path.read_bytes())
        save_json(path,new)
    print('LOCAL_EFFORT_RECIPES_PREPARED',sum(j['kind']=='nonverbal_effort' for j in new['jobs']))


if __name__=='__main__':prepare()
