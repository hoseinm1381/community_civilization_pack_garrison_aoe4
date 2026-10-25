"""Retained first-pass analysis, superseded by audited inventory corrections.

This is provenance, not a supported regeneration command. Do not overwrite the
reviewed UNIT_INVENTORY.json with the earlier inference-based inventory.
"""
raise SystemExit('Historical first-pass analysis only; read UNIT_INVENTORY.json and UNIT_COVERAGE.md. This script intentionally performs no writes.')
from pathlib import Path
import re,json,hashlib,datetime
root=Path(r'Community_civilization_pack_garrison')
out=root/'0.8.0'; tool=out/'research_tools'; tool.mkdir(parents=True,exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p): return p.read_text(encoding='utf-8-sig',errors='replace').splitlines()
# local squad definitions
roster=[]
for p in sorted((root/'assets/attrib/instances/sbps/vietnam').glob('*.xml')):
    ls=lines(p); s='\n'.join(ls)
    parent=re.search(r'<instance_reference name="parent_pbg" value="([^"]*)"',s)
    ages=sorted(set(re.findall(r'value="(scar_age[1-4])"',s)))
    fem=re.search(r'<float name="squad_female_chance" value="([^"]+)"',s)
    speaker=re.search(r'<string name="squad_speaker_code" value="([^"]*)"',s)
    name=re.search(r'<string name="squad_name_code" value="([^"]*)"',s)
    race=re.search(r'<enum name="squad_race_code" value="([^"]*)"',s)
    pbg=re.search(r'<uniqueid name="pbgid" value="([^"]+)"',s)
    # first occurrence lines
    def ev(pattern):
      for i,l in enumerate(ls,1):
       if re.search(pattern,l): return i
      return None
    roster.append(dict(id=p.stem,path=str(p.relative_to(root)).replace('\\','/'),sha256=sha(p),pbgid=pbg.group(1) if pbg else None,parent=parent.group(1) if parent else None,age_tags=ages,female_chance=float(fem.group(1)) if fem else None,speaker=speaker.group(1) if speaker else None,squad_name=name.group(1) if name else None,race_code=race.group(1) if race else None,evidence={k:v for k,v in [('parent_pbg',ev('parent_pbg')),('squad_type_age',ev('scar_age')),('female_chance',ev('squad_female_chance')),('speaker',ev('squad_speaker_code')),('name_code',ev('squad_name_code'))] if v}))
# all squad refs in EBPS Vietnam, unique by reference with source locations
refs={}
for p in sorted((root/'assets/attrib/instances/ebps/vietnam').glob('*.xml')):
 ls=lines(p)
 for i,l in enumerate(ls,1):
  m=re.search(r'<instance_reference name="squad" value="([^"]+)"',l)
  if m:
   val=m.group(1); refs.setdefault(val,[]).append(dict(path=str(p.relative_to(root)).replace('\\','/'),line=i))
# army and scar evidence
army=root/'assets/attrib/instances/army/vietnam/vn_normal_chinese.xml'; scar=root/'assets/scar/vietnam/initialization.scar'; dock=root/'assets/attrib/instances/ebps/vietnam/vn_building_unit_naval_chi.xml'
# official naval roster with local official DB evidence references from summary
ships=[
 dict(id='unit_naval_fireship_3_chi',kind='fireship',age_tag='scar_age3',profile='NAVAL_FIRE',evidence='research_tools/official_attrib/building_unit_naval_chi.xml (decoded from official Attrib.sga); stock chinese_fireship.spd'),
 dict(id='unit_naval_fishing_boat_2_chi',kind='fishing boat',age_tag='scar_age2',profile='NAVAL_FISH',evidence='official Dock production queue; stock SBPS tag; chinese_ship.spd'),
 dict(id='unit_naval_transport_ship_2_chi',kind='transport ship',age_tag='scar_age2',profile='NAVAL_TRANSPORT',evidence='official Dock production queue; stock SBPS tag; chinese_ship.spd'),
 dict(id='unit_naval_combat_ship_2_chi',kind='combat ship',age_tag='scar_age2',profile='NAVAL_MILITARY',evidence='official Dock production queue; stock SBPS tag; chinese_warship.spd'),
 dict(id='unit_naval_combat_warship_4_chi',kind='combat warship',age_tag='scar_age4',profile='NAVAL_MILITARY',evidence='official Dock production queue; stock SBPS tag; chinese_warship.spd'),
 dict(id='unit_naval_war_galley_3_chi',kind='war galley',age_tag='scar_age3',profile='NAVAL_MILITARY',evidence='official Dock production queue; stock SBPS tag; chinese_warship.spd'),
 dict(id='unit_naval_trade_ship_3_chi',kind='trade ship',age_tag='scar_age3',profile='NAVAL_TRADE',evidence='official Dock production queue; stock SBPS tag; chinese_tradeship.spd')]
