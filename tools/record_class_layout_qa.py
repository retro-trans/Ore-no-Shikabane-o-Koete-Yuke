"""Record measured class-layout changes; runtime visual QA pending. Dry run first."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from build_class_layout import V
from record_prologue_wrap_qa import sha, dump


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/class-layout-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'class.report.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert sha(out / 'EBOOT.class.elf') == report['elf_sha256']
    assert sha(out / 'data.class.ore') == report['archive_sha256']
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    assert len(report['descriptions']) == 8
    assert all(len(row['line_advances']) <= 3 and max(row['line_advances']) <= 420 for row in report['descriptions'])
    path = ui / 'title.png'
    assert Image.open(path).size == (480,272)
    screens = [dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path))]
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    proof = dict(version=V, result='STATIC PASS: all eight descriptions fit the widened layout; runtime visual verification pending',
        iso=identity, layout=report['layout'], descriptions_measured=report['descriptions'],
        screenshots=screens, checks=report['checks'],
        texture_replacement=False, save_state_loaded=False, save_preservation=preservation, github_release=False,
        limits=['All eight descriptions measured; five guarded native layout arguments and all untouched executable/archive bytes checked.',
            'A QA-only attempt to enter the viewer directly stopped the guest CPU before a class frame could be captured. This does not verify the class layout; its diagnostic entry record is marked failed.',
            'The new-child arrival sequence, actual class frame/hint clearance, gender switching and physical PSP remain untested.'])
    print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity, layout=proof['layout']), indent=2))
    if not args.write:
        return
    diagnostic = ui / 'preview-entry.json'
    if diagnostic.exists():
        obj = json.loads(diagnostic.read_text())
        obj.update(result='FAILED: guest CPU stopped before a class frame could be captured',
            rendering_verified=False, diagnostic_only=True)
        dump(diagnostic, obj)
    dump(ui / 'verification.json', proof)
    dump(ui / 'image-identity.json', identity)
    report['runtime_verification'] = 'PENDING: actual class screen and new-child flow not visually verified'
    dump(out / 'class.report.json', report)
    for relative in ['docs/local_build_status.json', 'docs/translation_progress.json']:
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj['class_description_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'], bytes=identity['bytes'], sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V, visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['class_description_and_hints'] = proof['result']
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
        'Current local test build: **0.2.43**, 2026-10-18; archive-text draft: **0.2.43**.',
        'Current local test build: **0.2.44**, 2026-10-18; archive-text draft: **0.2.44**.')
    line = '- `work/output/english-native-0.2.44.iso`: wider class descriptions with button hints directly above the box. All eight descriptions measured; runtime class-screen visual check pending. See [checks and limits](../work/ui/class-layout-0.2.44/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.43.iso`', line + '- `work/output/english-native-0.2.43.iso`', 1)
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'CHANGELOG.md'
    text = path.read_text(encoding='utf-8')
    entry_text = '''## 0.2.44 (2026-10-18)

- Extended the shared class-description panel from 288 to 432 pixels and centered it at x=24. Moved it from y=198 to y=204, retaining its 66px height and all three complete lines. All eight descriptions fit without wording changes.
- Moved Switch Gender and Back from their bottom anchors to y=180, directly above the description and below the class labels, as requested. Native buttons, gender switching, class unlocks and selection logic are unchanged.
- Only five guarded layout arguments change; no added code/RAM. Archive changes only its title version and all prior fixes are preserved. Source/target hashes, unchanged code/assets and all eight description widths pass static checks. Runtime class-screen visual verification is pending: a QA-only attempt to enter the viewer directly stopped the guest CPU before capture. No preview routing change is included in the delivered ISO. Original project saves restored; user source only read/copied. Local build only; no GitHub release. New-child flow and physical PSP testing remain pending.

'''
    if '## 0.2.44 ' not in text:
        path.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n'+entry_text, 1), encoding='utf-8')


if __name__ == '__main__':
    main()
