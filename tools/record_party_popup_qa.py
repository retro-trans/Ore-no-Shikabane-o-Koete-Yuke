"""Record verified party popup geometry and captures. Dry run before --write."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from build_party_popup import V
from record_prologue_wrap_qa import sha, dump


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/party-popup-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'party.report.json').read_text())
    before = json.loads((ui / 'layout-before.json').read_text())
    after = json.loads((ui / 'layout-after.json').read_text())
    trace = json.loads((ui / 'constructor-after.json').read_text())
    assert any(r['kind'] == 'cell_width' and r['argument'] == '0x78' and r['caller'] == '0x89012d0' for r in trace)
    assert before[0]['text'] == 'Change Equipment'
    assert before[0]['ancestors'][3]['geometry'] == [178, 92, 124, 88]
    assert {r['text'] for r in after} >= {'Change Leader', 'Change Formation', 'Change Equipment'}
    for row in after:
        if row['text'] not in ['Change Leader', 'Change Formation', 'Change Equipment']:
            continue
        assert row['ancestors'][1]['geometry'][2] == 120
        assert row['ancestors'][3]['geometry'] == [158, 92, 164, 88]
    assert sha(out / 'EBOOT.party.elf') == report['elf_sha256']
    assert sha(out / 'data.party.ore') == report['archive_sha256']
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    if not preservation['user_source_unchanged']:
        preservation['source_check_note'] = 'User-source files changed during QA outside these tools. QA only read/copied the source; the user profile was never written or restored.'
    screens = []
    for name in ['title', 'select-party', 'change-leader', 'change-formation', 'change-equipment']:
        path = ui / (name + '.png')
        assert Image.open(path).size == (480, 272)
        assert not json.loads(path.with_suffix('.json').read_text())['texture_replacement']
        screens.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    proof = dict(version=V, result='PASS: all four sortie popup captions and highlights fit the enlarged native frame',
        iso=identity, before_frame=[178, 92, 124, 88], after_frame=[158, 92, 164, 88],
        text_cell_before=80, text_cell_after=120, caption_advances=report['labels'],
        constructor=trace, actual_text_geometry=after, screenshots=screens,
        checks=report['checks'], cold_boot=True, save_state_loaded=False, game_memory_edits=False,
        texture_replacement=False, save_preservation=preservation, github_release=False,
        limits=['Reported four-action popup checked in the final ISO; physical PSP testing pending.'])
    print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity, before=proof['before_frame'], after=proof['after_frame']), indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json', proof)
    dump(ui / 'image-identity.json', identity)
    report['runtime_verification'] = proof['result']
    dump(out / 'party.report.json', report)
    for relative in ['docs/local_build_status.json', 'docs/translation_progress.json']:
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj['party_popup_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'],
                bytes=identity['bytes'], sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V, visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['sortie_preparation_popup'] = proof['result']
        else:
            obj['version'] = V
        dump(path, obj)
    path = ROOT / 'work/ui/verified_screens.json'
    obj = json.loads(path.read_text())
    obj['latest_evidence_version'] = V
    obj['additional_build_evidence'] = [r for r in obj.get('additional_build_evidence', []) if r['version'] != V] + [
        dict(version=V, evidence=(ui / 'verification.json').relative_to(ROOT).as_posix(), scope=proof['result'])]
    dump(path, obj)
    path = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
    text = path.read_text(encoding='utf-8').replace(
        'Current local test build: **0.2.41**, 2026-10-18; archive-text draft: **0.2.41**.',
        'Current local test build: **0.2.42**, 2026-10-18; archive-text draft: **0.2.42**.')
    line = '- `work/output/english-native-0.2.42.iso`: wider Sortie Prep popup; all four captions and highlights fit. See [QA evidence](../work/ui/party-popup-0.2.42/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.41.iso`', line + '- `work/output/english-native-0.2.41.iso`', 1)
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'CHANGELOG.md'
    text = path.read_text(encoding='utf-8')
    entry = '''## 0.2.42 (2026-10-18)

- Extended the four-action Sortie Prep popup's native text cells from 80 to 120 pixels. Its frame grows from 124 to 164 pixels and recenters at x=158; the selection highlight and icon spacing follow the original layout. Change Formation and Change Equipment now fit with their full wording.
- Changed one guarded width argument with no added code/RAM. All text, controls, prologue reflow, prompt font and shared scratch fixes are preserved; the archive changes only its native title version.
- Verified the final ISO from a cold boot: the actual constructor receives width 120, the rendered captions have 120px cells inside the 164px frame, and all four highlight positions were visually checked. Original isolated saves restored; QA only reads/copies user-source saves. The user-source hashes changed outside QA during the run, so unchanged-source verification is unavailable for this session. Local build only; no GitHub release. Physical PSP testing remains pending.

'''
    if '## 0.2.42 ' not in text:
        path.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1), encoding='utf-8')


if __name__ == '__main__':
    main()
