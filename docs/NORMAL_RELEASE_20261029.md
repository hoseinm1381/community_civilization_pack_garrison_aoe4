# Normal GitHub distribution — 29 October 2026

Source branch: `normal`. Playable and editable ZIP branch: `normal-release`.
These are independent of Garrison's `main`, `releases`, and the older
`base_game_release` distribution. Credits: **hosein81 and chilly5**.

This build includes China/Vietnam, Delhi/Persia and Zhu Xi/Korea selection,
conditional prematch loading, Literature generation/presentation, the Keep/Hwacha
barrage cleanup, normal Korean construction times, and the Observatory allowance
repair. Standard fresh Dark Age human matches are the supported milestone.

## Completed evidence

- A new native Content Editor burn completed on 29 October. Its BuildApplet
  copied the final SGA to the owned build output; the burn log has no error lines.
- Archive namespace: `a743d7d1d7534cf78817e29d8ded7366`.
- All 1,035 archive members pass stored CRC/SHA1 checks; header signature is not
  validated. All 910 local tuning instances are present; obsolete Persia probe
  members are absent.
- All 44 packaged SCAR files match current editable source after BOM/newline
  normalization. The rejected Observatory modifier is absent.
- Native RGD readback verifies all 27 corrected construction times across every
  packaged variant, Literature storage 100,000, stock action cap two, Korean book
  icon and preserved olive-oil icon.
- Portable verification and 81 maintained tests pass. Installed tuning and SCAR
  validation and the refreshed official inheritance audit passed for this source.
- All 104 original Persia edits and all 463 donor asset files retain their hashes.
  No Garrison source or installed game mod was changed.

The build helper's former single-dash options could exit without building. It now
uses the verified native double-dash BuildApplet options, keeps intermediates in
`output/`, and rejects missing/stale logs or missing/stale/empty archives. The
read-only package verifier also uses the current Normal project filename.

`normal-package-20261029.json` records archive/ZIP hashes, script hashes, native
construction readbacks and log hashes. Generated logs and readbacks remain local
under `work/normal_publish_20261029` and `output/normal-release`.

## Measured package budget

| Measurement | Bytes |
| --- | ---: |
| Final SGA | 12,839,445 |
| Playable local ZIP | 12,585,477 |
| Previous Normal ZIP, 26 October | 7,253,990 |
| Incremental complete ZIP | 5,331,487 |
| Korea-exclusive archive paths, stored | 5,414,754 |
| Korea-exclusive archive paths, decoded | 12,872,473 |

The incremental ZIP includes all changes since the older Normal distribution.
Exclusive-path totals exclude shared resource overrides and shared entry scripts.
The full ZIP is below 600,000,000 bytes; the additional civilization contribution
is below 200,000,000 bytes. Existing icon RGBA8 estimates remain 11,606,016 bytes
at base level / 15,474,688 with full mips. These are not measured GPU residency.

## Remaining gates

This package has not been installed or played by the agent. The owner's earlier
native matches establish opening selection and reported Literature behavior,
but the latest construction/Observatory repairs still need a fresh native match.
Follow `KOREA_CONSTRUCTION_20261029.md` and `KOREA_REPAIR_20261029.md` for the
checklist. Multiplayer and matched VRAM/frame-time measurements remain unverified.
Korean/Persian AI, Nomad, later-age starts and save/load remain outside scope.

Use the source branch for development. The `normal-release` README supplies
download links, installation instructions, exact source commit and SHA-256 sums.
