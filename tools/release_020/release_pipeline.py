"""Append-only 0.2.0 release stages; native reference cook is an explicit token gate."""
import sys
import re
from pathlib import Path
from common import OUT, guarded, read, sha, write
from guard_source_contract import verify as guard_source
from media import donor_models, scratch_models, hideout_models
from assemble_media import assemble
from reference import qualify
from compose import compose
from verify_archive import verify as verify_archive
from release_checks import verify as release_checks
from package_release import package, verify_existing
from cook_art import prepare as prepare_art, cook as cook_art
from cook_roofs import cook as cook_roofs
from cook_shelters import prepare as prepare_shelters, cook as cook_shelters
from compile_candidate import compile_candidate

sys.dont_write_bytecode = True
WORK = OUT / 'integration'


def prepare():
    guarded()
    guard_source()
    donor_models()
    scratch_models()
    hideout_models()
    media = assemble()
    from placement import verify as verify_placement
    placement = verify_placement()
    assert placement['status'] == 'passed' and len(placement['stamps']) == 9
    return media


def finish(label):
    guarded()
    media = read(WORK / 'media-020.json')
    reference = read(WORK / 'reference-cook.json')
    assert media['status'] == reference['status'] == 'passed'
    assert reference['models'] == media['models']
    candidate = compose(label)
    receipt = WORK / 'runs' / label / 'candidate.json'
    assert candidate['sha256'] == read(receipt)['sha256']
    verify_archive(receipt)
    release_checks(receipt)
    package(receipt)
    print('RELEASE_020_DELIVERED', sha(OUT / 'package-verification.json'))


def verify_only():
    guarded()
    pointer = read(WORK / 'candidate-pointer.json')
    candidate = Path(pointer['receipt'])
    assert sha(candidate) == pointer['sha256']
    verify_archive(candidate)
    release_checks(candidate)
    verify_existing(candidate)
    print('RELEASE_020_VERIFY_ONLY_PASSED')


def resume(candidate_path):
    """Finish a composed, freshly qualified candidate without repeating its cooks."""
    guarded()
    candidate_path = Path(candidate_path).resolve(strict=True)
    assert candidate_path.is_relative_to((WORK / 'runs').resolve())
    pointer = read(WORK / 'candidate-pointer.json')
    assert candidate_path == Path(pointer['receipt']).resolve(strict=True)
    assert sha(candidate_path) == pointer['sha256']
    candidate = read(candidate_path)
    assert candidate['status'] == 'passed' and sha(candidate['archive']) == candidate['sha256']
    verify_archive(candidate_path)
    release_checks(candidate_path)
    package(candidate_path)
    from cleanup_release import cleanup
    from report_release import report
    cleanup(True)
    verify_only()
    cleanup(True)
    report()
    print('RELEASE_020_CANDIDATE_RESUME_PASSED', str(candidate_path))


def rebuild(label):
    """Build one fresh, append-only 0.2.0 run from current frozen authoring inputs.

    The caller must hold the exclusive native cook token for the whole stage.
    """
    guarded()
    assert re.fullmatch(r'[a-z][a-z0-9-]{1,15}', label), label
    slug = label.replace('-', '')
    run_label = 'c020' + slug
    reference_label = 'cc020ref' + slug
    for target in (WORK / 'runs' / run_label,
                   WORK / 'candidate-sources' / run_label,
                   OUT / 'reference-cook' / reference_label,
                   OUT / 'art-cook/projects' / run_label,
                   OUT / 'shelter-cook/projects' / run_label):
        assert not target.exists(), ('Release label already used', str(target))
    prepare_art(run_label)
    cook_art('cc020-art-' + run_label)
    cook_roofs('cc020-roofs-' + run_label)
    prepare_shelters(run_label)
    cook_shelters('cc020-shelters-' + run_label)
    compile_candidate(run_label)
    prepare()
    qualify(reference_label)
    finish(run_label)
    from cleanup_release import cleanup
    from report_release import report
    cleanup(True)
    verify_only()
    cleanup(True)
    report()
    print('RELEASE_020_FRESH_REBUILD_PASSED', run_label)


if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'prepare': prepare()
    elif stage == 'reference': qualify(sys.argv[2])
    elif stage == 'finish': finish(sys.argv[2])
    elif stage == 'verify-only': verify_only()
    elif stage == 'rebuild': rebuild(sys.argv[2])
    elif stage == 'resume': resume(sys.argv[2])
    else: raise SystemExit('Stages: rebuild <label> | resume <candidate.json> | prepare | reference <label> | finish <label> | verify-only')
