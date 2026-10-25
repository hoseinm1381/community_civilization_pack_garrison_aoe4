"""Pin the six exact ranged donor/rig sources for separate per-tier authoring."""
from pathlib import Path
from common import ART, OUT, RECIPES, guard, owned, read, sha, write

guard()
audit=OUT/'qualification/ranged-rig-audit/report.json'
summary=OUT/'qualification/ranged-rig-audit/summary.json'
approved=OUT/'representatives/selection-seven.json'
target=owned(RECIPES/'ranged-roster-060.json')
if target.exists():
    raise FileExistsError(target)
report=read(audit)
digest=sha(audit)
overview=read(summary)
if overview['source_report_sha256']!=digest or not read(approved)['style_approved'] is False:
    raise RuntimeError('Ranged audit or approved sample manifest drift')

designs={
    'vn_unit_archer_2_vit':('archer2','approved v3l teal split tunic, headcloth and owner-color lower panel','bow_recurve',2),
    'vn_unit_archer_3_vit':('archer3','fitted teal service tunic, broader cloth shoulders and retained native age-III protection','bow_recurve',3),
    'vn_unit_archer_4_vit':('archer4','short split overcoat, compact dark padded shoulders and retained age-IV helmet','bow_recurve',4),
    'vn_unit_crossbowman_3_chi':('crossbow3','teal close tunic under native crossbow armor and dark waist wrap','bow_cross',3),
    'vn_unit_crossbowman_4_chi':('crossbow4','heavier broad chest guard over dark teal coat, native age-IV helmet and arbalest','bow_arbalest',4),
    'vn_unit_handcannon_4_chi':('handcannon4','short protected gunner coat with dark padded chest and native firearm rig','ott_gun_janissary',4),
}
tiers=[]
for ebp,(slug,style,weapon,age) in designs.items():
    trace=report['tiers'][ebp]
    matches=[r for r in trace['body_models'] if r.endswith('.rgm')]
    if len(matches)!=1:
        raise RuntimeError(f'Expected one active native body model for {ebp}')
    model=matches[0]
    donor=report['models'][model]
    manifest=Path(donor['manifest'])
    if sha(manifest)!=donor['manifest_sha256']:
        raise RuntimeError(f'Native donor manifest drift for {ebp}')
    static=overview['tiers'][ebp]
    if static['skeleton_bones']!=48 or static['palette_bones']!=[46] or len(static['lod_geometry'])!=3:
        raise RuntimeError(f'Unexpected ranged rig/LODs for {ebp}')
    weapon_models=[item['logical_path'] for item in trace['primary_weapon_models']]
    if not any(weapon in name for name in weapon_models):
        raise RuntimeError(f'Unexpected stock weapon route for {ebp}')
    tiers.append({
        'ebp':ebp,'slug':slug,'age':age,'style':style,
        'exact_native_body_model':model,
        'decoded_manifest':str(manifest),'decoded_manifest_sha256':sha(manifest),
        'native_lods':static['lod_geometry'],
        'native_skeleton_bones':48,'native_palette_bones':46,
        'primary_weapon_attachment':trace['primary_weapon_attachment'],
        'primary_weapon_models':weapon_models,
        'authoring_target':str(ART/'ranged_roster'/slug/(slug+'_v1.blend')),
        'approach':('reuse pinned approved v3l source, then export three native Archer LODs' if slug=='archer2'
                    else 'import exact per-tier donor and remodel native weighted garment/armor surfaces across all three LODs'),
    })

write(target,{
    'schema':'ccp-060-ranged-roster/1','status':'prepared_for_exclusive_blender_authoring',
    'source_audit':str(audit),'source_audit_sha256':digest,
    'source_summary':str(summary),'source_summary_sha256':sha(summary),
    'approved_sample':str(approved),'approved_sample_sha256':sha(approved),
    'tiers':tiers,
    'shared_rules':{
        'anatomy_and_motions':'each tier keeps its exact Chinese donor anatomy, 48-bone rig, 46-bone skin palette and native weapon class/animation owner',
        'materials':'one shared native atlas/material per tier and LOD; make a private albedo variant only after checking each tier’s own neutral cloth and owner-mask charts',
        'owner_color':'find safe native pattern mask per tier; never assume Archer II UV coordinates fit other atlases',
        'geometry':'visible broad garment/armor silhouette changes at stock game distance; preserve donor LOD weights and UVs outside intentional garment faces',
        'upgrade':'keep Rattan overlay separate; native conditional upgrade switch unqualified and deferred',
        'scope':'authoring and private art integration only, no new gameplay tiers or weapon remakes',
    },
})
print(str(target),sha(target),len(tiers))
