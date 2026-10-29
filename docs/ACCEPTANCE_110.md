# Garrison 1.1.0 source acceptance — 2026-10-29

The owner tested the temp candidate, reported "it worked", and requested updating
the GitHub source without pushing a release. This authorizes transferring the
reviewed source, tests, documentation and compact rebuild delta to main.
Specific gameplay scenarios, player counts and performance measurements were
not reported. Preserve the detailed native checklist; do not mark every item
passed. Korean AI, Nomad, later-age starts and save/load remain excluded.

Accepted test ZIP SHA-256:
`f3c51cdf8060b69cb0c936703e6e8d92ec202d6e46f92918c048aa4340fcf344`.
SGA SHA-256:
`80d8e008e9320232d4b8d56072c5fa6cc1040a4f3df526b63541dd4b8f60b4eb`.
The build/package measurements and pre-acceptance results are retained in
RELEASE_110.md and BUILD_110.json. Their candidate-only status fields describe
the preparation stage; this record supplies the later owner acceptance.

The promotion preserves the five reviewed existing asset changes, 425 additions,
378 private Korean definitions and the accepted 1.0.6 art/voice resources.
One 11,381,219-byte pack carries the gameplay/rebuild delta; a small additional
pack records the current acceptance documentation without rewriting old packs.
The current index is updated. No full playable ZIP or SGA is added to Git.

The latest published Garrison release remains 1.0.6. The existing Normal and
normal-release branches, release tags/assets, temp delivery, editable art,
recovery stores and prior immutable packs are preserved. No release upload,
installation, model work or cleanup is included in this source update.
