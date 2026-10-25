# Maintained workspace tools

Run from the Garrison project root. Read `../AGENTS.md`, `STORAGE.md`, and
`docs/GARRISON_WORKFLOW.md` first. Tools never automatically import/install a mod.

- `verify_workspace.py`: storage, tool, identity and private-reference checks.
  `--storage-only` checks seven junctions; `--preservation` additionally hashes the
  entire normal edition and compares copied source after reversing only approved
  identity changes. Use preservation for migration acceptance; later intentional
  content changes require a new baseline, not altered migration evidence.
  Optional `--report PATH` writes JSON only under owned external output/provenance.
- `workspace_support.py`, `workspace.ps1`: shared guards; never create fallback
  directories. Module imports have no workspace side effects.
- `prepare_garrison.ps1`: initialize/adopt the art project or reapply the same
  preparation settings. Refuses an existing foreign identity. `-CheckOnly`
  inspects without updating settings. Neither route cooks or packages.
- `build.ps1`: future owner-run Content Editor build using the new project and
  linked F: output/cache. `-ValidateOnly` prints validated wiring without launching
  the editor or creating build output. `-EditorRoot` optionally selects an editor.
- `generate_prematch_precache.py`: owner-run regeneration of the existing private
  entity/squad hook from `VietnamMode.rdo`; checks storage before writing and
  allocates no identities. Use after deliberate RDO precache edits.
- `verify_runtime_package.py`: future read-only SGA identity/SCAR comparison;
  requires `--package` and existing `--runtime`. Never builds, downloads, or
  installs dependencies. Exit 0: match; 1: mismatch; 2: unreadable input.
  Compiled tuning and native behavior remain separate gates.

Use the `workspace.json` Python with `-B`. The retained `.tools/python` Lupa 2.6
dependency matches Python 3.12; recheck compatibility after interpreter updates.
No dependency was downloaded.
