# Normal source verification, 2026-10-26

The full import passes the portable source verifier: 530 instances, 280 original
Persia instances, 27 Persian icons and 850 localization rows. All 29 maintained
tests pass, including selection, conversion failure handling, landmark eligibility,
dynasty requirements, effective inheritance and explicit editor-path precedence.
.NET XmlReader also parses all 530 instance XML files.

Refreshed current official inheritance resolves 373 private entity/squad records
against 5,758 official records with zero errors. The installed tuning validator
reports zero errors and zero warnings. SCAR/RDO static validation reports zero
errors; its warnings were reviewed: the engine-owned Player_GetSquads observer
must not be destroyed, full squad enumeration deliberately rejects an invalid
starting army, cardinal.scar provides PLAYERS through the mode entry, and the
selection table's five functions are defined in selection_core.scar. API checking
finds no missing localization IDs. Its unknown tokens are local functions, Lua
string operations, table methods and comment/parser artifacts; low-confidence
entries have signatures in the official API index.

All 249 existing Normal attribute files are byte-identical to the user-accepted
selection baseline commit 48a1897c3790aefc1ca68bda3c2cd8e14e63aeb4. The older
pre-selection ZIP differs in one market file, already present in that accepted
baseline; this import does not change it. All 315 recorded original Persia source
files retain their hashes. All 280 imported gameplay scalar/statetree values are
preserved apart from the approved additional Il-Khanid eligibility branch.

The staged diff contains four original Persian locale values ending in spaces.
These source strings are retained deliberately. Native source files preserve
their bytes in Git; contributor tooling and Markdown have declared line endings.

A clean staged export also passes the source verifier and all 29 tests with a
freshly installed declared Lupa 2.8 dependency, without work, .tools or machine
configuration. Temporary copy cleanup was rejected by automatic approval review;
the generated copies remain outside tracked source, as recorded in the handoff.

Native Content Editor burn, final SGA identity/readback, game import, full roster
behavior, landmark donor-effect teardown and multiplayer remain unverified.
See PERSIA_FULL_PORT.md for the native acceptance matrix and known limitations.
