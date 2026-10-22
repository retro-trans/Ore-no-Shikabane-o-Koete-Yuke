"""Record weather-spacing checks and local build metadata. Dry run first."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from record_prologue_wrap_qa import sha, dump
from strip_jp import export

V = '0.2.46'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/weather-spacing-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'weather.report.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert sha(out / 'EBOOT.weather.elf') == report['elf_sha256']
    assert sha(out / 'data.weather.ore') == report['archive_sha256']
    screens = []
    for name in ['title.png','banner.png']:
        path = ui / name
        assert Image.open(path).size == (480,272)
        screens.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
    fixture_path = ui / 'preview-label.json'
    fixture = json.loads(fixture_path.read_text()) if fixture_path.exists() else None
    assert fixture and fixture['result'] == 'LABEL SELECTED'
    assert not fixture['weather_state_changed'] and not fixture['code_or_pc_changed']
    assert sha(ui / 'banner.png') == sha(ui / 'tutorial2.png')
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    result = 'PASS: slash spacing, complete effects line and wider native weather frame verified'
    proof = dict(version=V, result=result, iso=identity, text=report['text'], native_layout=report['native_layout'],
        visual_review='Full effects line and separator clear inside the centered frame in tutorial2.png, copied unchanged to banner.png.',
        screenshots=screens, checks=report['checks'], label_preview=fixture,
        save_preservation=preservation, save_state_loaded=False, texture_replacement=False, github_release=False,
        limits=['Downpour text selected once in the native label lookup for layout QA; weather/gameplay state unchanged.',
            'Random Downpour conditions, other weather effects and physical PSP not tested.'])
    print(json.dumps(dict(write=args.write, result=result, iso=identity),indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json', proof)
    dump(ui / 'image-identity.json', identity)
    report['runtime_verification'] = result
    dump(out / 'weather.report.json', report)
    batch_path = ROOT / 'work/translation/en/ui_batch_011.json'
    batch = json.loads(batch_path.read_text(encoding='utf-8'))
    row = next(r for r in batch['rows'] if r['id'] == report['text']['id'])
    assert row['translation_en'] == report['text']['after']
    row['fit_status'] = 'verified_native_banner_preview_' + V
    batch_path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    batch_path.with_suffix('.en.json').write_text(json.dumps(export(batch_path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for relative in ['docs/local_build_status.json','docs/translation_progress.json']:
        p = ROOT / relative
        obj = json.loads(p.read_text())
        obj['weather_spacing_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'], bytes=identity['bytes'], sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V, visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['weather_banner_spacing'] = result
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
    text = p.read_text(encoding='utf-8').replace('**0.2.45**, 2026-10-18; archive-text draft: **0.2.45**.', '**0.2.46**, 2026-10-18; archive-text draft: **0.2.46**.')
    line = '- `work/output/english-native-0.2.46.iso`: spaces around the Downpour effect separator; native weather banner automatically widens. Actual label preview verified; see [evidence and limits](../work/ui/weather-spacing-0.2.46/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.45.iso`',line+'- `work/output/english-native-0.2.45.iso`',1)
    p.write_text(text,encoding='utf-8')
    p = ROOT / 'CHANGELOG.md'
    text = p.read_text(encoding='utf-8')
    entry = '''## 0.2.46 (2026-10-18)

- Added spaces around the Downpour weather-effect separator: `Fire power DOWN↓ / Poor visibility`. Retained all wording, the arrow, color/size markup and the two-line layout. The native auto-size routine widens the centered frame to fit the extra spaces.
- Executable byte-identical to 0.2.45; only this text record and title version change in the archive. All other text rows and archive payloads checked unchanged. Verified the complete line, separator and wider frame in the actual native dungeon banner using a one-time QA label selection; weather/gameplay state and delivered executable unchanged. Original project saves restored; user saves read/copied only. Local build only; no GitHub release. Random Downpour conditions, other weather effects and physical PSP not tested.

'''
    if '## 0.2.46 ' not in text:
        p.write_text(text.replace('# Changelog\n\n','# Changelog\n\n'+entry,1),encoding='utf-8')
    (ROOT / 'docs/weather-banner-spacing.txt').write_text(
        'Weather banner spacing, local build 0.2.46\n\n'
        'Record ore:00027000:0000:11:0001; dungeon_common.mlb section 11 index 1.\n'
        'Two spaces added around slash; all wording and markup retained.\n'
        'Weather string accessor 0x08815afc; native banner setup 0x08891078..0x08891124.\n'
        'Center alignment: 0x088910f0. Auto-size: 0x088910fc -> 0x088244b0.\n'
        'Auto-size measures all ten text children; width=max rendered line+16, then native placement centers the frame.\n'
        'No executable changes, added code or RAM.\n'
        'QA preview selects text index 1 once at 0x08815b10, caller guarded 0x08891080; no PC/code/weather/save changes.\n'
        'Evidence and limits: work/ui/weather-spacing-0.2.46/verification.json\n',encoding='utf-8')


if __name__ == '__main__':
    main()
