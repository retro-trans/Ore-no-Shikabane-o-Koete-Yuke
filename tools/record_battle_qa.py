"""Package battle HUD translations and accurately record available QA. Dry run first."""
import argparse,json,shutil
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
VERSION='0.2.25';UI=ROOT/'work/ui/battle-hud-0.2.25';OUT=ROOT/'work/output/english-native-0.2.25-c'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    report=json.loads((OUT/'battle.report.json').read_text())
    assert sha(OUT/'EBOOT.battle.elf')==report['elf_sha256'] and sha(OUT/'data.battle.ore')==report['archive_sha256']
    tests=(ROOT/'work/source/test-battle-names-0.2.25.txt').read_text();assert '13 full native text-setter cases' in tests and tests.startswith('PASS:')
    before=json.loads((UI/'save-before.json').read_text());savepath=ROOT/'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117';current={p.name:sha(p) for p in savepath.iterdir() if p.is_file()};assert before==current
    screens=[]
    for name in ('title-menu-c.png','current-c.png','battle-after.png'):
        p=UI/name
        if p.exists():
            assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
            screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    assert len(screens)>=2
    native=UI/'font-battle.json';complete=native.exists() and (UI/'battle-after.png').exists()
    if complete:
        font=json.loads(native.read_text());assert font['result']=='PASS' and set(font['required'])=={'Genta','Orin'}
    qa='PASS: translated battle panel and both native 4x parent names' if complete else 'PARTIAL: title/prologue boot and native MIPS name conversion pass; combat transition halts at PC 0 in isolated testing, also observed on base 0.2.24; battle visual check pending'
    candidate=ROOT/'work/source/qa-battle-0.2.25c.iso';final=ROOT/'work/output/english-native-0.2.25.iso'
    identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=candidate.stat().st_size,sha256=sha(candidate))
    print(json.dumps(dict(write=a.write,iso=identity,translations=['HP','MP','Genta','Orin'],qa=qa,screens=len(screens),save_files='unchanged'),indent=2))
    if not a.write:return
    if not final.exists():shutil.copyfile(candidate,final)
    assert sha(final)==identity['sha256'] and final.stat().st_size==identity['bytes'];shutil.copyfile(candidate.with_suffix('.manifest.json'),final.with_suffix('.manifest.json'))
    dump(UI/'image-identity.json',identity);dump(UI/'save-preservation.json',dict(result='PASS',files=current))
    metrics=json.loads((ROOT/'work/ui/vwf_metrics.json').read_text())['glyphs']
    names=[dict(translation_en=t,full_advance_at_size_16=sum(metrics[str(ord(c))]['advance'] for c in t)*16/14) for t in ('Genta','Orin')]
    dump(UI/'layout.json',dict(version=VERSION,native_resolution=[480,272],stat_badge_native_size=[32,16],stat_badge_sample_rectangle=[0,0,24,16],parent_display_names=names,name_matching=report['names'],portrait_art_and_hud_coordinates='unchanged',source_records='unchanged',scripts='byte-identical'))
    dump(UI/'verification.json',dict(version=VERSION,result=qa,screens=screens,mips=tests.strip(),native_font_evidence='font-battle.json' if complete else None,checks=report['checks'],texture_replacement=False,save_files='unchanged',github_release=False,limits=([] if complete else ['Battle panel has not yet been visually verified in this isolated test run'])+['Full-playthrough and physical PSP tests remain pending']))
    report['runtime_verification']=qa;dump(OUT/'battle.report.json',report)
    dump(ROOT/'work/translation/en/graphics/battle_hud.en.json',dict(version=VERSION,status='Draft; compact native battle badges',rows=report['graphics']))
    dump(ROOT/'work/translation/en/character/parent_display_names.en.json',dict(version=VERSION,status='Draft; MIPS text-setter behavior verified',rows=[dict(translation_en=t,file='EBOOT:parent_display_alias',context='Exact canonical parent display name; underlying character/save record retained',fit_status='runtime_verified' if complete else 'pending_battle_visual_check') for t in ('Genta','Orin')]))
    p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text(encoding='utf-8'));q['latest_evidence_version']=VERSION
    q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/battle-hud-0.2.25/verification.json',scope=qa+'; core fit count unchanged')];dump(p,q)
    p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=VERSION,archive_translation_version=VERSION,build_date='2026-10-18',file=identity['delivered_iso'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=41,additional_character_native_literals=9,battle_hud_evidence='work/ui/battle-hud-0.2.25/verification.json')
    q['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/battle-hud-0.2.25/title-menu-c.png');q['checks']['battle_hud']=qa;dump(p,q)
    p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.25 (2026-10-18)

- Translated the compact battle stat icons to HP and MP, inside their original 24-by-16-pixel sampled regions. Portrait artwork, gauges, values and HUD coordinates remain unchanged.
- Added exact display aliases for Genta and Orin after text formatting and before native line construction. The text setter borrows the English strings; character records, saved names and source buffers are unchanged. Other names, prefixes and sentences retain their original handling.
- Verified 13 MIPS trampoline cases and 13 complete native text-setter cases, including correct child-line strings/counts, null/empty inputs, nonmatching names, source-buffer identity, stack and saved registers. The title/prologue boot with the native 4x font. Scripts and unrelated archive members match 0.2.24; the exclamation-spacing fix is retained.
- Battle visual QA: '''+qa+'''. Evidence: work/ui/battle-hud-0.2.25/. Saves unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

'''
    if '## 0.2.25 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
    p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');s=s.replace('**0.2.24**, 2026-10-18; archive-text draft: **0.2.24**.','**0.2.25**, 2026-10-18; archive-text draft: **0.2.25**.').replace('thirty-nine native graphic assets/label groups','forty-one native graphic assets/label groups')
    line='- `work/output/english-native-0.2.25.iso`: English battle HP/MP badges and Genta/Orin display aliases. See [QA evidence](work/ui/battle-hud-0.2.25/verification.json).\n'
    if line not in s:s=s.replace('- `work/output/english-native-0.2.24.iso`',line+'- `work/output/english-native-0.2.24.iso`',1)
    p.write_text(s,encoding='utf-8')
    (ROOT/'docs/battle-hud.txt').write_text('Battle HUD translation — local build 0.2.25\n\nCompact battle badges 11.ppt and 12.ppt (common archive entries13/24)\nread HP and MP. Their original32x16 textures and24x16 sample regions\nare retained. The two parent names use exact aliases in the borrowed-text\nsetter at0x0882B544, after formatting and before lines are constructed.\nOnly the exact terminated canonical name matches; longer strings and\nother characters remain unchanged. Source/save records are never rewritten.\n\n'+tests+'\nQA: '+qa+'\nThe final ISO matches the tested candidate. All script payloads and\nunrelated assets match0.2.24; the earlier punctuation fix remains.\nEvidence: work/ui/battle-hud-0.2.25/. No GitHub release.\n',encoding='utf-8')

if __name__=='__main__':main()
