"""Verify live tournament literal and recorded final-build text/fonts. Dry run first."""
import argparse
import base64
import json

from catalog_text import ROOT
from build_vwf import IMAGE
from build_tournament_help import HELP_ID
from ppsspp_debug import Session

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--execute',action='store_true')
args = ap.parse_args()
if not args.execute:
    print('DRY RUN: read final-build text traces, font choices, two live instructions and Emperor literal; save runtime.json. No guest memory writes.')
    raise SystemExit
ui = ROOT / 'work/ui/tournament-help-0.2.48'
report = json.loads((ROOT / 'work/output/english-native-0.2.48/tournament.report.json').read_text())
prompt = json.loads((ROOT / 'work/output/english-native-0.2.39/prompt.report.json').read_text())
circle_image = hex(prompt['pages']['0x25cb']['image'])
main_image = hex(IMAGE)
def rows(name):
    return json.loads((ui / name).read_text())
help_rows,rules_rows,bracket_rows = rows('help-tree.json'),rows('rules-tree.json'),rows('bracket-tree.json')
expected_help = report['edits'][HELP_ID]['after'].split('\n')
help_by_text = {r['text']:r for r in help_rows}
for text in expected_help:
    assert text in help_by_text,text
    assert help_by_text[text]['font_image'] == (circle_image if '\u25cb' in text else main_image)
rules = ['- Items may not be used during matches.','- Retreat changes to Surrender.']
for text in rules+['Emperor']:
    row = next(r for r in rules_rows if r['text'] == text)
    assert row['font_image'] == main_image
footer = next(r for r in bracket_rows if r['text'] == 'Press \u25cb to begin the match.')
assert footer['font_image'] == circle_image
team_names = {r['text'] for r in report['team_fit']}
observed = sorted({r['text'].strip() for r in bracket_rows if r['text'].strip() in team_names})
assert len(observed) >= 12,observed
for row in bracket_rows:
    if row['text'].strip() in team_names:
        assert row['font_image'] == main_image
patches = []
with Session() as s:
    assert not s.call('cpu.status')['stepping']
    s.call('cpu.stepping')
    try:
        for patch in report['literal']['patches']:
            pc = int(patch['address'],16)
            actual = s.call('memory.disasm',address=pc,count=1,displaySymbols=False)['lines'][0]['encoding']
            assert actual == int(patch['after'],16)
            patches.append(dict(address=hex(pc),word=hex(actual)))
        raw = base64.b64decode(s.call('memory.read',address=int(report['literal']['address'],16),size=8)['base64'])
        assert raw == b'Emperor\0'
    finally:
        s.call('cpu.resume')
proof = dict(version='0.2.48',result='PASS',help_lines=expected_help,
    help_font='Native HD ASCII/Circle pages; no fallback',rules=rules,
    speaker='Emperor',rules_font=main_image,bracket_footer=footer['text'],footer_font=circle_image,
    observed_fixed_teams=observed,all_fixed_teams_measured=len(report['team_fit']),
    native_literal_patches=patches,literal_bytes=raw.hex(),
    guest_memory_writes=False,save_state_loaded=False,texture_replacement=False)
(ui / 'runtime.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof,indent=2))
