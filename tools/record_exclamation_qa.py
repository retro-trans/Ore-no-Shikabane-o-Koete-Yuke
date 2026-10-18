"""Verify the reported dialogue spacing and package the tested ISO; dry run first."""
import argparse, json, shutil
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha, dump

VERSION='0.2.24'
UI=ROOT/'work/ui/punctuation-0.2.24'
OUT=ROOT/'work/output/english-native-0.2.24'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args()
    report=json.loads((OUT/'spacing.report.json').read_text())
    before=json.loads((UI/'runtime-before.json').read_text());after=json.loads((UI/'runtime-after.json').read_text())
    assert before['result']==after['result']=='PASS'
    assert before['instruction']['encoding']==0x24020021
    assert after['instruction']['encoding']==0x2402FFFF
    comparisons=[]
    for old,new in zip(before['objects'],after['objects']):
        assert old['text']==new['text'] and old['atlas']==new['atlas']=='0x9b5c010'
        assert len(old['glyphs'])==len(new['glyphs'])
        shifts=[]
        for b,c in zip(old['glyphs'],new['glyphs']):
            assert b['code']==c['code'] and b['advance']==c['advance'] and b['uv']==c['uv']
            if b['code']==33:
                dx=[b['quad'][i]-c['quad'][i] for i in (0,2)]
                assert all(d in (11,12) for d in dx),dx
                assert b['quad'][1::2]==c['quad'][1::2]
                shifts.append(dict(before=b['quad'],after=c['quad'],left_shift_native_pixels=dx[0]/4))
            else: assert b['quad']==c['quad']
        assert len(shifts)==2
        comparisons.append(dict(text=old['text'],exclamation_positions=shifts,other_glyphs='identical',atlas='native 4x'))
    assert 'PASS: 65,536' in (ROOT/'work/source/test-punctuation-0.2.24.txt').read_text()
    assert sha(OUT/'EBOOT.spacing.elf')==report['elf_sha256']
    assert sha(OUT/'data.spacing.ore')==report['archive_sha256']
    screenshots=[]
    for name in ('dialogue-before.png','dialogue-after.png','title-after.png'):
        p=UI/name;assert Image.open(p).size==(480,272)
        assert json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False
        screenshots.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    saved=json.loads((UI/'save-before.json').read_text())
    savepath=ROOT/'work/source/emulator/memstick/PSP/SAVEDATA/UCJS10117'
    current={p.name:sha(p) for p in savepath.iterdir() if p.is_file()};assert saved==current
    candidate=ROOT/'work/source/qa-punctuation-0.2.24.iso';final=ROOT/'work/output/english-native-0.2.24.iso'
    identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=candidate.stat().st_size,sha256=sha(candidate))
    print(json.dumps(dict(write=a.write,iso=identity,comparisons=comparisons,save_files='unchanged'),indent=2))
    if not a.write:return
    if not final.exists():shutil.copyfile(candidate,final)
    assert sha(final)==identity['sha256'] and final.stat().st_size==identity['bytes']
    shutil.copyfile(candidate.with_suffix('.manifest.json'),final.with_suffix('.manifest.json'))
    dump(UI/'image-identity.json',identity)
    dump(UI/'save-preservation.json',dict(result='PASS',files=current))
    dump(UI/'layout.json',dict(version=VERSION,scope='ASCII exclamation glyph positioning',helper='0x089BB234',patch=report['patch'],original_offset=14,new_offset=0,offset_units='quarter units before native text scaling',native_resolution=[480,272],comparisons=comparisons,script_row='ore:06f76800:0000:00:0003',text_and_line_breaks='unchanged',question_marks_and_fullwidth_punctuation='unchanged'))
    dump(UI/'verification.json',dict(version=VERSION,result='PASS',scope='Reported Orin dialogue in the prologue, original and final builds',screenshots=screenshots,comparisons=comparisons,mips_cases=65536,checks=report['checks'],save_files='unchanged',texture_replacement=False,memory_writes=False,github_release=False,limits=['Full playthrough and physical PSP testing remain pending']))
    report['runtime_verification']='PASS: work/ui/punctuation-0.2.24/verification.json';dump(OUT/'spacing.report.json',report)
    p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text(encoding='utf-8'));q['latest_evidence_version']=VERSION
    q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/punctuation-0.2.24/verification.json',scope='ASCII exclamation marks closer to preceding letters; exact Orin passage before/after; existing core fit count unchanged')];dump(p,q)
    p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=VERSION,archive_translation_version=VERSION,build_date='2026-10-18',file=identity['delivered_iso'],bytes=identity['bytes'],sha256=identity['sha256'],punctuation_spacing_evidence='work/ui/punctuation-0.2.24/verification.json')
    q['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/punctuation-0.2.24/title-after.png')
    q['checks']['ascii_exclamation_spacing']='PASS: removed native 14-unit offset only for ASCII !; 65,536 MIPS comparisons and exact Orin passage before/after; native 4x atlas and advances retained';dump(p,q)
    p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8')
    entry='''## 0.2.24 (2026-10-18)

- Moved English exclamation marks closer to the preceding text by removing the original renderer's special 14-quarter-unit horizontal offset for ASCII `!`. Both marks in `!!` move together. Text, line breaks, font artwork and character advances remain unchanged.
- Verified the exact reported Orin passage ("Tch!! / Not even time to catch our breath!!") before and after in PPSSPP. Each exclamation moves left by about 2.75 native pixels at this text size; every other glyph position and all native 4x font UVs match.
- Compared all 65,536 UTF-16 values through the actual original and patched MIPS helper. Only ASCII `!` changes; question marks, fullwidth punctuation, null behavior, stack and saved registers are preserved. Scripts and unrelated archive payloads remain byte-identical to 0.2.23.
- Updated title footer to v0.2.24. Evidence: work/ui/punctuation-0.2.24/. Saves unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

'''
    if '## 0.2.24 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
    p.write_text(s,encoding='utf-8')
    p=ROOT/'README.md';s=p.read_text(encoding='utf-8')
    s=s.replace('Current local test build: **0.2.20**, 2026-10-17; archive-text draft: **0.2.20**.','Current local test build: **0.2.24**, 2026-10-18; archive-text draft: **0.2.24**.')
    s=s.replace('thirty-four native graphic assets/label groups','thirty-nine native graphic assets/label groups')
    line='- `work/output/english-native-0.2.24.iso`: tighter English exclamation spacing, verified in the reported Orin dialogue; all earlier fixes retained.\n'
    if line not in s:s=s.replace('- `work/output/english-native-0.2.23.iso`',line+'- `work/output/english-native-0.2.23.iso`',1)
    p.write_text(s,encoding='utf-8')
    (ROOT/'docs/punctuation-spacing.txt').write_text('''English exclamation spacing — local build 0.2.24

The reported translation already contains no space before the exclamation.
The native helper at 0x089BB234 adds 14 quarter units to the glyph origin
for !, ?, and their fullwidth equivalents. One guarded instruction at
0x089BB24C disables only the ASCII ! comparison using an impossible -1
sentinel. The existing zero-extended UTF-16 comparison and all other cases
retain their original behavior. Both marks in !! move left together;
character advances, atlas and measured line widths are unchanged. Native
coordinate rounding yields a 2.75 to 3 pixel shift at the reported text size.

Before/after captures and native draw descriptors of the exact reported
Orin passage are in work/ui/punctuation-0.2.24/. The final build uses its
embedded native 4x font. Each ! moves about 2.75 native pixels left here.
All other glyph positions and all UVs match. The renderer helper passes
65,536 actual MIPS original/patched comparisons, including caller state.
Scripts and unrelated archive payloads match 0.2.23; only the title footer
version changes in data.ore. Original saves are hash-identical.

Tools: build_exclamation_spacing.py, test_exclamation_spacing.py,
check_exclamation_runtime.py, record_exclamation_qa.py. Dry run before writes.
The delivered ISO is identical to the tested candidate. No GitHub release.
Full-playthrough and physical PSP testing remain pending.
''',encoding='utf-8')

if __name__=='__main__':main()