# pull speaker metadata from decoded SPDs when available
profiles={
 'SCOUT':dict(stock_spd='chinese_scout.spd',speaker='scout',records=673,media_refs=1551,contexts=['acknowledge','attack','attackMove','attackSameType','charge','enemySpotted','formation','move','select','stop','resourceHunt','pickUpCarcass','dropOffHerd','dropOffCarcass','efforts']),
 'SCOUT_F':dict(stock_spd='chinese_scoutfemale.spd',speaker='scoutFemale',records=656,media_refs=1593,contexts=['acknowledge','attack','attackMove','attackSameType','charge','enemySpotted','formation','move','select','stop','resourceHunt','pickUpCarcass','dropOffHerd','efforts']),
 'NAVAL_FISH':dict(stock_spd='chinese_ship.spd',speaker='ship',records=427,media_refs=807,contexts=['acknowledge','attack','attackMove','celebrate','efforts','hold','move','reactProud','select','stop','targetDestroyed','underAttack','weaponAim','weaponFire']),
 'NAVAL_TRANSPORT':dict(stock_spd='chinese_ship.spd',speaker='ship',records=427,media_refs=807,contexts=['acknowledge','hold','move','select','stop','underAttack']),
 'NAVAL_MILITARY':dict(stock_spd='chinese_warship.spd',speaker='warship',records=0,media_refs=0,contexts=['acknowledge','attack','attackMove','celebrate','efforts','hold','move','select','stop','targetDestroyed','underAttack','weaponAim','weaponFire']),
 'NAVAL_TRADE':dict(stock_spd='chinese_tradeship.spd',speaker='tradeShip',records=391,media_refs=752,contexts=['acknowledge','celebrate','dropoff','efforts','garrisonUnits','unloadUnits','hold','move','select','stop','resourceFish','setUpTradeRoute','tradeRouteSet','structureRepair','underAttack']),
 'NAVAL_FIRE':dict(stock_spd='chinese_fireship.spd',speaker='fireShip',records=230,media_refs=408,contexts=['acknowledge','celebrate','detonate','efforts','hold','move','select','stop','targetDestroyed','underAttack'])
}
# specific SPDs hashes and extracted SPD paths
for k,v in profiles.items():
 p=tool/'stock_profiles'/v['stock_spd']
 if p.exists():v['sha256']=sha(p);v['path']=str(p.relative_to(root)).replace('\\','/')
# speech profile summaries
profiles.update({
 'CIV_M':dict(current_metadata='Vietnam villager SBPS sets race_code=chinese, inherits speaker/gender attachment metadata; direct effective speaker unresolved',profile_status='inherited unresolved'),
 'CIV_F':dict(current_metadata='same as CIV_M; female stock branch is inherited, not confirmed effective Vietnamese runtime selection',profile_status='inherited unresolved'),
 'INFANTRY':dict(current_metadata='No custom speaker metadata found on local line squads; inherits Chinese donor speech metadata; effective per-unit resolution untraced'),
 'ARCHER':dict(current_metadata='No custom speaker metadata found on local archer squads; inherits Chinese donor speech metadata; effective resolution untraced'),
 'CROSSBOW':dict(current_metadata='No custom speaker metadata found; inherits donor or local parent; effective resolution untraced'),
 'GUNNER':dict(current_metadata='No custom speaker metadata found on local gunner squads; inherited effective speaker unresolved'),
 'CAVALRY':dict(current_metadata='No custom speaker metadata found on local cavalry squads; inherited effective speaker unresolved'),
 'MONK':dict(current_metadata='local vn_unit_monk_3_chi sets squad_speaker_code=monk, squad_name_code=monk; female branch and SPD not inspected'),
 'OFFICIAL':dict(current_metadata='vn_unit_official_1_chi sets male speaker villagerMale and female speaker villagerFemale; distinct OFFICIAL voice not serialized'),
 'TRADER':dict(current_metadata='local trader profile effective fields not confirmed; profile key is role-bank assignment pending source resolution'),
 'ELEPHANT':dict(current_metadata='private war elephants and elephant handcannon set speaker warelephant, name war_elephant, race no_race; crew dialogue is not evidenced'),
 'SIEGE':dict(current_metadata='local private siege squads primarily inherit; physical crew presence and crew dialogue inference excluded unless explicit'),
})
# exact sourced hash objects
sources=[]
for p in [army,dock,scar,*sorted((root/'assets/attrib/instances/sbps/vietnam').glob('*.xml'))]:
 sources.append(dict(path=str(p.relative_to(root)).replace('\\','/'),sha256=sha(p),bytes=p.stat().st_size))
