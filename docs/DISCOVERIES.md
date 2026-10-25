# Verified discoveries and pitfalls

These are project findings, each with its evidence scope. Follow the dated release
reports and preserved recipes for exact implementation. Do not treat old failed
experiments as current engine limitations or static success as runtime acceptance.

## Archive identity is a runtime namespace

The normal-to-Garrison port originally missed `_default.burnproj` NiceName. Native
compilation passed but Vietnam selection requested blueprints under a different
namespace and crashed. Project GUID, manifest/RDO/SCAR edits are insufficient:
check the final SGA header `name` with `list --verify`. See `RELEASE_073_IDENTITY_FIX.md`.

## A source cook can lose working compiled resources

Some art bindings and native owning-resource fixes were selectively integrated into
the delivered SGA. Preserve the accepted owning archive and overlay only explicitly
approved members. Verify every untouched member and its TOC. Relevant scripts,
resource stores and reports remain available; a broad cook is not a safe substitute.

## Native extension inheritance must include parent variants

An extension absent in a child XML may already be supplied by private/official
parents. Duplicate singleton extensions broke Content Editor builds twice. Resolve
the full chain, use exact inherited native list identities, refresh official evidence
after game updates and run the inheritance audit in addition to generic validation.

## Native buffalo animation works within a qualified scope

The original 45-bone cattle skeleton accepts custom idle and full four-leg walking
RHKA after a metadata-preserving Havok tagfile writer/predictive encoder. The user
confirmed those motions worked. Keep its actual native TYPE metadata and indices;
do not use an unrelated prototype skeleton or a scripted pose workaround. This does
not qualify other animal families, attacks/deaths, detailed transitions or multiplayer.
See `docs/ai/workflows/aoe4-garrison-blender/references/native-predictive-animation.md`
and `tools/release_082_animation`.

## Scripted voices require complete suppression closure

Garrison.audio does not mute original speech. Paired EBPS and SBPS tables plus active
age/gender attachment_speaker_code overrides must be inspected. Private voice owners,
attachment variants, naval inheritance and reachable upgrade/spawn routes matter.
The 0.8.4 coverage and typed overlay are preserved; in-game compressed playback,
correct routing, overlap, effort timing, save/load and multiplayer are still pending.

The final bank contains 9,702 spoken takes. 128 retain user-approved minor speech
imperfections, bound individually to jobs/audio/request/original/transcript hashes.
Do not call these exact-word or native-speaker-approved takes. Fifteen synthetic
efforts are archived outside delivery. Original stock pain/death media uses scripted
timing, and eight female infantry consumers explicitly use female villager efforts.

## Windows text translation can invalidate a correct bank

The first final assembly rejected two CRLFs introduced by write_text. Hashes matched
only after LF normalization, proving an emitter bug. The fix writes canonical UTF-8
bytes; the assembler comparison remains strict. The actual failing/passing regression
and tests are retained. Do not weaken hash checks or normalize away integrity errors.

## Storage names are not ownership evidence

The old `*_temp` folder owns required voice masters, recipes and recovery stores.
Its exFAT allocation unit is 262,144 bytes, so many tiny files consume much more than
their logical sizes. Hash-addressed lossless bundles reduce duplicate data and small
file overhead. Do not use hardlinks on exFAT or infer deletability from `cache/output`.

## SCAR lifecycle and deterministic gameplay

Use spawned-only group access when members may despawn. Presentation-only voice
arbitration, cooldowns and repetition avoidance must be independent of simulation RNG.
Keep teardown, ownership, death, mixed-selection and save/load checks separate.

## Historical freezes are evidence

Old absolute paths and outdated readmes are deliberately retained. Use this guide
and `RELEASE_084_DELIVERY.md` for current status. Never refresh a baseline to accept
an unintended edit or claim that a restored historical fixture was freshly compiled.
