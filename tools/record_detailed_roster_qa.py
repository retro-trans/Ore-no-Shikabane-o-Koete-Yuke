"""Verify loaded roster tables and package selected UI evidence. Dry run unless --write."""
import argparse,base64,hashlib,json,shutil
from PIL import Image
from catalog_text import ROOT
from ppsspp_debug import Session
VERSION='0.2.22';UI=ROOT/'work/ui/detailed-roster-0.2.22';OUT=ROOT/'work/output/english-native-0.2.22'
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--runtime',action='store_true');ap.add_argument('--write',action='store_true');a=ap.parse_args();r=json.loads((OUT/'roster.report.json').read_text())
 if a.runtime:
  with Session() as s:
   assert s.call('game.status')['game']['id']=='UCJS10117' and not s.call('cpu.status')['stepping']
   for p in r['patches']:
    data=base64.b64decode(s.call('memory.read',address=int(p['address'],16),size=len(bytes.fromhex(p['after'])))['base64']);assert data.hex()==p['after'],p
   assert not s.call('cpu.breakpoint.list')['breakpoints']
  proof=dict(version=VERSION,iso='work/source/qa-roster-0.2.22b.iso',elf_sha256=r['elf_sha256'],archive_sha256=r['archive_sha256'],native_layout_tables_verified=4,game_memory_writes=False,save_record_writes=False)
  print(json.dumps(proof,indent=2))
  if a.write:dump(UI/'runtime-tables.json',proof)
  return
 proof=json.loads((UI/'runtime-tables.json').read_text());assert proof['elf_sha256']==r['elf_sha256'] and proof['archive_sha256']==r['archive_sha256']
 screens=[]
 for name,scope in [('stats-after.png','English HP, MP, LOY, HLTH, ATK, DEF and AGI; separate name and stat columns'),('equipment-after.png','Four full equipment names with separate English slot labels'),('equipment-second.png','Second character selection and four equipment rows'),('simple-after.png','Shared badge translation and existing portrait selector retained'),('title.png','Version 0.2.22 and full project URL')]:
  p=UI/name;assert Image.open(p).size==(480,272);assert json.loads(p.with_suffix('.json').read_text())['texture_replacement'] is False;screens.append(dict(file=p.relative_to(ROOT).as_posix(),sha256=sha(p),observed=scope,fit='pass'))
 assert json.loads((UI/'font-equipment.json').read_text())['result']=='PASS'
 assert 'ALL 49 BATCHES PASS' in (ROOT/'work/source/check-translations-0.2.22.txt').read_text()
 assert sha(OUT/'EBOOT.roster.elf')==r['elf_sha256'] and sha(OUT/'data.roster.ore')==r['archive_sha256']
 candidate=ROOT/'work/source/qa-roster-0.2.22b.iso';final=ROOT/'work/output/english-native-0.2.22.iso';identity=dict(version=VERSION,tested_iso=candidate.relative_to(ROOT).as_posix(),delivered_iso=final.relative_to(ROOT).as_posix(),bytes=candidate.stat().st_size,sha256=sha(candidate))
 print(json.dumps(dict(write=a.write,screens=len(screens),graphics=r['graphics'],iso=identity,layout=r['layout']),indent=2))
 if not a.write:return
 if not final.exists():shutil.copyfile(candidate,final)
 assert sha(final)==identity['sha256'] and final.stat().st_size==identity['bytes'];shutil.copyfile(candidate.with_suffix('.manifest.json'),final.with_suffix('.manifest.json'));dump(UI/'image-identity.json',identity);dump(UI/'layout.json',r['layout'])
 dump(UI/'verification.json',dict(version=VERSION,result='PASS: selected detailed roster status/equipment screens',screens=screens,layout=r['layout'],checks=r['checks'],native_font='Actual equipment name draws use the embedded 4x atlas and expected UVs',runtime_layout_tables_verified=4,texture_replacement=False,github_release=False,limits=['Selected initial two-character party; full-playthrough and real PSP testing remain pending']))
 r['runtime_verification']='PASS: work/ui/detailed-roster-0.2.22/verification.json';dump(OUT/'roster.report.json',r)
 dump(ROOT/'work/translation/en/graphics/detailed_roster.en.json',dict(version=VERSION,rows=[dict(**x,fit_evidence='work/ui/detailed-roster-0.2.22/stats-after.png') for x in r['graphics']]))
 dump(ROOT/'work/glossary/status_badges.json',dict(version=VERSION,scope='Compact native status badges; full names retain core glossary spelling',terms=[dict(jp='\u4f53\u529b',en='HP',full='Hit points'),dict(jp='\u5065\u5eb7',en='HLTH',full='Health'),dict(jp='\u5fe0\u5fc3',en='LOY',full='Loyalty')]))
 p=ROOT/'work/ui/verified_screens.json';q=json.loads(p.read_text(encoding='utf-8'));q['latest_evidence_version']=VERSION;q['additional_build_evidence']=[x for x in q.get('additional_build_evidence',[]) if x['version']!=VERSION]+[dict(version=VERSION,evidence='work/ui/detailed-roster-0.2.22/verification.json',scope='English HP/Loyalty/Health badges and separated detailed-roster equipment/status columns; core fit count unchanged')];dump(p,q)
 p=ROOT/'docs/local_build_status.json';q=json.loads(p.read_text());q.update(latest_local_build=VERSION,archive_translation_version=VERSION,build_date='2026-10-18',file=identity['delivered_iso'],bytes=identity['bytes'],sha256=identity['sha256'],native_graphic_labels=38,detailed_roster_evidence='work/ui/detailed-roster-0.2.22/verification.json');q['title_branding'].update(version='v'+VERSION,visual_evidence='work/ui/detailed-roster-0.2.22/title.png');q['checks']['detailed_roster']='PASS: English HP/LOY/HLTH badges; four separate full-name equipment rows; reorganized status columns; two characters selected in PPSSPP';dump(p,q)
 p=ROOT/'CHANGELOG.md';s=p.read_text(encoding='utf-8');entry='''## 0.2.22 (2026-10-18)

- Translated native HP, LOY (Loyalty), and HLTH (Health) badges. Retained the English MP, ATK/DEF/AGI, role and equipment-slot labels from earlier builds.
- Arranged detailed-roster equipment into four separate rows, with a 208-pixel name budget. All 463 fixed equipment names fit; item names remain unchanged. Moved status columns clear of longer character names.
- Verified four native coordinate tables and both characters in actual PPSSPP captures, plus equipment-name font atlas/UVs. All 49 translation batches pass. Native instructions, scripts and unrelated archive members remain unchanged from 0.2.21. The archive builder can now retain its finished buffer to avoid an extra large allocation on 32-bit Python.
- Evidence: work/ui/detailed-roster-0.2.22/. Original project-profile saves restored after QA. Local test build only; no GitHub release. Full-playthrough and real PSP checks remain pending.

'''
 if '## 0.2.22 ' not in s:s=s.replace('# Changelog\n\n','# Changelog\n\n'+entry)
 p.write_text(s,encoding='utf-8');p=ROOT/'README.md';s=p.read_text(encoding='utf-8');line='- `work/output/english-native-0.2.22.iso`: English status badges and separated detailed-roster equipment/status columns. See [layout notes](docs/detailed-roster-layout.txt).\n'
 if line not in s:s=s.replace('- `work/output/english-native-0.2.21.iso`',line+'- `work/output/english-native-0.2.21.iso`',1)
 p.write_text(s,encoding='utf-8')
 (ROOT/'docs/detailed-roster-layout.txt').write_text('''Detailed roster UI — local build 0.2.22

Source: delivered 0.2.21. Three common native status images now read HP,
LOY (Loyalty), and HLTH (Health). Native palettes and 4x font remain.
Equipment: four rows, 15-pixel pitch, labels at x160 and names at x192
relative to the 400x61 card. Text budget208; maximum202.286 among463 fixed
equipment names. Names, item IDs and controls remain unchanged.
Status columns move right to leave space for longer character names.
Four coordinate tables change; no native instructions or script payloads change.
Native ordering, filtering and roster paging remain. Exact coordinates and
actual framebuffers are under work/ui/detailed-roster-0.2.22/.

Build: build_detailed_roster.py and build_iso.py (dry run before --write).
Checks: record_detailed_roster_qa.py --runtime; check_shop_font.py;
all49 translation batches; original asset palettes and unrelated members;
actual status/equipment/selection/simple-view captures in PPSSPP.
Final ISO is byte-identical to the tested qa-roster-0.2.22b.iso.
Full-playthrough and real PSP checks remain pending. No GitHub release.
''',encoding='utf-8')
if __name__=='__main__':main()
