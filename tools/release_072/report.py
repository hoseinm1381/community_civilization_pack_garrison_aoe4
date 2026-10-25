from freeze import *
def main():
    delivery=json.loads((OUT/'delivery-proof.json').read_text());assert delivery['package_verified']
    label=delivery['assembly_label'];assembly=json.loads((OUT/('assembly-'+label+'.json')).read_text());overlay=json.loads((OUT/('overlay-'+label+'.json')).read_text())
    assert delivery['sga_sha256']==assembly['sga_sha256'];assert sha(OUT/'delivery/community_civilization_pack.sga')==delivery['sga_sha256'];assert sha(OUT/'delivery/community_civilization_pack-0.7.2.zip')==delivery['zip_sha256']
    report=f'''# Community Civilization Pack — Garrison 0.7.2

Credits: **hosein81 and chilly5**.

The active editable Garrison workspace now contains the complete normal v12
gameplay with all existing Garrison custom art retained. Normal source, original
0.7.1 delivery, exact 0.7.0 rollback, and all 1,497 protected art/rebuild/delivery
files remain hash-identical. Generated Garrison game mode and Live Reload remain
disabled. No Blender source, geometry, material, animation or texture was edited.

## Delivery

- ZIP: `output/release_072/delivery/community_civilization_pack-0.7.2.zip`
- ZIP bytes: {delivery['zip_bytes']:,}
- ZIP SHA-256: `{delivery['zip_sha256']}`
- SGA SHA-256: `{delivery['sga_sha256']}`
- Strict manifest version **0.7.2**, existing bundle key/project GUID, one tuning
  archive, one manifest basename throughout the ZIP, CRC/member hashes verified.

## Gameplay and visuals

All 246 normal definitions are preserved semantically after namespace translation,
visual-only fields and donor-proven equivalent private identity references.
This includes Buffalo speed 3.5 m/s (UI 0.875), Supervise E, Paddy Wood, removed TC
counter, smaller influence display, 8 m tunnel loading allowance and the cleaned
game mode route. The retired army and 61 reviewed old definitions are absent
from the packaged definition set. Garrison's display-name row 1001 is retained;
all other localization row IDs and current normal text are preserved.

Existing custom buildings/units/equipment keep their exact native art. New normal
units without compatible existing art keep their normal visuals. Retired art
remains available as authoring/rebuild input without restoring obsolete gameplay.

The final archive has **{len(assembly['members'])} members** and preserves **952
art/attachment resources** byte for byte, including lifecycle selectors, stamps,
materials and model media. It reads back all **28 current SCAR files** exactly;
2,083 own blueprint references resolve and 398 PBG IDs are collision-free.

Native assembly changes only 105 render/identity field tables across 25 freshly
compiled EBPS/SBPS records. Undoing these edits recovers their exact fresh bytes.
Private squads, crews, market production, ram and siege-tower construction remain
connected to their custom actors. Four deliberately changed normal siege
production entries retain v12's units. No old gameplay actor/squad is copied whole.

## Verification

- Real completed Content Editor burn: source v3, **376 instances**, no errors,
  successful run state/exit0. Source inputs stayed unchanged during the burn.
- Refreshed current official inheritance: **198 private / 5,758 official**, 0 errors.
  The actual historical duplicate-extension regression remains preserved.
- Tuning: **376 instances, 0 errors**. 130 warnings are existing version-2 art/support
  definitions outside the validator's supplied version corpus; the native editor
  successfully compiled them. External official references are informational.
- **102 behavioral tests**, 0 failures/errors/skips, against actual Garrison SCAR.
  Four independent source/parity tests and four active-port contracts pass.
  Three historical exact-source/visual freezes are explicitly superseded by
  current semantic preservation, rather than changing historical test files.
- 29 SCAR/RDO files statically checked, 0 errors; .NET XmlReader parsed 380 files.
  CSV/RDO checks validate 536 unique locale IDs, object IDs and destination GUID parts.
- MCP context/checks reviewed: apparent unknowns are Lua keywords, local helpers
  or imported project definitions. Existing official low-usage API confidence
  warnings remain documented; this port introduces no engine call.
- Independent review found 39 activation links missing from candidate v3 despite
  exact media bytes. Actual compiled regression failed RED, final v5 passes GREEN;
  reviewer independently confirmed all 39 restored and no remaining important issue.
- Full final member/mount readback and independent native preservation passed.
  Both installed skill fixture smoke tests passed. All 7 storage links verified.

Initial failed native v1 source/logs, rejected intermediate assembly evidence,
source freezes and review remain under `output/release_072` and `staging/r72`.
The final source burn is v3, final native assembly/package is **{label}**.
No broad cleanup or retirement of editable/rebuild inputs was performed.

## Import and focused native checks

Close AoE4, import the 0.7.2 ZIP through Garrison, enable it, and select Community
Civilization Pack as **both Game Mode and Tuning Pack**. Choose China in the lobby,
then Vietnam at match start. Start a fresh match. Expected revision:
`20261023-runtime-v12-garrison-072`.

Check custom building/unit appearance at all available ages, construction, damage,
destruction, persistent landmark ruins and repair. Check unbuilt families retain
normal visuals. Confirm Buffalo speed, E supervision and Paddy Wood, removed TC
diamond and smaller influence display. Tunnel 35–50 eligible units from a spread
formation and verify every arrival, cancellation/recovery and cooldown.

**Not performed:** Garrison client import/lobby test, native appearance/gameplay,
save/load or multiplayer. No fresh art cook was needed: existing cooked media
were preserved exactly. Static/build/package results do not establish runtime
behavior or compatibility with older saves.

See `docs/DEVELOPMENT_072.md` for current ownership/build/recovery instructions.
'''
    (ROOT/'docs/RELEASE_072_REPORT.md').write_text(report,encoding='utf-8')
    print('Report generated from verified final delivery',label)
if __name__=='__main__':main()
