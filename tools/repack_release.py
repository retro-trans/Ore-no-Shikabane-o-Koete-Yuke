"""Repackage 0.2.38 with the verified smaller delta. Dry run before --write."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.2.38'
NAME = 'OreNoShikabane-English-0.2.38-compact.xdelta'


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    bundle = ROOT / ('work/output/release-' + VERSION)
    backup = ROOT / ('work/output/release-' + VERSION + '-original-assets')
    small = ROOT / ('work/output/patch-size-study-' + VERSION + '/large-window.xdelta')
    source = ROOT / 'Ore no Shikabane o Koete Yuke (Japan).iso'
    target = ROOT / ('work/output/english-native-' + VERSION + '.iso')
    manifest = json.loads((bundle / 'BUILD-MANIFEST.json').read_text())
    old = dict(manifest['patches'][0])
    assert old['patch_bytes'] == 189434623
    assert small.stat().st_size == 2559594
    assert sha(source) == old['source_sha256'] and source.stat().st_size == old['source_bytes']
    assert sha(target) == old['target_sha256'] and target.stat().st_size == old['target_bytes']
    print(json.dumps(dict(write=args.write, old_patch=old['patch'], old_bytes=old['patch_bytes'],
        new_patch=NAME, new_bytes=small.stat().st_size, new_sha256=sha(small),
        target_sha256=old['target_sha256'], target_unchanged=True,
        backup=str(backup), bundle=str(bundle)), indent=2), flush=True)
    if not args.write:
        return
    assert not backup.exists()
    sys.path.insert(0, str(ROOT / 'work/source/retro-trans-tools'))
    from retro_trans.core import decode, engine_context
    from retro_trans.catalog import atomic_json
    from retro_trans.release import validate_directory
    validate_directory(bundle)
    with tempfile.TemporaryDirectory(prefix='compact-release-', dir=ROOT / 'work/output') as temporary:
        stage = Path(temporary)
        with engine_context() as engine:
            decoded = stage / 'verification.iso'
            decode(engine, source, small, decoded, old['target_bytes'])
            assert sha(decoded) == old['target_sha256'] and decoded.stat().st_size == old['target_bytes']
            decoded.unlink()
        assert sha(source) == old['source_sha256'] and sha(target) == old['target_sha256']
        shutil.copy2(small, stage / NAME)
        manifest['patches'][0].update(patch=NAME, patch_bytes=small.stat().st_size, patch_sha256=sha(small))
        atomic_json(stage / 'BUILD-MANIFEST.json', manifest)
        atomic_json(stage / 'VALIDATION.json', dict(schema_version=1,
            manifest_sha256=sha(stage / 'BUILD-MANIFEST.json'), patches=[dict(
                patch=NAME, roundtrip_verified=True, target_sha256=old['target_sha256'])]))
        (stage / 'SHA256SUMS.txt').write_text(''.join(
            sha(path) + '  ' + path.name + '\n' for path in sorted(stage.iterdir())), encoding='utf-8')
        validate_directory(stage)
        shutil.copytree(bundle, backup)
        for path in stage.iterdir():
            shutil.copy2(path, bundle / path.name)
        (bundle / old['patch']).unlink()
        validate_directory(bundle)
    docs = ROOT / ('docs/releases/' + VERSION)
    for name in ('BUILD-MANIFEST.json', 'VALIDATION.json', 'SHA256SUMS.txt'):
        shutil.copy2(bundle / name, docs / name)
    atomic_json(docs / 'REPACKAGING.json', dict(version=VERSION,
        reason='Larger xdelta source window avoids embedding relocated unchanged archive bytes.',
        source_commit=manifest['source_commit'], original_patch=old,
        replacement_patch=manifest['patches'][0], source_window_bytes=1073741824,
        roundtrip_verified=True, source_and_target_unchanged=True,
        catalog_strategy='Withdraw the exact old record; add the compact asset with a distinct URL.'))
    notes = docs / 'RELEASE_NOTES.md'
    text = notes.read_text(encoding='utf-8').replace(old['patch'], NAME)
    text = text.replace('### Apply\n', '### Apply\n\nRepacked download: **2.44 MiB** instead of 180.66 MiB. '
        'The patched ISO is byte-for-byte identical to the original 0.2.38 release.\n', 1)
    notes.write_text(text, encoding='utf-8')
    print('PASS: smaller patch decoded through Retro Trans Tools; all bundle checks passed.', flush=True)


if __name__ == '__main__':
    main()
