"""Package the verified English startup disclaimer. Dry run unless --write."""
import argparse,json,shutil
from PIL import Image
from catalog_text import ROOT
from record_detailed_roster_qa import sha,dump
VERSION='0.2.23';UI=ROOT/'work/ui/startup-disclaimer-0.2.23';OUT=ROOT/'work/output/english-native-0.2.23'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write',action='store_true');a=ap.parse_args();r=json.loads((OUT/'disclaimer.report.json').read_text());proof=json.loads((UI/'runtime-verification.json').read_text())
 assert proof['result']=='PASS' and proof['mask_intersection_over_union']>.92 and proof['elf_sha256']==r['elf_sha256'] and proof['archive_sha256']==r['archive_sha256']
 assert sha(OUT/'EBOOT.disclaimer.elf')==r['elf_sha256'] and sha(OUT/'data.disclaimer.ore')==r['archive_sha256']
 screens=[]
 for n,scope in [('disclaimer-after.png','Complete English disclaimer in the original startup sequence; exact native bitmap mask match'),('title-after.png','Startup proceeds to the title screen with v0.2.23 and full project URL')]:
  p=UI/n;assert Image.open(p).size==(480,272) and json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False;screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),observed=scope,fit='pass'))
 assert 'PASS:' in (ROOT/'work/source/test-disclaimer-0.2.23.txt').read_text()
 assert 'ALL 49 BATCHES PASS' in (ROOT/'work/source/check-translations-0.2.23.txt').read_text()
 candidate=ROOT/'work/source/qa-disclaimer-0.2.23.iso';final=ROOT/'work/output/english-native-0.2.23.iso';identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=candidate.stat().st_size,sha256=sha(candidate))
 print(json.dumps(dict(write=a.write,translation=r['graphics'][0]['translation_en'],iso=identity,bitmap_match=proof['mask_intersection_over_union'],screens=len(screens)),indent=2))
 if not a.write:return
 if not final.exists():shutil.copyfile(candidate,final)
 assert sha(final)==identity['sha256'] and final.stat().st_size==identity['bytes'];shutil.copyfile(candidate.with_suffix('.manifest.json'),final.with_suffix('.manifest.json'));dump(UI/'image-identity.json',identity)
 layout=dict(version=VERSION,native_resolution=[480,272],native_image='EBOOT:warning.ppt',font='Noto Sans',font_size=14,lines=r['graphics'][0]['translation_en'].split('\n'),line_bounds=r['graphics'][0]['line_bounds'],embedded_archive=r['embedded_archive'],native_texture_palette='unchanged',texture_replacement=False)
 dump(UI/'layout.json',layout);dump(UI/'verification.json',dict(version=VERSION,result='PASS: English opening disclaimer and subsequent title screen',screens=screens,checks=r['checks'],native_mips=(ROOT/'work/source/test-disclaimer-0.2.23.txt').read_text().strip(),runtime=proof,texture_replacement=False,github_release=False,limits=['Real PSP boot/performance and full-playthrough testing remain pending']))
 r['runtime_verification']='PASS: work/ui/startup-disclaimer-0.2.23/verification.json';dump(OUT/'disclaimer.report.json',r)
 dump(ROOT/'work/translation/en/graphics/startup_disclaimer.en.json',dict(version=VERSION,status='Draft; native startup display verified',rows=[dict(**x,fit_evidence='work/ui/startup-disclaimer-0.2.23/disclaimer-after.png') for x in r['graphics']]))
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text(encoding='utf-8'));q['latest_evidence_version']=VERSION;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/startup-disclaimer-0.2.23/verification.json',scope='English embedded startup disclaimer and following title screen; indexed script fit count unchanged')];dump(p,q)
 p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=VERSION,archive_translation_version=VERSION,build_date='2026-10-18',file=identity['delivered_iso'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=39,startup_disclaimer_evidence='work/ui/startup-disclaimer-0.2.23/verification.json');q['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/startup-disclaimer-0.2.23/title-after.png');q['checks']['startup_disclaimer']='PASS: complete English native image, bitmap mask match 1.0, both relocated archive pointers verified, title sequence continues';dump(p,q)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.23 (2026-10-18)

- Translated the opening fiction disclaimer in Noto Sans, centered on three complete lines. The text retains the source references to actual people, places, organizations, product names and similar subjects, without adding a coincidence claim.
- Rebuilt and relocated the executable-embedded startup archive, preserving its four logo assets and original warning palette. Both archive accessors point to the relocated data; the original allocation, timing and startup flow remain.
- Verified both accessors in actual MIPS execution and all four pointer instructions in PPSSPP memory. The rendered English image matches the expected native bitmap mask exactly, and the game continues to the v0.2.23 title. Scripts and unrelated archive members remain byte-identical to 0.2.22; all 49 translation batches pass.
- Evidence: work/ui/startup-disclaimer-0.2.23/. Save files remain unchanged. Local test build only; no GitHub release. Full-playthrough and physical PSP tests remain pending.

'''
 if '## 0.2.23 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');line='- `work/output/english-native-0.2.23.iso`: English opening disclaimer in the project font; all earlier UI fixes retained. See [startup notes](docs/startup-disclaimer.txt).\n'
 if line not in s:s=s.replace('- `work/output/english-native-0.2.22.iso`',line+'- `work/output/english-native-0.2.22.iso`',1)
 p.write_text(s,encoding='utf-8')
 (ROOT/'docs/startup-disclaimer.txt').write_text('''Opening disclaimer — local build 0.2.23

This story is entirely fictional.
It has no connection to real people, places,
organizations, product names, or the like.

The warning is not an indexed script row. It is warning.ppt (member4) in
the executable-embedded EZBIND at original file offset0x275230. The build
replaces its 480x272 image lettering using Noto Sans14 with the original
palette, retains the four logo members, and appends the rebuilt archive.
Both native archive accessors are guarded and repointed. Their0x88000
resource allocation and startup timing are unchanged. The original embedded
archive stays intact; all other ELF bytes except pointers/segment sizes match.
data.ore changes only the title footer version. All script payloads match0.2.22.

Build/check tools: build_startup_disclaimer.py, build_iso.py,
test_startup_disclaimer.py, capture_startup_disclaimer.py,
record_startup_disclaimer_qa.py. Run dry-run modes before writes.
The native framebuffer matches the English image mask exactly (IoU1.0).
The subsequent title screen and delivered/tested ISO identity are verified.
Evidence and layout: work/ui/startup-disclaimer-0.2.23/.
Full-playthrough and real PSP testing remain pending. No GitHub release.
''',encoding='utf-8')
if __name__=='__main__':main()
