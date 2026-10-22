"""Record verified deity sorting and confirmation layout. Dry run first."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from record_prologue_wrap_qa import sha, dump

V = '0.2.47'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/union-layout-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'union.report.json').read_text())
    runtime = json.loads((ui / 'runtime.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert runtime['result'] == 'PASS'
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    assert sha(out / 'EBOOT.union.elf') == report['elf_sha256']
    assert sha(out / 'data.union.ore') == report['archive_sha256']
    screens = []
    for name in ['title.png','sort.png','sort-longest.png','sort-last.png','confirmation.png','cancelled.png','deity-returned.png']:
        p = ui / name
        assert Image.open(p).size == (480,272)
        screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
    result = 'PASS: eight sort options and highlights fit; full required-points caption and value on separate rows inside taller confirmation card'
    proof = dict(version=V,result=result,iso=identity,layout=report['layout'],runtime=runtime,
        measurements=report['measurements'],screenshots=screens,checks=report['checks'],
        save_preservation=preservation,save_state_loaded=False,texture_replacement=False,
        gameplay_memory_writes=False,union_performed=False,github_release=False,
        limits=['Previewed Hayate with Sasara no Oen and cost 13, then selected No and Choose Another Deity.',
            'Other parent/deity combinations, applying every sort order, large displayed cost values and physical PSP not tested.'])
    print(json.dumps(dict(write=args.write,result=result,iso=identity),indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json',proof)
    dump(ui / 'image-identity.json',identity)
    report['runtime_verification'] = result
    dump(out / 'union.report.json',report)
    for relative in ['docs/local_build_status.json','docs/translation_progress.json']:
        p = ROOT / relative
        obj = json.loads(p.read_text())
        obj['union_layout_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V,visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['deity_sort_and_confirmation'] = result
        else:
            obj['version'] = V
        dump(p,obj)
    p = ROOT / 'work/ui/verified_screens.json'
    obj = json.loads(p.read_text())
    obj['latest_layout_candidate_version'] = V
    obj['additional_build_evidence'] = [r for r in obj.get('additional_build_evidence',[]) if r['version'] != V] + [
        dict(version=V,evidence=(ui / 'verification.json').relative_to(ROOT).as_posix(),scope=result)]
    dump(p,obj)
    p = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
    text = p.read_text(encoding='utf-8').replace('**0.2.46**, 2026-10-18; archive-text draft: **0.2.46**.','**0.2.47**, 2026-10-18; archive-text draft: **0.2.47**.')
    line = '- `work/output/english-native-0.2.47.iso`: wider deity sort columns and separate caption/value rows in the taller confirmation card. Actual screens and native geometry verified; see [evidence and limits](../work/ui/union-layout-0.2.47/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.46.iso`',line+'- `work/output/english-native-0.2.46.iso`',1)
    p.write_text(text,encoding='utf-8')
    p = ROOT / 'CHANGELOG.md'
    text = p.read_text(encoding='utf-8')
    entry = '''## 0.2.47 (2026-10-18)

- Doubled each deity sort-menu cell from 80 to 160 pixels. The centered native frame is now 348x91 at (66,90), with all eight complete captions and selection highlights inside it. Native colors, two-column ordering and controls retained.
- Extended the confirmation deity card from 48 to 60 pixels tall. Kept the full Offering Points Required caption, moved it left to the name inset and set it to 12px; moved the right-aligned value from y=162 to its own row at y=178. The card ends at y=196, clear of the confirmation prompt starting at y=200.
- Cold-started the final local ISO and verified the sort menu, longest/last option highlights, full caption, cost 13, card geometry and cancellation back to the deity list. Five live guarded layout instructions verified; only those five arguments change, with no added code/RAM. Archive changes only its title version; all text and other payloads unchanged. Original project saves restored and user saves read/copied only. No union performed. Local build only; no GitHub release. Other pairings, applying every sort order, large cost values and physical PSP remain untested.

'''
    if '## 0.2.47 ' not in text:
        p.write_text(text.replace('# Changelog\n\n','# Changelog\n\n'+entry,1),encoding='utf-8')
    (ROOT / 'docs/union-sort-confirmation-layout.txt').write_text(
        'Divine Union sort and confirmation layout, local build 0.2.47\n\n'
        'Sort popup builder: 0x088e2e14. Cell width instruction 0x088e3000: 80 -> 160.\n'
        'Native frame [66,90,348,91]; eight cells [10/178,10/29/48/67,160,16].\n'
        'Confirmation constructor: 0x0893ada8. Card at object+0x1550.\n'
        '0x0893b018: height 48 -> 60; frame [291,136,160,60].\n'
        '0x0893b0f0: caption font 14 -> 12; 0x0893b110: caption x315 -> 299.\n'
        '0x0893b15c: value y162 -> 178; right anchor 447 and font 14 unchanged.\n'
        'Caption remains at y162; measured advance 147.43 within 152px remaining frame width.\n'
        'Frame bottom 196; prompt top 200. No added code/RAM or translation changes.\n'
        'Native runtime reads and screenshots: work/ui/union-layout-0.2.47/verification.json\n'
        'Tools: build_union_layout.py, verify_union_layout.py, record_union_layout_qa.py (dry run first).\n',encoding='utf-8')


if __name__ == '__main__':
    main()
