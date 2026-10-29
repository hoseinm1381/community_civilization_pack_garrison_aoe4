"""Extract the donor's active numerical weapon effects into maintained data.

Does not copy the standalone mode, legacy globals, polling implementations, or
stock DynastyUI replacement. Run only as part of the documented one-time port.
"""
import argparse
import ast
import json
import re
from pathlib import Path
from import_korea import ROOT, GUID, lua


def number(text):
    node = ast.parse(text.strip(), mode='eval').body
    def value(n):
        if isinstance(n,ast.Constant) and type(n.value) in (int,float): return n.value
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub): return -value(n.operand)
        if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Div): return value(n.left)/value(n.right)
        raise ValueError(text)
    return value(node)


def body(source, file, name):
    code = (source/'assets/scar/winconditions'/file).read_text(encoding='utf-8-sig')
    code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.S)
    code = re.sub(r'--[^\n]*', '', code)
    m = re.search(r'^function\s+'+name+r'\s*\([^\n]*\)(.*?)(?=^function\s|\Z)', code, re.S|re.M)
    assert m, (file,name)
    return m[1]


def run(source):
    ledger = json.loads((ROOT/'docs/korea-import.json').read_text())
    idnames = {str(r['source_pbg_id']):r['source'].split('\\')[-1] for r in ledger['instances']}
    kinds = {
        'ApplySpecificWeaponRangeModifier':'range_weapon_modifier',
        'ApplySpecificWeaponRangeModifier_with_player_id':'range_weapon_modifier',
        'ModifyWeaponBonusDamage':'weapon_damage_per_unit_type_modifier',
        'ModifyWeaponBonusDamage_player_id':'weapon_damage_per_unit_type_modifier',
        'ModifyWeaponDamage':'damage_weapon_modifier',
        'ModifyWeaponReloadTime':'reload_weapon_modifier',
        'ModifyWeaponcooldown':'cooldown_weapon_modifier',
        'ApplyWeaponBurstRateModifierForWeapon':'weapon_burst_rate_of_fire_modifier',
    }
    def effects(code):
        result=[]
        for m in re.finditer(r'\b('+ '|'.join(kinds)+r')\s*\([^,]+,\s*"([^"\n]+)"\s*,\s*([^,)]+)(?:,\s*([12]))?\s*\)',code):
            effect={'weapon':m[2], 'property':kinds[m[1]], 'value':number(m[3]), 'multiply':m[4]!='1'}
            if effect not in result:result.append(effect)
        return result
    unique='unit_sepcial_upgrades.scar'
    iron=body(source,unique,'unique_upgrade_unit_handler').split('elseif elite_knight_upgrade')[0]
    data={'start':effects(body(source,'unique_unit/tiger_hunter.scar','changing_tiger_hunter_weapon')+body(source,'water_mechanics.scar','initilize_water_weapon_range')),'upgrades':{}}
    functions={'9000601':iron,'2127459':body(source,unique,'Dangpa_Trident_bonus_activation'),
               '1266879':body(source,unique,'Chongtong_code_upgrade_extra_range'),
               '2089169':body(source,unique,'increase_archer_range'),
               '2089171':body(source,unique,'Reflex_Bow_apply'),
               '2089166':body(source,unique,'hwacha_additional_barrel')}
    for id,code in functions.items():
        name = idnames[id]; data['upgrades'][name]=effects(code)
    # Owner-approved correction: Castle archer uses the same multiplier.
    for effect in data['upgrades'][idnames['2089169']]:
        if effect['weapon']=='weapon_archer_3': effect['multiply']=True
    out=ROOT/'assets/scar/korea'
    (out/'effect_catalog.scar').write_text('-- Active donor weapon values, with approved Arrow Chutes correction.\nKoreaEffectCatalog = '+lua(data)+'\n',encoding='utf-8')
    entities=sorted(GUID+':'+r['private'].split('\\')[-1] for r in ledger['instances'] if r['private'].startswith('ebps\\'))
    squads=sorted(GUID+':'+r['private'].split('\\')[-1] for r in ledger['instances'] if r['private'].startswith('sbps\\'))
    code='-- Complete private Korean roster; prematch loading precedes selection.\nKoreaBlueprints = '+lua({'entities':entities,'squads':squads})+'\n'
    code+='''
function KoreaBlueprints_Available()
    for _, name in ipairs(KoreaBlueprints.entities) do if not EBP_Exists(name) then return false end end
    for _, name in ipairs(KoreaBlueprints.squads) do if not SBP_Exists(name) then return false end end
    return true
end

function KoreaPrecache_Init()
    if not CCPLoading_Required("chinese_ha_01") then
        print("CCP_PRECACHE_SKIP family=korea")
        return
    end
    CCPLoading_Shared()
    for _, name in ipairs(KoreaBlueprints.entities) do
        if EBP_Exists(name) then Scar_PrecachePrematchResource(BP_GetEntityBlueprint(name))
        else print("KOREA_PRECACHE_MISSING_ENTITY " .. name) end
    end
    for _, name in ipairs(KoreaBlueprints.squads) do
        if SBP_Exists(name) then Scar_PrecachePrematchResource(BP_GetSquadBlueprint(name))
        else print("KOREA_PRECACHE_MISSING_SQUAD " .. name) end
    end
end

Scar_AddInit(KoreaPrecache_Init)
'''
    (out/'blueprints.scar').write_text(code,encoding='utf-8')
    ignored=['senobi/out_dated.scar','senobi/senbi_seowon.scar','senobi/ui_for_foreign_tech_caster_mode.scar',
             'senobi_new/extra_senobi_seowon_stuff.scar','senobi_new/senobi_ai_automatic.scar','senobi_new/seowon.scar']
    ledger['script_migration']={'unimported_donor_scripts':ignored,
        'stock_ui_replacement_omitted':'chinese_dynasty_ui.scar; official DynastyUI remains engine-owned',
        'research_dispatch':'91 active routes consolidated; naval extended-lines missing queue repaired',
        'weapon_effects':sum(len(v) for v in data['upgrades'].values())+len(data['start']),
        'duplicate_identical_weapon_calls':'deduplicated; repeated Bill tier-2 brace entries were accidental',
        'approved_corrections':['Castle archer Arrow Chutes uses x1.4','Hangul retains 2 gold per 6 seconds per nearby scholar']}
    (ROOT/'docs/korea-import.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
    print('Extracted',ledger['script_migration']['weapon_effects'],'weapon effects;',len(entities),'entities;',len(squads),'squads')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True)
    run(parser.parse_args().source.resolve())
