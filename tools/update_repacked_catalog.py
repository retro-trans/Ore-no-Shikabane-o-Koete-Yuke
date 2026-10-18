"""Retire the large delta and register its byte-identical replacement. Dry run first."""
import argparse
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = 'retro-trans/Ore-no-Shikabane-o-Koete-Yuke'
CATALOG = 'repos/retro-trans/retro-trans-tools/contents/retro_trans/resources/catalog.json'


def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], text=True, encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    assert not args.publish or args.write
    response = gh('api', CATALOG)
    old = json.loads(base64.b64decode(response['content']))
    new = copy.deepcopy(old)
    row = next(r for r in new['releases'] if r['repo'] == REPO and r['tag'] == 'v0.2.38')
    assert len(row['manifest']['patches']) == 1 and row['manifest']['patches'][0]['patch_bytes'] == 189434623
    retired = copy.deepcopy(row)
    retired['reason'] = 'Replaced at maintainer request with a 2.44 MiB compact delta; source and output ISO bytes unchanged.'
    manifest = json.loads((ROOT / 'work/output/release-0.2.38/BUILD-MANIFEST.json').read_text())
    name = manifest['patches'][0]['patch']
    assert name != retired['manifest']['patches'][0]['patch']
    row['manifest'] = manifest
    row['assets'] = {name: f'https://github.com/{REPO}/releases/download/v0.2.38/{name}'}
    new.setdefault('withdrawn_releases', []).append(retired)
    sys.path.insert(0, str(ROOT / 'work/source/retro-trans-tools'))
    from retro_trans.catalog import Catalog, assert_immutable
    before, after = Catalog(old), Catalog(new)
    assert_immutable(before, after)
    for r in old['releases']:
        if r['repo'] != REPO:
            assert r in new['releases']
    assert len(after.edges) == len(before.edges)
    assert len(after.withdrawn_edges) == len(before.withdrawn_edges) + 1
    proof = dict(write=args.write, publish=args.publish, previous_blob=response['sha'],
        retired_patch=retired['manifest']['patches'][0]['patch'], active_patch=name,
        active_patch_bytes=manifest['patches'][0]['patch_bytes'],
        old_identity_preserved=True, catalog_immutability_check='PASS', unrelated_records_unchanged=True)
    print(json.dumps(proof, indent=2), flush=True)
    if not args.write:
        return
    folder = ROOT / 'work/source/publication-0.2.38'
    request = folder / 'repacked-catalog-request.json'
    payload = dict(message='Replace oversized Oreshika delta with verified compact encoding', sha=response['sha'],
        content=base64.b64encode((json.dumps(new, indent=2, ensure_ascii=False) + '\n').encode()).decode())
    request.write_text(json.dumps(payload), encoding='utf-8')
    if args.publish:
        result = gh('api', '--method', 'PUT', CATALOG, '--input', str(request))
        proof['catalog_commit'] = result['commit']['sha']
        (folder / 'repacked-catalog-update.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
        print('Catalog updated: ' + result['commit']['sha'], flush=True)


if __name__ == '__main__':
    main()
