# Source and evidence policy

## Contents

1. Evidence order
2. How to approve a symbol
3. How to use unofficial code
4. What to do when evidence conflicts

## Evidence order

Use the strongest available evidence in this order:

1. Official API signature in `Essence_ScarFunctions.api` or constant in `Essence_Constants.api`.
2. Exact usage in official AoE4 SCAR source, preferably in two independent files.
3. Official-source results from the AoE4 MCP (`api_context`, `find_api`, `find_usage`, `inspect_symbol`, `find_module`).
4. A definition and all import/call sites in the current mod project.
5. Unofficial examples from the supplied corpus.
6. General Lua knowledge, only for Lua language behavior rather than AoE4 engine behavior.

Do not invent an AoE4 helper, callback, event field, blueprint, constant, return type, or import path. If a required symbol remains unverified, stop that part of the implementation and report the unresolved contract.

## Approve a symbol

For every engine or framework call added or changed:

1. Find the exact spelling and parameter list in the official API or MCP.
2. Find official usage with the same argument types and lifecycle context.
3. Distinguish an engine API from an imported Lua wrapper. A wrapper requires its defining file and import path.
4. Confirm the return value before indexing, comparing, or storing it.
5. Confirm event callback context fields from an official handler for the same event.
6. Run AoE4 MCP `check_code` on the finished SCAR text.

Use `scar-symbol-provenance.tsv` for a quick offline lookup:

- `official-api`: documented engine API.
- `official-source`: Lua function defined in official source; import its module when required.
- `official-terrain-lua`: generated-map helper, not proof of availability in match-time SCAR.
- `unofficial-definition`: secondary evidence only; inspect its full definition and dependencies.
- `usage-only`: not enough to infer a signature.

The provenance index covers the supplied corpus, not every engine-bundled core library. A framework call can therefore appear as `usage-only` even when AoE4 MCP can locate its definition in a source file absent from the corpus. Resolve that gap with `inspect_symbol`, `find_module`, and exact official usages; do not relabel the generated index by guesswork.

## Use unofficial code

Unofficial code is useful for discovering possible mechanics, RDO layouts, UI experiments, and integration ideas. It is not proof that a call exists or that a pattern is multiplayer-safe.

Before reusing unofficial code:

1. Trace every called helper to a definition or official API.
2. Trace every import and required global.
3. Replace copied global names with a module-specific prefix.
4. Check whether intervals, events, modifiers, UI, groups, and timers are cleaned up.
5. Check whether repeated callbacks can register the same rule or stack the same modifier.
6. Check whether local UI actions are synchronized before changing simulation state.
7. Preserve the idea only when the implementation contract survives those checks.

## Resolve conflicts

- Prefer current official source over old documentation when the source shows a clear, working signature.
- Prefer current project definitions over a similarly named unofficial helper, but inspect all call sites before changing behavior.
- Treat an official example as evidence, not perfection. The corpus contains duplicate global definitions and incomplete cleanup patterns; improve them in new code.
- Treat one MCP miss as incomplete search rather than proof that a ScarDoc-documented symbol is invalid. Cross-check the raw API, official source, and local definition.
- When API docs, official source, MCP, and local code disagree, state the conflict and require an engine test. Do not silently choose a signature.
- Never claim engine validation from static checks alone.
