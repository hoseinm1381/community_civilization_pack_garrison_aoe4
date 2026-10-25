"""Rebuild preparation documents only. Never builds or imports an AoE4 mod.

Run from any directory with the bundled Python. All writes are confined to the
parent 0.8.0 directory. Hand-edited dialogue belongs in script_texts.py.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import re
import unicodedata
from script_texts import TEXTS, ROLE_SELECT, EFFORTS
from age_texts import AGE_TEXTS

ROOT = Path(__file__).resolve().parent.parent
assert ROOT.name == '0.8.0'

AGES = {
 'A1': {'game_age': 'Dark', 'years': [700, 1000], 'range_kind': 'editorial_not_linguistic_boundary',
        'direction': 'Concrete, direct phrasing; early historical realization requires specialist reconstruction. Do not imitate broken modern Vietnamese.',
        'historical_pronunciation_status': 'whole_line_unresolved'},
 'A2': {'game_age': 'Feudal', 'years': [1000, 1250], 'range_kind': 'editorial_not_linguistic_boundary',
        'direction': 'Practical vernacular with settled confidence; retain only individually reviewed early sound features.',
        'historical_pronunciation_status': 'whole_line_unresolved'},
 'A3': {'game_age': 'Castle', 'years': [1250, 1500], 'range_kind': 'editorial_not_linguistic_boundary',
        'direction': 'Concise collective and occupational phrasing; literate register only where the role warrants it. Nôm evidence is word-specific.',
        'historical_pronunciation_status': 'whole_line_unresolved'},
 'A4': {'game_age': 'Imperial', 'years': [1500, 1700], 'range_kind': 'editorial_not_linguistic_boundary',
        'direction': 'Clear practiced occupational delivery; seventeenth-century Middle Vietnamese target needs Northern dialect review, not automatic modern Hanoi.',
        'historical_pronunciation_status': 'whole_line_unresolved'},
}

# These context definitions are editorial semantic categories. Native labels and
# proof are kept separately; a matching phrase is never a new SCAR trigger.
CONTEXTS = {}
def context(key, text_key=None, evidence='proposed_adapter_context', native=(), sources=('G03', 'G04'), condition='Only after actual trigger/capability is traced.'):
    CONTEXTS[key] = {'text_key': text_key or key, 'evidence_status': evidence,
                     'native_context_hints': list(native), 'source_ids': list(sources),
                     'activation_condition': condition, 'runtime_implemented': False}

context('select', 'select_{age}', 'stock_profile_context', ('select',), condition='Verified selected squad/actor; one responder for a group.')
context('acknowledge', evidence='stock_profile_context', native=('acknowledge','acknowledgeGMR'), condition='A verified acknowledgement event; GMR routing meaning remains unresolved.')
context('marching_idle', evidence='stock_profile_context', native=('marchingIdle',), condition='Only the observed native marching-idle context; no polling-driven ambient chatter is added.')
context('role_select', 'ROLE_SELECT', 'proposed_text_alternative_for_stock_select', ('select',), condition='Same selection event as select; pools are alternatives, never both played.')
context('move', 'move_{age}', 'stock_profile_context', ('move',), condition='Confirmed movement acknowledgement; do not assume every right-click target is movement.')
context('attack', 'melee_{age}', 'stock_profile_context', ('attack',), condition='Confirmed explicit attack; context-specific family bank overrides generic melee wording.')
context('attack_move', 'melee_{age}', 'stock_profile_context', ('attackMove',), condition='Explicit attack-move; intentionally reuses attack text, a separately recorded trigger slot.')
context('retreat', 'retreat_{age}', condition='Only a verified retreat/flee route; do not infer solely from low health.')
context('stop', evidence='stock_profile_context', native=('stop',), condition='Confirmed explicit stop order.')
context('hold', 'guard', 'stock_profile_context', ('hold',), condition='Confirmed hold-position order; no new defensive mechanic.')
context('guard', 'guard', condition='Verified guard/protect capability; not the same as hold by assumption.')
context('garrison', evidence='stock_profile_context', native=('garrison',), condition='Verified garrison order into a permitted structure/transport.')
context('ungarrison', evidence='proposed_adapter_context', native=('unload',), condition='Verified ungarrison/unload callback for this exact owner.')
context('celebrate', evidence='stock_profile_context', native=('celebrate',), condition='Verified celebration event; not inferred from a random kill.')
context('flee', evidence='stock_profile_context_semantics', native=('fear',), condition='Only actual fear/flee context; no morale mechanic is added.')
context('stealth', evidence='stock_delivery_and_local_ability_candidate', native=('iStealth',), condition='Verified concealed/stealth presentation or existing ability; iStealth is a raw label, not a universal trigger.')
context('ability_ack', condition='Named existing ability and verified event required; no automatic response for all abilities.')
for k in ['farm', 'forage', 'hunt', 'herd', 'wood', 'gold', 'stone', 'build', 'repair', 'carry', 'trade', 'trade_return', 'tax', 'supervise', 'heal', 'relic', 'convert', 'explore']:
    context(k, sources=('G04', 'L03'), condition='Confirm the exact task/ability and unit capability from the source inventory; proposed text does not prove trigger observability.')
for k in ['horse_move', 'elephant_move', 'siege_move', 'sail']:
    context(k, evidence='proposed_family_text_for_stock_move', native=('move',), condition='Same move event, family-specific alternative only; no second simultaneous line.')
for k in ['spear', 'sword', 'bow', 'crossbow', 'gun', 'horse_attack', 'elephant_attack', 'siege_attack', 'siege_ram', 'naval_attack']:
    context(k, evidence='proposed_family_text_for_stock_attack', native=('attack',), condition='Same attack event, gated to the actual weapon/crew; no second simultaneous line.')
for k in ['siege_deploy', 'siege_pack']:
    context(k, condition='Only an actor with verified pack/unpack or setup capability; never play for every siege unit.')
context('naval_stop', evidence='proposed_family_text_for_stock_stop', native=('stop',), condition='Vessel stop context; avoid land-specific words.')
context('fish', evidence='stock_profile_context', native=('resourceFish',), sources=('G04', 'H06'), condition='Verified fishing ship/resource task; no land-unit fishing assumed.')
context('naval_trade', evidence='stock_profile_context_semantics', native=('setUpTradeRoute', 'tradeRouteSet'), sources=('G04', 'H06'), condition='Verified naval trade-route event; do not treat movement alone as route establishment.')
context('naval_trade_return', evidence='proposed_adapter_context', native=('dropoff',), sources=('G04', 'H06'), condition='Verified trade return/dropoff, not a timer guessing the journey is done.')
context('transport_load', evidence='stock_profile_context', native=('garrison',), condition='Verified ownable transport and loading event; ship profile membership alone is not a usable transport.')
context('transport_unload', evidence='stock_profile_context', native=('unload',), condition='Verified transport unloading event.')
for k, raw in [('under_attack','underAttack'), ('target_destroyed','targetDestroyed'), ('enemy_spotted','enemySpotted'), ('formation','formation'), ('aim','weaponAim'), ('detonate','detonate'), ('pickup_carcass','pickUpCarcass'), ('dropoff_carcass','dropOffCarcass'), ('fish_dropoff','dropoff')]:
    context(k, evidence='stock_profile_context_semantics', native=(raw,), condition='Trace the exact native record and consumer. Not automatically observable through a scripted route.')

PROFILE_META = {
 'CIV_M': ('VM01', 'male civilian', 'Warm mid baritone, practical and unhurried; adult, no peasant caricature.', ['L03','H01']),
 'CIV_F': ('VF01', 'female civilian', 'Clear lower mezzo, capable and grounded; adult, equal task coverage.', ['L03','H01']),
 'SCOUT': ('VM02', 'scout', 'Light tenor with alert focus; quiet breath control, keen observation.', ['H03','L03']),
 'INFANTRY': ('VM03', 'spearman / fire-lance / man-at-arms', 'Firm middle baritone; coordinated rank voice, no fantasy growl.', ['H03','L01']),
 'ARCHER': ('VM04', 'archer', 'Focused upper baritone; precise diction and restrained breath.', ['H03','L03']),
 'CROSSBOW': ('VM05', 'crossbowman', 'Compact mid register, patient technical confidence.', ['H03','L03']),
 'GUNNER': ('VM06', 'handgunner', 'Dry centered baritone; measured firing directions, no modern drill-sergeant accent.', ['H05','L02']),
 'CAVALRY': ('VM07', 'horseman / knight', 'Open resonant middle register, mobile breath, controlled projection.', ['H01','L03']),
 'MONK': ('VM08', 'religious unit', 'Mature gentle low tenor; articulate, humane, no fabricated chant.', ['H02','L03']),
 'OFFICIAL': ('VM09', 'official', 'Measured middle voice, literate precision without pompous comedy.', ['H07','L03']),
 'TRADER': ('VM10', 'land trader', 'Conversational middle tenor, reliable and observant, no sales caricature.', ['H06','L03']),
 'ELEPHANT': ('VM11', 'human elephant handler / crew caller', 'Strong low middle voice, patient rhythmic calls; never an animal imitation.', ['H03','L03']),
 'SIEGE': ('VM12', 'human siege crew caller', 'Broad middle baritone, shared-labor rhythm and concise coordination.', ['H05','L03']),
 'NAVAL_FISH': ('VM13', 'fishing crew caller', 'Easy weathered tenor, economical river-worker delivery; no pirate accent.', ['H06','H03']),
 'NAVAL_TRADE': ('VM14', 'trade vessel caller', 'Even mid register, practical cargo handling and navigation.', ['H06','L02']),
 'NAVAL_MILITARY': ('VM15', 'combat vessel caller', 'Projected baritone, clear bearing and coordinated commands.', ['H03','H04']),
 'NAVAL_TRANSPORT': ('VM16', 'transport vessel caller', 'Steady low tenor, reassuring boarding instructions without claims of invulnerability.', ['H03','H06']),
 'NAVAL_FIRE': ('VM17', 'demolition vessel caller', 'Tense focused mid voice; commitment and warnings, no maniacal laugh.', ['H03','H05']),
}

CIV_TASKS = ['farm','forage','hunt','herd','wood','gold','stone','build','repair','carry']
COMMON = ['select','role_select','acknowledge','move','stop','hold','under_attack','flee','celebrate']
MILITARY = ['attack','attack_move','retreat','target_destroyed','formation']
PROFILE_CONTEXTS = {
 'CIV_M': COMMON + CIV_TASKS + ['attack','retreat','garrison','ungarrison','ability_ack'],
 'CIV_F': COMMON + CIV_TASKS + ['attack','retreat','garrison','ungarrison','ability_ack'],
 'SCOUT': COMMON + MILITARY + ['explore','enemy_spotted','hunt','herd','pickup_carcass','dropoff_carcass','horse_move','horse_attack','garrison','ungarrison','marching_idle'],
 'INFANTRY': COMMON + MILITARY + ['spear','sword','garrison','ungarrison','guard','ability_ack'],
 'ARCHER': COMMON + MILITARY + ['bow','aim','stealth','garrison','ungarrison','ability_ack'],
 'CROSSBOW': COMMON + MILITARY + ['crossbow','aim','garrison','ungarrison'],
 'GUNNER': COMMON + MILITARY + ['gun','aim','garrison','ungarrison'],
 'CAVALRY': COMMON + MILITARY + ['horse_move','horse_attack','guard','ability_ack'],
 'MONK': COMMON + ['heal','relic','convert','retreat','garrison','ungarrison','ability_ack'],
 'OFFICIAL': COMMON + ['tax','supervise','carry','retreat','garrison','ungarrison'],
 'TRADER': COMMON + ['trade','trade_return','retreat'],
 'ELEPHANT': COMMON + MILITARY + ['elephant_move','elephant_attack','aim','ability_ack'],
 'SIEGE': COMMON + MILITARY + ['siege_move','siege_attack','siege_ram','siege_deploy','siege_pack','aim'],
 'NAVAL_FISH': ['select','role_select','acknowledge','sail','naval_stop','hold','under_attack','flee','celebrate','fish','fish_dropoff','repair'],
 'NAVAL_TRADE': ['select','role_select','acknowledge','sail','naval_stop','hold','under_attack','flee','celebrate','naval_trade','naval_trade_return'],
 'NAVAL_MILITARY': ['select','role_select','acknowledge','sail','naval_stop','hold','under_attack','flee','celebrate','naval_attack','aim','target_destroyed'],
 'NAVAL_TRANSPORT': ['select','role_select','acknowledge','sail','naval_stop','hold','under_attack','flee','celebrate','transport_load','transport_unload'],
 'NAVAL_FIRE': ['select','role_select','acknowledge','sail','naval_stop','hold','under_attack','flee','celebrate','naval_attack','detonate','target_destroyed'],
}

LEXICON = [
 {'id':'LEX_SKY_OLD', 'modern_form':'trời', 'meaning':'sky / heaven', 'source_form':'*plời',
  'historical_ipa_feature':'/pl-/', 'feature_scope':'initial only; not a full word or sentence transcription',
  'source_ids':['L01'], 'locator':'p.55 note 2 and p.59, §1.3',
  'status':'scholarly_reconstructed_initial_projected_modern_rime',
  'direction':'Do not turn this into a global tr-to-pl rule. Not scheduled in current spoken lines.'},
 {'id':'LEX_SKY_NOM', 'modern_form':'trời', 'meaning':'sky / heaven', 'source_form':'pləj²',
  'historical_ipa_feature':'pləj²', 'feature_scope':'source reconstruction notation, tone category 2; no absolute F0 specified',
  'source_ids':['L03'], 'locator':'Phàm lệ, §B.3 Chính tả',
  'status':'source_IPA_like_reconstruction_not_new_phonetic_measurement',
  'direction':'Specialist comparison only. Do not collapse this with L01 notation.'},
 {'id':'LEX_SKY_MIDDLE', 'modern_form':'trời', 'meaning':'sky / heaven', 'source_form':'blời',
  'historical_ipa_feature':None, 'feature_scope':'historical spelling cited indirectly, not complete IPA',
  'source_ids':['L01','L05'], 'locator':'Gong p.59 cites Rhodes 1651, column 45',
  'status':'historical_orthography_indirect',
  'direction':'Collate original scan before prescribing a Northern pronunciation.'},
 {'id':'LEX_SWORD', 'modern_form':'gươm', 'meaning':'sword', 'source_form':'gươm',
  'historical_ipa_feature':None, 'feature_scope':'historical lexical comparison; not a dated command',
  'source_ids':['L01'], 'locator':'p.57, §1.2', 'status':'lexical_history_background',
  'direction':'Current sword lines remain creative; do not substitute a proposed proto-form automatically.'},
 {'id':'LEX_TA_MODERN', 'modern_form':'ta', 'meaning':'we / our; self-reference depends on context',
  'source_form':'ta', 'historical_ipa_feature':None, 'modern_rehearsal_ipa':'/ta/ + ngang category',
  'feature_scope':'broad modern rehearsal segments and named tone, not medieval IPA',
  'source_ids':['L04'], 'locator':'p.382 initial-consonant examples', 'status':'modern_only',
  'direction':'Pronoun review required in every role; player is not automatically sovereign.'},
 {'id':'LEX_CHANG', 'modern_form':'chăng', 'meaning':'interrogative/modal candidate',
  'source_form':'chăng…thì chớ', 'historical_ipa_feature':None,
  'feature_scope':'inspected literary dictionary sense; not whole-sentence or A1 attestation',
  'source_ids':['L03'], 'locator':'chăn/chăng entry page: chăng sense 2, Ngôn chí 16.8 and Tự thán 77.8',
  'status':'literary_lexical_evidence_period_of_earlier_use_unresolved', 'direction':'A few draft questions use chăng; native editor must judge pragmatics. Not a universal A1 marker.'},
 {'id':'LEX_CHAN', 'modern_form':'chăn', 'meaning':'tend grazing livestock',
  'source_form':'chăn', 'historical_ipa_feature':None,
  'feature_scope':'literary lexical sense, not period pronunciation',
  'source_ids':['L03'], 'locator':'chăn verb entry, Thủ vĩ ngâm 1.4',
  'status':'inspected_dictionary_lexical_evidence', 'direction':'Useful herd-task lexical candidate; current full herd sentences remain creative adaptations.'},
]

def write_json(name, obj):
    target = ROOT / name
    assert target.resolve().parent == ROOT
    target.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def modern_guide(vi):
    syllables = re.findall(r"[^\W\d_]+", vi, flags=re.UNICODE)
    categories = []
    marks = {'\u0300':'huyền','\u0301':'sắc','\u0309':'hỏi','\u0303':'ngã','\u0323':'nặng'}
    for syll in syllables:
        d = unicodedata.normalize('NFD', syll)
        tone = next((name for mark,name in marks.items() if mark in d), 'ngang')
        categories.append({'written_syllable':syll,'orthographic_tone_category':tone})
    return {'kind':'modern_written_rehearsal_only', 'syllables':categories,
            'instruction':'Native Northern reader: retain marked lexical tones and closed final stops; read connected speech naturally. This is not a medieval phonetic transcription.',
            'source_ids':['L04'], 'historical_ipa':None,
            'historical_ipa_status':'unresolved_whole_line; only individually sourced examples in PRONUNCIATION_LEXICON.json may guide later reconstruction'}

def takes_for(context_key, effort=False):
    if effort:
        directions = ['Small, contained realization of this effort; natural onset and release.',
                      'Medium, immediate realization of the same effort; vary breath timing, not identity.',
                      'Stronger supported realization of the same effort; fresh performance, no forced rasp.']
    elif context_key in {'attack','attack_move','spear','sword','bow','crossbow','gun','horse_attack','elephant_attack','siege_attack','siege_ram','naval_attack','detonate','under_attack','target_destroyed','enemy_spotted','retreat'}:
        directions = ['Decisive controlled projection to nearby allies; clear lexical tones.',
                      'More urgent, shorter lead-in; same words, same actor and intended tone categories.',
                      'Firm supported call across a small group; change intention and rhythm, never fake a new voice.']
    elif context_key == 'stealth':
        directions = ['Close, quiet voiced delivery; retain tones, avoid an airy stage whisper.',
                      'Hushed urgency with a brief intake; identical text and recognizable timbre.',
                      'Low restrained caution; fresh performance, no pitch-shifted copy.']
    else:
        directions = ['Matter-of-fact, relaxed readiness; clear natural connected speech.',
                      'Prompt acknowledgement, slightly quicker start; same words and actor.',
                      'Reassuring commitment, subtle breath and rhythm change; no new accent.']
    return [{'take': f'T{i}', 'direction': direction, 'new_performance_required':True,
             'text_change_allowed':False, 'digital_pitch_variant_counts_as_take':False}
            for i,direction in enumerate(directions,1)]

LEXICAL_CANDIDATES = {
 'cung':('bow','Equipment-specific wording; distinguish from crossbow. Lexical dating and period pronunciation unverified.'),
 'nỏ':('crossbow','Equipment-specific wording; distinguish from bow. Lexical dating and period pronunciation unverified.'),
 'súng':('gun','Gun wording reserved for a verified gun-bearing consumer; early banks are dormant. Exact historical subtype terminology unverified.'),
 'voi':('elephant','Calls are a proposed human handler voice; no human owner has been qualified. Do not replace animal vocalizations.'),
 'lúa':('rice plant','Use for the rice-farm task only, not all food gathering. Whole-line historical wording unverified.'),
 'lưới':('net','Fishing occupational wording, not proof every fishing animation uses a net. Historical lexical date unverified.'),
 'bến':('landing','Riverine navigation/trade setting; not a named historical port or a dated command.'),
 'thuế':('tax','Administrative task, distinct from trade. Exact contemporary address and tax vocabulary need review.'),
 'sổ':('ledger','Written-account role cue; not evidence every unit/age was literate or used this sentence.'),
 'gỗ':('wood/timber','Concrete work material; dates and pronunciation of the complete command unverified.'),
 'cột':('post','Practical building cue; no historical construction drill is claimed.'),
 'gươm':('sword','L01 p.57 §1.2 supplies lexical-history background; this drafted sentence is unattested.'),
 'chăng':('interrogative/modal','L03 entry chăng sense 2 supplies literary interrogative evidence; A1 dating and this whole question remain unverified.'),
}
CONTEXT_RATIONALE = {
 'select':'Answer a selection without presuming the player is a monarch.',
 'role_select':'Establish the occupation through equipment/task vocabulary, not a claimed historical catchphrase.',
 'move':'Acknowledge a destination without explaining game mechanics.',
 'farm':'Field/rice labor rather than treating every food source as a rice paddy.',
 'forage':'Fruit gathering kept distinct from farming and hunting.',
 'hunt':'Quarry tracking or meat gathering; do not use for harvesting plants.',
 'herd':'Tending and moving livestock; animal sounds remain separate.',
 'wood':'Timber gathering with short tool/material language.',
 'gold':'Ore/gold task without a claim about a specific medieval extraction method.',
 'stone':'Quarrying distinct from gold mining.',
 'build':'Post/foundation/material language as an editorial building cue.',
 'repair':'Restoration/mending, not construction of a replacement entity.',
 'carry':'Transport a resource load without claiming it has already been deposited.',
 'tax':'Collection/accounting role; preserve distinction from commercial profit.',
 'supervise':'Oversight rather than direct resource collection.',
 'trade':'Cargo and market travel without naming a later port or foreign company.',
 'naval_trade':'River/landing commerce; no European captain stereotype.',
 'heal':'Human care wording; no invented medieval medical formula or miracle chant.',
 'relic':'Care/custody of a sacred object; religious terminology needs local review.',
 'convert':'Original appeal to listen, not a historically attested conversion ritual.',
 'bow':'Bow handling/loosing; no crossbow or gun terminology.',
 'crossbow':'Crossbow bolt/string/release language; do not route to ordinary bow users.',
 'gun':'Generic gun readiness/firing; no unverified detailed loading or ignition drill.',
 'siege_attack':'Coordinated engine operation; excludes ram-specific impact wording.',
 'siege_ram':'Pushing/ramming, with no projectile-fire wording.',
 'sail':'Waterway and helm language rather than land travel or an assumed seagoing dialect.',
 'fish':'Fishing task, distinct from cargo trade despite shared stock speaker ownership.',
 'detonate':'Existing demolition action only; warnings do not promise crew escape or survival.',
 'elephant_move':'Proposed human coordination around a living mount; human voice ownership remains a hard gate.',
 'elephant_attack':'Proposed human crew coordination; no elephant imitation or automatic animal-audio replacement.',
}
def rationale(ctx,age,vi,en):
    notes=[]
    for word,(meaning,note) in LEXICAL_CANDIDATES.items():
        if re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',vi.lower()):
            notes.append({'word':word,'meaning':meaning,'review_note':note,
                          'attestation_status':'inspected_literary_sense_not_full_line' if word=='chăng' else ('lexical_history_only' if word=='gươm' else 'period_use_unverified_editorial_choice')})
    core=CONTEXT_RATIONALE.get(ctx,'Short task/response wording for this semantic pool; conditional capability must be verified.')
    lexical='; '.join(f'{n["word"]}: {n["review_note"]}' for n in notes)
    return (f'Intent: {en} {core} {AGES[age]["direction"]} '+(lexical if lexical else 'No phrase-specific historical attestation is asserted; the wording is an editorial choice.'),notes)

def main():
    profiles = {}
    for p,(actor,role,direction,sources) in PROFILE_META.items():
        profiles[p] = {'actor_id':actor,'role':role,'casting_direction':direction,
                       'source_ids':sources,'ages':list(AGES),'contexts':PROFILE_CONTEXTS[p],
                       'same_actor_all_ages':True,'same_actor_all_three_takes':True,
                       'gender_policy':'female' if p=='CIV_F' else 'male_casting_default_not_historical_exclusion',
                       'casting_status':'proposed_unrecorded',
                       'recording_gate':'blocked_until_actual_human_voice_owner_verified' if p=='ELEPHANT' else 'native_editor_and_historical_review_required',
                       'effort_owner':'human_speaker_only_never_mount_hull_or_siege_mechanism'}
    entries=[]
    for p,profile in profiles.items():
        for age in AGES:
            for ctx in profile['contexts']:
                text_key = CONTEXTS[ctx]['text_key'].format(age=age)
                if ctx=='role_select':
                    texts=ROLE_SELECT[p]
                    template='role_select_'+p
                else:
                    texts=TEXTS[text_key]
                    template=text_key
                # Civilian attack and specialized family attack pools must not
                # accidentally turn noncombatants into commanders.
                if ctx in {'attack','attack_move'}:
                    if p in {'ARCHER','CROSSBOW','GUNNER'}:
                        template='ranged_'+age
                    elif p=='CAVALRY': template='horse_attack'
                    elif p=='ELEPHANT': template='elephant_attack'
                    elif p=='SIEGE': template='siege_attack'
                    texts=TEXTS[template]
                if (template,age) in AGE_TEXTS:
                    texts=AGE_TEXTS[(template,age)]
                    template=template+'_'+age
                for i,(vi,en) in enumerate(texts,1):
                    line_id=f'VN070_{p}_{age}_{ctx.upper()}_L{i:02d}'
                    historical_rationale,lexical_notes=rationale(ctx,age,vi,en)
                    entries.append({'id':line_id,'profile':p,'actor_id':profile['actor_id'],
                     'age_bank':age,'context':ctx,'phrase_number':i,
                     'vietnamese':unicodedata.normalize('NFC',vi),'english_meaning':en,
                     'text_template_id':template+f'_L{i:02d}',
                     'dialogue_status':'original_creative_adaptation_not_historical_quote',
                     'historical_rationale':historical_rationale,'lexical_notes':lexical_notes,
                     'source_locators':[
                       {'source_id':'L02','locator':'pp.167–169, dialect basis and tones','scope':'pronunciation research framework only'},
                       {'source_id':'L03','locator':'Phàm lệ §B.3; chăng sense 2 where used','scope':'transcription method; word-specific literary evidence only where noted'},
                       {'source_id':'G04','locator':'UNIT_VOICE_MAP.json consumer/profile entries; UNIT_INVENTORY.json source path/line evidence','scope':'role/task scope, not historical vocabulary attestation'}],
                     'source_ids':list(dict.fromkeys(profile['source_ids']+CONTEXTS[ctx]['source_ids']+['L02','L03'])),
                     'source_scope':'background_only_not_sentence_attestation',
                     'confidence':{'semantic_draft':'unreviewed_native_editor_required','period_phrase':'unverified','period_pronunciation':'unresolved'},
                     'pronunciation':modern_guide(vi),'takes':takes_for(ctx),
                     'activation':{'implemented':False,'condition':CONTEXTS[ctx]['activation_condition'],
                                   'bank_availability':'research_bank_not_proof_of_unit_age_availability'},
                     'recording_status':'not_recorded'})
            for effort,directions in EFFORTS.items():
                for i,direction in enumerate(directions,1):
                    entries.append({'id':f'VN070_{p}_{age}_{effort.upper()}_E{i:02d}',
                     'profile':p,'actor_id':profile['actor_id'],'age_bank':age,
                     'context':effort,'phrase_number':i,'kind':'nonverbal_effort',
                     'vietnamese':None,'english_meaning':None,'performance_description':direction,
                     'text_template_id':effort+f'_E{i:02d}',
                     'dialogue_status':'nonverbal_original_performance_direction',
                     'historical_rationale':'Human effort production choice; no recoverable medieval recording is claimed.',
                     'source_ids':['G03','G04'],'source_scope':'workflow_and_ownership_only',
                     'confidence':{'semantic_draft':'not_applicable_nonverbal','period_phrase':'not_applicable','period_pronunciation':'not_applicable'},
                     'pronunciation':None,'takes':takes_for(effort,True),
                     'activation':{'implemented':False,'condition':'Only a verified human effort event and human speech owner; do not replace animal, hull, mechanism or shared weapon effects.',
                                   'bank_availability':'research_bank_not_proof_of_unit_age_availability'},
                     'recording_status':'not_recorded'})

    for row in entries:
        if row['profile']=='ELEPHANT':
            row['activation']['condition']='BLOCKED: qualify an actual human speech owner first; warelephant code alone is insufficient. '+row['activation']['condition']
            row['recording_gate']='blocked_until_actual_human_voice_owner_verified'
        else:
            row['recording_gate']='native_editor_and_historical_review_required'

    reuse=defaultdict(list)
    for row in entries:
        content=row.get('vietnamese') or row['performance_description']
        digest=hashlib.sha256(content.encode('utf-8')).hexdigest()
        row['semantic_text_sha256']=digest
        reuse[digest].append(row['id'])
    groups={k:v for k,v in reuse.items() if len(v)>1}
    for row in entries:
        peers=groups.get(row['semantic_text_sha256'],[])
        row['intentional_reuse']={'present':bool(peers),'group_id':row['semantic_text_sha256'] if peers else None,
          'reason':'Shared short response/task text across chronological banks, related contexts or different actors; performance identities and takes remain separate.' if peers else None,
          'reuse_is_not_additional_unique_wording':True}

    dialogue=[x for x in entries if x.get('kind')!='nonverbal_effort']
    efforts=[x for x in entries if x.get('kind')=='nonverbal_effort']
    totals={'voice_profiles':len(profiles),'age_banks':4,'dialogue_rows':len(dialogue),
            'effort_rows':len(efforts),'total_rows':len(entries),
            'dialogue_directed_takes':len(dialogue)*3,'effort_directed_takes':len(efforts)*3,
            'total_directed_takes':len(entries)*3,
            'distinct_dialogue_texts':len({x['vietnamese'] for x in dialogue}),
            'distinct_effort_directions':len({x['performance_description'] for x in efforts}),
            'recorded_audio_files':0,'includes_conditional_and_dormant_banks':True,
            'playable_required_recording_total':'not_established_until_consumer_age_and_context_routing_is_qualified'}
    data={'schema':'community-civilization-pack.voice-preparation/v1',
          'date':'2026-10-18','timezone':'Asia/Tehran','version_label':'0.8.0_preparation_only',
          'status':'complete_creative_draft_bank_pending_native_and_historical_review',
          'credits':'hosein81 and chilly5','regional_target':'Northern Đại Việt / Red River center',
          'unit_mapping_file':'UNIT_INVENTORY.json',
          'unit_age_policy':'All four chronological banks are authored as research capacity. Never infer training age from bank presence or scar_age tags alone. Use inventory requirements; unresolved consumers stay conditional.',
          'source_register':'SOURCES.md','pronunciation_lexicon_file':'PRONUNCIATION_LEXICON.json',
          'variation_policy':{'phrases_per_profile_context_age':6,'takes_per_phrase':3,
             'pool_policy':'Generic and family-specific alternatives sharing one native event are mutually exclusive, never additive playback.',
             'no_repeat_policy':'Future presentation-only selection should avoid immediate phrase repeats; no runtime dispatcher supplied.'},
          'ages':AGES,'profiles':profiles,'contexts':CONTEXTS,'totals':totals,
          'reuse_groups':groups,'lines':entries}
    write_json('VOICE_SCRIPTS.json',data)
    write_json('PRONUNCIATION_LEXICON.json',{'schema':'voice-preparation.pronunciation-lexicon/v1','entries':LEXICON,
      'all_full_sentence_historical_ipa':'unresolved; no automatic spelling substitution'})
    write_json('SCRIPT_TOTALS.json',totals)
    tracks=defaultdict(list)
    for row in dialogue:
        tracks[(row['profile'],row['context'],row['phrase_number'])].append(row['vietnamese'])
    unchanged=sum(len(set(v))==1 for v in tracks.values())
    write_json('AGE_VARIATION_AUDIT.json',{
      'schema':'voice-preparation.age-variation/v1','dialogue_tracks_compared':len(tracks),
      'tracks_with_identical_text_all_four_ages':unchanged,
      'tracks_with_at_least_one_age_wording_difference':len(tracks)-unchanged,
      'interpretation':'Text diversity only; no proof of historical language evolution. Unchanged concrete-task text is intentional, with historical pronunciation unqualified.',
      'age_sensitive_extra_pools':sorted({k for k,a in AGE_TEXTS}),
      'historical_sound_progression_status':'research targets only; no fully reconstructed sentence pronunciation approved'})

    # Preserve every raw stock context, including delivery/chronology suffixes.
    # This is a research crosswalk, not a native SPD replacement or scheduler.
    native_map = {
      'acknowledge':'acknowledge','acknowledgeGMR':'acknowledge',
      'select':'select','selectGC':'select','selectSameTypeGC':'select','selectCart':'select',
      'moveGC':'move','moveSU':'move','moveSameTypeGC':'move',
      'attack':'attack','attackMoveGC':'attack_move','attackMoveSU':'attack_move',
      'attackSameTypeGC':'attack','engage':'attack','charge':'horse_attack',
      'stop':'stop','hold':'hold','celebrate':'celebrate','reactProud':'celebrate',
      'changeFormation':'formation','marchingIdle':'marching_idle',
      'enemySpotted':'enemy_spotted','underAttack':'under_attack','targetDestroyed':'target_destroyed',
      'resourceHunt':'hunt','pickUpCarcass':'pickup_carcass','dropOffCarcass':'dropoff_carcass','dropOffHerd':'herd',
      'resourceFish':'fish','dropoff':'carry','setUpTradeRoute':'naval_trade','tradeRouteSet':'naval_trade',
      'garrisonUnits':'transport_load','unloadUnits':'transport_unload','structureRepair':'repair',
      'weaponAim':'aim','weaponFire':'attack','detonate':'detonate',
      'effortAttack':'attack_effort','effortAttackBig':'attack_effort',
      'effortPain':'pain_light','effortPainBig':'pain_heavy','effortDeath':'death',
      'effortExertion':'exertion','effortExertionBig':'exertion','effortFear':'fear_effort',
      'effortPanic':'fear_effort','effortIncomingProjectile':'incoming_effort',
      'effortWarcry':'warcry_effort','effortCough':'cough_effort',
      'effortHealed':'healed_effort','effortInspired':'inspired_effort',
    }
    crosswalk=[]
    for path in sorted((ROOT/'research_tools/profile_json').glob('*.json')):
        native=json.loads(path.read_text(encoding='utf-8'))
        contexts=defaultdict(list)
        for record in native.get('records',[]):
            contexts[record['context']].extend(record.get('media_paths',[]))
        for raw,media in contexts.items():
            prefix=re.split(r'_i|_c',raw,maxsplit=1)[0]
            crosswalk.append({'stock_profile':path.stem+'.spd','raw_context':raw,'prefix':prefix,
              'semantic_candidate':native_map.get(prefix),
              'mapping_status':'editorial_candidate_requires_consumer_and_event_validation' if prefix in native_map else 'unresolved',
              'stock_media_reference_count':len(media),'stock_media_paths':media,
              'native_delivery_and_chronology':'raw suffixes preserved; meanings and scheduling not established',
              'important_limit':'Profile membership alone does not give every consumer this ability. Do not derive player age from cLowest/cLow/cMed/cHigh.',
              'audio_replaced':False})
    write_json('NATIVE_CONTEXT_MAPPING.json',{
      'schema':'voice-preparation.native-context-crosswalk/v1',
      'status':'research_crosswalk_not_runtime_mapping',
      'source':str(len(list((ROOT/'research_tools/profile_json').glob('*.json'))))+' structurally decoded installed Chinese SPD profiles, full raw contexts retained',
      'exclusions':'Undecoded villager and other land-unit profiles remain unresolved; no all-native-slot coverage claim.',
      'delivery_policy':'Three takes are performance alternates, NOT aliases for iNorm/iHigh/iStealth. These delivery labels require separate qualification and may require extra recordings.',
      'family_overrides':{'NAVAL_*':'move->sail; stop->naval_stop; attack/attack_move->naval_attack only where the ship can attack; dropoff->fish_dropoff or naval_trade_return after resolving resource',
                          'CAVALRY':'move->horse_move; attack->horse_attack',
                          'ELEPHANT':'move->elephant_move; attack->elephant_attack',
                          'SIEGE':'move->siege_move; attack->siege_attack or siege_ram by verified weapon'},
      'unresolved_prefixes':sorted({x['prefix'] for x in crosswalk if x['semantic_candidate'] is None}),
      'entries':crosswalk})

    inventory=json.loads((ROOT/'UNIT_INVENTORY.json').read_text(encoding='utf-8'))
    unit_map=[]
    def role_for(name):
        n=name.lower()
        if 'villager' in n: return ['CIV_M','CIV_F']
        if 'war_elephant' in n: return ['ELEPHANT']
        if 'handcannon' in n: return ['GUNNER']
        if 'crossbow' in n: return ['CROSSBOW']
        if 'archer' in n: return ['ARCHER']
        if 'spearman' in n or 'manatarms' in n: return ['INFANTRY']
        if 'horseman' in n or 'knight' in n or 'abbey_king' in n: return ['CAVALRY']
        if 'monk' in n: return ['MONK']
        if 'official' in n: return ['OFFICIAL']
        if 'trade' in n: return ['TRADER']
        if 'scout' in n: return ['SCOUT']
        if any(s in n for s in ['bombard','culverin','ribauldequin','mangonel','springald','trebuchet','workshop_ram']): return ['SIEGE']
        return []
    def row_for(name, roles, origin, evidence):
        weapon='generic_role_only_until_effective_weapon_verified'
        if 'workshop_ram' in name: weapon='siege_ram_only_no_shooting_lines'
        elif 'spearman' in name: weapon='spear_candidate; fire_lance_mode_requires_effective_weapon_check'
        elif 'manatarms' in name: weapon='sword_candidate'
        elif 'crossbow' in name: weapon='crossbow_candidate'
        elif 'archer' in name: weapon='bow_candidate'
        elif 'war_elephant_handcannon' in name: weapon='elephant_human_caller; gun_context_only_after_crew_binding_check'
        elif roles==['NAVAL_TRANSPORT']: weapon='no_attack_or_weapon_lines'
        elif roles==['NAVAL_FIRE']: weapon='detonate_only_when_confirmed; no_gun_wording'
        elif roles==['NAVAL_FISH'] or roles==['NAVAL_TRADE']: weapon='civilian_vessel_no_attack_assumption'
        excluded='gaia_herdable_sheep' in name
        return {'consumer_id':name,'origin':origin,'profile_candidates':roles,
          'mapping_status':'excluded_animal_sounds_not_human_dialogue' if excluded else ('proposed_voice_role_not_runtime_binding' if roles else 'unresolved_role'),
          'reachability_status':'serialized_reference_or_definition_only_see_inventory_for_gates',
          'age_policy':'all_four_research_banks_available; actual_player_age_or_tier_routing_unqualified',
          'gender_policy':'both_civilian_profiles_reserved; effective_gender_attachment_route_unresolved' if 'villager' in name else 'follow_verified_owner_and_appearance_do_not_infer_from_stock_profile_existence',
          'equipment_filter':weapon,'evidence':evidence}
    for unit in inventory['local_squad_definitions']:
        unit_map.append(row_for(unit['id'],role_for(unit['id']),'local_private_squad_definition',
          {'path':unit['path'],'sha256':unit['sha256'],'explicit_age_tags':unit['age_tags'],
           'locators':unit['evidence'],'not_independently_trainable_by_definition':True}))
    for name,refs in inventory['ebps_squad_consumers'].items():
        unit_map.append(row_for(name,role_for(name),'local_building_squad_reference',{'references':refs}))
    for unit in inventory['official_inherited_naval_roster']:
        unit_map.append(row_for(unit['id'],[unit['profile']],'official_inherited_dock_queue',
          {'path':unit['source_xml'],'sha256':unit['source_sha256'],
           'stock_speaker':unit.get('effective_squad_speaker_code'),
           'stock_spd':unit.get('stock_spd'),'explicit_age_tag':unit['age_tag']}))
    # Include all literal SBPS references across categories, not just building
    # queues. This captures army upgrade targets and ability/action references.
    source_root=ROOT.parent
    all_refs=defaultdict(list)
    speech_consumers=[]
    for xml in sorted((source_root/'assets/attrib/instances').rglob('*.xml')):
        rel=xml.relative_to(source_root).as_posix()
        for number,line in enumerate(xml.read_text(encoding='utf-8-sig').splitlines(),1):
            for value in re.findall(r'value="(sbps\\[^\"]+)"',line):
                all_refs[value].append({'path':rel,'line':number})
            if any(term in line for term in ['speech_ext','speaker_code','attachment_speaker_code']):
                speech_consumers.append({'path':rel,'line':number,'serialized_xml':line.strip(),
                  'effective_value_status':'literal_only_parent_and_variant_resolution_required'})
            elif 'attachments' in rel and 'parent_pbg' in line:
                speech_consumers.append({'path':rel,'line':number,'serialized_xml':line.strip(),
                  'effective_value_status':'inherited_attachment_speaker_values_not_collated'})
    existing={u['consumer_id'] for u in unit_map}
    for name,refs in all_refs.items():
        if name not in existing:
            unit_map.append(row_for(name,role_for(name),'additional_literal_attribute_squad_reference',{'references':refs}))
    write_json('SPEECH_CONSUMERS.json',{
      'schema':'voice-preparation.local-speech-consumers/v1',
      'status':'literal_editable_source_inventory_not_effective_compiled_bindings',
      'entries':speech_consumers,
      'no_literal_field_does_not_mean_silent':True,
      'limit':'Generated/cooked attachment lists and inherited stock speaker fields are not exhaustively decoded. No suppression changes are made.',
      'all_literal_squad_references':dict(all_refs)})
    write_json('UNIT_VOICE_MAP.json',{'schema':'voice-preparation.consumer-role-map/v1',
      'status':'complete_candidate_mapping_of_inventoried_rows_not_proof_of_exhaustive_runtime_roster',
      'entries':unit_map,'unresolved':[u['consumer_id'] for u in unit_map if u['mapping_status']=='unresolved_role'],
      'important_limits':['Unresolved inherited land producers and army upgrade consumers are recorded in UNIT_COVERAGE.md; no missing lookup is labeled an invalid unit.',
         'New TRADER bank is reserved even if exact canonical trader consumer remains unresolved.',
         'NAVAL_MILITARY intentionally shares a new caller across original ship/warShip speakers.',
         'The English Abbey King is a conditional inherited consumer; CAVALRY is a draft voice-role candidate, not a historical Vietnamese royal title.']})

    preview=['# Script preview — use the full bank for recording', '',
      'All sentences below are original, unreviewed creative drafts. Modern spelling is a reading aid; no full-line historical IPA is claimed.', '',
      '| Role / actor | A1 selection example | A4 selection example | Role-specific example |', '|---|---|---|---|']
    for p,profile in profiles.items():
        specific=next((c for c in profile['contexts'] if c not in COMMON and c not in MILITARY),'role_select')
        r=next(x for x in dialogue if x['profile']==p and x['age_bank']=='A4' and x['context']==specific)
        preview.append(f'| {p} / {profile["actor_id"]} | {TEXTS["select_A1"][0][0]} | {TEXTS["select_A4"][0][0]} | {r["vietnamese"]} — {r["english_meaning"]} |')
    preview += ['', 'Selection examples intentionally use the shared generic pool; each actor also has a separate role-selection candidate pool. Choose one pool per event.', '',
      'Example ARCHER / A3 / bow phrase: **Giương cung!** — “Draw the bows!” T1: controlled call nearby. T2: urgent onset. T3: firm group call. The words stay identical in all three fresh takes.', '',
      'For the full six phrases × three take directions, see VOICE_SCRIPTS.md or filter VOICE_SCRIPTS.json by profile, age_bank and context.', '']
    (ROOT/'SAMPLE_LINES.md').write_text('\n'.join(preview),encoding='utf-8')

    rows_by_profile=[]
    for p in profiles:
        rows_by_profile.append(f'| {p} | {len(PROFILE_CONTEXTS[p])} | {len(PROFILE_CONTEXTS[p])*24} | {len(PROFILE_CONTEXTS[p])*72} |')
    counts=['# Script accounting', '',
      'Generated expanded draft capacity. Conditional/dormant banks and mutually exclusive alternatives are included; this is not an active recording order.', '',
      f'- Voice identities: **{len(profiles)}**; chronological banks: **4**.',
      f'- Unique Vietnamese text strings: **{totals["distinct_dialogue_texts"]}**.',
      f'- Expanded dialogue phrase rows: **{len(dialogue):,}**; three directed takes each: **{len(dialogue)*3:,}**.',
      f'- Expanded nonverbal effort rows: **{len(efforts):,}**; three directed takes each: **{len(efforts)*3:,}**.',
      f'- Total expanded rows/takes: **{len(entries):,} / {len(entries)*3:,}**.',
      '- Recorded audio files: **0**. Full native-slot recording total: **not established**.', '',
      '| Profile | Semantic dialogue pools per age | Dialogue rows, four ages | Directed dialogue takes |',
      '|---|---:|---:|---:|']+rows_by_profile+['',
      'Each profile also has 11 nonverbal effort categories × six directions × four bank copies × three takes. The 66 distinct effort directions are intentionally shared; final approved efforts may be aliased across ages. Do not mistake the expanded copies for different effort designs.', '',
      f'Native research crosswalk: **{len(crosswalk)}** distinct full raw contexts across **{len(list((ROOT/"research_tools/profile_json").glob("*.json")))}** decoded profile files; all prefixes have an editorial semantic candidate, not a qualified engine mapping.', '',
      f'Consumer-role mapping: **{len(unit_map)}** inventory/reference rows, including duplicates across evidence classes and explicit nonhuman exclusions. Not a count of independently obtainable units.', '']
    (ROOT/'SCRIPT_ACCOUNTING.md').write_text('\n'.join(counts),encoding='utf-8')

    # A complete readable companion; every JSON line is represented once.
    out=['# Vietnamese recording scripts — 0.8.0', '',
         '**Original creative drafts. No audio recorded; native and historical reviews pending.**', '',
         'All ages use modern spelling as a reading aid. Historical full-line IPA is unresolved. See HISTORY_AND_LANGUAGE.md and PRONUNCIATION_LEXICON.json.', '',
         'Each phrase has three fresh takes by its profile\'s actor. Native context membership is not proof of an available scripted trigger. Generic and specialized alternatives are mutually exclusive.', '',
         'Full per-line sources, orthographic tone categories, conditional activation and reuse membership are in VOICE_SCRIPTS.json.', '']
    index=defaultdict(list)
    for row in entries: index[(row['profile'],row['age_bank'],row['context'])].append(row)
    for p,profile in profiles.items():
        out += [f'## {p} — {profile["actor_id"]}: {profile["role"]}', '', profile['casting_direction'], '',
                'Source background: '+', '.join(profile['source_ids'])+'. Complete sentences remain creative.', '']
        for age,meta in AGES.items():
            out += [f'### {age} / {meta["game_age"]}: c. {meta["years"][0]}–{meta["years"][1]}', '',meta['direction'],'']
            for ctx in profile['contexts']+list(EFFORTS):
                rows=index[(p,age,ctx)]
                out += [f'#### {ctx}', '',
                        CONTEXTS[ctx]['activation_condition'] if ctx in CONTEXTS else 'Human nonverbal effort only; never an animal/hull/mechanism replacement.', '',
                        '| Stable ID | Vietnamese / effort direction | English meaning |', '|---|---|---|']
                for row in rows:
                    out.append(f'| {row["id"]} | {row.get("vietnamese") or row["performance_description"]} | {row.get("english_meaning") or "Nonverbal; no spoken word"} |')
                out += ['', 'Three takes for **each** of the six rows:', '']
                for take in rows[0]['takes']: out.append(f'- **{take["take"]}:** {take["direction"]}')
                out += ['', 'Pronunciation: modern Northern native-reader rehearsal only; retain written tone categories. Historical sentence realization unresolved. Text reused elsewhere is intentional and must not be counted as fresh wording.', '']
    (ROOT/'VOICE_SCRIPTS.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
    print(json.dumps(totals,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
