# Garrison 0.7.4: Hideout construction time

User request: set Hideout construction time to 30 seconds and release 0.7.4.

The only gameplay source changes are `cost_ext/time_cost/time_seconds` from
60 to 30 in `vn_building_defense_outpost_chi.xml` and
`vn_building_defense_outpost_2_chi.xml`, including each campaign variant.
Both fortified children inherit the matching parent. Existing extension list
identities, PBG IDs, costs, upgrades, visuals and SCAR remain unchanged.

`output/release_074/before-source.zip` and `before.json` preserve the pre-edit
Garrison source and release metadata. 0.7.3 remains the package rollback;
its pinned SGA SHA-256 is
`907b596c01e147342e76e0700170cb72c76b525bd766a1a1dfb71a45b4107f8d`.
The normal edition already had two Hideout XML changes relative to the 0.7.2
freeze before this build. `normal-preexisting-drift.json` records those paths;
`normal-baseline.json` pins the current normal source for this task without
altering historical evidence. This release does not edit normal source.

Build with `tools/build_release_074.ps1 -Label <unique-label>`. This verifies
storage, checks the 0.7.3 identity contract, refreshes official extension
inheritance evidence, and runs the supported native Content Editor build in an
isolated F: source copy under the shared native-build lock. The build requires
completed native logs validating all 376 instances.

Assembly starts from the correctly named native archive and preserves every
0.7.3 member except the four Hideout RGD records taken from that native build.
It compares all member hashes and mounts, verifies the final archive namespace,
and verifies ZIP CRC, one manifest, version and embedded SGA hash. Custom art
and compiled-only resource overlays stay owned by the 0.7.3 baseline.
The SCAR revision banner is preserved and is independent of package version.

Static validation: 376 instances, zero errors, 130 existing warnings and one
unresolved-reference summary. The validator self-test and .NET XmlReader checks
on all four Hideout source files pass. Refreshed inheritance: 198 local / 5,758
official blueprints, zero errors.

Completed build: `tools/build_release_074.ps1 -Label v1` passed. Native logs
confirmed all 376 instances validated and completed burn. Exactly the four
Hideout RGD members changed; the other 1,263 members and every mount are
identical to 0.7.3. Final archive identity and ZIP verification passed.
`output/release_074/verification-v1.json` and `delivery-proof.json` retain
the exact hashes. The package is
`output/release_074/delivery/community_civilization_pack-0.7.4.zip`.

Automatic approval review rejected the attempted deletion of regenerable
074 extraction/assembly caches with "blocked by policy" before the command
ran. No cleanup was performed; all generated caches and diagnostics remain.

Native import, fresh-match timing, save/load and multiplayer are separate
unverified gates. Import the ZIP into Garrison, enable it, select the pack as
both Game Mode and Tuning Pack, then select China and Vietnam. Check the base
Hideout construction time; worker count and construction bonuses can affect
observed completion time. Also check the fortified upgrade still works.
