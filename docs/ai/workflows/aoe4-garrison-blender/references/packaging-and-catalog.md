# Packaging, previews and catalogs

Read for release metadata, manifest compatibility, previews/minimaps, client installation, catalog updates or explicitly requested publication. Reconciled from installed 0.1.4 guide on 2026-10-11; online catalog state and new native results were not checked.

## Release and manifest contract

**Mod Project -> Edit: Build & Package -> Release details** requires a saved semantic version and one-line summary, at most 180 characters. Author/Changes are optional. Increase the version for a shared update. Package consumes the latest successful cook; source edits require their relevant Build/Save, then Cook. Live Reload must be off in that cook. Reimport the ZIP to update the independent client-library copy.

Outputs are `dist/<key>.sga`, `dist/package/{garrison.json,SGA files,START-HERE.txt,optional cover}` and `dist/<key>-<version>.zip`. A ZIP contains exactly one `garrison.json`; a containing folder is supported. Manifest import requires its sibling payloads. Preserve unowned/edited output conflicts rather than overwriting them to regenerate a package. Built outputs do not back up the `.blend`, library project, scripts or source media.

Count manifest basenames across the **entire ZIP**, including documentation and archived handoff folders, before delivery. Berber 0.7.5 was rejected with `The ZIP must contain exactly one garrison.json with its SGA files` because it contained both root `garrison.json` and `documentation/handoff/garrison.json`. A reference manifest must use a non-manifest basename such as `garrison.json.txt`, or stay outside the delivery. Root-only validation missed this. After renaming/removing a reference, regenerate any packaged checksums, verify member hashes/CRC again, and verify each declared SGA path/hash. This error is distinct from the older many-file installer rejection.

For the [qualified scripted voice route](scripted-unit-voices.md), the ordinary import ZIP can contain only the manifest, SGA with embedded audio/scripts, and concise instructions/coverage. It does not need an installer, launch script, development DLL or backend executable. Normal Garrison owns its matching runtime/backend; do not bundle an experimental runtime as if it were a mod dependency declared by `garrison.json`.

Use the generated strict `garrison.mod/v1` manifest. Its documented structure is:

| Field | Meaning |
|---|---|
| `schema`, `bundle_key` | `garrison.mod/v1` and stable bundle key |
| `members[]` | Each archive's `mod_key`, `role`, relative `path` and measured `sha256` |
| `details` | `id` (same as bundle key), `name`, required semantic `version`/`summary`; documented optional `author`, `updated`, `min_garrison`, `content_types`, `description`, `changelog`, `cover` |

Unknown fields/schemas and legacy `mod.bundle.json` are refused; rebuild a current package instead of renaming an incompatible manifest. A bare SGA can be imported but missing release metadata is displayed as Not supplied. `garrison.json` cannot request an executable or custom launch arguments; native-audio companions remain separately owned deployments.

Archive role, content type and lobby selection are different. Use actual generated roles, not a guessed role derived from a filename. Content types are `map`, `game-mode`, `tuning-pack`; a Game Mode can live in a map-role archive without a Crafted map. A Crafted map can live inside a tuning archive. Inspect archive content and `START-HERE.txt`: select every required Map, Game Mode and Tuning Pack explicitly. **Session -> Check match setup** reads the current launch log and can report a missing companion; Connected alone does not prove the mod's result.

## Preview, minimap and cover are distinct

**Preview image -> Pack Preview** accepts PNG, 16-2048 pixels per side and at most 16 MiB, and copies it into the project. `mod.png` does not automatically populate a Crafted map card. **Override map preview and minimap** defaults off; enable only for a true overhead map, since it also replaces terrain on the in-game minimap. It affects internal Crafted maps; external companions own their own overview. Reclick Pack Preview after changing the toggle, then Cook/Package. Independently edited previews are preserved/reported for review.

Content Editor's **Export Minimap** supplies `<map>_mm_generated.tga`, cooked to `.rrtex`. Keep that authored overview when removing a handmade override; deleting both can leave the default AoE image. Prefer the documented **1024 x 1024** overview route. In the guide's custom-map/tuning fixture, 768 x 768 BC7 cooked successfully but crashed before the menu; replacing only the texture with its 1024 x 1024 cook allowed startup. This is fixture evidence, not proof every other dimension always fails.

Package's automatic cover uses a qualifying packed PNG. General manifest covers may be PNG/JPEG/WebP, at most 4 MiB and 4096 pixels per dimension. An 8:3 image fits the compact card; other ratios crop. Cover limits do not qualify game overview dimensions or UI-image import dimensions.

## Client and catalog lifecycle

Install from file accepts ZIP, `garrison.json` or SGA. Local imports normally enable a new import; **new catalog installations start disabled**. Updates preserve Enabled. Close AoE4 and complete session cleanup before replacing installed mods; Essence Editor/GPUBurner may remain open during launch. Installed catalog mods stay in Catalog while available; unavailable/removed source entries fall back to Local without uninstalling their copy. Deleting a client copy does not delete authoring sources.

The official index is `https://raw.githubusercontent.com/AOE-Garrison/garrison-mod-catalog/main/catalog.json`. Its public index/download route needs no GitHub login. Other private GitHub catalogs require authorized access/CLI login; keep repository-scoped secrets out of manifests and redirect requests. **Source** accepts an HTTPS JSON index, not a repository page; source changes apply only after successful Sync.

Only the official source autosyncs: at startup without a saved index, or when it is over a day old. Custom sources use explicit Sync. Sync refreshes index/covers without installing updates. Failure retains the last successful offline index; retry on next startup or explicit Sync, without a repeating automatic loop. Removing an entry does not remove an installed mod.

Updates download and verify the entire version before installation, preserving the prior copy on download/hash failure and using the installation rollback journal on failure. Cancellation is checked during download and before the install transaction; let a started transaction finish. Older catalog versions do not automatically replace newer local releases. Matching names/keys do not authorize replacement of a local or other-source copy: use the explicit Replace workflow within the requested scope. Identical published ZIP copies can link without downloading; `garrison-play catalog-link <mod-id> <release.zip>` is the guide's advanced verified ID/version/archive linking route, after Sync. Verify the installed CLI before prescribing it; this does not imply a separately distributed `garrison-play.exe`.

`garrison://install/<mod-id>` opens/highlights the catalog card; it does not install it. IDs follow the catalog's at-most-64 ASCII letter/digit/underscore/hyphen rule, exclude `groups`, and match `details.id`. This differs from the stricter runtime/audio Mod Project key rule.

The bundled guide warns that the official catalog's older `mod.toml` builder/release ZIPs need migration from `mod.bundle.json`; it may list mods whose ZIPs cannot install. Treat this as a dated documentation warning. Inspect the actual requested release/manifest before claiming the online repository is still unmigrated or already fixed.

## Publishing when requested

In the target catalog repository, the documented `python scripts/publish_mod.py <release.zip>` verifies the package, creates GitHub release `<id>-v<version>` with asset `<id>-<version>.zip`, and updates `catalog.config.json`; commit/push then lets its workflow generate `catalog.json`. Read that repository's current instructions/tools first. Publication is an external action only within the user's requested scope. Keep stable mod ID/key and increase version; derive catalog metadata from the ZIP's manifest instead of maintaining duplicate descriptions manually.

Sources: installed `guide/{mods-catalog,cook-and-package,pack-the-mod,play,start-here,tools-and-pipeline}.html`.
