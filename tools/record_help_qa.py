"""Record Help panel runtime evidence and local build status. Dry run first."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from record_prologue_wrap_qa import sha, dump

V = '0.2.45'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/help-dialogue-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'help.report.json').read_text())
    runtime = json.loads((ui / 'runtime.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert runtime['result'] == 'PASS'
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    assert sha(out / 'EBOOT.help.elf') == report['elf_sha256']
    assert sha(out / 'data.help.ore') == report['archive_sha256']
    screens = []
    for name in ['title.png', 'faq-after.png', 'overflow-after.png']:
        path = ui / name
        assert Image.open(path).size == (480,272)
        screens.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    proof = dict(version=V, result='PASS: wider six-line Help panel, complete text inside its frame, opaque background confirmed',
        iso=identity, layout=report['layout'], runtime=runtime, measured_example=report['measured_example'],
        screenshots=screens, checks=report['checks'], save_preservation=preservation,
        texture_replacement=False, save_state_loaded=False, github_release=False,
        limits=['Verified the first two Passage of Time Help pages in a cold-started software PPSSPP instance.',
            'Other Help topics and physical PSP not visually tested. The inherited 0.2.44 class-screen runtime check remains pending.'])
    print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity), indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json', proof)
    dump(ui / 'image-identity.json', identity)
    report['runtime_verification'] = proof['result']
    dump(out / 'help.report.json', report)
    for relative in ['docs/local_build_status.json', 'docs/translation_progress.json']:
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj['help_dialogue_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'], bytes=identity['bytes'], sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V, visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['help_dialogue_frame'] = proof['result']
        else:
            obj['version'] = V
        dump(path, obj)
    path = ROOT / 'work/ui/verified_screens.json'
    obj = json.loads(path.read_text())
    obj['latest_layout_candidate_version'] = V
    obj['additional_build_evidence'] = [r for r in obj.get('additional_build_evidence', []) if r['version'] != V] + [
        dict(version=V, evidence=(ui / 'verification.json').relative_to(ROOT).as_posix(), scope=proof['result'])]
    dump(path, obj)
    path = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
    text = path.read_text(encoding='utf-8').replace(
        'Current local test build: **0.2.44**, 2026-10-18; archive-text draft: **0.2.44**.',
        'Current local test build: **0.2.45**, 2026-10-18; archive-text draft: **0.2.45**.')
    line = '- `work/output/english-native-0.2.45.iso`: wider six-line Help panel; full text and opaque background verified in actual Passage of Time pages. See [evidence](../work/ui/help-dialogue-0.2.45/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.44.iso`', line + '- `work/output/english-native-0.2.44.iso`', 1)
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'CHANGELOG.md'
    text = path.read_text(encoding='utf-8')
    entry = '''## 0.2.45 (2026-10-18)

- Widened the native six-line Help dialogue from 300 to 336 pixels, keeping x=8, y=144 and height=120. The reported 311px line now fits inside the 330px text area without cutting or rewrapping any wording. The native frame and advance marker follow the new size.
- Confirmed the Help background is already fully opaque: every texture palette and vertex alpha is 255, and sprite/window/ancestor opacity is 1.0. Retained these settings; story-dialogue translucency is unchanged.
- Cold-started the final local ISO and visually checked both Passage of Time pages, the complete reported line, frame and advance marker. One guarded width argument changes; no added code/RAM. All archive payloads except title version are byte-identical to 0.2.44; prior fixes retained. Original project saves restored and user saves only read/copied. Local build only; no GitHub release. Other Help topics, physical PSP and the inherited 0.2.44 class-screen runtime check remain pending.

'''
    if '## 0.2.45 ' not in text:
        path.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n'+entry, 1), encoding='utf-8')
    (ROOT / 'docs/help-dialogue-layout.txt').write_text(
        'Help dialogue layout, local build 0.2.45\n\n'
        'FAQ view constructor: 0x088fa6b4; six-line window at view+0x110.\n'
        'Width instruction 0x088fa718: 0x2405012c -> 0x24050150 (300 -> 336).\n'
        'Frame: [8,144,336,120]. Native text area: 330px. Reported longest line: 311.14px.\n'
        'Background sprite: window+0x130; vertex colors at +0x220. Texture and vertex alpha 255, sprite and inherited opacity 1.0: already opaque.\n'
        'No words, scripts, controls or story-dialogue opacity changed. No added code/RAM.\n'
        'Runtime evidence: work/ui/help-dialogue-0.2.45/verification.json\n'
        'Tools: build_help_dialogue.py, verify_help_runtime.py, record_help_qa.py (dry run first).\n', encoding='utf-8')


if __name__ == '__main__':
    main()