# include all EBPS files that contain direct squad refs
for val,locs in refs.items():
 for loc in locs:
  p=root/loc['path']
  if not any(x['path']==loc['path'] for x in sources): sources.append(dict(path=loc['path'],sha256=sha(p),bytes=p.stat().st_size))
# key roster info and distinguish static vs produced
inv=dict(schema='0.7.0-vietnam-unit-inventory-v1',generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Static source inventory only; does not claim runtime availability, voice playback, build/cook/import or native match proof.',profiles=profiles,local_squad_definitions=roster,ebps_squad_consumers=refs,official_inherited_naval_roster=ships,naval_dock_parent='ebps\\races\\chinese\\buildings\\building_unit_naval_chi\\building_unit_naval_chi',naval_notes={'availability':'Official Dock queue items require the Vietnamese private dock (which inherits the Chinese dock) and relevant stock unlocks. scar_ageN tag is classification evidence, not a direct proof of a training gate.','dock_queue':'The seven units above appear in official production queue; Vietnamese dock introduces no local ship queue override. An internal naval scout construction reference is not treated as player-trainable.','transport_actions':'No crew dialogue inferred. Ship-level transport actions limited to movement/select/acknowledge/under-attack; no combat payload assumed.','fireship_actions':'Detonate exists in stock fireship SPD; inclusion here records a context, not proof of action routing or runtime playback.','repair_garrison':'Trade ship SPD includes structureRepair and garrisonUnits/unloadUnits. Applicability depends on engine routing and stock ability availability, not proven for all units. No local Vietnamese-specific override found.'},army={'path':str(army.relative_to(root)).replace('\\','/'),'sha256':sha(army),'line_evidence':{'starting_units':[314,315,316],'starting_resources':[321,322,323],'production_buildings_empty':[302]},'starting_units':['1 Vietnamese scout vn_unit_scout_1_chi','6 Vietnamese villagers vn_unit_villager_1_chi','1 Vietnamese war elephant vn_unit_war_elephant_1_vit'],'campaign_starting_force':'same composition in campaign variant; compare source around lines 680-688','notes':'The five sheep are not speech-bearing army unit profiles.'},scar={'path':str(scar.relative_to(root)).replace('\\','/'),'sha256':sha(scar),'spawn_evidence':'Squad_CreateAndSpawnToward(elephant, player.id, 0, elephantPos, center) at line 66; spawned squad identifier is a war elephant. No other unit spawn APIs found by targeted search.'},official_speech={'source':'Installed SoundSpeechChinese.sga; selectively listed/extracted only 8 SPD files into research_tools/stock_profiles; SHA-256 and decoded summaries included under profiles.','decode_status':'speech helper emitted structural_readback_only; no qualified audio/playback/runtime proof. Chinese villager SPD parse failed Invalid media list; raw files retained with hashes where extracted.','contexts':'Suffixes cLowest/cLow/cMed/cHigh and iNorm/iHigh/iStealth were observed but their chronology/delivery interpretation was not traced; preserve as unverified.'},source_files=sources,excluded_or_unresolved=['No custom Vietnamese naval unit SBPS/EBPS roster found; all seven ship queue entries are stock Chinese units inherited through Vietnamese dock.','Official Attrib MCP lookup miss is not evidence of invalid data.','Stock scoutfemale SPD exists; private vn_unit_scout_1_chi female_chance must be read from source and reconciled with attachment inheritance before using SCOUT_F.','Official siege/shop and trader queue references are stock consumers, but full effective inheritance chain requires further resolution.','Current ship/siege separate physical crew actors and their potential dialogue are not proven.','No voice-bank chronology mapping inferred from suffixes.'])
(out/'UNIT_INVENTORY.json').write_text(json.dumps(inv,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('wrote',out/'UNIT_INVENTORY.json','local squads',len(roster),'consumer refs',len(refs),'sources',len(sources))
