"""Validate dossier content and source preservation; never runs game tools/builds."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import re
import sys
import unicodedata

ROOT=Path(__file__).resolve().parent.parent
assert ROOT.name=='0.8.0'
SOURCE=ROOT.parent
errors=[]
checks=[]
def require(ok,label):
    if not ok: errors.append(label)
def load(name): return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

data=load('VOICE_SCRIPTS.json')
profiles=data['profiles']; ages=data['ages']; lines=data['lines']
required=['README.md','HISTORY_AND_LANGUAGE.md','SOURCES.md','UNIT_COVERAGE.md','CASTING_AND_DELIVERY.md',
          'VOICE_SCRIPTS.md','RECORDING_HANDOFF.md','TECHNICAL_PREPARATION.md','SCRIPT_ACCOUNTING.md','SAMPLE_LINES.md',
          'UNIT_INVENTORY.json','UNIT_VOICE_MAP.json','SPEECH_CONSUMERS.json','NATIVE_CONTEXT_MAPPING.json','PRONUNCIATION_LEXICON.json']
for name in required: require((ROOT/name).is_file(),'missing '+name)
checks.append('Required deliverable files')

source_ids=set(re.findall(r'\*\*([LHG]\d{2}) —', (ROOT/'SOURCES.md').read_text(encoding='utf-8')))
source_ids|={'G01','G02','G03','G04'}
groups=defaultdict(list)
ids=[]
text_groups=defaultdict(list)
for row in lines:
    ids.append(row['id']); p=row['profile'];age=row['age_bank'];ctx=row['context']
    groups[(p,age,ctx)].append(row)
    require(p in profiles and age in ages,'undefined actor or age '+row['id'])
    require(row['actor_id']==profiles[p]['actor_id'],'actor identity mismatch '+row['id'])
    require(len(row['takes'])==3 and [t['take'] for t in row['takes']]==['T1','T2','T3'],'three takes '+row['id'])
    require(all(t['new_performance_required'] and not t['text_change_allowed'] for t in row['takes']),'take policy '+row['id'])
    require(len({t['direction'] for t in row['takes']})==3,'distinct take directions '+row['id'])
    require(set(row['source_ids'])<=source_ids,'undefined source '+row['id'])
    require(row['recording_status']=='not_recorded' and not row['activation']['implemented'],'false runtime/audio claim '+row['id'])
    if row.get('kind')=='nonverbal_effort':
        require(row['vietnamese'] is None and row['english_meaning'] is None,'nonverbal contains dialogue '+row['id'])
        text=row['performance_description']
    else:
        text=row['vietnamese']
        require(bool(text) and bool(row['english_meaning']),'missing dialogue/meaning '+row['id'])
        require(unicodedata.is_normalized('NFC',text),'not NFC '+row['id'])
        require(row['dialogue_status']=='original_creative_adaptation_not_historical_quote','attestation overclaim '+row['id'])
        require(row['pronunciation']['historical_ipa'] is None,'unexpected whole-line IPA '+row['id'])
        require(bool(row['pronunciation']['syllables']),'missing pronunciation breakdown '+row['id'])
        require(bool(row.get('historical_rationale')) and 'Intent:' in row['historical_rationale'],'missing phrase-specific rationale '+row['id'])
        require(isinstance(row.get('lexical_notes'),list) and bool(row.get('source_locators')),'missing lexical/source locator fields '+row['id'])
    if p=='ELEPHANT':
        require(row.get('recording_gate')=='blocked_until_actual_human_voice_owner_verified','elephant human voice gate missing '+row['id'])
    d=hashlib.sha256(text.encode('utf-8')).hexdigest()
    require(d==row['semantic_text_sha256'],'semantic text hash '+row['id'])
    text_groups[d].append(row)
require(len(ids)==len(set(ids)),'duplicate stable IDs')
for (p,age,ctx),rows in groups.items():
    require(len(rows)==6,'six rows '+str((p,age,ctx)))
    require(len({r.get('vietnamese') or r.get('performance_description') for r in rows})==6,'six distinct phrases/directions '+str((p,age,ctx)))
for p in profiles:
    for age in ages:
        for ctx in profiles[p]['contexts']:
            require((p,age,ctx) in groups,'missing requested bank '+str((p,age,ctx)))
for d,rows in text_groups.items():
    if len(rows)>1:
        require(all(r['intentional_reuse']['present'] for r in rows),'undisclosed reuse '+d)
        require(set(data['reuse_groups'].get(d,[]))=={r['id'] for r in rows},'incomplete reuse group '+d)
checks.append('Stable IDs, actor/age/context coverage, six unique phrases and three distinct take directions')
checks.append('Pronunciation, source references, creative status and disclosed text reuse')

tracks=defaultdict(list)
for row in lines:
    if row.get('kind')!='nonverbal_effort': tracks[(row['profile'],row['context'],row['phrase_number'])].append(row['vietnamese'])
audit=load('AGE_VARIATION_AUDIT.json')
require(audit['dialogue_tracks_compared']==len(tracks),'age diversity track count')
require(audit['tracks_with_identical_text_all_four_ages']==sum(len(set(v))==1 for v in tracks.values()),'age wording reuse accounting')

dialogue=[r for r in lines if r.get('kind')!='nonverbal_effort']
effort=[r for r in lines if r.get('kind')=='nonverbal_effort']
t=data['totals']
require(t['dialogue_rows']==len(dialogue) and t['effort_rows']==len(effort),'row totals')
require(t['total_directed_takes']==len(lines)*3,'take totals')
require(t['distinct_dialogue_texts']==len({r['vietnamese'] for r in dialogue}),'unique text totals')
require(t==load('SCRIPT_TOTALS.json'),'totals receipt mismatch')
companion=(ROOT/'VOICE_SCRIPTS.md').read_text(encoding='utf-8')
md_ids=re.findall(r'\| (VN070_[A-Z0-9_]+) \|',companion)
require(Counter(md_ids)==Counter(ids),'readable companion omits or duplicates JSON line IDs')
checks.append('JSON/readable companion complete parity and recording accounting')

inv=load('UNIT_INVENTORY.json'); mapping=load('UNIT_VOICE_MAP.json')['entries']
mapped={r['consumer_id'] for r in mapping}
require({r['id'] for r in inv['local_squad_definitions']}<=mapped,'unmapped local squads')
require(set(inv['ebps_squad_consumers'])<=mapped,'unmapped producer references')
require({r['id'] for r in inv['official_inherited_naval_roster']}<=mapped,'unmapped naval roster')
for row in mapping:
    require(row['mapping_status'].startswith('excluded_') or bool(row['profile_candidates']) or row['mapping_status']=='unresolved_role','unclassified consumer '+row['consumer_id'])
    require(set(row['profile_candidates'])<=set(profiles),'undefined consumer profile '+row['consumer_id'])
    if row['profile_candidates']==['NAVAL_TRANSPORT']:
        require(row['equipment_filter']=='no_attack_or_weapon_lines','transport combat leakage')
require(len(inv['official_inherited_naval_roster'])==7,'expected seven inherited naval queue members')
checks.append('Every inventoried squad/producer/naval row maps to profiles or explicit exclusions/unresolved status')

native=load('NATIVE_CONTEXT_MAPPING.json')
expected=set()
for f in (ROOT/'research_tools/profile_json').glob('*.json'):
    d=json.loads(f.read_text(encoding='utf-8-sig'))
    expected|={(f.stem+'.spd',r['context']) for r in d.get('records',[])}
    spd=ROOT/'research_tools/stock_profiles'/(f.stem+'.spd')
    require(spd.is_file() and digest(spd)==d['sha256'],'decoded SPD source hash '+f.name)
require(expected=={(r['stock_profile'],r['raw_context']) for r in native['entries']},'native contexts lost in crosswalk')
require(not native['unresolved_prefixes'],'unmapped native prefix (explicit gap required)')
checks.append('All decoded stock context strings retained; raw SPD hashes match structural decoder receipts')

content_errors=list(errors)
before=load('SOURCE_PRESERVATION_BEFORE.json')
# Baseline schema from the read-only inventory worker; accept its actual shape.
baseline_files=before.get('files') or before.get('entries') or []
if isinstance(baseline_files,dict): baseline_files=[{'path':p,**v} if isinstance(v,dict) else {'path':p,'sha256':v} for p,v in baseline_files.items()]
require(bool(baseline_files),'no baseline files available')
changed=[]
comparison=[]
for item in baseline_files:
    rel=item.get('path') or item.get('relative_path')
    path=SOURCE/rel
    actual=digest(path) if path.is_file() else None
    if actual!=item['sha256']: changed.append(rel)
    comparison.append({'path':rel,'before_sha256':item['sha256'],'after_sha256':actual,
       'unchanged':actual==item['sha256'],
       'current_mtime_utc_epoch':path.stat().st_mtime if path.is_file() else None})
require(not changed,'protected editable source changed: '+str(changed[:12]))
checks.append('Preservation baseline SHA-256 comparison for '+str(len(baseline_files))+' protected files; excludes art and external/output caches as recorded')

audio_ext={'.wav','.wem','.ogg','.mp3','.flac','.aac'}
unexpected_audio=[p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in audio_ext]
require(not unexpected_audio,'audio generated/copied unexpectedly: '+str(unexpected_audio))
if unexpected_audio: content_errors.append('unexpected audio files')
checks.append('Zero audio files; stock SPD metadata is not audio media')

(ROOT/'SOURCE_PRESERVATION_AFTER_080.json').write_text(json.dumps({
  'schema':'voice-preparation.source-comparison/v1','baseline':'SOURCE_PRESERVATION_BEFORE.json',
  'status':'unchanged' if not changed else 'drift_observed_baseline_not_refreshed',
  'checked_files':len(comparison),'unchanged_files':len(comparison)-len(changed),
  'changed_paths':changed,'comparisons':comparison,
  'note':'This preparation writes only 0.8.0. Changes outside that folder are left intact and must not be erased to obtain a passing hash comparison.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'CONTENT_VALIDATION_080.json').write_text(json.dumps({
  'schema':'voice-preparation.content-validation/v1','status':'passed' if not content_errors else 'failed',
  'errors':content_errors,'checks':checks[:-2]+[checks[-1]],
  'scope':'Dossier content only. Read VALIDATION_080.json and SOURCE_PRESERVATION_AFTER_080.json for the separate strict source-preservation gate.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

result={'schema':'voice-preparation.validation/v1','status':'passed' if not errors else 'failed',
        'content_status':'passed' if not content_errors else 'failed',
        'source_preservation_status':'unchanged' if not changed else 'drift_observed',
        'checks':checks,'errors':errors,'counts':t,'protected_files_checked':len(baseline_files),
        'protected_changes':changed,'native_profiles':len(list((ROOT/'research_tools/profile_json').glob('*.json'))),
        'native_contexts':len(expected),'consumer_mapping_rows':len(mapping),
        'gates_not_run':['native Vietnamese editorial review','historical linguistic approval','recording/auditions','encoding/cook/build','package/import/lobby','audible native match','multiplayer']}
(ROOT/'VALIDATION_080.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
sys.exit(1 if errors else 0)
