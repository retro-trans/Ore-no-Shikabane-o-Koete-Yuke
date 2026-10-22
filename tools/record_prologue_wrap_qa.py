"""Record read-only save hashes and verified prologue captures. Dry run first."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
import numpy as np
from catalog_text import ROOT
from build_prologue_wrap import V, EDITS
from capture_prologue_wrap import NAMES
from strip_jp import export

UI = ROOT / ('work/ui/dialogue-reflow-' + V)
OUT = ROOT / ('work/output/english-native-' + V)


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            result.update(block)
    return result.hexdigest()


def saves():
    folders = dict(project=ROOT / 'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117',
        user_source=Path('C:/Users/Binh/Documents/PPSSPP/PSP/SAVEDATA/UCJS10117'))
    return {key: {name: sha(folder / name) for name in ['SAVEDATA.BIN', 'PARAM.SFO', 'ICON0.PNG', 'PIC1.PNG']}
            for key, folder in folders.items()}


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--begin', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.begin:
        current = saves()
        print(json.dumps(dict(action='Hash only; no save writes', hashes=current, write=args.write), indent=2))
        if args.write:
            assert not (UI / 'save-before.json').exists()
            dump(UI / 'save-before.json', current)
        return
    report = json.loads((OUT / 'prologue.report.json').read_text())
    layout = json.loads((UI / 'layout.json').read_text())
    before = json.loads((UI / 'save-before.json').read_text())
    assert saves() == before
    assert sha(OUT / 'EBOOT.prologue.elf') == report['elf_sha256']
    assert sha(OUT / 'data.prologue.ore') == report['archive_sha256']
    records = []
    for rid, name in NAMES.items():
        path = UI / (name + '.png')
        native = json.loads(path.with_suffix('.native.json').read_text())
        meta = json.loads(path.with_suffix('.json').read_text())
        assert native['id'] == rid and native['translation'] == EDITS[rid][1]
        assert native['naturally_selected'] and native['exact_final_build_text']
        assert not native['register_or_memory_writes'] and not meta['texture_replacement']
        assert Image.open(path).size == (480, 272)
        evidence = dict(id=rid, screenshot=path.relative_to(ROOT).as_posix(),
            sha256=sha(path), native=native)
        if name != 'narration':
            # White glyph cores inside the actual purple portrait panel.
            # Exclude the animated advance icon at x=288..300.
            pixels = np.array(Image.open(path).convert('RGB')).astype(int)
            white = (pixels.min(2) >= 150) & (pixels.max(2) - pixels.min(2) <= 35)
            ys = np.flatnonzero(white[208:258, 26:280].sum(1) >= 2) + 208
            groups = []
            for y in ys:
                if not groups or y - groups[-1][-1] > 3:
                    groups.append([int(y)])
                else:
                    groups[-1].append(int(y))
            assert len(groups) == 3, (name, 'Incomplete visible text', groups)
            row = next(r for r in layout['rows'] if r['id'] == rid)
            boxes = []
            for group, advance in zip(groups, row['line_widths']):
                yy, xx = np.where(white[group[0]:group[-1]+1, 26:280])
                box = [int(xx.min()+26), group[0], int(xx.max()+27), group[-1]+1]
                assert abs(26 + advance - box[2]) <= 4, (name, 'Missing rendered text', box, advance)
                assert box[2] <= 296 and box[3] <= 260
                boxes.append(box)
            assert boxes[-1][2] + 8 < 288
            evidence.update(frame=[16, 198, 288, 66], text_ink_rectangles=boxes,
                advance_icon_envelope=[288, 244, 301, 258],
                last_line_to_icon_gap=288 - boxes[-1][2],
                measurement='Actual white glyph cores; shadow excluded. Complete text also visually inspected.')
        records.append(evidence)
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    proof = dict(version=V, result='PASS: three reflowed prologue passages selected naturally and visually checked in the final ISO',
        audited_passages=36, changed_passages=3, iso=identity, records=records,
        wording_and_controls='unchanged', maximum_lines=3, executable='byte-identical to 0.2.40',
        cold_boot=True, save_state_loaded=False, game_memory_writes=False, texture_replacement=False,
        saves='All four files in each project/user-source folder unchanged', github_release=False,
        limits=['All 36 passages measured; runtime visual checks cover the three changed passages. Physical PSP testing pending.'])
    print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity, screenshots=[x['screenshot'] for x in records]), indent=2))
    if not args.write:
        return
    dump(UI / 'verification.json', proof)
    dump(UI / 'image-identity.json', identity)
    dump(UI / 'save-preservation.json', dict(result='PASS', before=before, after=saves(), user_source_written=False))
    report['runtime_verification'] = proof['result']
    dump(OUT / 'prologue.report.json', report)
    layout['runtime_verification'] = proof['result']
    for row in layout['rows']:
        if row['changed']:
            row.update(fit_status='verified_selected_context_' + V,
                screenshot=next(r['screenshot'] for r in records if r['id'] == row['id']))
    dump(UI / 'layout.json', layout)
    for name in ['initial_batch', 'events_batch_001']:
        path = ROOT / ('work/translation/en/' + name + '.json')
        batch = json.loads(path.read_text(encoding='utf-8'))
        for row in batch['rows']:
            if row['id'] in EDITS:
                row['fit_status'] = 'verified_selected_context_' + V
                note = 'Exact naturally selected text and complete native framebuffer fit visually verified: work/ui/dialogue-reflow-' + V + '/verification.json'
                if note not in row['review_notes']:
                    row['review_notes'].append(note)
        dump(path, batch)
        dump(path.with_suffix('.en.json'), export(path))
    for relative in ['docs/local_build_status.json', 'docs/translation_progress.json']:
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj['prologue_wrap_evidence'] = (UI / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'],
                bytes=identity['bytes'], sha256=identity['sha256'])
            obj['title_branding'].update(version='v' + V, visual_evidence=(UI / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['prologue_wrap'] = proof['result']
        else:
            obj['version'] = V
        dump(path, obj)
    path = ROOT / 'work/ui/verified_screens.json'
    obj = json.loads(path.read_text())
    obj['latest_evidence_version'] = V
    ids = set(obj.get('visual_fit_verified_record_ids', [])) | set(EDITS)
    obj['visual_fit_verified_record_ids'] = sorted(ids)
    obj['additional_build_evidence'] = [x for x in obj.get('additional_build_evidence', []) if x['version'] != V] + [
        dict(version=V, evidence=(UI / 'verification.json').relative_to(ROOT).as_posix(), scope=proof['result'])]
    dump(path, obj)
    path = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
    text = path.read_text(encoding='utf-8').replace(
        'Current local test build: **0.2.40**, 2026-10-18; archive-text draft: **0.2.40**.',
        'Current local test build: **0.2.41**, 2026-10-18; archive-text draft: **0.2.41**.')
    line = '- `work/output/english-native-0.2.41.iso`: prologue narration and portrait dialogue rewrapped with every word retained. All 36 passages measured; three changed passages visually verified. See [QA evidence](../work/ui/dialogue-reflow-0.2.41/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.40.iso`', line + '- `work/output/english-native-0.2.40.iso`', 1)
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'CHANGELOG.md'
    text = path.read_text(encoding='utf-8')
    entry = '''## 0.2.41 (2026-10-18)

- Rewrapped the prologue's overflowing milk/hungry-baby reply, nearby post-fight dialogue and one opening narration passage. Every word, punctuation mark, control and record boundary is retained; each passage uses at most three lines and leaves clearance for the frame and advance icon.
- Audited all six opening narration records and thirty opening event dialogue records using native VWF advances. The other 33 passages already fit the conservative 268px / 254px final-line budget and remain unchanged.
- Replayed the final ISO from a cold boot and captured all three changed records through their actual MLT selections; complete wording and frame/icon clearance visually verified. Executable is byte-identical to 0.2.40, retaining the shared scratch protection and button font fixes.
- Both modified translation batches pass source/control/glossary/export checks; unrelated archive payloads verified byte-identical. All project and user-source save files unchanged. Local build only; no GitHub release. Physical PSP testing remains pending.

'''
    if '## 0.2.41 ' not in text:
        path.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1), encoding='utf-8')


if __name__ == '__main__':
    main()
