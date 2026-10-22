"""Record the shared framebuffer scratch repair. Dry run before --write."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from catalog_text import ROOT

V = '0.2.40'
UI = ROOT / ('work/ui/boot-scratch-' + V)
OUT = ROOT / ('work/output/english-native-' + V)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def saves():
    folders = dict(project=ROOT / 'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117',
        user_source=Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117'))
    return {key: {name: sha(folder / name) for name in ['SAVEDATA.BIN', 'PARAM.SFO', 'ICON0.PNG', 'PIC1.PNG']}
        for key, folder in folders.items()}


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--begin', action='store_true', help='Record read-only save hashes before the replay')
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
if args.begin:
    before = saves()
    print(json.dumps(dict(write=args.write, action='Record save hashes; no save files are changed', hashes=before), indent=2))
    if args.write:
        assert not (UI / 'save-before.json').exists()
        dump(UI / 'save-before.json', before)
    raise SystemExit
report = json.loads((OUT / 'scratch.report.json').read_text())
runtime = json.loads((UI / 'runtime.json').read_text())
tests = json.loads((UI / 'mips-tests.json').read_text())
assert runtime['result'] == tests['result'] == 'PASS'
assert sha(OUT / 'EBOOT.scratch.elf') == report['elf_sha256']
assert sha(OUT / 'data.scratch.ore') == report['archive_sha256']
before = json.loads((UI / 'save-before.json').read_text())
assert saves() == before
screen = UI / 'opening-battle.png'
assert Image.open(screen).size == (480, 272)
assert not json.loads(screen.with_suffix('.json').read_text())['texture_replacement']
iso = ROOT / ('work/output/english-native-' + V + '.iso')
identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
proof = dict(version=V, result='PASS: opening battle preserves parent names and vital icons after the framebuffer transfer',
    iso=identity, runtime=runtime, tests=tests, scratch=report['scratch'],
    screenshot=dict(file=screen.relative_to(ROOT).as_posix(), sha256=sha(screen)),
    cold_boot=True, save_state_loaded=False, game_memory_writes=False, texture_replacement=False,
    project_and_user_saves='All four files in each folder unchanged', github_release=False,
    limits=['Opening battle HUD and its preceding capture transition checked; full playthrough and physical PSP testing pending.'])
print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity, scratch=report['scratch']), indent=2))
if not args.write:
    raise SystemExit
dump(UI / 'verification.json', proof)
dump(UI / 'image-identity.json', identity)
dump(UI / 'save-preservation.json', dict(result='PASS', before=before, after=saves(), user_source_written=False))
report['runtime_verification'] = proof['result']
dump(OUT / 'scratch.report.json', report)
path = ROOT / 'docs/local_build_status.json'
data = json.loads(path.read_text())
data.update(latest_local_build=V, archive_translation_version=V, file=identity['file'], bytes=identity['bytes'],
    sha256=identity['sha256'], shared_boot_scratch_evidence='work/ui/boot-scratch-' + V + '/verification.json')
data['title_branding'].update(version='v'+V, visual_evidence='work/ui/boot-scratch-' + V + '/title.png')
data['checks']['opening_battle_shared_scratch'] = proof['result']
data['checks']['battle_hud'] = proof['result']
dump(path, data)
path = ROOT / 'docs/translation_progress.json'
data = json.loads(path.read_text())
data.update(version=V, shared_boot_scratch_evidence='work/ui/boot-scratch-' + V + '/verification.json')
dump(path, data)
path = ROOT / 'work/ui/verified_screens.json'
data = json.loads(path.read_text())
data['latest_evidence_version'] = V
data['additional_build_evidence'] = [x for x in data.get('additional_build_evidence', []) if x['version'] != V] + [dict(
    version=V, evidence='work/ui/boot-scratch-' + V + '/verification.json', scope=proof['result'])]
dump(path, data)
path = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
text = path.read_text(encoding='utf-8').replace('Current local test build: **0.2.39**, 2026-10-18; archive-text draft: **0.2.39**.',
    'Current local test build: **0.2.40**, 2026-10-18; archive-text draft: **0.2.40**.')
line = '- `work/output/english-native-0.2.40.iso`: protected shared startup/framebuffer scratch; opening battle names and icons verified from a cold boot. See [QA evidence](../work/ui/boot-scratch-0.2.40/verification.json).\n'
if line not in text:
    text = text.replace('- `work/output/english-native-0.2.39.iso`', line + '- `work/output/english-native-0.2.39.iso`', 1)
path.write_text(text, encoding='utf-8')
path = ROOT / 'CHANGELOG.md'
text = path.read_text(encoding='utf-8')
entry = '''## 0.2.40 (2026-10-18)

- Fixed the corrupt parent names and black vital-icon boxes in the opening battle. The translated startup archive's accessors also supply a later framebuffer scratch area. The earlier relocation reserved only the 30,548-byte archive; a 480x272 RGBA capture on 512-pixel rows overwrote later added code, names and graphics.
- Restored the original 0x88000-byte writable workspace and placed the unchanged English startup archive inside it. The English archive is smaller than the original and fits with its existing zero padding, so no extra executable/RAM space is needed. Both accessors return the original shared address; earlier patch code/assets, text, controls and save records are unchanged. The data.ore archive changes only its title version.
- Verified both MIPS accessors and simulated the observed 272-row transfer plus a full buffer write. Replayed the prologue from a cold boot in the final ISO: the actual GPU transfer uses the reserved buffer, Genta/Orin remain intact, and all ten vital/element palettes and pixel payloads match the executable. Opening battle names and icons visually checked.
- All four isolated and user-source save files remain unchanged; no save state or game-memory edits. Local build only; no GitHub release. Full playthrough and physical PSP testing remain pending.

'''
if '## 0.2.40 ' not in text:
    text = text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1)
path.write_text(text, encoding='utf-8')
