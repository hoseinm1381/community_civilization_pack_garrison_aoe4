# Release 0.6.1 native visibility diagnosis

Read-only investigation on 2026-10-18. Storage guard passed before any write:
`tools/verify_workspace.py --storage-only` reported status `passed` and all seven configured F: targets under `F:\aoe_4_temp\Community_civilization_pack_garrison_temp`.

## Finding: 0.6.0 new private native RGDs are mounted under the wrong TOC

The delivered 0.6.0 SGA (`output/release_060/assembly/candidate-r2/community_civilization_pack.sga`, SHA-256 `204a889662e2b403b5c0caccb4b79f08bdf0654f90b5f9095ebebfd773b641c8`) has 1,196 members. Its 80 newly added private Vietnamese RGDs under `attrib/.../release_060/` all report `toc: data`. Example: `attrib/attachments/attachment_lists/vietnam/release_060/v6i0363b8c.rgd`, 2,223 bytes, is stored in `data`.

This is directly explained by `tools/release_060/assemble_payload_archive_060.py`: it sends the complete mixed 447-member overlay through one `sga-archiver set-members ... --alias data` call. The alias applies to new members; existing baseline members retain their `attrib` TOC. Thus 62 changed existing Vietnamese RGD members remain in `attrib`, while all 80 new private identities/list RGDs land in `data`. This breaks the standard `attrib/*.rgd` lookup contract and makes new visual attachment selectors and private owners unavailable at runtime. Their target media being present is insufficient.

## Berber comparison

The working Berber 0.9.0 SGA (`F:\aoe_4_temp\Berber_future_kingdom_ai_20261014\output\berber_update_0_9_0\Berber_future_kingdom.sga`) confirms the intended split:

- Private native attachment lists such as `attrib/attachments/attachment_lists/garrison/berber_buildings_040/v040_fez_tier.rgd` are stored in `toc: attrib` (all four sampled 040 list RGDs).
- Berber native art resources such as `art/scenario/garrison/bb026/barracks_age1/barracks_age1.rgm` and its `.../palette_.../albedotex.rrtex` are stored in `toc: data`.
- CCP's model and texture resources, e.g. `art/scenario/garrison/v60b01/m001/m001.rgm` (42,597 bytes) and `.../albedotexture.rrtex` (37,841 bytes), correctly reside in `data` too. No broad media repackaging or material rebinding is indicated by this TOC finding.

The package-level minimal repair is to partition the pinned payload rows by member type/expected TOC and apply them in sequence to the same isolated candidate: new `attrib/*.rgd` members with `--alias attrib`; new `art/...` model/material/texture members with `--alias data`. Keep existing-member updates on their original TOC. Then regenerate a fresh full archive readback, verify all 80 private RGDs report `attrib`, all art media report `data`, and preserve byte-identical untouched members. Do not use a blanket `--alias attrib` on the entire mixed payload.

## Scouts and villagers

The report and handoff show that scout and villager models/materials are included in the broader 0.6.0 payload, but static evidence alone cannot establish why those units were visible in the user's match. Their observed visibility is consistent with them resolving through pre-existing/stock selector routes while the new private 0.6.0 attachment-list RGDs fail to resolve; the archive proves the mount defect but not the exact live fallback path. To make that distinction conclusive, compare the scout/villager selected attachment-list paths in the same final archive/readback and match them against the 80 new RGDs. No gameplay or native runtime test was run here.

## Castle landmarks

The Castle landmark issue is a separate pre-existing custom-resource gate, not explained by the 0.6.0 private-RGD TOC error: their models/materials were already in 0.5.3. The 0.5.2 Test A user result says both restored *stock* completed models render and explicitly inferred the completed landmark attachment path worked, leaving custom model/resource rendering as the isolated concern. The 0.5.2 diagnostic-C candidate changed only two custom landmark `model.rrmaterial` option values (from 0 to 1) and included a separate stealth candidate; no user-native result for Test C was found in the inspected result folder. Therefore that material probe remains unqualified. Do not claim the 0.6.0 TOC fix alone repairs the Castle landmarks; test the isolated Test C material candidate or recook/compare the private landmark model-material resource path separately.

## Scope limits

No archive was modified or cooked; no Blender scene or source file was opened for editing. The archive listings were read with the installed `sga-archiver` 0.3.0. Import, lobby selection and native match behavior remain unverified by this diagnosis.
