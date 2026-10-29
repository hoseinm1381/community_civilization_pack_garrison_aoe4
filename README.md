# Community Civilization Pack â€” Garrison

Current source: **1.1.0 â€” Vietnam, Persia and Korea**. Accepted baseline: **1.0.6**.

- China: China or Vietnam. Delhi Sultanate: Delhi or Persia.
- Zhu Xi's Legacy: Zhu Xi's Legacy or Korea.
- Shared 30-second selection; timeout and AI retain the original civilization.
- Fresh standard Dark Age human matches. Korean models come later.
- Accepted Persian/Vietnamese art, voices and native resource fixes are preserved.

Read [the 1.1.0 report and native checklist](docs/RELEASE_110.md).
Native build and full package readback passed. On 2026-10-29 the owner reported
that it worked and accepted the source for GitHub. Individual gameplay cases,
multiplayer and measured performance have no additional recorded results.
See [the acceptance record](docs/ACCEPTANCE_110.md). The latest published
Garrison release remains 1.0.6; no 1.1.0 release upload was requested.

Run `python -B tools/verify_current_source.py`,
`python -B tools/verify_korea_garrison.py`, and both maintained suites under
`tests/current` and `tests/persia`. Test dependency: `requirements-tests.txt`.
Native/compact rebuild: configure `workspace.local.json`, then run
`python -B tools/compact/github_build.py native` and `package`.
Do not substitute a broad native burn for the owning archive assembly.

Keep this permanent repository at its existing path. Candidate work belongs in
`F:/aoe_4_temp/Temp_before_github_push`; promote only after owner confirmation.
Keep immutable packs and editable art/audio/recovery inputs. No automatic push,
publication, installation or cleanup follows from candidate preparation.

Credits: **hosein81 and chilly5**.
