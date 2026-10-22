"""Record investment ribbon/currency QA. Dry run before --write."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from build_investment_ui import V
from record_prologue_wrap_qa import sha, dump


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/investment-' + V)
    out = ROOT / ('work/output/english-native-' + V)
    report = json.loads((out / 'investment.report.json').read_text())
    ribbon = json.loads((ui / 'runtime-ribbon.json').read_text())
    currency = json.loads((ui / 'runtime-currency.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert ribbon['result'] == 'PASS' and ribbon['required'] == 'INVESTMENT'
    assert ribbon['elf_sha256'] == report['elf_sha256'] == sha(out / 'EBOOT.investment.elf')
    assert ribbon['archive_sha256'] == report['archive_sha256'] == sha(out / 'data.investment.ore')
    assert any(x['text'] == 'ryo' for x in currency)
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    screens = []
    for name in ['title', 'investment-menu', 'amount-zero', 'amount-one']:
        path = ui / (name + '.png')
        assert Image.open(path).size == (480, 272)
        assert not json.loads(path.with_suffix('.json').read_text())['texture_replacement']
        screens.append(dict(file=path.relative_to(ROOT).as_posix(), sha256=sha(path)))
    iso = ROOT / ('work/output/english-native-' + V + '.iso')
    identity = dict(version=V, file=iso.relative_to(ROOT).as_posix(), bytes=iso.stat().st_size, sha256=sha(iso))
    proof = dict(version=V, result='PASS: native INVESTMENT ribbon and ryo currency visible beside zero and nonzero input amounts',
        iso=identity, ribbon=ribbon, currency_text=currency, screenshots=screens,
        checks=report['checks'], cold_boot=True, save_state_loaded=False, game_memory_edits=False,
        texture_replacement=False, investment_confirmed=False, saves=preservation, github_release=False,
        limits=['Investment list and editable Public Works amount checked; physical PSP testing pending.'])
    print(json.dumps(dict(write=args.write, result=proof['result'], iso=identity,
        restored_project_saves=True, user_source_hashes_unchanged=preservation['user_source_unchanged']), indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json', proof)
    dump(ui / 'image-identity.json', identity)
    report['runtime_verification'] = proof['result']
    dump(out / 'investment.report.json', report)
    for relative in ['docs/local_build_status.json', 'docs/translation_progress.json']:
        path = ROOT / relative
        obj = json.loads(path.read_text())
        obj['investment_ui_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V, archive_translation_version=V, file=identity['file'],
                bytes=identity['bytes'], sha256=identity['sha256'], native_graphic_labels=71,
                additional_investment_native_literals=1)
            obj['title_branding'].update(version='v'+V, visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['investment_banner_and_currency'] = proof['result']
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
        'Current local test build: **0.2.42**, 2026-10-18; archive-text draft: **0.2.42**.',
        'Current local test build: **0.2.43**, 2026-10-18; archive-text draft: **0.2.43**.')
    text = text.replace('two Pack literals, and 70 native graphic assets/label groups',
        'two Pack literals, one investment currency literal, and 71 native graphic assets/label groups')
    line = '- `work/output/english-native-0.2.43.iso`: native INVESTMENT ribbon and ryo unit in the investment amount field. See [QA evidence](../work/ui/investment-0.2.43/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.42.iso`', line + '- `work/output/english-native-0.2.42.iso`', 1)
    path.write_text(text, encoding='utf-8')
    path = ROOT / 'CHANGELOG.md'
    text = path.read_text(encoding='utf-8')
    entry = '''## 0.2.43 (2026-10-18)

- Translated the left investment ribbon to INVESTMENT using the existing native English ribbon style. The T4 resource keeps its original 13,744-byte loader budget and logical geometry; texture replacement remains disabled.
- Changed the investment amount dialog's separate currency literal to ryo. Values, digit editing, category IDs, investment effects, dialogue and previous fixes remain unchanged. Only the guarded currency literal, one ribbon and title version change.
- Verified the final cold-boot ISO's exact ribbon palette/pixels/UVs and naturally rendered ryo text. Captured the investment list and zero/nonzero editable amounts; cancelled without investing. Restored the original isolated saves; QA never writes user-source saves. Local build only; no GitHub release. Physical PSP testing remains pending.

'''
    if '## 0.2.43 ' not in text:
        path.write_text(text.replace('# Changelog\n\n', '# Changelog\n\n' + entry, 1), encoding='utf-8')


if __name__ == '__main__':
    main()
