"""Record the button-prompt font fix and local build identity. Dry run before --write."""
import argparse
import hashlib
import json

from PIL import Image
from catalog_text import ROOT

V = '0.2.39'
UI = ROOT / ('work/ui/prompt-font-' + V)
OUT = ROOT / ('work/output/english-native-' + V)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--write', action='store_true')
args = parser.parse_args()
report = json.loads((OUT / 'prompt.report.json').read_text())
assert sha(OUT / 'EBOOT.prompt.elf') == report['elf_sha256']
assert sha(OUT / 'data.prompt.ore') == report['archive_sha256']
runtime = json.loads((UI / 'runtime-circle.json').read_text())
assert runtime['result'] == 'PASS' and runtime['text'] == 'and press the \u25cb button.'
tests = json.loads((UI / 'mips-tests.json').read_text())
assert tests['result'] == 'PASS'
save = json.loads((UI / 'save-preservation.json').read_text())
assert save['result'] == 'PASS' and save['user_source_unchanged']
screen = UI / 'settings-circle.png'
assert Image.open(screen).size == (480, 272)
iso = ROOT / ('work/output/english-native-' + V + '.iso')
identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
proof = dict(version=V, result='PASS: consistent native English font in the Settings Circle-button prompt',
    iso=identity, runtime=runtime, mips_tests=tests,
    screenshot=dict(file=screen.relative_to(ROOT).as_posix(), sha256=sha(screen)),
    extra_ram_bytes=report['extra_ram_bytes'], text_and_controls='unchanged',
    existing_ascii_glyphs='unchanged; duplicated into two tightly packed button-symbol pages',
    symbols=['Circle', 'Triangle'], japanese_fallback='preserved', texture_replacement=False,
    save_preservation='PASS: isolated normal saves restored; user save source unchanged',
    github_release=False, limits=['Circle prompt visually checked in the actual Settings explanation.',
        'Triangle prompts verified by executing the MIPS selector, not navigated live.',
        report['fallback'], 'Full playthrough and physical PSP testing remain pending.'])
print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity,
    mips_cases=tests['mips_cases'], glyph_geometry_checks=tests['glyph_geometry_checks']), indent=2))
if not args.write:
    raise SystemExit
dump(UI / 'verification.json', proof)
dump(UI / 'image-identity.json', identity)
report['runtime_verification'] = proof['result']
dump(OUT / 'prompt.report.json', report)
path = ROOT / 'docs/local_build_status.json'
data = json.loads(path.read_text())
data.update(latest_local_build=V, archive_translation_version=V, file=identity['file'], bytes=identity['bytes'],
    sha256=identity['sha256'], prompt_font_evidence='work/ui/prompt-font-' + V + '/verification.json')
data['title_branding'].update(version='v' + V, visual_evidence='work/ui/prompt-font-' + V + '/title.png')
data['checks']['english_button_prompt_font'] = proof['result']
dump(path, data)
path = ROOT / 'docs/translation_progress.json'
data = json.loads(path.read_text())
data.update(version=V, prompt_font_evidence='work/ui/prompt-font-' + V + '/verification.json')
dump(path, data)
path = ROOT / 'work/ui/verified_screens.json'
data = json.loads(path.read_text())
data['latest_evidence_version'] = V
data['additional_build_evidence'] = [x for x in data.get('additional_build_evidence', []) if x['version'] != V] + [dict(
    version=V, evidence='work/ui/prompt-font-' + V + '/verification.json', scope=proof['result'])]
dump(path, data)
path = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
text = path.read_text(encoding='utf-8').replace('Current local test build: **0.2.38**, 2026-10-18; archive-text draft: **0.2.38**.',
    'Current local test build: **0.2.39**, 2026-10-18; archive-text draft: **0.2.39**.')
line = '- `work/output/english-native-0.2.39.iso`: consistent native English font in Circle/Triangle prompts; Settings explanation visually verified. See [QA evidence](../work/ui/prompt-font-0.2.39/verification.json).\n'
if line not in text:
    text = text.replace('- `work/output/english-native-0.2.38.iso`', line + '- `work/output/english-native-0.2.38.iso`', 1)
path.write_text(text, encoding='utf-8')
path = ROOT / 'CHANGELOG.md'
text = path.read_text(encoding='utf-8')
entry = '''## 0.2.39 (2026-10-18)

- Fixed the mixed font in Itsuka's Settings explanation: Circle and Triangle symbols can now share the native 4x English font path with surrounding text. Each symbol has a hardware-sized atlas page containing exact copies of all existing English glyph rasters. Ordinary ASCII text retains its existing atlas and advances.
- Kept dialogue wording, control codes, spacing, destination geometry and Japanese fallback. The archive differs only in its title version footer. Added 264,052 bytes of executable/RAM data for the two button pages and guarded selector.
- Passed 12 actual MIPS cases, 343 glyph geometry checks and 190 exact ASCII raster comparisons. Verified the naturally selected Settings Circle-button line and its native UVs in the final ISO; Triangle prompts remain covered by MIPS execution rather than live navigation. Unsupported symbols and lines combining both button shapes retain the original fallback.
- Restored the isolated normal save and verified the user's source save unchanged. Local test build only; no GitHub release. Full playthrough and physical PSP testing remain pending.

'''
if '## 0.2.39 ' not in text:
    text = text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1)
path.write_text(text, encoding='utf-8')
