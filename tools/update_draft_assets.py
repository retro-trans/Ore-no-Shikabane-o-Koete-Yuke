"""Replace the requested draft release assets. Dry run before --write."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'retro-trans/Ore-no-Shikabane-o-Koete-Yuke'
RELEASE_ID = 416255191


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    release = json.loads(gh('api', f'repos/{REPO}/releases/{RELEASE_ID}'))
    assert release['draft'] and release['tag_name'] == 'v0.2.38'
    assert json.loads(gh('api', 'user'))['login'] == 'binhlt0402'
    folder = ROOT / 'work/output/release-0.2.38'
    names = ['OreNoShikabane-English-0.2.38-compact.xdelta', 'VALIDATION.json',
             'SHA256SUMS.txt', 'BUILD-MANIFEST.json']
    assert {p.name for p in folder.iterdir()} == set(names)
    print(json.dumps(dict(write=args.write, draft=True,
        remove=[dict(id=a['id'], name=a['name'], bytes=a['size']) for a in release['assets']],
        upload=[dict(name=n, bytes=(folder / n).stat().st_size,
            sha256=hashlib.sha256((folder / n).read_bytes()).hexdigest()) for n in names]), indent=2), flush=True)
    if not args.write:
        return
    for asset in release['assets']:
        gh('api', '--method', 'DELETE', f"repos/{REPO}/releases/assets/{asset['id']}")
    for name in names:
        gh('release', 'upload', 'v0.2.38', str(folder / name), '--repo', REPO)
    gh('release', 'edit', 'v0.2.38', '--repo', REPO, '--notes-file',
       str(ROOT / 'docs/releases/0.2.38/RELEASE_NOTES.md'))
    assert json.loads(gh('api', f'repos/{REPO}/releases/{RELEASE_ID}'))['draft']
    print('Draft assets replaced; release remains unpublished.', flush=True)


if __name__ == '__main__':
    main()
