"""Record final Help/tournament fixes and local build state. Dry run first."""
import argparse
import json

from PIL import Image
from catalog_text import ROOT
from build_tournament_help import HELP_ID
from record_prologue_wrap_qa import sha, dump
from strip_jp import export

V = '0.2.48'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write',action='store_true')
    args = ap.parse_args()
    ui = ROOT / ('work/ui/tournament-help-'+V)
    out = ROOT / ('work/output/english-native-'+V)
    report = json.loads((out / 'tournament.report.json').read_text())
    runtime = json.loads((ui / 'runtime.json').read_text())
    preservation = json.loads((ui / 'save-preservation.json').read_text())
    assert runtime['result'] == 'PASS'
    assert preservation['result'] == 'PASS' and not preservation['user_source_written']
    assert preservation['original_project_hashes'] == preservation['restored_project_hashes']
    assert sha(out / 'EBOOT.tournament.elf') == report['elf_sha256']
    assert sha(out / 'data.tournament.ore') == report['archive_sha256']
    screens = []
    for name in ['title.png','help.png','rules.png','bracket.png']:
        p = ui / name
        assert Image.open(p).size == (480,272)
        screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    iso = ROOT / ('work/output/english-native-'+V+'.iso')
    identity = dict(version=V,file=iso.relative_to(ROOT).as_posix(),bytes=iso.stat().st_size,sha256=sha(iso))
    result = 'PASS: Help reflow, HD rule bullets, Emperor speaker label, sampled 16-team bracket and HD Circle prompt verified'
    proof = dict(version=V,result=result,iso=identity,runtime=runtime,screenshots=screens,
        checks=report['checks'],team_fit=report['team_fit'],team_aliases=report['team_aliases'],
        save_preservation=preservation,save_state_loaded=False,texture_replacement=False,
        gameplay_memory_writes=False,tournament_match_started=False,github_release=False,
        limits=['All 33 fixed team names measured; one natural draw containing 15 fixed teams and Karasuma Clan visually checked.',
            'Other draws, extreme player-clan letter widths, other tournament rounds, and physical PSP not tested.',
            'The existing 0.2.39 Circle font fix and 0.2.45 Help width are inherited; no new font code added.'])
    print(json.dumps(dict(write=args.write,result=result,iso=identity),indent=2))
    if not args.write:
        return
    dump(ui / 'verification.json',proof)
    dump(ui / 'image-identity.json',identity)
    report['runtime_verification'] = result
    dump(out / 'tournament.report.json',report)
    observed = set(runtime['observed_fixed_teams'])
    for name in ['ui_batch_008','ui_batch_014']:
        path = ROOT / ('work/translation/en/'+name+'.json')
        batch = json.loads(path.read_text(encoding='utf-8'))
        for row in batch['rows']:
            if row['id'] == HELP_ID or (row['file'] == 'eMltGozen.mlb' and row['section'] == 0 and row['index'] == 43):
                row['fit_status'] = 'verified_in_game_'+V
            elif row['file'] == 'eMltGozen.mlb' and row['section'] == 5 and row['index'] > 0:
                row['fit_status'] = ('verified_bracket_' if row['translation_en'] in observed else 'measured_bracket_')+V
        path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        path.with_suffix('.en.json').write_text(json.dumps(export(path),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for relative in ['docs/local_build_status.json','docs/translation_progress.json']:
        p = ROOT / relative
        obj = json.loads(p.read_text())
        obj['tournament_help_evidence'] = (ui / 'verification.json').relative_to(ROOT).as_posix()
        if 'latest_local_build' in obj:
            obj.update(latest_local_build=V,archive_translation_version=V,file=identity['file'],bytes=identity['bytes'],sha256=identity['sha256'])
            obj['title_branding'].update(version='v'+V,visual_evidence=(ui / 'title.png').relative_to(ROOT).as_posix())
            obj['checks']['public_help_and_tournament_reports'] = result
        else:
            obj['version'] = V
        dump(p,obj)
    p = ROOT / 'work/ui/verified_screens.json'
    obj = json.loads(p.read_text())
    obj['latest_layout_candidate_version'] = V
    obj['additional_build_evidence'] = [r for r in obj.get('additional_build_evidence',[]) if r['version'] != V]+[
        dict(version=V,evidence=(ui / 'verification.json').relative_to(ROOT).as_posix(),scope=result)]
    dump(p,obj)
    p = ROOT / 'docs/LOCAL_DEVELOPMENT.md'
    text = p.read_text(encoding='utf-8').replace('**0.2.47**, 2026-10-18; archive-text draft: **0.2.47**.','**0.2.48**, 2026-10-18; archive-text draft: **0.2.48**.')
    line = '- `work/output/english-native-0.2.48.iso`: full-word Help reflow, readable tournament rules, Emperor speaker label and compact tournament team names. All reported contexts checked in-game; see [evidence and limits](../work/ui/tournament-help-0.2.48/verification.json).\n'
    if line not in text:
        text = text.replace('- `work/output/english-native-0.2.47.iso`',line+'- `work/output/english-native-0.2.47.iso`',1)
    p.write_text(text,encoding='utf-8')
    p = ROOT / 'CHANGELOG.md'
    text = p.read_text(encoding='utf-8')
    entry = '''## 0.2.48 (2026-10-18)

- Rewrapped the reported Changing Clan Heads Help passage into six fitting lines while retaining every word, punctuation and both placeholder circles. Reuses the wider 0.2.45 Help panel and the 0.2.39 Circle font fix; all six lines checked on the native HD font pages.
- Replaced the tournament rules' two Japanese list markers with ASCII hyphen bullets so their English text stays on the native HD font. Translated the hardcoded speaker label to Emperor with an 8-byte literal and two guarded pointer arguments; its name box sizes correctly. No new code or font data added.
- Shortened 27 over-budget tournament team names consistently, with full/display-name mappings in work/glossary/tournament-team-display.en.json. Six fixed names already fit and remain unchanged. All 33 fixed names measure within 112px at 12px. One natural 16-team draw, including Karasuma Clan and 15 fixed teams, fits on-screen; the Circle match prompt also uses the inherited HD font fix.
- Cold-started the final local ISO and verified the exact Help page, tournament rules/speaker and bracket. Live font choices, literal bytes and pointer instructions verified; unchanged rows, controls and other archive payloads checked. Original project saves restored, user saves read/copied only; no tournament match started. Local build only; no GitHub release. Other draws, extreme player-clan letter widths, later rounds and physical PSP remain untested.

'''
    if '## 0.2.48 ' not in text:
        p.write_text(text.replace('# Changelog\n\n','# Changelog\n\n'+entry,1),encoding='utf-8')
    (ROOT / 'docs/tournament-help-layout.txt').write_text(
        'Public screenshot fixes, local build 0.2.48\n\n'
        'Help: ore:0000c000:0019:01:0214; six reflowed lines, longest 276.857px in the existing 330px area.\n'
        'Rules: eMltGozen.mlb section 0 index 43; ASCII hyphen bullets avoid U+30FB whole-run font fallback.\n'
        'Speaker: native literal 0x08a3e20c reference replaced at 0x08914a84/0x08914a8c; appended Emperor at 0x09cfcd40.\n'
        'No added code; English literal adds eight bytes to the existing asset segment. Native name box auto-sizing retained.\n'
        'Teams: eMltGozen.mlb section 5 indexes 1..33; 27 concise names, six unchanged. 112px advance budget at 12px.\n'
        'Names remain consistent in bracket and match announcements. Full/display mappings: work/glossary/tournament-team-display.en.json.\n'
        'Inherited Circle/Triangle pages and ASCII rasters remain unchanged.\n'
        'Runtime evidence: work/ui/tournament-help-0.2.48/verification.json\n'
        'Tools: build_tournament_help.py, verify_tournament_help.py, record_tournament_help_qa.py (dry run first).\n',encoding='utf-8')


if __name__ == '__main__':
    main()
