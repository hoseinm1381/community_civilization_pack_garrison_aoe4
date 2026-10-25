# Garrison 0.7.3: Vietnam selection archive identity fix

The user reported a fatal SCAR error immediately after selecting Vietnam in
0.7.2: `Cannot find b7fcea91257b408fb9e8ae4d8bc402e1:vn_building_town_center_capital_chi`
at `initialization.scar:50`. The preserved warnings log also shows missing
Garrison-qualified prematch blueprints.

## Confirmed cause and minimal correction

The project ID, attribute manifest, RDO localization and SCAR were already
translated to Garrison. However, `assets/_default.burnproj` still supplied normal
GUID `a743d7d1d7534cf78817e29d8ded7366` in ArchiveParameters `NiceName`.
The actual 0.7.2 SGA header `name` confirms that normal namespace was emitted.
`tools/release_072/port.py::translated` only translated selected suffixes and
excluded `.burnproj`. A successful compile and basename-only reference checks
therefore missed this release-breaking error.

0.7.3 changes only that single NiceName to
`b7fcea91257b408fb9e8ae4d8bc402e1` in editable gameplay/build source.
SCAR, tuning instances, localization, art and mod GUID are preserved. Release
metadata advances to 0.7.3. The runtime banner intentionally still says 072:
changing it would unnecessarily change the previously delivered script bytes.

## Mandatory future port procedure

1. Keep the destination Garrison GUID and stable bundle key. Translate the normal
   edition's own references without creating a dependency on the normal pack.
2. Include `.burnproj` in identity translation. Check ArchiveParameters NiceName,
   `.aoe4mod` ID, attribute `guid`, locstrings, RDO GUID parts, SCAR blueprint
   prefixes, and any generated metadata. Preserve foreign official identities.
3. Run `tools/release_073/check_identity.py` before compilation. It rejects the
   actual broken 0.7.2 source even though project/attrib IDs match.
4. After the native burn and every overlay/assembly, run the checker with
   `--archive <final.sga>`. Inspect the actual header, not the filename or ZIP
   bundle key. The final header name must match the destination normalized GUID.
5. Verify private reference targets and retained art/compiled-only owning
   resources. Member basenames alone do not prove runtime namespace resolution.
6. Keep package/import, fresh-match Vietnam selection, save/load and multiplayer
   as separate gates. Do not infer engine behavior from a static pass.

## Rebuild and evidence

Run `tools/build_release_073.ps1 -Label <new-unique-label>` from this root.
The build refreshes official inheritance evidence, compiles an isolated source
copy with the supported Garrison core/Content Editor route under the shared
native lock, and requires completed validation of every source instance.
It uses that correctly named native archive as the assembly base, overlays all
four TOCs from the pinned 0.7.2 resource baseline, then reads back and compares
every member hash and mount. This retains compiled-only art/lifecycle fixes.

`output/release_073/before-source.zip` is the exact pre-fix source snapshot;
`before.json` pins source hashes. `warnings-072.log` and `reported-error.png`
preserve user failure evidence. Original 0.7.2 delivery stays in its own directory.
The original 0.7.1 delivery, exact 0.7.0 rollback, normal source and protected art
are rechecked using the existing immutable freeze. No source from normal is edited.

`verification-<label>.json`, `delivery-proof.json`, and the native run/logs under
owned F: `staging/r73/<label>/run` record final evidence. The delivery is
`output/release_073/delivery/community_civilization_pack-0.7.3.zip`.

Native retest: import 0.7.3 in Garrison, enable it, select the pack as BOTH Game
Mode and Tuning Pack, select China, then choose Vietnam in a fresh match. Confirm
conversion completes with private Town Center, six villagers, scout and Water
Buffalo, with no missing-blueprint/fatal messages. Native import/match, save/load
and multiplayer are unverified until actually exercised.

## Completed verification (2026-10-23)

- `tools/build_release_073.ps1 -Label v1`: passed. Native run status succeeded,
  exit 0, 262.642 seconds; all 376 private source instances validated, no reported
  editor errors. Actual native logs are retained, not inferred from exit alone.
- Current official inheritance refresh: 198 local / 5,758 official blueprints,
  zero inheritance errors.
- Installed tuning validator: 376 instances, zero errors, 130 pre-existing
  warnings and one unresolved-reference summary, identical counts/code classes
  to 0.7.2. No tuning instance was changed. Skill validator self-test passed.
- Three identity regression tests passed. The actual pre-fix source rejection
  is saved in `actual-072-red.log`; the original 0.7.2 archive is also rejected
  even with fixed source. Final 0.7.3 archive GUID check passed.
- All 1,267 final member SHA-256 values and TOC mounts exactly match 0.7.2.
  No packaged gameplay, SCAR, localization, UI or art member changed.
- Strict ZIP CRC/readability, exactly one manifest, version, embedded SGA hash
  and standalone SGA integrity passed. `delivery-proof.json` pins delivery hashes.
- Normal source, 1,497 protected art/delivery/rollback inputs and the original
  0.7.2 SGA remain unchanged. No prior release or diagnostic evidence was deleted.

The native fresh-match retest described above remains required; it was not run
as part of this build/package repair.
